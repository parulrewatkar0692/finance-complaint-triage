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
| `data/relevance/` | Relevance labels for retrieval and citations (draft labels for validation; test to be labelled by the team) |
| `report/` | Exploration tables for the full 16.6M-row snapshot |
| `rag/` | Ask CFPB guidance collector and the first search index (bge-small, FAISS) |

**Run in Colab:**
[open the notebook](https://colab.research.google.com/github/parulrewatkar0692/finance-complaint-triage/blob/main/notebooks/make_dataset_colab.ipynb),
then choose **Runtime → Run all**. Step 9 checks that you got the team's frozen split. Step 11
builds the fine-tuning files (`sft/cfpb_train.jsonl`, `sft/cfpb_val.jsonl`, `sft/cfpb_test.jsonl`) and checks
them against the team's build.

**Fine-tuning:** each line of `sft/cfpb_train.jsonl` has `messages` (system, user, assistant), the
format that `trl`'s `SFTTrainer` reads directly with Qwen2.5-7B-Instruct's chat template. The
longest example is about 2,400 tokens, so a maximum sequence length of 3,072 fits all of them.
Score the model on `sft/cfpb_test.jsonl` with `python eval/run.py predictions.jsonl`.

**Baseline:** step 12 runs Qwen2.5-7B-Instruct without fine-tuning on the test set and scores it,
which gives the "before" numbers. It needs a GPU runtime (T4 is enough).
First result (170 test rows): product accuracy 48.8%, issue accuracy 15.9%, out-of-scope
recall 45%, valid JSON 94.7%, replies passing the rules 39.3%. Full table in `data/README.md`.

The complaint files, and the fine-tuning files built from them, are not stored here. The notebook rebuilds them from an archived public
snapshot, and the snapshot still needs instructor approval. Course prototype: not for use with
real customers.

## Fine-tuning readiness checklist (24 October 2026)

21 checks: 7 done, 12 partly done, 2 not done. The data and evaluation are solid; the open items are about training, deployment and compliance.

**1. Purpose and goal**

| Check | Status | Evidence |
| --- | --- | --- |
| Problem clearly defined | ✅ Done | Complaint in; product, issue, grounded draft reply and citations out, or a polite decline. |
| Fine-tuning is needed (not only prompting) | ⚠️ Partly | Zero-shot baseline is weak (product 48.8%, issue 15.9%, out-of-scope declined 45%). A few-shot baseline is required by the course plan's Week 1 gate and is not run yet: the Week 2 training notebook runs it (`MODE = "baseline"`, `FEW_SHOT = 3`) on the IIT GPU from 8 November. |

**2. Dataset quality**

| Check | Status | Evidence |
| --- | --- | --- |
| Clean: no duplicates, little noise | ✅ Done | Exact and near duplicates removed, non-English dropped, text artifacts fixed, privacy scan done. 9 near-template test complaints listed and reported separately. |
| Labels accurate and consistent | ⚠️ Partly | Product and issue come from CFPB but are chosen by the customer; label audit not done. Teacher replies pass all rule checks; human review of 100 pending. Citations checked: 49 of 51 validation citations point to a relevant page; test relevance labels pending. |
| Large enough to avoid overfitting | ⚠️ Partly | 1,200 training examples (about 111 per product): typical for QLoRA, but small. Watch validation loss; 1 to 3 epochs. |
| Represents the real-world use case | ⚠️ Partly | Balanced 135 per product, while real traffic is skewed. Out-of-scope examples are written, not real. English only, 2023 to 2026. |

**3. Model choice**

| Check | Status | Evidence |
| --- | --- | --- |
| Base model suits the domain | ✅ Done | Text instruction model; baseline already returns 94.7% valid JSON. |
| Supports LoRA / QLoRA | ✅ Done | Standard Hugging Face model; 4-bit loading verified on a Colab T4. |
| Size fits the compute | ⚠️ Partly | Inference on a T4 verified (after the out-of-memory fix). QLoRA training not tested: 7B with 3,072-token examples is tight on 15 GB. |

**4. Resources and constraints**

| Check | Status | Evidence |
| --- | --- | --- |
| Enough compute (GPU, memory) | ⚠️ Partly | Free Colab T4 works for inference; sessions are recycled and GPU time is limited. |
| Training time and cost estimated | ❌ Not done | Rough guess 2 to 4 hours on a T4 for 2 to 3 epochs; needs a short test run to measure. |
| Full vs parameter-efficient decided | ✅ Done | QLoRA, as in the proposal. |

**5. Evaluation plan**

| Check | Status | Evidence |
| --- | --- | --- |
| Clear metrics defined | ✅ Done | eval/run.py: accuracy, macro F1, out-of-scope recall, false refusals, citation validity, reply rules, 95% ranges. citation_relevant added (grounding); judge model needs an API key. |
| Separate validation and test sets | ✅ Done | Frozen 100 / 170 split checked by SHA-256; the teacher never saw test complaints. |
| Baseline to compare against | ⚠️ Partly | Zero-shot base model measured; still valid, because the first retriever is kept. |

**6. Reusability**

| Check | Status | Evidence |
| --- | --- | --- |
| Generalizes to similar datasets | ⚠️ Partly | Not tested on other data yet. |
| Know when re-fine-tuning is needed | ⚠️ Partly | New labels, domain, language or writing style need more fine-tuning; not yet documented in detail. |
| Easy to share or deploy | ⚠️ Partly | Data pipeline shared (GitHub, one-click Colab). Model sharing (adapter upload, inference script or API) not planned yet. |

**7. Ethics and compliance**

| Check | Status | Evidence |
| --- | --- | --- |
| Privacy and licensing respected | ⚠️ Partly | Privacy scan: 0 matches; complaint text kept out of the public repo. Snapshot licence needs instructor approval. Confirm the terms for training on Claude-generated replies. |
| Bias and harmful outputs checked | ❌ Not done | Teacher data filtered for harmful phrases, but no bias analysis or per-product breakdown yet. |
| Guardrails after fine-tuning | ⚠️ Partly | Human review required by design; no runtime guardrail yet (JSON and label check, citation filter, banned phrases, refusal fallback). |

**Before training, in order:**

1. Label the test relevance sheet (data/relevance/sheet_test.csv) so citation_relevant can be scored.
2. Human review of the 100 teacher replies, and human relevance labels for the test set.
3. A short QLoRA test run on the T4 to measure memory and training time.
4. Confirm licensing: snapshot approval and the terms for Claude-generated training data.
5. Done (week1-fixes): eval/run.py prints a per-product breakdown (basic bias check).
6. Build a small output guardrail script.
7. Few-shot baseline (required by the course plan's Week 1 gate, not optional): run with the Week 2 notebook on the IIT GPU.
