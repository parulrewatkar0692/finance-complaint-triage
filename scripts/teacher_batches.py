#!/usr/bin/env python3
"""Show train and validation complaints to the teacher in fixed batches (data plan step 7).

Usage
  python scripts/teacher_batches.py status      # which batches have replies
  python scripts/teacher_batches.py show 3      # print batch 3 for the teacher to answer

The order is fixed (train then val, each sorted by product and complaint id), so batch numbers
never change. Test complaints are never shown.
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH = 30
PASSAGE_PREVIEW = 35   # words of each passage shown to the teacher
MAX_COMPLAINT = 260    # words of the complaint shown (longer ones are cut, marked with ...)


def load():
    rows = []
    for split in ["train", "val"]:
        with open(os.path.join(ROOT, "data", f"real_{split}.jsonl"), encoding="utf-8") as f:
            rows += [dict(json.loads(l), split=split) for l in f]
    with open(os.path.join(ROOT, "data", "passages.jsonl"), encoding="utf-8") as f:
        pas = {r["complaint_id"]: r["passages"] for r in map(json.loads, f)}
    for r in rows:
        r["passages"] = pas[r["complaint_id"]]
    return rows


def batch_path(n):
    return os.path.join(ROOT, "data", "teacher", f"batch_{n:02d}.jsonl")


def main():
    rows = load()
    n_batches = (len(rows) + BATCH - 1) // BATCH
    if sys.argv[1] == "status":
        done = [n for n in range(n_batches) if os.path.exists(batch_path(n))]
        print(f"{len(rows)} complaints, {n_batches} batches; done: {len(done)}; "
              f"next: {next((n for n in range(n_batches) if n not in done), None)}")
        return
    n = int(sys.argv[2])
    for r in rows[n * BATCH:(n + 1) * BATCH]:
        w = r["narrative"].split()
        text = " ".join(w[:MAX_COMPLAINT]) + (" ..." if len(w) > MAX_COMPLAINT else "")
        print(f"### {r['complaint_id']} | {r['product']} | {r['issue']}")
        print(text)
        for p in r["passages"]:
            pw = p["text"].split()
            print(f"  [{p['doc_id']}] {p['title']} :: {' '.join(pw[:PASSAGE_PREVIEW])}")
        print()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
