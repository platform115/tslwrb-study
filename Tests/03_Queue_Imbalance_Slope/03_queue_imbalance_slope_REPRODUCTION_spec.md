# Test 03 — queue_imbalance_slope (REPRODUCTION SPEC)
Self-contained recipe for a fresh chat (which has CURRENT_STATE.md: open-stamp; WRB+60s; MBP-10
schema; ESZ5; sizes uint32->int64; grouping; window designs; imbalance orientation). Mode:
exploration. Status: COMPLETE — near-null.

## Purpose
Stall via book ratio: does the SLOPE of oriented queue-imbalance across the window separate
target_reached from failed_trades? (favorable book support fading = stall.)

## Result (headline)
PRIMARY all 0.436 / excl-22 0.448 ; CONTROL Design A (W=60s) 0.458, 95% CI [0.341, 0.575].
All at/below 0.5 -> imbalance SLOPE does not separate the groups.
Defect/repair history (same index): first run OOM'd at ~19 GB -> reader rewritten to stream narrow
per-batch arrays + filter in-loop (repair). Orientation self-check fired corr -0.357; the population
diagnostic below showed that was a MISCALIBRATED long-horizon/small-n statistic, NOT an inverted
feature -> orientation (bid-heavy = favorable for long) is correct; AUCs stand.

## Population orientation diagnostic  (book_level_direction_population.py — result promoted to CURRENT_STATE)
73.7M snapshots reduced to a per-second grid (~256k rows, ~71 grid-hours) over the whole windowed file.
corr(imbalance LEVEL, forward mid return), depth x horizon: POSITIVE everywhere (continuation),
strongest L1 @ 1s = +0.154 (dir-hit 0.630), decaying to +0.025 / 0.516 by 60s. No absorption flip;
L1 cleanest, deeper dilutes. => favorable book = bid-heavy(long)/ask-heavy(short); signal is ~1s-scale,
~chance by 60s. Run: `python3 book_level_direction_population.py --config config.toml`.

## Inputs
tsl_episodes_clean.parquet (side, first_entry_utc, last_exit_utc, source_file, episode_id, trading_date);
wrb_1m.parquet (ts_event, symbol, timeframe, direction); MBP-10 windowed parquet
(ts_event, instrument_id=294973, bid_px_00, ask_px_00, bid_sz_00..09, ask_sz_00..09).

## Grouping (= CURRENT_STATE; Reading B, inclusive; P&L not used)
target_reached 52 / failed_trades 40.

## Feature
Per book snapshot: imbalance = (Sum bid_sz_00..09 - Sum ask_sz_00..09)/(Sum both)  (L1-10).
oriented = imbalance * (+1 long / -1 short). feature = OLS slope of oriented imbalance on elapsed
seconds within the window (per-second). Descriptive secondary: mean oriented level.
NB population says L1 (not L1-10) carries the cleaner LEVEL signal; not re-run since slope is near-null.

## Designs (= CURRENT_STATE window definitions)
PRIMARY: up to 3 1-min bars before anchor (pt1 bar reached / exit bar failed), floored at entry,
anchor excluded, entry-bar fallback; report 52/40 and excl-entry-bar-pt1 (30/40).
CONTROL Design A: 60s trailing window; each failed cut vs reached peers still open & pre-pt1-open at
the same elapsed tau (auto-excludes the 22). Per-cut AUC + cluster-bootstrap CI.

## Statistic
AUC = P(reached slope > failed slope) (pre-registered direction). Pure-numpy. Design A = per-cut AUC,
95% CI via cluster bootstrap over the 40 cuts (seed 0). The in-script orientation self-check is
known-miscalibrated — trust the population L1/1s sign instead.

## Reproduce
Deterministic, memory-safe per-batch streaming. Scripts: book_level_direction_population.py (--config),
then queue_imbalance_slope.py (--config --wrb /path/to/wrb_1m.parquet).
