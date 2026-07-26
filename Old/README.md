# tslwrb-study

Research/EDA study inferring mechanical entry-timing and exit rules from forum trader **wrbtrader**'s ES futures record, using Databento MBP-10 order-flow data. Sibling to `es-trading-agent-v3`, kept separate on purpose (fast-iterating analysis, not the backtester's write-once-spec discipline). If a rule proves out, it gets ported into the backtester as a YAML spec — one-way export.

- **Full context:** `HANDOFF_wrbtrader_timing_inference.md` (read first).
- **Working rules + conventions:** `CLAUDE.md` (auto-applied by Code sessions).
- **External paths + pinned deps:** `config.toml` (the only place paths live; scripts read from it).

## Layout

```
scripts/   numbered pipeline: 01_cost_check.py, 02_reduce_to_windows.py, 03_align_verify.py, 04_diag_*.py ...
results/   committed small summary outputs, tagged <contract>_<month>
config.toml, CLAUDE.md, HANDOFF_*.md, .gitignore
```
Big data (raw DBN, windowed parquet) lives on the external SSD and is gitignored — the repo holds only scripts, small results, docs, and config.

## Run

```bash
python3 -m venv venv && source venv/bin/activate
pip install databento pandas pyarrow duckdb     # then pin databento version in config.toml
# edit config.toml paths first, then:
python3 scripts/01_cost_check.py
```

First script after the whole-month pull is **alignment/verification** (resample MBP-10 trades to 1m, reconcile against `es_1m_front`) — before any feature is built.
