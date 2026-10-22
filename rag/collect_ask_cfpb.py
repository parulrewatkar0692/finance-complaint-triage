#!/usr/bin/env python3
"""Collect Ask CFPB answers for the search corpus (proposal v2, data plan step 6).

consumerfinance.gov refuses scripted requests (HTTP 403 from its CDN), so this reads the
Internet Archive's copies instead. For each English answer (URL ending -en-<id>/) it takes
the newest snapshot listed in rag/raw/cdx_ask_cfpb.txt, keeps title, category, last-reviewed
date, answer text, original URL, archive URL and fetch date.

Usage
  python rag/collect_ask_cfpb.py fetch    # download pages (cached, 1 request per second)
  python rag/collect_ask_cfpb.py parse    # build rag/docs/ask_cfpb.jsonl

The CDX list was made with:
  curl "https://web.archive.org/cdx/search/cdx?url=consumerfinance.gov/ask-cfpb/&matchType=prefix
        &from=2024&filter=statuscode:200&collapse=urlkey&fl=original,timestamp"
"""

import datetime as dt
import gzip
import json
import os
import re
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CDX = os.path.join(HERE, "raw", "cdx_ask_cfpb.txt")
HTML_DIR = os.path.join(HERE, "raw", "html")
OUT = os.path.join(HERE, "docs", "ask_cfpb.jsonl")
UA = "CapstoneResearch/1.0 (course project; contact via repository)"
MIN_WORDS = 20

# Ask CFPB breadcrumb category -> our product labels (data/labels.json).
CATEGORY_TO_PRODUCTS = {k.lower(): v for k, v in {
    "Credit reports and scores": ["Credit reporting or other personal consumer reports"],
    "Debt collection": ["Debt collection"],
    "Bank accounts and services": ["Checking or savings account"],
    "Credit cards": ["Credit card"],
    "Money transfers": ["Money transfer, virtual currency, or money service"],
    "Mortgages": ["Mortgage"],
    "Student loans": ["Student loan"],
    "Auto loans": ["Vehicle loan or lease"],
    "Payday loans": ["Payday loan, title loan, personal loan, or advance loan"],
    "Prepaid cards": ["Prepaid card"],
    "Prepaid cards and other prepaid accounts": ["Prepaid card"],
    "Reverse mortgages": ["Mortgage"],
    # cross-product guidance (identity theft, scams): indexed, tied to no single product
    "Fraud and scams": ["general"],
}.items()}

# The catch-all "Ask CFPB" category is mostly off-topic (children and money, Social
# Security). These answers in it clearly belong to one of our products.
DOC_OVERRIDES = {
    286: ["Mortgage"],
    901: ["Payday loan, title loan, personal loan, or advance loan"],
    905: ["Payday loan, title loan, personal loan, or advance loan"],
    911: ["Payday loan, title loan, personal loan, or advance loan"],
    2124: ["Debt collection"],
    2125: ["Debt collection"],
    2127: ["Credit reporting or other personal consumer reports"],
    2136: ["Student loan"],
}


def answers():
    """answer id -> (original url, newest timestamp)"""
    best = {}
    with open(CDX, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) != 2:
                continue
            url, ts = parts
            m = re.search(r"-en-(\d+)/?$", url.split("?")[0])
            if not m:
                continue
            aid = int(m.group(1))
            if aid not in best or ts > best[aid][1]:
                best[aid] = (url.split("?")[0], ts)
    return best


def fetch_one(aid, url, ts):
    path = os.path.join(HTML_DIR, f"{aid}.html")
    if os.path.exists(path):
        return
    arch = f"https://web.archive.org/web/{ts}id_/{url}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(arch, headers={"User-Agent": UA,
                                                        "Accept-Encoding": "gzip"})
            with urllib.request.urlopen(req, timeout=60) as r:
                body = r.read()
            if body.startswith(bytes([0x1F, 0x8B])):  # gzip
                body = gzip.decompress(body)
            with open(path + ".part", "wb") as f:
                f.write(body)
            os.replace(path + ".part", path)
            break
        except Exception as e:  # network errors, 429 and 5xx: back off and retry
            print(f"  {aid}: {e}; retry {attempt + 1}", flush=True)
            time.sleep(10 * (attempt + 1))
    time.sleep(1)


def fetch(workers=3):
    from concurrent.futures import ThreadPoolExecutor
    os.makedirs(HTML_DIR, exist_ok=True)
    todo = sorted(answers().items())
    print(f"{len(todo)} answers", flush=True)
    with ThreadPoolExecutor(workers) as ex:
        for n, _ in enumerate(ex.map(lambda kv: fetch_one(kv[0], *kv[1]), todo), 1):
            if n % 50 == 0:
                print(f"  {n}/{len(todo)}", flush=True)


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def parse():
    from bs4 import BeautifulSoup
    best = answers()
    fetched = dt.date.today().isoformat()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    kept, skipped = [], {"missing_html": 0, "no_answer_text": 0, "too_short": 0}
    for aid, (url, ts) in sorted(best.items()):
        path = os.path.join(HTML_DIR, f"{aid}.html")
        if not os.path.exists(path):
            skipped["missing_html"] += 1
            continue
        soup = BeautifulSoup(open(path, encoding="utf-8", errors="replace").read(), "html.parser")
        body = soup.select_one(".answer-text")
        h1 = soup.find("h1")
        if body is None or h1 is None:
            skipped["no_answer_text"] += 1
            continue
        blocks = [clean(el.get_text(" ")) for el in body.find_all(["p", "li", "h2", "h3"])
                  if not el.find(["p", "li"])]
        text = "\n".join(b for b in blocks if b)
        if len(text.split()) < MIN_WORDS:
            skipped["too_short"] += 1
            continue
        crumbs = [clean(a.get_text()) for a in soup.select(".m-breadcrumbs_crumb, .m-breadcrumbs__crumb")]
        category = crumbs[-1] if crumbs else ""
        reviewed = soup.select_one(".answer-edited-date")
        kept.append({
            "doc_id": f"askcfpb-{aid:04d}",
            "title": clean(h1.get_text()),
            "category": category,
            "products": DOC_OVERRIDES.get(aid) or CATEGORY_TO_PRODUCTS.get(category.lower(), []),
            "last_reviewed": reviewed.get("datetime") if reviewed else None,
            "url": url,
            "archive_url": f"https://web.archive.org/web/{ts}/{url}",
            "snapshot": f"{ts[:4]}-{ts[4:6]}-{ts[6:8]}",
            "fetched": fetched,
            "words": len(text.split()),
            "text": text,
        })
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        for d in kept:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(json.dumps({"answers_listed": len(best), "kept": len(kept), "skipped": skipped,
                      "in_our_products": sum(bool(d["products"]) and d["products"] != ["general"] for d in kept),
                      "general": sum(d["products"] == ["general"] for d in kept),
                      "not_indexed": sum(not d["products"] for d in kept)}, indent=2))


if __name__ == "__main__":
    {"fetch": fetch, "parse": parse}[sys.argv[1]]()
