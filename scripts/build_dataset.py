#!/usr/bin/env python3
"""Build the real-complaint part of the Track A dataset (proposal v2, data plan steps 2-5 and 9).

  2. Filter: narratives of 50-400 words from one date window, product names mapped
     with data/product_map.json, exact and near duplicates (MinHash, Jaccard >= 0.9) dropped.
  3. Fix the labels: the top N products by eligible narratives (each needs >= 170),
     each product's 5 most common issues, the rest mapped to "other" -> data/labels.json.
  4. Sample: an equal number of complaints per product (1,350 in total by default).
  5. Privacy pass: mask emails, phone numbers, card/account numbers and SSNs; log counts.
  9. Split with seed 42, stratified by product, and record SHA-256 hashes.

It reads the parquet snapshot in batches and keeps only a fixed-size random candidate
set per product in memory, so it runs on a laptop.

Usage
  python build_dataset.py --data raw/cfpb_mouwiya/data --out data
"""

import argparse
import ast
import codecs
import glob
import hashlib
import json
import os
import re
import warnings
from collections import Counter

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds

MIN_WORDS, MAX_WORDS = 50, 400
COLS = ["date_received", "product", "issue", "sub_issue",
        "consumer_complaint_narrative", "complaint_id"]

# A small set of very common English words. Narratives below MIN_EN_SHARE of these
# among their alphabetic words are treated as non-English and left out.
EN_WORDS = set("""the and to of i in my was that it for on is with have not this they
be as had but at by from or an are their we were been would so you will all
did has them do there which about when what account""".split())
MIN_EN_SHARE = 0.15

PII_PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone": re.compile(r"(?:\+?1[ .-]?)?(?:\(\d{3}\)\s?|\b\d{3}[ .-])\d{3}[ .-]\d{4}\b"),
    "card_or_account": re.compile(r"\b\d(?:[ -]?\d){7,18}\b"),
}


def word_count(arr):
    return pc.list_value_length(pc.utf8_split_whitespace(arr))


def en_share(text):
    toks = re.findall(r"[a-z]+", text.lower())
    toks = [t for t in toks if t != "xxxx"]
    return sum(t in EN_WORDS for t in toks) / len(toks) if toks else 0.0


def shingles(text, n=3):
    w = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(1, len(w) - n + 1))}


BYTES_REPR = re.compile(r"""^b(['"])""")


def unwrap(text):
    """Some narratives in the snapshot are the repr of a Python bytes object, for
    example b'I called ...\\n...' with escaped newlines and UTF-8 bytes. Turn them back
    into plain text. Some lost their closing quote. Returns (text, changed)."""
    t = text.strip()
    m = BYTES_REPR.match(t)
    if not m:
        return text, False
    # a backslash before XXXX is an "invalid escape": Python keeps it and warns, so mute that
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (SyntaxWarning, DeprecationWarning))
        try:
            return ast.literal_eval(t).decode("utf-8", errors="replace"), True
        except (ValueError, SyntaxError):
            body = t[2:-1] if t.endswith(m.group(1)) else t[2:]
            body = re.sub(r"\\+$", lambda s: s.group()[: len(s.group()) // 2 * 2], body)
            raw = codecs.escape_decode(body.encode("utf-8", "backslashreplace"))[0]
            return raw.decode("utf-8", errors="replace"), True


def scrub(text, counts):
    for name, pat in PII_PATTERNS.items():
        text, k = pat.subn("XXXX", text)
        counts[name] += k
    return text


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="folder of parquet files")
    ap.add_argument("--out", default="data")
    ap.add_argument("--since", default="2023-01-01")
    ap.add_argument("--until", default=None, help="inclusive end date, default: end of data")
    ap.add_argument("--product-map", default=None, help="JSON {raw name: label}")
    ap.add_argument("--n-products", type=int, default=10)
    ap.add_argument("--min-per-product", type=int, default=170)
    ap.add_argument("--n-issues", type=int, default=5)
    ap.add_argument("--per-product", type=int, default=135)
    ap.add_argument("--split", default="111,9,15", help="train,val,test per product")
    ap.add_argument("--candidates", type=int, default=1500,
                    help="random candidates kept per product for dedupe and sampling")
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    n_train, n_val, n_test = map(int, a.split.split(","))
    assert n_train + n_val + n_test == a.per_product

    pmap = {}
    if a.product_map:
        with open(a.product_map) as f:
            pmap = json.load(f)["map"]

    since = pd.Timestamp(a.since)
    until = pd.Timestamp(a.until) + pd.Timedelta(days=1) if a.until else None
    files = sorted(glob.glob(os.path.join(a.data, "**", "*.parquet"), recursive=True))

    def batches():
        # The snapshot mixes timestamp[us] and timestamp[us, tz=UTC] across files,
        # so each file gets a filter built for its own date type.
        for f in files:
            d = ds.dataset(f, format="parquet")
            typ = d.schema.field("date_received").type
            lit = lambda ts: pa.scalar(ts.tz_localize("UTC") if typ.tz else ts, typ)
            filt = ds.field("date_received") >= lit(since)
            if until is not None:
                filt &= ds.field("date_received") < lit(until)
            yield from d.to_batches(columns=COLS, filter=filt, batch_size=200_000)

    log = Counter()
    prod_n, issue_n = Counter(), Counter()
    raw_names = Counter()
    hash_key = f"cfpbseed{a.seed:08d}"[:16]
    cand = {}  # product -> DataFrame of the lowest-key candidates

    # ---- pass 1: stream, filter, count, keep random candidates -------------
    for batch in batches():
        log["rows_in_window"] += batch.num_rows
        text = batch.column("consumer_complaint_narrative")
        if not pa.types.is_string(text.type) and not pa.types.is_large_string(text.type):
            # a file whose narrative column holds no text at all is stored as numbers
            assert text.null_count == len(text), text.type
            continue
        has = pc.fill_null(pc.greater(pc.utf8_length(pc.utf8_trim_whitespace(text)), 0), False)
        log["with_text"] += pc.sum(has).as_py() or 0
        b = batch.filter(has)
        if b.num_rows == 0:
            continue
        words = word_count(b.column("consumer_complaint_narrative"))
        ok = pc.and_(pc.greater_equal(words, MIN_WORDS), pc.less_equal(words, MAX_WORDS))
        b = b.filter(ok)
        df = b.to_pandas()
        if df["date_received"].dt.tz is not None:
            df["date_received"] = df["date_received"].dt.tz_convert(None)
        un = df["consumer_complaint_narrative"].map(unwrap)
        changed = un.str[1].to_numpy(dtype=bool)
        if changed.any():
            log["unwrapped_bytes_repr"] += int(changed.sum())
            df["consumer_complaint_narrative"] = un.str[0]
        df["words"] = df["consumer_complaint_narrative"].str.split().str.len()
        # unwrapping can split "word\nword" into two words, so re-check the length
        df = df[df["words"].between(MIN_WORDS, MAX_WORDS)].copy()
        log["eligible_50_400"] += len(df)
        df["product_raw"] = df["product"].fillna("(missing)")
        raw_names.update(df["product_raw"])
        df["product"] = df["product_raw"].map(lambda p: pmap.get(p, p))
        df["issue"] = df["issue"].fillna("(missing)")
        prod_n.update(df["product"])
        issue_n.update(zip(df["product"], df["issue"]))
        df["_key"] = pd.util.hash_pandas_object(df["complaint_id"], index=False,
                                                hash_key=hash_key).to_numpy()
        for prod, g in df.groupby("product"):
            g = pd.concat([cand[prod], g]) if prod in cand else g
            cand[prod] = g.nsmallest(a.candidates, "_key")
        print(f"  {log['rows_in_window']:,} rows in window, {log['eligible_50_400']:,} eligible",
              flush=True)

    # ---- step 3: labels ----------------------------------------------------
    ranked = [p for p, n in prod_n.most_common() if p != "(missing)"]
    chosen = [p for p in ranked if prod_n[p] >= a.min_per_product][:a.n_products]
    if len(chosen) < a.n_products:
        print(f"WARNING: only {len(chosen)} products have >= {a.min_per_product} eligible")
    labels = {"products": []}
    for p in chosen:
        iss = sorted(((n, i) for (pp, i), n in issue_n.items() if pp == p), reverse=True)
        top = [i for _, i in iss[:a.n_issues]]
        tot = sum(n for n, _ in iss)
        labels["products"].append({
            "product": p,
            "issues": top + ["other"],
            "eligible_in_window": prod_n[p],
            "top_issue_share": round(sum(n for n, _ in iss[:a.n_issues]) / tot, 4),
        })
    top_issues = {d["product"]: set(d["issues"][:-1]) for d in labels["products"]}

    # ---- pass 2: dedupe, language, sample ----------------------------------
    from datasketch import MinHash, MinHashLSH
    pool = pd.concat([cand[p] for p in chosen]).sort_values("_key")
    log["candidates"] = len(pool)
    pool["_norm"] = pool["consumer_complaint_narrative"].str.strip().str.lower()
    before = len(pool)
    pool = pool.drop_duplicates("_norm")
    log["dropped_exact_duplicate"] = before - len(pool)

    pool["_en"] = pool["consumer_complaint_narrative"].map(en_share)
    log["dropped_non_english"] = int((pool["_en"] < MIN_EN_SHARE).sum())
    pool = pool[pool["_en"] >= MIN_EN_SHARE]

    lsh = MinHashLSH(threshold=0.9, num_perm=128)
    keep = []
    for cid, t in zip(pool["complaint_id"], pool["consumer_complaint_narrative"]):
        m = MinHash(num_perm=128, seed=a.seed)
        for s in shingles(t):
            m.update(s.encode())
        if lsh.query(m):
            keep.append(False)
            continue
        lsh.insert(str(cid), m)
        keep.append(True)
    log["dropped_near_duplicate"] = int(len(keep) - sum(keep))
    pool = pool[np.array(keep)]

    rng = np.random.default_rng(a.seed)
    parts, pii = [], Counter()
    for p in chosen:
        g = pool[pool["product"] == p].head(a.per_product).copy()
        if len(g) < a.per_product:
            raise SystemExit(f"{p}: only {len(g)} usable candidates; raise --candidates")
        g["consumer_complaint_narrative"] = [scrub(t, pii) for t in g["consumer_complaint_narrative"]]
        order = rng.permutation(len(g))
        split = np.empty(len(g), dtype=object)
        split[order[:n_test]] = "test"
        split[order[n_test:n_test + n_val]] = "val"
        split[order[n_test + n_val:]] = "train"
        g["split"] = split
        parts.append(g)
    sample = pd.concat(parts)
    sample["issue_raw"] = sample["issue"]
    sample["issue"] = [i if i in top_issues[p] else "other"
                       for p, i in zip(sample["product"], sample["issue"])]

    # ---- write -------------------------------------------------------------
    out_cols = ["complaint_id", "date_received", "product", "issue", "product_raw",
                "issue_raw", "sub_issue", "words", "narrative"]
    sample = sample.rename(columns={"consumer_complaint_narrative": "narrative"})
    sample["date_received"] = sample["date_received"].dt.strftime("%Y-%m-%d")
    sample["words"] = sample["words"].astype(int)
    hashes = {}
    for s in ["train", "val", "test"]:
        part = sample[sample["split"] == s].sort_values(["product", "complaint_id"])
        path = os.path.join(a.out, f"real_{s}.jsonl")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in part[out_cols].to_dict("records"):
                # missing values (sub_issue) become null; pandas 3 gives NaN, which is not JSON
                r = {k: None if isinstance(v, float) and v != v else v for k, v in r.items()}
                f.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n")
        hashes[os.path.basename(path)] = {"rows": len(part), "sha256": sha256(path)}

    labels["out_of_scope"] = "out_of_scope"
    labels["window"] = {"since": a.since, "until": a.until or "end of snapshot"}
    with open(os.path.join(a.out, "labels.json"), "w", encoding="utf-8") as f:
        json.dump(labels, f, indent=2, ensure_ascii=False)

    issue_mix = (sample.groupby(["product", "issue"]).size()
                 .rename("n").reset_index().to_dict("records"))
    build = {
        "args": vars(a),
        "counts": dict(log),
        "pii_masked": dict(pii),
        "products_chosen": chosen,
        "product_counts_eligible": dict(prod_n.most_common()),
        "raw_product_names_eligible": dict(raw_names.most_common()),
        "sample_rows": len(sample),
        "sample_other_share": round(float((sample["issue"] == "other").mean()), 4),
        "sample_issue_mix": issue_mix,
        "date_range_sample": [sample["date_received"].min(), sample["date_received"].max()],
        "files": hashes,
    }
    with open(os.path.join(a.out, "build_log.json"), "w", encoding="utf-8") as f:
        json.dump(build, f, indent=2, ensure_ascii=False, default=str)
    print(json.dumps({k: build[k] for k in ["counts", "pii_masked", "products_chosen",
                                             "sample_other_share", "files"]}, indent=2))


if __name__ == "__main__":
    main()
