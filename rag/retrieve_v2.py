#!/usr/bin/env python3
"""Second retriever: chunks, hybrid search and a reranker (grounding plan, part 1).

What changed from the first index (rag/build_index.py):
  - Chunks: each Ask CFPB page is split into passages of at most CHUNK_WORDS words on sentence
    boundaries, so the passage shown is the part of the page that matches, not its first words.
  - Hybrid candidates: dense search (bge-small-en-v1.5 on chunks) and keyword search (BM25 on
    chunks) are merged with reciprocal rank fusion; the best chunk per page is kept.
  - Reranker: BAAI/bge-reranker-base scores each (complaint, chunk) pair and orders the
    candidates. The score lets build_sft.py drop weak matches (see RERANK_MIN there).

Output: data/passages_v2.jsonl, one line per complaint (real and out of scope), with the top
TOP_K pages: {doc_id, title, text (the chunk), score (reranker relevance, 0 to 1)}.

Usage
  python rag/retrieve_v2.py            # all 1,470 complaints (minutes on a GPU, hours on a CPU)
  python rag/retrieve_v2.py --limit 5  # quick check, prints the results
"""

import argparse
import json
import math
import os
import re
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "data"))
import build_index as B  # noqa: E402

CHUNK_WORDS = 120
N_DENSE = N_BM25 = 40       # candidates from each search
N_RERANK = 15               # pages (best chunk each) sent to the reranker
TOP_K = 5                   # pages kept per complaint
RRF_K = 60
RERANKER = "BAAI/bge-reranker-base"
OUT = os.path.join(ROOT, "data", "passages_v2.jsonl")

STOP = set("""a an and are as at be been but by can do does for from had has have he her his i if
in into is it its me my no not of on or our she so that the their them then there they this to
was we were what when which who will with you your xxxx xx year""".split())


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP and len(w) > 1]


# Sentences about filing a CFPB complaint are boilerplate, not guidance, and match every
# complaint ("I complained..."); replies must not mention the CFPB either. They are dropped.
BOILERPLATE = re.compile(r"\bCFPB\b|consumerfinance\.gov|\(855\)|submit (?:a|your) complaint|"
                         r"your complaint|forward your complaint", re.I)
MIN_CHUNK_WORDS = 40


def chunk_docs(docs):
    """Split each page into passages of at most CHUNK_WORDS words, on sentence boundaries,
    without boilerplate sentences; a short last piece is joined to the chunk before it."""
    chunks = []
    for d in docs:
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", d["text"].strip())
                     if s and not BOILERPLATE.search(s)]
        pieces, cur = [], []
        for s in sentences:
            if cur and len(" ".join(cur + [s]).split()) > CHUNK_WORDS:
                pieces.append(cur)
                cur = []
            cur.append(s)
        if cur:
            if pieces and len(" ".join(cur).split()) < MIN_CHUNK_WORDS:
                pieces[-1] += cur
            else:
                pieces.append(cur)
        chunks += [{"doc_id": d["doc_id"], "title": d["title"], "text": " ".join(p)}
                   for p in pieces]
    return chunks


class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.tf = [Counter(d) for d in docs]
        self.len = np.array([len(d) for d in docs], dtype=float)
        self.avg = self.len.mean()
        df = Counter(w for d in docs for w in set(d))
        n = len(docs)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}
        self.k1, self.b = k1, b

    def scores(self, query):
        out = np.zeros(len(self.tf))
        for w in set(query):
            if w not in self.idf:
                continue
            f = np.array([tf.get(w, 0) for tf in self.tf], dtype=float)
            out += self.idf[w] * f * (self.k1 + 1) / (
                f + self.k1 * (1 - self.b + self.b * self.len / self.avg))
        return out


def complaints():
    rows = []
    for split in ["train", "val", "test"]:
        with open(os.path.join(ROOT, "data", f"real_{split}.jsonl"), encoding="utf-8") as f:
            rows += [dict(json.loads(l), split=split) for l in f]
    import out_of_scope_source as O
    rows += O.examples()
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    a = ap.parse_args()

    import torch
    from sentence_transformers import CrossEncoder, SentenceTransformer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("device:", device)
    docs = B.load_docs()
    chunks = chunk_docs(docs)
    print(f"{len(docs)} pages -> {len(chunks)} chunks")
    m = SentenceTransformer(B.MODEL, device=device)
    cache = os.path.join(B.IDX_DIR, f"chunks_v2_{CHUNK_WORDS}_{len(chunks)}.npy")   # embedding takes ~20 min on CPU
    if os.path.exists(cache) and np.load(cache).shape[0] == len(chunks):
        emb = np.load(cache)
    else:
        emb = m.encode([c["title"] + "\n" + c["text"] for c in chunks], batch_size=32,
                       normalize_embeddings=True, show_progress_bar=False).astype(np.float32)
        os.makedirs(B.IDX_DIR, exist_ok=True)
        np.save(cache, emb)
    bm25 = BM25([tokens(c["title"] + " " + c["text"]) for c in chunks])
    reranker = CrossEncoder(RERANKER, max_length=512, device=device)

    rows = complaints()
    if a.limit:
        rows = rows[:a.limit]
    q = m.encode([B.QUERY_PREFIX + r["narrative"] for r in rows], batch_size=16,
                 normalize_embeddings=True).astype(np.float32)
    out = []
    for n, (r, qv) in enumerate(zip(rows, q), 1):
        dense = np.argsort(-(emb @ qv))[:N_DENSE]
        sparse = np.argsort(-bm25.scores(tokens(r["narrative"])))[:N_BM25]
        fused = Counter()
        for ranking in (dense, sparse):
            for rank, i in enumerate(ranking):
                fused[int(i)] += 1 / (RRF_K + rank + 1)
        best = {}                                  # best fused chunk per page
        for i, s in fused.most_common():
            best.setdefault(chunks[i]["doc_id"], i)
            if len(best) == N_RERANK:
                break
        cand = [chunks[i] for i in best.values()]
        scores = reranker.predict([(r["narrative"], c["title"] + "\n" + c["text"]) for c in cand],
                                  batch_size=16, show_progress_bar=False)
        top = sorted(zip(cand, scores), key=lambda x: -x[1])[:TOP_K]
        out.append({"complaint_id": r["complaint_id"], "split": r["split"],
                    "passages": [dict(c, score=round(float(s), 3)) for c, s in top]})
        if n % 50 == 0:
            print(f"  {n}/{len(rows)}", flush=True)

    if a.limit:
        for o, r in zip(out, rows):
            print("\n#", r["complaint_id"], r.get("product"), "|", r["narrative"][:150])
            for p in o["passages"]:
                print(f"   {p['score']:6.2f} {p['doc_id']} {p['title'][:80]}")
        return
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(f"wrote {len(out)} rows to {OUT}")


if __name__ == "__main__":
    main()
