# tslwrb-study

Research/EDA project inferring mechanical entry-timing and exit rules from forum trader **wrbtrader**'s ES futures trade record, using Databento MBP-10 order-flow data. Sibling to `es-trading-agent-v3` — kept separate on purpose: this is fast-iterating exploratory analysis, not the backtester's write-once-immutable-spec discipline. If a rule proves out here, it gets ported into the backtester as a YAML spec (one-way export).

Full context lives in `HANDOFF_wrbtrader_timing_inference.md` — read it first.

## Working rules

- **Scripts compute, the LLM does not.** All numbers, fills, feature values, and reductions come from deterministic Python. The LLM gathers intent and writes/reads scripts; it never produces a result number itself.
- **Flag decisions for sign-off** rather than silently defaulting. Where no established precedent exists, say so explicitly — do not invent terms, concepts, or stories.
- **Diagnostic before rule.** Run the pre-specified diagnostic and compare against a within-window null before building any rule. A null result is an acceptable, money-saving end — ship the R2 scaffold + documented discretion and stop.
- **Argue both sides, then weigh.** Surface competing interpretations and flag self-serving or overfitting reasoning, especially in-sample results that may not survive the holdout.

## Structure & naming

- **Big data is gitignored.** Raw `.dbn` and the windowed parquet live on the external SSD (path in `config`). Never commit gigabytes. Repo = scripts + small summary outputs + docs + config only.
- **Numbered pipeline:** `01_cost_check.py`, `02_reduce_to_windows.py`, `03_align_verify.py`, `04_diag_*.py`, ... Execution order must be legible from filenames.
- **Tag every data + result file with contract + month:** `mbp10_ESZ5_2025-10_windowed.parquet`, `03_align_ESZ5_2025-10.md`. Adding a new month = new tagged files, never a restructure.
- **Reproducibility:** every result stamped with git commit + data provenance (contract / month / window definition). Pin the `databento` version in `config`.
- **Commit small summary outputs** (the tables pasted back into chat) — they're the durable, auditable record if SSD data is later deleted.

## Data acquisition (MBP-10)

- Buy the **whole sample month** per contract (the request wizard makes per-window requests impractical); **window locally** in `02_reduce_to_windows.py`. Run `metadata.get_cost` before buying.
- Month 1: **October 2025, contract `ESZ5`**. Month 2 (only after M1 validates): **February 2022, contract `ESH2`**.
- First script after the pull is **alignment/verification** (resample MBP-10 trades to 1m, reconcile against `es_1m_front`) — before any feature is built.

## Environment

- Python venv at the `tslwrb-study` project root (do not reuse the backtester's venv).
- Process the ~92GB month by **streaming** (DBN iterator or DuckDB out-of-core) — never load the whole file into RAM on the M1.
