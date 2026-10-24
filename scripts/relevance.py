#!/usr/bin/env python3
"""Relevance labels for retrieval and citations (grounding plan, part 2).

For every validation and test complaint, the pages to judge are the union of the first
retriever's top 3 (data/passages.jsonl, data/passages_oos.jsonl) and the second retriever's top 5
(data/passages_v2.jsonl). They are listed in a random order with no hint of which retriever found
them, so the labels are fair to both.

A page is relevant (1) when it gives guidance that fits this complaint: a next step the customer
could take, or an explanation of the rule or process the complaint is about. A page that only
shares a topic word is not relevant (0). Out-of-scope messages normally have no relevant page.

Labels are kept in data/relevance/labels_{val,test}.jsonl, one line per (complaint, page):
  {"complaint_id", "doc_id", "relevant": 0 or 1, "annotator"}
These files hold no complaint text, so they are committed. The sheets used to label them hold
the complaint text and are git-ignored.

Usage
  python scripts/relevance.py sheet            # write data/relevance/sheet_{val,test}.csv
  python scripts/relevance.py import FILE NAME # read the "relevant" column of a filled sheet
  python scripts/relevance.py eval [val|test]  # compare the two retrievers on the labels
"""

import csv
import json
import os
import random
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")
REL = os.path.join(DATA, "relevance")
sys.path.insert(0, DATA)
SEED = 42


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def complaints(split):
    import out_of_scope_source as O
    rows = [dict(r, source="real") for r in read_jsonl(os.path.join(DATA, f"real_{split}.jsonl"))]
    rows += [dict(r, product="out_of_scope", issue="other", source="out_of_scope")
             for r in O.examples() if r["split"] == split]
    return rows


def retrieved():
    """{complaint_id: {"v1": [doc ids], "v2": [(doc id, score)], "text": {doc id: passage}}}"""
    out = defaultdict(lambda: {"v1": [], "v2": [], "text": {}, "title": {}})
    for name in ["passages.jsonl", "passages_oos.jsonl"]:
        for r in read_jsonl(os.path.join(DATA, name)):
            for p in r["passages"]:
                out[r["complaint_id"]]["v1"].append(p["doc_id"])
                out[r["complaint_id"]]["text"].setdefault(p["doc_id"], p["text"])
                out[r["complaint_id"]]["title"][p["doc_id"]] = p["title"]
    for r in read_jsonl(os.path.join(DATA, "passages_v2.jsonl")):
        for p in r["passages"]:
            out[r["complaint_id"]]["v2"].append((p["doc_id"], p["score"]))
            out[r["complaint_id"]]["text"][p["doc_id"]] = p["text"]   # prefer the matching chunk
            out[r["complaint_id"]]["title"][p["doc_id"]] = p["title"]
    return out


def pool(cid, ret):
    docs = list(dict.fromkeys(ret[cid]["v1"] + [d for d, _ in ret[cid]["v2"]]))
    random.Random(f"{SEED}-{cid}").shuffle(docs)
    return docs


def sheet():
    ret = retrieved()
    os.makedirs(REL, exist_ok=True)
    for split in ["val", "test"]:
        path = os.path.join(REL, f"sheet_{split}.csv")
        n = 0
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["complaint_id", "product", "issue", "complaint", "doc_id", "page_title",
                        "passage", "relevant", "notes"])
            for r in complaints(split):
                cid = r["complaint_id"]
                for d in pool(cid, ret):
                    w.writerow([cid, r["product"], r["issue"], r["narrative"], d,
                                ret[cid]["title"][d], ret[cid]["text"][d], "", ""])
                    n += 1
        print(f"{path}: {n} pages to judge")


def label_path(split):
    return os.path.join(REL, f"labels_{split}.jsonl")


def load_labels(split):
    labels = {}
    if os.path.exists(label_path(split)):
        for r in read_jsonl(label_path(split)):
            labels[(r["complaint_id"], r["doc_id"])] = r
    return labels


def save_labels(split, labels):
    os.makedirs(REL, exist_ok=True)
    with open(label_path(split), "w", encoding="utf-8", newline="\n") as f:
        for k in sorted(labels):
            f.write(json.dumps(labels[k], ensure_ascii=False) + "\n")


def import_sheet(path, annotator):
    """Human labels replace any earlier label for the same (complaint, page)."""
    split = "test" if "test" in os.path.basename(path) else "val"
    labels = load_labels(split)
    n = 0
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            v = row["relevant"].strip()
            if v in ("0", "1"):
                labels[(row["complaint_id"], row["doc_id"])] = {
                    "complaint_id": row["complaint_id"], "doc_id": row["doc_id"],
                    "relevant": int(v), "annotator": annotator}
                n += 1
    save_labels(split, labels)
    print(f"imported {n} labels from {path} into {label_path(split)}")


def evaluate(split, thresholds=(None, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5)):
    """Hit@3: a relevant page is among the pages shown. Precision: share of shown pages that are
    relevant. None-rate: complaints shown no page. Reported for real and out-of-scope rows."""
    labels = load_labels(split)
    ret = retrieved()
    rows = complaints(split)
    judged = [r for r in rows if all((r["complaint_id"], d) in labels
                                     for d in pool(r["complaint_id"], ret))]
    print(f"{split}: {len(judged)} of {len(rows)} complaints fully labelled")
    rel = lambda cid, d: labels[(cid, d)]["relevant"]  # noqa: E731
    has_any = [r for r in judged if r["source"] == "real"
               and any(rel(r["complaint_id"], d) for d in pool(r["complaint_id"], ret))]
    print(f"real complaints with at least one relevant page in the pool: {len(has_any)}")

    def report(name, shown_fn):
        out = {}
        for src in ["real", "out_of_scope"]:
            rs = [r for r in judged if r["source"] == src]
            if not rs:
                continue
            shown = [shown_fn(r["complaint_id"]) for r in rs]
            hits = sum(any(rel(r["complaint_id"], d) for d in s) for r, s in zip(rs, shown))
            n_shown = sum(len(s) for s in shown)
            good = sum(rel(r["complaint_id"], d) for r, s in zip(rs, shown) for d in s)
            out[src] = {"n": len(rs), "hit": round(hits / len(rs), 3),
                        "precision": round(good / n_shown, 3) if n_shown else None,
                        "avg_shown": round(n_shown / len(rs), 2),
                        "none_shown": round(sum(not s for s in shown) / len(rs), 3)}
        print(f"{name:28s} {json.dumps(out)}")
        return out

    results = {"v1 top3": report("v1 (first index) top 3", lambda c: ret[c]["v1"][:3])}
    for t in thresholds:
        name = "v2 top3" if t is None else f"v2 top3, score >= {t}"
        results[name] = report(name, lambda c, t=t: [d for d, s in ret[c]["v2"][:3]
                                                     if t is None or s >= t])
    return results


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "sheet":
        sheet()
    elif cmd == "import":
        import_sheet(sys.argv[2], sys.argv[3])
    elif cmd == "eval":
        evaluate(sys.argv[2] if len(sys.argv) > 2 else "val")
