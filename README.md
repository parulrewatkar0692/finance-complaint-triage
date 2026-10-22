# Finance Complaint Triage: Track A capstone (data and search)

Course capstone: fine-tune a 7B model to triage US consumer finance complaints. It returns the
product, the issue, and a grounded draft reply for a human agent to review. This repository
holds the Week 1 data work.

| Folder | What it holds |
| --- | --- |
| `notebooks/` | `make_dataset_colab.ipynb`: get, clean, label and split the CFPB complaints in Colab |
| `scripts/` | The same build as scripts: `explore_cfpb.py` and `build_dataset.py` |
| `data/` | Exploration note and build record (`README.md`), `labels.json`, `product_map.json` |
| `report/` | Exploration tables for the full 16.6M-row snapshot |
| `rag/` | Ask CFPB guidance collector and the first search index (bge-small, FAISS) |

**Run in Colab:**
[open the notebook](https://colab.research.google.com/github/parulrewatkar0692/finance-complaint-triage/blob/main/notebooks/make_dataset_colab.ipynb),
then choose **Runtime → Run all**. Step 9 checks that you got the team's frozen split.

The complaint files are not stored here. The notebook rebuilds them from an archived public
snapshot, and the snapshot still needs instructor approval. Course prototype: not for use with
real customers.
