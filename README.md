# Finance Complaint Triage: Track A capstone (data and search)

Course capstone: fine-tune a 7B model to triage US consumer finance complaints. It returns the
product, the issue, and a grounded draft reply for a human agent to review. This repository
holds the Week 1 data work: the dataset, ready for fine-tuning, and the evaluation script.

| Folder | What it holds |
| --- | --- |
| `notebooks/` | `make_dataset_colab.ipynb`: get, clean, label and split the CFPB complaints in Colab |
| `scripts/` | The same build as scripts (`explore_cfpb.py`, `build_dataset.py`), retrieval, reply checks, and `build_sft.py` for the fine-tuning files |
| `data/` | Build record (`README.md`), labels, reply style guide, out-of-scope examples, retrieved passages, teacher replies (`teacher/`) |
| `eval/` | `run.py`: scores test predictions, with bootstrap confidence intervals |
| `report/` | Exploration tables for the full 16.6M-row snapshot |
| `rag/` | Ask CFPB guidance collector and the first search index (bge-small, FAISS) |

**Run in Colab:**
[open the notebook](https://colab.research.google.com/github/parulrewatkar0692/finance-complaint-triage/blob/main/notebooks/make_dataset_colab.ipynb),
then choose **Runtime → Run all**. Step 9 checks that you got the team's frozen split. Step 11
builds the fine-tuning files (`sft/train.jsonl`, `sft/val.jsonl`, `sft/test.jsonl`) and checks
them against the team's build.

**Fine-tuning:** each line of `sft/train.jsonl` has `messages` (system, user, assistant), the
format that `trl`'s `SFTTrainer` reads directly with Qwen2.5-7B-Instruct's chat template. The
longest example is about 2,400 tokens, so a maximum sequence length of 3,072 fits all of them.
Score the model on `sft/test.jsonl` with `python eval/run.py predictions.jsonl`.

**Baseline:** step 12 runs Qwen2.5-7B-Instruct without fine-tuning on the test set and scores it,
which gives the "before" numbers. It needs a GPU runtime (T4 is enough).

The complaint files, and the fine-tuning files built from them, are not stored here. The notebook rebuilds them from an archived public
snapshot, and the snapshot still needs instructor approval. Course prototype: not for use with
real customers.
