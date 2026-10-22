#!/usr/bin/env python3
"""Retrieve the top 3 Ask CFPB passages for every real complaint (data plan step 7 input).

Uses the Week 1 first index (rag/index/first_index.faiss, bge-small-en-v1.5, whole document per
chunk). Each passage is the document title plus the start of its answer, cut so that the three
passages together stay within about 600 tokens (the proposal's cap).

Usage
  python scripts/retrieve_passages.py          # writes data/passages.jsonl
  python scripts/retrieve_passages.py oos      # writes data/passages_oos.jsonl (out-of-scope set)
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "rag"))
import build_index as B  # noqa: E402

TOP_K = 3
PASSAGE_WORDS = 130  # 3 x ~130 words + titles is roughly 600 tokens


def passage(doc):
    words = doc["text"].split()
    body = " ".join(words[:PASSAGE_WORDS]) + (" ..." if len(words) > PASSAGE_WORDS else "")
    return {"doc_id": doc["doc_id"], "title": doc["title"], "text": body}


def main():
    import faiss
    docs = {d["doc_id"]: d for d in B.load_docs()}
    index = faiss.read_index(os.path.join(ROOT, "rag", "index", "first_index.faiss"))
    with open(os.path.join(ROOT, "rag", "index", "doc_ids.json")) as f:
        ids = json.load(f)
    rows = []
    if sys.argv[1:] == ["oos"]:
        sys.path.insert(0, os.path.join(ROOT, "data"))
        import out_of_scope_source as O
        rows = [(r["split"], r) for r in O.examples()]
        out = os.path.join(ROOT, "data", "passages_oos.jsonl")
    else:
        for split in ["train", "val", "test"]:
            with open(os.path.join(ROOT, "data", f"real_{split}.jsonl"), encoding="utf-8") as f:
                rows += [(split, json.loads(l)) for l in f]
        out = os.path.join(ROOT, "data", "passages.jsonl")
    m = B.model()
    top = B.search(m, index, ids, [r["narrative"] for _, r in rows], TOP_K)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for (split, r), t in zip(rows, top):
            f.write(json.dumps({"complaint_id": r["complaint_id"], "split": split,
                                "passages": [passage(docs[i]) for i in t]},
                               ensure_ascii=False) + "\n")
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
