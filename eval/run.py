#!/usr/bin/env python3
"""Score model predictions on the test set (proposal v2, evaluation plan).

Predictions are a JSONL file with one line per test example: {"id": ..., "output": "<raw model
text>"}. The output should be the JSON object the system prompt asks for; code fences and text
around the object are tolerated, but count against strict JSON validity.

Metrics, each with a bootstrap 95% confidence interval (1,000 resamples, seed 42):
  json_valid        output parses as an object with product, issue, reply and citations
  product_acc       exact match on product (10 products plus out_of_scope)
  product_macro_f1  macro F1 over the 11 product labels
  issue_acc         exact match on issue
  issue_acc_given_product  issue accuracy on rows where the product is right
  oos_recall        out-of-scope rows predicted as out_of_scope
  false_refusal     in-scope rows predicted as out_of_scope
  refusal_exact     out-of-scope rows whose reply is exactly the fixed refusal line
  citation_valid    rows whose citations are all among the retrieved documents
  reply_rules       in-scope replies that pass the style guide's hard rules (60 to 120 words,
                    no banned phrase, update closing), the same checks as the teacher replies
  citation_relevant share of cited pages that a relevance label marks relevant to the
                    complaint (data/relevance/labels_test.jsonl; unlabelled pages are skipped)
  citation_entailed rows with citations where every cited page entails one of the reply's next
                    steps (strict NLI check in scripts/grounding.py), when --groundedness is given.
                    Strict: it rejected about 90% of the teacher's relevant citations.
  judge_*           mean of each judge score, when --judge is given

Everything is reported on all rows and again without the val/test complaints that have a
near-template twin in train (data/template_overlap.json).

Usage
  python eval/run.py predictions.jsonl
  python eval/run.py predictions.jsonl --judge judge_scores.jsonl --out report.json
  python eval/run.py predictions.jsonl --groundedness   # also loads the NLI model (CPU is fine)
  python eval/run.py --self-test          # scores the gold labels; every metric should be 1.0

The judge file has one line per id: {"id": ..., "scores": {"helpfulness": 4, "safety": 5}}.
"""

import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_sft import REFUSAL  # noqa: E402
from check_replies import BANNED_RE  # noqa: E402

KEYS = {"product", "issue", "reply", "citations"}
OOS = "out_of_scope"
N_BOOT = 1000
SEED = 42


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def parse(text):
    """Return (object or None, strict) where strict means the text was only the JSON object."""
    if not isinstance(text, str):
        return None, False
    try:
        obj = json.loads(text.strip())
        return (obj, True) if isinstance(obj, dict) else (None, False)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            return (obj, False) if isinstance(obj, dict) else (None, False)
        except json.JSONDecodeError:
            pass
    return None, False


def reply_ok(reply):
    if not isinstance(reply, str) or not 60 <= len(reply.split()) <= 120:
        return False
    if any(rx.search(reply) for _, rx in BANNED_RE):
        return False
    sentences = reply.split(".")
    return len(sentences) > 1 and "update" in sentences[-2].lower()


def score_rows(test, preds):
    """Per-row results: a dict of metric -> 0/1 (or None when the metric does not apply)."""
    rows = []
    for ex in test:
        gold = ex["target"]
        obj, strict = parse(preds.get(ex["id"]))
        valid = obj is not None and KEYS <= set(obj)
        obj = obj or {}
        prod, issue = obj.get("product"), obj.get("issue")
        cits = obj.get("citations")
        is_oos = gold["product"] == OOS
        r = {
            "id": ex["id"], "gold_product": gold["product"], "pred_product": prod,
            "json_valid": int(valid and strict),
            "json_parsed": int(valid),
            "product_acc": int(prod == gold["product"]),
            "issue_acc": int(prod == gold["product"] and issue == gold["issue"]),
            "issue_acc_given_product": (int(issue == gold["issue"])
                                        if prod == gold["product"] else None),
            "oos_recall": int(prod == OOS) if is_oos else None,
            "false_refusal": None if is_oos else int(prod == OOS),
            "refusal_exact": int(obj.get("reply") == REFUSAL) if is_oos else None,
            "citation_valid": int(isinstance(cits, list)
                                  and all(isinstance(c, str) for c in cits)
                                  and set(cits) <= set(ex["retrieved"])),
            "reply_rules": None if is_oos else int(reply_ok(obj.get("reply"))),
            "_reply": obj.get("reply"), "_cits": cits, "_is_oos": is_oos,
        }
        rows.append(r)
    return rows


def macro_f1(rows):
    labels = sorted({r["gold_product"] for r in rows})
    f1s = []
    for lab in labels:
        tp = sum(r["gold_product"] == lab and r["pred_product"] == lab for r in rows)
        fp = sum(r["gold_product"] != lab and r["pred_product"] == lab for r in rows)
        fn = sum(r["gold_product"] == lab and r["pred_product"] != lab for r in rows)
        f1s.append(2 * tp / (2 * tp + fp + fn) if tp else 0.0)
    return sum(f1s) / len(f1s) if f1s else 0.0


def shown_pages(ex):
    """{doc id: "title
text"} for the guidance documents in the user message."""
    pages, cur = {}, None
    for line in ex["messages"][1]["content"].split("\n"):
        m = re.match(r"^\[(askcfpb-\d+)\] (.*)$", line)
        if m:
            cur = m.group(1)
            pages[cur] = m.group(2)
        elif cur and line.strip() and not line.startswith("</complaint>"):
            pages[cur] += "\n" + line
    return pages


def add_groundedness(test, rows):
    """citation_entailed: 1 when every cited page entails a next step of the reply (NLI), None
    when the row is out of scope, has no valid citations, or cites nothing."""
    from grounding import SUPPORT_MIN, support_scores
    by_id = {ex["id"]: ex for ex in test}
    pairs, owner = [], []
    for r in rows:
        r["citation_entailed"] = None
        if (r["_is_oos"] or not r["citation_valid"] or not r["_cits"]
                or not isinstance(r["_reply"], str)):
            continue
        pages = shown_pages(by_id[r["id"]])
        for c in r["_cits"]:
            pairs.append((pages.get(c, ""), r["_reply"]))
            owner.append(r)
    scores = support_scores(pairs) if pairs else []
    worst = {}
    for r, s in zip(owner, scores):
        worst[id(r)] = min(worst.get(id(r), 1.0), s)
    for r in owner:
        r["citation_entailed"] = int(worst[id(r)] >= SUPPORT_MIN)


def add_relevance(rows, path):
    """citation_relevant: share of a row's cited pages labelled relevant (labelled pages only)."""
    labels = {(r["complaint_id"], r["doc_id"]): r["relevant"] for r in read_jsonl(path)}
    for r in rows:
        r["citation_relevant"] = None
        if r["_is_oos"] or not r["citation_valid"] or not r["_cits"]:
            continue
        known = [labels[(r["id"], c)] for c in r["_cits"] if (r["id"], c) in labels]
        if known:
            r["citation_relevant"] = sum(known) / len(known)


def metrics(rows, judge):
    out = {}
    for k in ["json_valid", "json_parsed", "product_acc", "issue_acc", "issue_acc_given_product",
              "oos_recall", "false_refusal", "refusal_exact", "citation_valid", "reply_rules",
              "citation_relevant", "citation_entailed"]:
        if k in ("citation_relevant", "citation_entailed") and k not in rows[0]:
            continue
        vals = [r[k] for r in rows if r[k] is not None]
        out[k] = sum(vals) / len(vals) if vals else None
    out["product_macro_f1"] = macro_f1(rows)
    if judge:
        names = sorted({n for s in judge.values() for n in s})
        for n in names:
            vals = [judge[r["id"]][n] for r in rows if r["id"] in judge and n in judge[r["id"]]]
            out[f"judge_{n}"] = sum(vals) / len(vals) if vals else None
    return out


def bootstrap(rows, judge):
    rng = random.Random(SEED)
    samples = [metrics([rows[rng.randrange(len(rows))] for _ in rows], judge)
               for _ in range(N_BOOT)]
    ci = {}
    for k in samples[0]:
        vals = sorted(s[k] for s in samples if s[k] is not None)
        if vals:
            ci[k] = [vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]]
    return ci


def report(rows, judge):
    point = metrics(rows, judge)
    ci = bootstrap(rows, judge)
    return {"n": len(rows),
            "metrics": {k: {"value": v, "ci95": ci.get(k)} for k, v in point.items()}}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("predictions", nargs="?")
    ap.add_argument("--test", default=os.path.join(ROOT, "data", "sft", "cfpb_test.jsonl"))
    ap.add_argument("--judge", help="JSONL of {id, scores: {name: number}}")
    ap.add_argument("--out", help="write the full report as JSON here")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--groundedness", action="store_true",
                    help="check that cited pages support the reply (loads an NLI model)")
    a = ap.parse_args()

    test = read_jsonl(a.test)
    if a.self_test:
        preds = {}
        for ex in test:
            t = ex["target"]
            reply = REFUSAL if t["product"] == OOS else (
                "Thank you for explaining the problem with your account. We understand your "
                "concern and we are sorry for the trouble this has caused you. Your complaint has "
                "been logged for review by the account services team. Please keep your statements "
                "and any letters you received, and send a written request describing the problem "
                "so the team has the details. You will receive an update once the review is "
                "complete.")
            preds[ex["id"]] = json.dumps({**t, "reply": reply, "citations": ex["retrieved"][:1]})
    elif a.predictions:
        preds = {p["id"]: p.get("output") for p in read_jsonl(a.predictions)}
    else:
        ap.error("give a predictions file or --self-test")

    missing = [ex["id"] for ex in test if ex["id"] not in preds]
    if missing:
        print(f"warning: {len(missing)} test ids have no prediction (scored as wrong)")
    judge = {j["id"]: j["scores"] for j in read_jsonl(a.judge)} if a.judge else None

    overlap_path = os.path.join(ROOT, "data", "template_overlap.json")
    overlap = {h["complaint_id"] for h in json.load(open(overlap_path))["test"]}
    rows = score_rows(test, preds)
    if a.groundedness:
        add_groundedness(test, rows)
    labels_path = os.path.join(ROOT, "data", "relevance", "labels_test.jsonl")
    if os.path.exists(labels_path):
        add_relevance(rows, labels_path)
    full = {"all": report(rows, judge),
            "without_template_overlap": report([r for r in rows if r["id"] not in overlap], judge),
            "excluded_ids": sorted(overlap)}

    print(f"{'metric':26s} {'all (n=' + str(full['all']['n']) + ')':>26s} "
          f"{'no overlap (n=' + str(full['without_template_overlap']['n']) + ')':>26s}")
    for k in full["all"]["metrics"]:
        cells = []
        for part in ["all", "without_template_overlap"]:
            m = full[part]["metrics"][k]
            if m["value"] is None:
                cells.append("n/a")
            else:
                lo, hi = m["ci95"] or (m["value"], m["value"])
                cells.append(f"{m['value']:.3f} [{lo:.3f}, {hi:.3f}]")
        print(f"{k:26s} {cells[0]:>26s} {cells[1]:>26s}")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(full, f, indent=2)
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
