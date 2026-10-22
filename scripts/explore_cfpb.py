#!/usr/bin/env python3
"""Explore the CFPB consumer complaint data for the Track A capstone.

Answers, with real counts:
  1. How big is the data, and which dates does it cover?
  2. How many complaints actually have complaint text (the model's input)?
  3. Which labels (product, issue) exist, and did their names change over time?
  4. How long are the complaints, and how much text is masked (XXXX)?
  5. Are there duplicate complaints?
  6. Is there enough clean data per product to build our dataset?

It reads the data in batches, so it runs on a laptop with about 8 GB of RAM.

Usage
  pip install pandas pyarrow huggingface_hub

  # Download the Hugging Face copy (about 1 GB) and explore it:
  python explore_cfpb.py --download --out report

  # Or point at files you already have (a folder of .parquet files, or one CSV,
  # such as an older complaints.csv from the CFPB website):
  python explore_cfpb.py --data path/to/folder_or_file --out report

  # Optional: choose the date window used for the feasibility check:
  python explore_cfpb.py --data ... --since 2023-01-01 --until 2026-08-13

Outputs (in --out)
  report.md               the summary to read first
  *.csv                   the full tables behind each section
  samples.csv             a few eligible complaints per product, to read by eye
"""

import argparse
import glob
import hashlib
import os
import sys
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

HF_REPO = "Mouwiya/cfpb-consumer-complaints"

# Column names used in this script. CFPB CSV headers are mapped onto them.
COLUMNS = [
    "date_received", "product", "sub_product", "issue", "sub_issue",
    "consumer_complaint_narrative", "company_response_to_consumer",
    "timely_response", "complaint_id",
]
CSV_HEADER_MAP = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Consumer complaint narrative": "consumer_complaint_narrative",
    "Company response to consumer": "company_response_to_consumer",
    "Timely response?": "timely_response",
    "Complaint ID": "complaint_id",
}

LENGTH_BINS = [0, 20, 50, 100, 200, 400, 800, 10**9]
LENGTH_LABELS = ["<20", "20-49", "50-99", "100-199", "200-399", "400-799", "800+"]
MIN_WORDS, MAX_WORDS = 50, 400       # the POC's eligible complaint length
SAMPLES_PER_PRODUCT = 5
TARGET_PER_PRODUCT = 150             # roughly what the POC needs per product


# ----------------------------------------------------------------------------
# Reading
# ----------------------------------------------------------------------------

def download(target_dir):
    from huggingface_hub import snapshot_download
    print(f"Downloading {HF_REPO} (about 1 GB) ...", flush=True)
    return snapshot_download(
        repo_id=HF_REPO, repo_type="dataset",
        allow_patterns=["*.parquet"], local_dir=target_dir,
    )


def iter_batches(path, batch_rows=250_000):
    """Yield pandas DataFrames with the COLUMNS above, from parquet or CSV."""
    if os.path.isdir(path):
        files = sorted(glob.glob(os.path.join(path, "**", "*.parquet"), recursive=True))
        csvs = sorted(glob.glob(os.path.join(path, "**", "*.csv"), recursive=True))
        if not files and len(csvs) == 1:
            path, files = csvs[0], []
        elif not files:
            sys.exit(f"No .parquet files (or a single .csv) found under {path}")
    else:
        files = [path] if path.endswith(".parquet") else []

    if files:
        import pyarrow.parquet as pq
        for i, f in enumerate(files, 1):
            pf = pq.ParquetFile(f)
            cols = [c for c in COLUMNS if c in pf.schema_arrow.names]
            print(f"  file {i}/{len(files)}: {os.path.basename(f)}", flush=True)
            for batch in pf.iter_batches(batch_size=batch_rows, columns=cols):
                yield batch.to_pandas()
        return

    # CSV (e.g. complaints.csv from the CFPB site, or our test file)
    head = pd.read_csv(path, nrows=0).columns
    rename = {c: CSV_HEADER_MAP.get(c, c) for c in head}
    usecols = [c for c in head if rename[c] in COLUMNS]
    for chunk in pd.read_csv(path, usecols=usecols, chunksize=batch_rows,
                             dtype=str, keep_default_na=True):
        yield chunk.rename(columns=rename)


# ----------------------------------------------------------------------------
# Counting
# ----------------------------------------------------------------------------

class Stats:
    def __init__(self, since, until):
        self.since, self.until = since, until
        self.rows = 0
        self.min_date = None
        self.max_date = None
        self.year_all = Counter()
        self.year_text = Counter()
        self.product_year_text = Counter()        # (product, year) -> n with text
        self.product_text = Counter()
        self.issue_text = Counter()               # (product, issue) -> n with text
        self.response_text = Counter()
        self.length_bins = Counter()
        self.masked = 0
        self.text_rows = 0
        self.ids = []
        self.text_hashes = []
        # feasibility window
        self.elig_product = Counter()
        self.elig_issue = Counter()
        self.elig_hashes = []
        self.samples = defaultdict(list)

    def add(self, df):
        n = len(df)
        self.rows += n

        # Parquet text columns arrive as Arrow-backed strings whose missing values
        # behave differently from plain Python. Convert them to plain objects,
        # with None for missing, so every step below sees the same thing.
        for c in ["product", "sub_product", "issue", "sub_issue",
                  "consumer_complaint_narrative", "company_response_to_consumer",
                  "timely_response", "complaint_id"]:
            col = df[c].astype(object)
            df[c] = col.where(pd.notna(col), None)

        dates = pd.to_datetime(df["date_received"], errors="coerce", utc=True)
        if dates.notna().any():
            lo, hi = dates.min(), dates.max()
            self.min_date = lo if self.min_date is None else min(self.min_date, lo)
            self.max_date = hi if self.max_date is None else max(self.max_date, hi)
        years = dates.dt.year.map(lambda y: "unknown" if pd.isna(y) else str(int(y)))
        self.year_all.update(years)

        if "complaint_id" in df:
            ids = pd.to_numeric(df["complaint_id"], errors="coerce").dropna()
            self.ids.append(ids.to_numpy(dtype=np.int64))

        text = df["consumer_complaint_narrative"]
        has = text.map(lambda v: isinstance(v, str) and v.strip() != "")
        if not has.any():
            return
        t = df.loc[has].copy()
        t["_year"] = years[has]
        t["_date"] = dates[has]
        t["product"] = t["product"].fillna("(missing)")
        t["issue"] = t["issue"].fillna("(missing)")
        body = t["consumer_complaint_narrative"].astype(str)
        words = body.str.split().str.len()

        self.text_rows += len(t)
        self.year_text.update(t["_year"])
        self.product_text.update(t["product"])
        self.product_year_text.update(zip(t["product"], t["_year"]))
        self.issue_text.update(zip(t["product"], t["issue"]))
        if "company_response_to_consumer" in t:
            self.response_text.update(t["company_response_to_consumer"].fillna("(missing)"))
        self.length_bins.update(pd.cut(words, LENGTH_BINS, right=False,
                                       labels=LENGTH_LABELS).astype(str))
        self.masked += int(body.str.contains("XXXX", regex=False).sum())
        h = pd.util.hash_pandas_object(body.str.strip().str.lower(), index=False)
        self.text_hashes.append(h.to_numpy())

        # Feasibility: inside the date window and 50-400 words
        ok = words.between(MIN_WORDS, MAX_WORDS)
        if self.since is not None:
            ok &= t["_date"] >= self.since
        if self.until is not None:
            ok &= t["_date"] <= self.until
        e = t.loc[ok]
        if len(e):
            self.elig_product.update(e["product"])
            self.elig_issue.update(zip(e["product"], e["issue"]))
            self.elig_hashes.append(h[ok.to_numpy()].to_numpy())
            for prod, grp in e.groupby("product"):
                need = SAMPLES_PER_PRODUCT - len(self.samples[prod])
                if need <= 0:
                    continue
                # deterministic pseudo-random pick, so reruns give the same samples
                key = grp["complaint_id"].map(
                    lambda v: hashlib.md5(str(v).encode()).hexdigest())
                pick = grp.loc[key.sort_values().index[:need]]
                for _, r in pick.iterrows():
                    self.samples[prod].append({
                        "complaint_id": r.get("complaint_id"),
                        "date_received": str(r["_date"])[:10],
                        "product": prod,
                        "issue": r["issue"],
                        "sub_issue": r.get("sub_issue"),
                        "words": len(str(r["consumer_complaint_narrative"]).split()),
                        "narrative": r["consumer_complaint_narrative"],
                    })


# ----------------------------------------------------------------------------
# Report
# ----------------------------------------------------------------------------

def pct(a, b):
    return f"{100 * a / b:.1f}%" if b else "n/a"


def md_table(df, max_rows=None):
    if max_rows is not None:
        df = df.head(max_rows)
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(
            f"{v:,}" if isinstance(v, (int, np.integer)) else str(v) for v in r) + " |")
    return "\n".join(lines)


def unique_count(chunks):
    if not chunks:
        return 0, 0
    a = np.concatenate(chunks)
    u = np.unique(a)
    return len(a), len(u)


def write_report(s, out):
    os.makedirs(out, exist_ok=True)
    R = []
    add = R.append

    add("# CFPB complaint data: exploration report\n")
    add(f"Window for the feasibility check: {s.since.date() if s.since is not None else 'start'}"
        f" to {s.until.date() if s.until is not None else 'end'}; "
        f"eligible = has text and {MIN_WORDS}-{MAX_WORDS} words.\n")

    # 1. Size
    add("## 1. Size and dates\n")
    add(f"- Rows: {s.rows:,}")
    add(f"- Dates: {s.min_date.date() if s.min_date is not None else '?'}"
        f" to {s.max_date.date() if s.max_date is not None else '?'}")
    n_ids, n_uid = unique_count(s.ids)
    add(f"- Complaint IDs: {n_ids:,} present, {n_uid:,} unique, "
        f"{n_ids - n_uid:,} repeated ({pct(n_ids - n_uid, n_ids)})\n")

    # 2. Text coverage
    add("## 2. How many complaints have text (the model's input)\n")
    add(f"- With text: {s.text_rows:,} of {s.rows:,} ({pct(s.text_rows, s.rows)})")
    n_t, n_ut = unique_count(s.text_hashes)
    add(f"- Identical texts: {n_t - n_ut:,} rows repeat an earlier text "
        f"({pct(n_t - n_ut, n_t)})")
    add(f"- Texts containing XXXX masks: {s.masked:,} ({pct(s.masked, s.text_rows)})\n")
    yr = pd.DataFrame({"year": sorted(s.year_all)})
    yr["rows"] = yr["year"].map(s.year_all).astype(int)
    yr["with_text"] = yr["year"].map(s.year_text).fillna(0).astype(int)
    yr["share_with_text"] = [pct(a, b) for a, b in zip(yr["with_text"], yr["rows"])]
    yr.to_csv(os.path.join(out, "by_year.csv"), index=False)
    add(md_table(yr) + "\n")

    # 3. Length
    add("## 3. Complaint length (words, complaints with text)\n")
    ln = pd.DataFrame({"words": LENGTH_LABELS})
    ln["complaints"] = ln["words"].map(s.length_bins).fillna(0).astype(int)
    ln["share"] = [pct(v, s.text_rows) for v in ln["complaints"]]
    ln.to_csv(os.path.join(out, "length.csv"), index=False)
    add(md_table(ln) + "\n")

    # 4. Labels
    add("## 4. Product labels (complaints with text)\n")
    add("Look for near-duplicate names: the CFPB renamed several products over the years, "
        "so the same kind of complaint can carry different labels in different years.\n")
    pr = pd.DataFrame(s.product_text.most_common(), columns=["product", "with_text"])
    pr["share"] = [pct(v, s.text_rows) for v in pr["with_text"]]
    years = sorted({y for (_, y) in s.product_year_text})
    pr["years_seen"] = [
        f"{min(ys)}-{max(ys)}" if ys else "" for ys in
        ([y for (p2, y) in s.product_year_text if p2 == p and y != 'unknown'] for p in pr["product"])]
    pr.to_csv(os.path.join(out, "products.csv"), index=False)
    add(md_table(pr) + "\n")
    py = pd.DataFrame(
        [(p, y, n) for (p, y), n in s.product_year_text.items()],
        columns=["product", "year", "with_text"])
    if len(py):
        py.pivot_table(index="product", columns="year", values="with_text",
                       fill_value=0, aggfunc="sum").to_csv(os.path.join(out, "product_by_year.csv"))
    iss = pd.DataFrame([(p, i, n) for (p, i), n in s.issue_text.items()],
                       columns=["product", "issue", "with_text"]).sort_values(
        ["product", "with_text"], ascending=[True, False])
    iss.to_csv(os.path.join(out, "issues.csv"), index=False)
    add(f"- Distinct issue labels: {iss['issue'].nunique():,} "
        f"across {iss['product'].nunique():,} products (full list in issues.csv)\n")

    # 5. Outcome labels
    add("## 5. Company response to consumer (complaints with text)\n")
    rs = pd.DataFrame(s.response_text.most_common(), columns=["response", "with_text"])
    rs["share"] = [pct(v, s.text_rows) for v in rs["with_text"]]
    rs.to_csv(os.path.join(out, "responses.csv"), index=False)
    add(md_table(rs) + "\n")

    # 6. Feasibility
    add("## 6. Feasibility for the POC\n")
    total_e = sum(s.elig_product.values())
    n_e, n_ue = unique_count(s.elig_hashes)
    add(f"- Eligible complaints: {total_e:,} (after removing identical texts: about {n_ue:,})")
    fe = pd.DataFrame(s.elig_product.most_common(), columns=["product", "eligible"])
    fe["share"] = [pct(v, total_e) for v in fe["eligible"]]
    top5 = []
    for p in fe["product"]:
        ii = sorted(((n, i) for (pp, i), n in s.elig_issue.items() if pp == p), reverse=True)
        tot = sum(n for n, _ in ii)
        top5.append(pct(sum(n for n, _ in ii[:5]), tot))
    fe["top5_issue_share"] = top5
    fe["enough_for_150"] = ["yes" if v >= TARGET_PER_PRODUCT * 3 else "tight"
                            if v >= TARGET_PER_PRODUCT else "no" for v in fe["eligible"]]
    fe.to_csv(os.path.join(out, "feasibility.csv"), index=False)
    add("\n`top5_issue_share` = how much of each product the 5 most common issues cover. "
        "`enough_for_150`: yes = at least 450 eligible, tight = 150-449, no = under 150.\n")
    add(md_table(fe) + "\n")

    rows = [r for prod in s.samples for r in s.samples[prod]]
    pd.DataFrame(rows).to_csv(os.path.join(out, "samples.csv"), index=False)
    add(f"Read samples.csv ({len(rows)} complaints) before trusting the labels.\n")

    with open(os.path.join(out, "report.md"), "w") as f:
        f.write("\n".join(R))
    print(f"\nDone. Read {os.path.join(out, 'report.md')}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", help="folder of .parquet files, a .parquet file, or a .csv")
    ap.add_argument("--download", action="store_true", help=f"download {HF_REPO} first")
    ap.add_argument("--download-dir", default="cfpb_data")
    ap.add_argument("--since", default="2023-01-01", help="feasibility window start (YYYY-MM-DD)")
    ap.add_argument("--until", default=None, help="feasibility window end (YYYY-MM-DD)")
    ap.add_argument("--max-rows", type=int, default=None, help="stop early, for a quick test")
    ap.add_argument("--out", default="report")
    a = ap.parse_args()

    path = download(a.download_dir) if a.download else a.data
    if not path:
        ap.error("give --data PATH or --download")

    since = pd.Timestamp(a.since, tz="UTC") if a.since else None
    until = pd.Timestamp(a.until, tz="UTC") + pd.Timedelta(days=1) if a.until else None
    s = Stats(since, until)
    for df in iter_batches(path):
        if a.max_rows is not None and s.rows >= a.max_rows:
            break
        for c in COLUMNS:
            if c not in df:
                df[c] = None
        s.add(df)
        print(f"  {s.rows:,} rows read", flush=True)
    write_report(s, a.out)


if __name__ == "__main__":
    main()
