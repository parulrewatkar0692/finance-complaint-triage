#!/usr/bin/env python3
"""Does a cited page support the reply? (grounding plan, part 3)

A reply's next steps are its middle sentences: everything except the acknowledgement, the
"logged for review" sentence, sympathy sentences and the closing update sentence. A cited page
supports the reply when an NLI model (cross-encoder/nli-deberta-v3-base) judges that the page
entails at least one next-step sentence with probability >= SUPPORT_MIN.

Used by scripts/build_sft.py (keep only supported citations in the training targets) and by
eval/run.py --groundedness (share of cited pages that support the reply).

Usage
  python scripts/grounding.py calibrate   # write data/relevance/support_sample.csv for checking
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
NLI_MODEL = "cross-encoder/nli-deberta-v3-base"
ENTAILMENT = 1                 # id2label: 0 contradiction, 1 entailment, 2 neutral
SUPPORT_MIN = 0.5

SKIP = re.compile(r"^(thank you|we understand|we are sorry|we're sorry|your complaint has been "
                  r"logged|you will receive an update)", re.I)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


VERBS = set("""ask avoid be call change check compare confirm consider contact continue dispute do
file follow include keep let list make mark monitor note place repeat report request respond
review save send share submit tell update use watch write""".split())


def next_steps(reply):
    """The reply's next steps as statements an NLI model can test against a page.

    "Please send a written notice of error, and keep proof of delivery." becomes
    ["You can send a written notice of error.", "You can keep proof of delivery."]; imperative
    sentences are split at "and" before a verb, other sentences are kept as they are."""
    out = []
    for s in sentences(reply):
        if SKIP.match(s):
            continue
        s = re.sub(r"^please\s+", "", s, flags=re.I).rstrip(".")
        words = s.split()
        if not words or words[0].lower() not in VERBS:
            out.append(s + ".")
            continue
        parts = re.split(r",?\s+and\s+(?=(?:" + "|".join(sorted(VERBS)) + r")\b)", s, flags=re.I)
        out += [f"You can {p[0].lower() + p[1:]}." for p in parts if p.strip()]
    return out


_model = None


def model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder
        _model = CrossEncoder(NLI_MODEL, device="cpu", max_length=512)
    return _model


def support_scores(pairs):
    """pairs: [(page text, reply)] -> [max entailment probability over the reply's next steps]."""
    import numpy as np
    flat, owner = [], []
    for k, (page, reply) in enumerate(pairs):
        for s in next_steps(reply):
            flat.append((page, s))
            owner.append(k)
    out = [0.0] * len(pairs)
    if flat:
        logits = model().predict(flat, batch_size=16, show_progress_bar=False,
                                 apply_softmax=True)
        for k, p in zip(owner, np.asarray(logits)[:, ENTAILMENT]):
            out[k] = max(out[k], float(p))
    return out


def page_text(p):
    return p["title"] + "\n" + p["text"]


def calibrate():
    """Score every (teacher reply, shown page) pair of the validation set and write a sheet."""
    import csv
    import json
    sys.path.insert(0, HERE)
    from teacher_batches import load
    v2 = {}
    with open(os.path.join(ROOT, "data", "passages_v2.jsonl"), encoding="utf-8") as f:
        for r in map(json.loads, f):
            v2[r["complaint_id"]] = r["passages"][:3]
    replies = {}
    import glob
    for path in glob.glob(os.path.join(ROOT, "data", "teacher", "batch_*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for r in map(json.loads, f):
                replies[r["complaint_id"]] = r
    rows = [r for r in load() if r["split"] == "val"]
    pairs, meta = [], []
    for r in rows:
        for p in v2[r["complaint_id"]]:
            pairs.append((page_text(p), replies[r["complaint_id"]]["reply"]))
            meta.append((r["complaint_id"], p))
    scores = support_scores(pairs)
    path = os.path.join(ROOT, "data", "relevance", "support_sample.csv")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["complaint_id", "doc_id", "support", "next_steps", "page"])
        for (cid, p), (page, reply), s in zip(meta, pairs, scores):
            w.writerow([cid, p["doc_id"], round(s, 3), " | ".join(next_steps(reply)), page])
    print(f"wrote {len(pairs)} pairs to {path}")


SUPPORT_FILE = os.path.join(ROOT, "data", "teacher", "support.jsonl")


def score():
    """Support of every (teacher reply, shown page) pair for train and val, using the pages the
    model is shown (data/passages*.jsonl). Writes data/teacher/support.jsonl (ids and scores
    only, no complaint text) so build_sft.py does not need the NLI model."""
    import glob
    import json
    passages = {}
    for name in ["passages.jsonl", "passages_oos.jsonl"]:
        with open(os.path.join(ROOT, "data", name), encoding="utf-8") as f:
            for r in map(json.loads, f):
                passages[r["complaint_id"]] = r["passages"]
    replies = {}
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "teacher", "batch_*.jsonl"))):
        with open(path, encoding="utf-8") as f:
            for r in map(json.loads, f):
                replies[r["complaint_id"]] = r
    from build_sft import all_rows, no_passage_ids
    skip = no_passage_ids(all_rows()[1], replies)  # shown no pages, so never cite
    ids = sorted(c for c in replies if c not in skip)
    out = []
    for n in range(0, len(ids), 50):
        chunk = ids[n:n + 50]
        pairs, meta = [], []
        for cid in chunk:
            for p in passages[cid]:
                pairs.append((page_text(p), replies[cid]["reply"]))
                meta.append((cid, p["doc_id"]))
        for (cid, doc), s in zip(meta, support_scores(pairs)):
            out.append({"complaint_id": cid, "doc_id": doc, "support": round(s, 4)})
        print(f"  {min(n + 50, len(ids))}/{len(ids)} replies", flush=True)
    with open(SUPPORT_FILE, "w", encoding="utf-8", newline="\n") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(out)} scores to {SUPPORT_FILE}")


if __name__ == "__main__":
    {"calibrate": calibrate, "score": score}[sys.argv[1]]()
