# SPEC 06-1 — Window-sparsity descriptive gate  &  06-4 — Behavioral relabel

Two infrastructure units (not hypothesis tests). Short by design.

===============================================================================
## 06-1 — Window-sparsity descriptive pass  (describe_window_sparsity.py)
PURPOSE: before freezing 07's estimator, measure (not assume) how many usable seconds a 60s
Design-A window has. Gates Amihud-vs-slope and 07b viability. Read-only, deterministic, NO test.
COUNTS per window: n_active_sec, n_trade_sec, n_with_flow_sec (oriented>0 = 07b subset),
n_withvol_sec, n_midmove_sec, sum_abs_dmid_ticks. Reports failed-cut vs reached-peer distributions.
RUN: python3 describe_window_sparsity.py --config <cfg> --wrb <wrb_1m.parquet>
RESULT (Oct): failed-cut n_with_flow_sec med 27, reached-peer 25 (min 8-9). 07b VIABLE (not sparse);
both Amihud ratio and slope estimable. Also surfaced: failed windows carry MORE price movement than
mid-flight peers (|Δmid| med 46 vs 31 ticks) — the asymmetry 08/07a later confirmed.

===============================================================================
## 06-4 — Behavioral relabel  (build_behavioral_relabel.py)
PURPOSE: the 52/40 contrast is muddy (most failed_trades are PROFITABLE early-exits, diluting any
exit signal). Relabel into clean behavior classes; produce a reusable single-source label.
CLASSES (priority order; losers take precedence over pt1, matching the exhaustion de-dupe):
    losing_trade     : realized_pnl < 0
    reached_target   : NOT losing AND pt1 reached
    below_target_win : NOT losing AND pt1 NOT reached    (the profitable early-exits)
  'scratch_trade' DROPPED: Oct pnl has no zero-cluster (1 trade ==0); any band is arbitrary. May be
  RE-INTRODUCED later as a BEHAVIORAL def (fast exit + near-zero excursion), needs MAE — not a pnl band.
RESULT (Oct): 16 / 47 / 29. Reconciles exactly with exhaustion spec (16 losers, 5 pt1-overlap, 47
non-loser reached). Clean EXIT contrast = losing_trade(16) vs reached_target(47) == the loser spine;
below_target_win(29) held out. realized_pnl is in POINTS (tick-granular), reconciles with extracted
entry/exit prices at corr 1.0.
OUTPUT: behavioral_relabel_2025-10.parquet/.csv (uid, side, entries, group, realized_pnl, is_loser,
failure_tag, hold, pt1_open_el). Attach as single-source exit label in downstream tests.
RUN: python3 build_behavioral_relabel.py --config <cfg> --wrb <wrb_1m.parquet> --out behavioral_relabel_<month>

## OCTOBER-HARDCODE DEBT (applies across 06-1..06-5 + spine)
horse_race_spine self-test, build_behavioral_relabel, and test_behavioral_baseline assert Oct counts
(52/40, 16/5/47, 16/47) and INSTRUMENT_ID=294973 / MONTH="2025-10" / SYMBOL="ESZ5" are hardcoded in
trade_flow_exhaustion.py. These FAIL LOUD on any other month BY DESIGN. De-Octoberize (resolve front
month by volume, parametrize month/instrument, drop count asserts) before any holdout run.
