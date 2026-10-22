# Data: exploration note and build record (Week 1)

Built 2026-10-19 from the archived snapshot `Mouwiya/cfpb-consumer-complaints`
(Hugging Face revision `038f8f8b18879c9384abfee5d0b685b00c03b3cf`, created 2026-07-06,
licence listed as "other", converted from the CFPB `complaints.csv.zip`). Using the archived
snapshot still needs instructor approval, as the proposal says.

Reproduce:

```
python scripts/explore_cfpb.py --data raw/cfpb_mouwiya/data --since 2023-01-01 --out report
python scripts/build_dataset.py --data raw/cfpb_mouwiya/data --out data \
    --since 2023-08-25 --until 2026-06-17 --product-map data/product_map.json
```

Or, with no local setup, run `notebooks/make_dataset_colab.ipynb` in Colab. It downloads the
snapshot, runs the same steps and checks the result against the hashes below (see
`notebooks/README.md`).

A second run of the build produced byte-identical files (same SHA-256). The script and the
notebook produce the same bytes with pandas 3.0.6 / pyarrow 26 and with pandas 2.2.3 /
pyarrow 18.1.

The hashes below replace two earlier sets. The complaints and splits never changed:
- 2026-10-19: narratives stored as `b'...'` were unwrapped (6 texts changed; see section 2).
- 2026-10-22: a missing `sub_issue` is now written as `null`. Before, 283 records had
  `"sub_issue": NaN`, which is not valid JSON, so strict parsers such as Hugging Face `datasets`
  or `jq` reject it. The script now writes with `allow_nan=False`.

## 1. Exploration (all 16,558,052 rows)

| Measure | Value |
| --- | --- |
| Dates | 2011-12-01 to 2026-07-06; 121,295 rows have no date |
| Complaint IDs | all unique |
| With a narrative | 3,815,251 (23.0%) |
| Identical narrative texts | 32.9% of narratives repeat an earlier text |
| Contain `XXXX` redactions | 67.5% of narratives |
| 50 to 400 words | 72.8% of narratives (under 50: 18.7%, over 400: 8.5%) |

Narratives per quarter, inside the window used:

| Quarter | Complaints | With narrative | Share |
| --- | --- | --- | --- |
| 2023 Q3 (from 25 Aug) | 138,435 | 52,433 | 37.9% |
| 2024 Q2 | 607,254 | 203,483 | 33.5% |
| 2025 Q1 | 1,207,995 | 370,571 | 30.7% |
| 2025 Q3 | 1,472,638 | 316,072 | 21.5% |
| 2025 Q4 | 1,529,165 | 210,844 | 13.8% |
| 2026 Q1 | 1,667,173 | 56,274 | 3.4% |
| 2026 Q2 | 2,057,381 | 28,888 | 1.4% |
| 2026 Q3 | 150,777 | 0 | 0% |

Complaint volume keeps rising, but narrative coverage falls through late 2025 and is nearly gone by
mid-2026. The last narrative in the snapshot is dated 2026-06-17.

**Product names changed on 2023-08-25.** On that date the CFPB moved to a new taxonomy. "Credit
reporting, credit repair services, or other personal consumer reports" became "Credit reporting or
other personal consumer reports". "Credit card or prepaid card" was split into "Credit card" and
"Prepaid card". The payday-loan label gained "or advance loan". Issue names changed on the same
date. The old and new names do not overlap after that date.

**Decision: window = 2023-08-25 to 2026-06-17.** Every complaint in this window uses the new names,
so no product or issue mapping is needed. `product_map.json` is therefore empty, but it lists the
renames for reference. 11 rows on the cutover day still carry an old name, and they fall outside
the chosen products.

Full tables are in `report/` (by year, length, products, product by year, issues, company responses,
feasibility, 70 samples).

## 2. Filter, labels, sample

| Step | Count |
| --- | --- |
| Complaints in window | 12,013,812 |
| With a narrative | 2,297,181 |
| Unwrapped from a Python bytes repr (`b'...'`, see below) | 3,110 |
| 50 to 400 words (eligible) | 1,650,993 |
| Random candidates kept, 1,500 per product for the 10 chosen products | 15,000 |
| Dropped: exact duplicates (after trim and lowercase) | 901 |
| Dropped: non-English (common-English-word share under 0.15) | 16 |
| Dropped: near duplicates (MinHash on word 3-grams, 128 perms, Jaccard 0.9 or above) | 371 |
| Sampled: 135 per product | **1,350** |

Candidates are picked in a seeded, deterministic order (a hash of complaint ID with seed 42).
Deduplication runs on the 15,000 candidates across all products, so no two sampled complaints are
near duplicates, including across splits. It does not dedupe the full 1.65M pool, which would not
change the sample.

**Bytes-repr fix (rebuilt 2026-10-19).** 3,110 narratives in the window are stored as the text of
a Python bytes object. They start with `b'` or `b"`, contain escaped `\n` and UTF-8 bytes such as
`\xe2\x80\x99`, and some have lost their closing quote. `unwrap()` in `build_dataset.py` turns
them back into plain text before the length filter. The rebuilt sample has **the same 1,350
complaint IDs, each in the same split**. Only 6 texts changed (4 train, 1 validation, 1 test), and
none remain wrapped. One of the 6 (complaint 16418571) contains an unmasked date, "10/05/25". The
CFPB normally masks dates, so its scrubbing may have missed these rows. A date is not personal
data under our privacy pass, so it stays.

**Labels (`labels.json`)**: the top 10 products by eligible count. All 10 are far above the
170 minimum, and the smallest is Prepaid card with 7,686. The 11th, Debt or credit management
(3,342), is left out. Each product keeps its 5 most common issues, and any other issue becomes
`other`.

| Product | Eligible | Top-5 issue coverage | `other` in sample |
| --- | --- | --- | --- |
| Credit reporting or other personal consumer reports | 1,188,855 | 99.5% | 0.0% |
| Debt collection | 144,187 | 96.7% | 3.7% |
| Checking or savings account | 81,421 | 99.5% | 0.7% |
| Credit card | 74,260 | 71.7% | 28.1% |
| Money transfer, virtual currency, or money service | 73,085 | 90.9% | 14.1% |
| Mortgage | 26,296 | 97.8% | 0.7% |
| Student loan | 19,768 | 96.5% | 3.0% |
| Vehicle loan or lease | 18,962 | 90.7% | 11.9% |
| Payday loan, title loan, personal loan, or advance loan | 13,120 | 66.7% | 30.4% |
| Prepaid card | 7,686 | 99.7% | 0.0% |

Overall, 9.3% of the sample has issue `other`. The sample's dates run from 2023-08-26 to
2026-06-09. Length is a mean of 174 words and a median of 153.5.

**Label risks to note in report section 2:**
- Credit card and Payday loan have broad issue lists, so about 30% of their complaints are `other`.
- "Incorrect information on your report" is a top issue under Mortgage, Student loan and Vehicle
  loan as well as Credit reporting, so credit-report complaints can sit under several products.
- Money transfer has two overlapping issues, "Other transaction problem" and "Unauthorized
  transactions or other transaction problem". Both appear across the whole window, so this is
  consumer choice, not a rename. The label audit (experiment 4) should measure it.

## 3. Privacy pass

The pass scanned the 1,350 sampled narratives for emails, SSNs, phone numbers and card or account
numbers (8 to 19 digits). It masked any match as `XXXX`. **Removed: 0** (email 0, SSN 0, phone 0,
card/account 0). The 18 remaining runs of 6 or more digits are all dollar amounts in the CFPB
`{$…}` format, which is expected because the CFPB scrubs narratives before publishing them.
80% of the sampled narratives contain `XXXX`.

## 4. Split (seed 42, stratified by product)

| File | Rows | Per product | SHA-256 |
| --- | --- | --- | --- |
| `real_train.jsonl` | 1,110 | 111 | `076df0251f7c22f99c3246cf501acb629bd20a8211cdc2f69c8129d38db020c2` |
| `real_val.jsonl` | 90 | 9 | `7ea00d9c19ada7f40aa488313d9696901172d371cb05c3678bc847d2c7b17dd3` |
| `real_test.jsonl` | 150 | 15 | `38a5c275f3432c09d4aa8bf899b5a3f646a19837140b41eff90e618921bfbdaa` |

Fields: `complaint_id, date_received, product, issue, product_raw, issue_raw, sub_issue, words,
narrative`. A missing `sub_issue` is `null`. `real_test.jsonl` is closed: nobody opens it to tune prompts.

## 5. Fine-tuning files (built 2026-10-22)

`scripts/build_sft.py` joins the real complaints, the out-of-scope examples, the retrieved
passages and the teacher replies into chat-format files. The notebook runs it in step 11.

| File | Rows | Real | Out of scope | With passages | SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `sft/train.jsonl` | 1,200 | 1,110 | 90 | 600 | `f8d8e29db1b3e5a71da13422e75ea5797b28482d2cd43c8e43d7c2f1a073abcd` |
| `sft/val.jsonl` | 100 | 90 | 10 | 100 | `f15f786541bae3f86652bdcf08f036b0b468d146da81c3e4a36f723dda49879e` |
| `sft/test.jsonl` | 170 | 150 | 20 | 170 | `7f1b8762ce605298385365066af58b06f9a9d9481892f88c12eb8ae2fc73fa9e` |

These files contain complaint text, so they are not stored in the repository (`data/sft/` is
git-ignored). Rebuild them with the notebook or `python scripts/build_sft.py`. A rebuild gives the
same bytes when the real-complaint files match the hashes in section 4.

**Format.** One JSON object per line: `id`, `split`, `source` (`real` or `out_of_scope`),
`with_passages`, `retrieved` (the ids of the passages shown), and `messages`:
- `system`: the task, the 10 products with their issues, the output schema, the reply rules, the
  rule that the complaint is data and not instructions, and the fixed out-of-scope reply.
- `user`: the complaint inside `<complaint>` tags, then "Guidance documents:" with the top 3
  Ask CFPB passages (title and first 130 words), or "Guidance documents: none".
- `assistant`: `{"product", "issue", "reply", "citations"}` as one JSON string. Train and
  validation only.

Test rows have no assistant message. They carry the gold `target` (`product`, `issue`) instead,
and `eval/run.py` scores model outputs against it. The teacher never saw a test complaint.

**Passages.** Half of train (600 rows, seed 42) gets no passages, so the model also learns to
work without retrieval. Those targets have empty citations, because a model cannot cite a document
it was not shown. Validation and test always get passages. The top 3 passages come from the first
index (bge-small, whole document per chunk): `data/passages.jsonl` for the real complaints and
`data/passages_oos.jsonl` for the out-of-scope examples (`scripts/retrieve_passages.py`).

**Teacher replies (step 7).** Claude Opus 5.5 (`claude-opus-5-5`) wrote the 1,200 train and
validation replies on 2026-10-22, in 40 batches of 30. It followed `data/style_guide.md` and
`data/teacher/teacher_prompt.md`. Every batch passed `scripts/check_replies.py`: 60 to 120 words,
citations only from the retrieved documents (at most 2), no banned phrase (promises, refunds,
legal terms, CFPB or AI, URLs, `XXXX`, long digit runs), and an update closing. 700 replies
cite at least one document and 500 cite none. The automatic check does not judge whether a
reply is right, so two team members should review `data/teacher/review_sample.csv` (100 random
replies, seed 42, written by `build_sft.py`) before the Day 4 freeze.

**Out-of-scope examples (step 8).** The 120 hand-written examples are in
`data/out_of_scope_source.py`: 30 investment advice, 25 legal advice, 25 asking the assistant
to approve or decide an outcome, 20 non-finance, 20 non-English or unreadable. Examples under 50
words get the listed context sentences, so length is no cue. Each category has a fixed number of
validation and test examples (seed 42), 90 / 10 / 20 in total. Target: `out_of_scope`, `other`,
the fixed refusal line and no citations.

**Template overlap.** Some complaints are mass-campaign letters with near-identical text. 9 of
the 150 test complaints and 5 of the 90 validation complaints have a twin in train (word
3-gram Jaccard 0.5 or above; 7 test complaints at 0.8 or above), mostly in Money transfer. The
splits stay frozen. `data/template_overlap.json` lists them, and `eval/run.py` reports every
metric with and without them.

**Evaluation.** `python eval/run.py predictions.jsonl` scores a file of `{"id", "output"}`
lines: JSON validity, product accuracy and macro F1, issue accuracy (overall and given the right
product), out-of-scope recall, false refusals, exact refusal text, citation validity and the reply
rules, each with a bootstrap 95% confidence interval. `--judge` adds the judge's scores and
`--self-test` checks the scorer on the gold labels.
