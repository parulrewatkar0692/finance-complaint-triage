#!/usr/bin/env python3
"""Check teacher replies against the style guide (data plan step 7).

Usage
  python scripts/check_replies.py            # check every batch file, print a summary
  python scripts/check_replies.py 3          # check batch 3 only

A reply fails when it breaks a hard rule: wrong id, not 60 to 120 words, a citation that was
not retrieved for that complaint, a banned phrase (promises, legal terms, CFPB or AI mentions,
URLs, XXXX, long digit runs), or a missing "update" closing.
"""

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from teacher_batches import BATCH, load  # noqa: E402

BANNED = [
    r"\bwill (?:be )?refund", r"\brefund (?:has been|was|is) (?:approved|issued|processed)",
    r"\bwe (?:will|have) (?:refund|reverse|credit|waive|remove|delete)", r"(?<!HUD-)\bapproved?\b",
    r"\bguarantee", r"\bpromise", r"\bentitled\b", r"\bcompensat", r"\bviolat", r"\bsue\b",
    r"\blawsuit", r"\battorney", r"\blawyer", r"\billegal", r"\bCFPB\b",
    r"\bConsumer Financial Protection", r"\bAI\b", r"\bassistant\b", r"https?://", r"www\.",
    r"XXXX", r"\d{6,}", r"askcfpb-", r"\byou are (?:right|wrong)", r"\bour (?:error|mistake)",
]
BANNED_RE = [(p, re.compile(p, re.I)) for p in BANNED]


def check_batch(n, rows, problems):
    path = os.path.join(ROOT, "data", "teacher", f"batch_{n:02d}.jsonl")
    want = rows[n * BATCH:(n + 1) * BATCH]
    want_ids = [r["complaint_id"] for r in want]
    retrieved = {r["complaint_id"]: {p["doc_id"] for p in r["passages"]} for r in want}
    got = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                got.append(json.loads(line))
            except json.JSONDecodeError as e:
                problems.append((n, f"line {i}", f"invalid JSON: {e}"))
    if [g.get("complaint_id") for g in got] != want_ids:
        problems.append((n, "-", "ids differ from the batch (order or content)"))
    for g in got:
        cid, reply, cits = g.get("complaint_id"), g.get("reply", ""), g.get("citations")
        w = len(reply.split())
        if not 60 <= w <= 120:
            problems.append((n, cid, f"{w} words"))
        if not isinstance(cits, list) or len(cits) > 2:
            problems.append((n, cid, f"citations not a list of at most 2: {cits}"))
        elif cid in retrieved and not set(cits) <= retrieved[cid]:
            problems.append((n, cid, f"citation not retrieved: {set(cits) - retrieved[cid]}"))
        for p, rx in BANNED_RE:
            if rx.search(reply):
                problems.append((n, cid, f"banned: {p}"))
        if "update" not in reply.split(".")[-2].lower():
            problems.append((n, cid, "no update closing"))
    return len(got)


def main():
    rows = load()
    files = sorted(glob.glob(os.path.join(ROOT, "data", "teacher", "batch_*.jsonl")))
    batches = [int(sys.argv[1])] if len(sys.argv) > 1 else \
        [int(os.path.basename(f)[6:8]) for f in files]
    problems, n = [], 0
    for b in batches:
        n += check_batch(b, rows, problems)
    for p in problems:
        print("FAIL", *p)
    print(f"checked {n} replies in {len(batches)} batches: {len(problems)} problems")


if __name__ == "__main__":
    main()
