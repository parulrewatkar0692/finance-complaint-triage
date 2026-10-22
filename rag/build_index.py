#!/usr/bin/env python3
"""Build the first search index (proposal v2, data plan step 6).

Fixed Week 1 choices: bge-small-en-v1.5, one chunk per whole document (title + answer,
truncated at the model's 512 tokens), cosine similarity in a FAISS flat index.
Indexed: documents mapped to one of our 10 products, plus cross-product "general" ones
(fraud, scams, identity theft).

Usage
  python rag/build_index.py build
  python rag/build_index.py check     # product-match proxy on the validation complaints
"""

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(HERE, "docs", "ask_cfpb.jsonl")
IDX_DIR = os.path.join(HERE, "index")
MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def load_docs():
    with open(DOCS, encoding="utf-8") as f:
        return [d for d in map(json.loads, f) if d["products"]]


def model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MODEL, device="cpu")


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def build():
    import faiss
    docs = load_docs()
    m = model()
    emb = m.encode([d["title"] + "\n" + d["text"] for d in docs], batch_size=32,
                   normalize_embeddings=True, show_progress_bar=True).astype(np.float32)
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(emb)
    os.makedirs(IDX_DIR, exist_ok=True)
    faiss.write_index(index, os.path.join(IDX_DIR, "first_index.faiss"))
    with open(os.path.join(IDX_DIR, "doc_ids.json"), "w", encoding="utf-8") as f:
        json.dump([d["doc_id"] for d in docs], f)
    truncated = sum(len(m.tokenizer(d["title"] + "\n" + d["text"])["input_ids"]) > 512
                    for d in docs)
    meta = {
        "model": MODEL, "chunking": "whole document (title + answer)",
        "max_tokens": 512, "docs_truncated_at_512": truncated,
        "similarity": "cosine (normalized embeddings, IndexFlatIP)",
        "query_prefix": QUERY_PREFIX, "documents": len(docs),
        "docs_sha256": sha256(DOCS),
        "per_product": Counter(p for d in docs for p in d["products"]),
    }
    with open(os.path.join(IDX_DIR, "index_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    print(json.dumps(meta, indent=2))


def search(m, index, ids, texts, k):
    q = m.encode([QUERY_PREFIX + t for t in texts], batch_size=16,
                 normalize_embeddings=True).astype(np.float32)
    _, I = index.search(q, k)
    return [[ids[i] for i in row] for row in I]


def check():
    """Not the 40 hand-labelled search pairs (Week 2): a cheap proxy on validation only.
    A hit means at least one of the top k documents belongs to the complaint's product."""
    import faiss
    docs = {d["doc_id"]: d for d in load_docs()}
    index = faiss.read_index(os.path.join(IDX_DIR, "first_index.faiss"))
    ids = json.load(open(os.path.join(IDX_DIR, "doc_ids.json")))
    with open(os.path.join(ROOT, "data", "real_val.jsonl"), encoding="utf-8") as f:
        val = [json.loads(l) for l in f]
    m = model()
    top = search(m, index, ids, [r["narrative"] for r in val], 5)
    hits = defaultdict(lambda: Counter())
    for r, t in zip(val, top):
        for k in (1, 3, 5):
            hits[r["product"]][k] += any(r["product"] in docs[i]["products"] for i in t[:k])
        hits[r["product"]]["n"] += 1
    rows = {p: {f"@{k}": round(h[k] / h["n"], 2) for k in (1, 3, 5)} for p, h in hits.items()}
    tot = {f"@{k}": round(sum(h[k] for h in hits.values()) / len(val), 3) for k in (1, 3, 5)}
    out = {"set": "real_val.jsonl", "n": len(val), "product_match": tot, "by_product": rows,
           "examples": [{"product": r["product"], "issue": r["issue"],
                         "complaint_start": r["narrative"][:200],
                         "top3": [f'{i}: {docs[i]["title"]}' for i in t[:3]]}
                        for r, t in list(zip(val, top))[::9]]}
    with open(os.path.join(IDX_DIR, "check_val.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: out[k] for k in ["n", "product_match", "by_product"]}, indent=2))


if __name__ == "__main__":
    {"build": build, "check": check}[sys.argv[1]]()
