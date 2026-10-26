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

## `train_qlora_colab.ipynb`: QLoRA fine-tuning and baselines (Week 2)

Fine-tunes Qwen2.5-7B-Instruct with QLoRA on `sft/cfpb_train.jsonl` and scores it on test with
`eval/run.py`, **with and without** the guidance passages (the Week 3 RAG comparison needs both).
`MODE = "baseline"` runs the base model through the same generation code, zero-shot or with
`FEW_SHOT = 3` (the course plan's Week 1 gate asks for both).

**Run it**
1. Share one Drive folder: the owner creates `cfpb-capstone`, shares it with the team as Editor,
   and each member adds a shortcut to it in My Drive ("Shared with me" → right-click →
   Organize → Add shortcut → My Drive). The owner then runs `make_dataset_colab.ipynb` once with
   `SAVE_TO_DRIVE = True` and `OUT_DIR = "cfpb-capstone/data"`.
2. Open this notebook on a **T4 GPU** runtime. Optional: add a Colab secret `WANDB_API_KEY` for
   W&B; otherwise runs are tracked with MLflow in `MyDrive/cfpb-capstone/data/runs/mlruns`.
3. In the configuration cell set `MEMBER`, pick a `RUN` (or `MODE = "baseline"`), then
   **Runtime → Run all**. First time: `SMOKE_STEPS = 20` measures memory and the full-run time.

Checkpoints are saved to Drive, so a recycled session resumes when you run all again. Each run
saves its scores in its own `runs/<run>/summary.json` (so members finishing at the same time never
overwrite each other), and `runs/runs.csv` is rebuilt from all of them: the comparison table for
the report. Storage counts against the folder owner's quota (about 1 to 3 GB per run with
checkpoints); delete a run's `checkpoints/` once its `adapter/` is saved.

**Runs (course plan: at least two configurations and one ablation; every member runs one job)**

| Run | What changes |
| --- | --- |
| `base_0shot`, `base_3shot` | Baselines (`MODE = "baseline"`, `FEW_SHOT = 0` / `3`) |
| `r16_lr2e-4` | Reference: rank 16, alpha 32, lr 2e-4, 2 epochs, all linear layers |
| `r64_lr1e-4` | Higher rank, lower learning rate |
| `r16_attn_only` | LoRA on attention projections only |
| `ablate_no_oos` | Ablation: no out-of-scope training rows (does refusal come from them?) |
