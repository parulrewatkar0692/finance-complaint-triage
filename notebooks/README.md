# Notebooks

## `make_dataset_colab.ipynb`: get, format and split the real complaints

This notebook rebuilds the team's 1,350 real complaints from the archived CFPB snapshot. It
splits them 1,110 / 90 / 150 and checks the result against the frozen split. Step 11 then gets
this repository (teacher replies, out-of-scope examples, passages) and builds the fine-tuning
files. It needs only an internet connection.

**Run it in Colab**
1. Open [colab.research.google.com](https://colab.research.google.com), choose **File → Upload
   notebook**, and pick `make_dataset_colab.ipynb`. If it is in a GitHub repository, open it from
   the GitHub tab instead.
2. Optional: in the configuration cell, set `SAVE_TO_DRIVE = True` to write the outputs to your
   Google Drive (`MyDrive/data`) instead of downloading a zip.
3. Choose **Runtime → Run all**. A CPU runtime is enough. The run takes about 15 minutes: the
   1 GB download takes a few minutes, and filtering the 12M complaints in the window takes about
   10 minutes.
4. Step 9 must print **"OK: this is the team's frozen split."** Step 11 must print **"OK: these
   are the team's fine-tuning files."**

**Outputs:** `real_train.jsonl`, `real_val.jsonl`, `real_test.jsonl`, `labels.json`,
`build_log.json`, the fine-tuning files in `sft/` (`cfpb_train.jsonl`, `cfpb_val.jsonl`, `cfpb_test.jsonl`,
`manifest.json`) and `review_sample.csv` (100 teacher replies for hand review). On a GPU runtime,
step 12 adds the base-model baseline: `baseline/predictions_base.jsonl` and
`baseline/report_base.json`. The record format is described in step 8 of the notebook and in
`data/README.md`.

**How it matches the scripts:** the notebook runs the same steps as
`scripts/build_dataset.py` (window 2023-08-25 to 2026-06-17, seed 42). The exploration in step 2
is a short version of `scripts/explore_cfpb.py`. If you change a rule in one, change it in the
other and rebuild.

**Checks:** step 9 compares two things against the team's build.
- **Complaint IDs per split.** These must match. If they do not, the snapshot or a setting differs.
- **File SHA-256.** This also matches when the library versions match the team's build.

Before sharing, it was run end to end twice: with pandas 3.0.6 / pyarrow 26 and with
pandas 2.2.3 / pyarrow 18.1.
