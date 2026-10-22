# Search corpus and first index (Week 1, data plan step 6)

Built 2026-10-19. **712 documents indexed**, above the proposal's minimum of 200 and its target of 250.

Reproduce:

```
python rag/collect_ask_cfpb.py fetch   # about 55 min: the archive throttles to ~13 pages a minute
python rag/collect_ask_cfpb.py parse
python rag/build_index.py build
python rag/build_index.py check
```

## Source

Ask CFPB answers, in English. consumerfinance.gov returns HTTP 403 to scripted requests, so the
pages come from the **Internet Archive**. For each answer the collector takes the newest snapshot
since 2024. Each document records its original URL, archive URL, snapshot date and fetch date.

| Step | Count |
| --- | --- |
| English answers listed in the archive (`raw/cdx_ask_cfpb.txt`) | 748 |
| Fetched | 747 (answer 172 refuses with HTTP 403 at the archive) |
| Dropped: answer under 20 words | 12 |
| Kept in `docs/ask_cfpb.jsonl` | 735 |
| Not indexed: catch-all "Ask CFPB" category, off-topic (children and money, Social Security, tenants) | 23 |
| **Indexed** | **712** |

Snapshots run from 2024-01-01 to 2026-10-12. The answers' "last reviewed" dates run from
2016-03-17 to 2026-09-02.

Document fields: `doc_id` (`askcfpb-0412` style), `title`, `category`, `products`,
`last_reviewed`, `url`, `archive_url`, `snapshot`, `fetched`, `words`, `text`.

## Mapping to our products

The Ask CFPB breadcrumb category decides the product. Two categories needed a rule of their own:
- **Fraud and scams** covers identity theft, scams and unauthorized charges across products, so it is
  tagged `general`.
- **"Ask CFPB"** (the catch-all category): 8 of its answers clearly belong to one of our products and
  are assigned by hand in `DOC_OVERRIDES` (mortgage hardship, personal lines of credit, medical debt,
  credit-report blocking, private student loans).

| Product | Documents |
| --- | --- |
| Mortgage (including reverse mortgages) | 217 |
| Checking or savings account | 104 |
| Credit reporting or other personal consumer reports | 66 |
| Student loan | 61 |
| Credit card | 58 |
| Vehicle loan or lease | 57 |
| Debt collection | 49 |
| Prepaid card | 33 |
| general (fraud, scams, identity theft) | 31 |
| Payday loan, title loan, personal loan, or advance loan | 23 |
| Money transfer, virtual currency, or money service | **13** |

**Gap:** Money transfer has only 13 documents, but it is 1 of our 10 products, and "Fraud or scam"
is its second most common issue. The 31 `general` fraud answers partly cover it. If the 40
search pairs show weak recall there, add the CFPB consumer guides on money transfers and P2P apps
(the proposal's fallback).

## First index

| Setting | Value |
| --- | --- |
| Embedding model | BAAI/bge-small-en-v1.5 (384 dimensions, CPU) |
| Chunking | Whole document (title and answer) as one chunk |
| Truncation | 142 of 712 documents exceed 512 tokens and are cut there |
| Store | FAISS `IndexFlatIP` on normalized vectors, which gives cosine similarity |
| Query | Complaint text, with the bge prefix "Represent this sentence for searching relevant passages: " |

The 142 truncated documents are one reason Week 3 compares whole documents against chunks of
200 tokens with 40 overlap.

| File | SHA-256 |
| --- | --- |
| `docs/ask_cfpb.jsonl` | `4cd5b9c9c961efba36c78eba7cf67880ee3680a7e7cc601464170142180b8c3d` |
| `index/first_index.faiss` | `9d2b357111a25d1aeb001341801333dc91c0bd77af557d466df3689826cce5bc` |
| `index/doc_ids.json` | `91424a4f2e573a83fffd2a77d2e678e5ff79d4f1838625b2ee4b13f462db985e` |

## Smoke test (validation only, 90 complaints)

This is **not** the recall@5 target, which is measured on the 40 hand-labelled search pairs in Week 2.
It is a cheap proxy: a hit means at least one of the top k documents is tagged with the
complaint's product. Results are in `index/check_val.json`, with examples.

| | @1 | @3 | @5 |
| --- | --- | --- | --- |
| All 90 | 0.48 | 0.64 | 0.71 |

By product at @3: Credit reporting 1.00, Mortgage 1.00, Debt collection 0.89, Checking 0.78,
Vehicle 0.78, Prepaid 0.67, and 0.33 each for Credit card, Money transfer, Payday and Student loan.

Reading the results shows the proxy understates relevance. Many "misses" are complaints filed under
one product but about another topic. For example, student-loan complaints about credit-report
errors retrieve credit-report dispute answers, which are the right guidance. Credit-card
purchase disputes retrieve "How do I dispute a charge on my credit card bill?", which is tagged
`general`.
