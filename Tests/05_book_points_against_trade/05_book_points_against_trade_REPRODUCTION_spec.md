# Test 05 — book_points_against_trade (REPRODUCTION SPEC)
Self-contained recipe for a fresh chat (which has CURRENT_STATE.md: open-stamp; WRB+60s; MBP-10
schema; ESZ5; sizes uint32->int64; grouping; window designs; imbalance orientation +1 long/-1 short).
Mode: exploration. Status: COMPLETE — null by the pre-set standard (CI must clear 0.5).

## Purpose (Phase B — directional book signal)
Does the population-oriented book direction (bid-heavy = up) point AGAINST the trade more, or more
strongly, for non-runners (failed_trades) than for runners (target_reached)? "Points against" =
negative oriented imbalance. Tests whether the weak L1 continuation signal from the population
diagnostic separates the two groups at the trade-decision horizon.

## Result (headline)
NULL by the agreed standard. SLOPE dead at L1 (A1 0.441 / A2 0.521 / B 0.458) — confirms 03's
slope-null was the statistic, not the L1-10 depth. PRE-ENTRY context (A1) null (level 0.515, CI
[0.436, 0.596]). B no-floor headline 0.545 is mostly the length-composition artifact (HIGH-pre-entry
stratum 0.596 vs LOW 0.509). The only lean: IN-TRADE LEVEL ~0.58 (A2 0.577; Design A cut-time-matched
0.584, 95% CI [0.499, 0.668]) — CI touches 0.5, and the orientation self-check over 180s windows is
-0.05 (book->direction channel NOT operating at this horizon, consistent with population decay by
60s). Suggestive, no working mechanism, not promotable. Nothing goes to the Feb holdout.

## Prior that frames the result (book_level_direction_population.csv)
Oriented L1 imbalance LEVEL leads forward mid return: corr +0.154 / dir-hit 0.630 at 1s, decaying to
+0.025 / 0.516 by 60s. L1 cleanest; L1-5/L1-10 dilute. => the book->direction channel is a ~1s effect,
~chance by 60s. Any feature routing through book direction is expected weak at the 60-180s trade
horizon. This is why 05 (and a same-channel 06) are expected null.

## Inputs
- tsl_episodes_clean.parquet (side, first_entry_utc, last_exit_utc, source_file, episode_id,
  trading_date). October universe: 92 episodes, single entry / single exit.
- wrb_1m.parquet (ts_event, symbol, timeframe, direction) — for pt1.
- MBP-10 windowed parquet (ts_event, instrument_id=294973, bid_px_00, ask_px_00, bid_sz_00..04,
  ask_sz_00..04 needed; ~73.7M rows on external SSD — stream, do not materialize).
- config.toml: paths.episodes, run.resolved.windowed_parquet. Script also takes --wrb.

## Grouping (= CURRENT_STATE; Reading B inclusive pt1; P&L not used)
pt1 = first 1m ESZ5 WRB in trade direction (bullish=long/bearish=short) with ts_event >= floor_min(entry).
reached = pt1 exists AND exit >= pt1 + 60s. anchor = pt1 (reached) / floor_min(exit) (failed).
target_reached 52 / failed_trades 40. entry-bar-pt1 cases = 22 (report excl-22 = 30/40).

## Feature
Per book snapshot, downsampled to one snapshot per SECOND (last in second):
  imbalance(L1) = (bid_sz_00 - ask_sz_00) / (bid_sz_00 + ask_sz_00)   in [-1,1]   (L1-5 = ride-along)
  oriented      = imbalance * (+1 long / -1 short)    (positive = book supports trade direction)
Per window:  LEVEL = mean(oriented)  [PRIMARY] ;  SLOPE = OLS(oriented on elapsed seconds) [secondary]
Pre-registered direction (both): AUC(reached > failed).

## Windows (three, pre-registered; anchor as above; per-second within each)
  A1  pre-entry context   [entry-180s, entry)                  fixed 180s, identical both groups.
  A2  in-trade run-up     [max(entry, anchor-180s), anchor)    entry-floored, anchor excluded.
  B   decision-point      [anchor-180s, anchor)                NO entry floor (live-screen feature).
Rationale for three: per-bar collapse was abandoned — the 3-bar window is mostly 1 bar (failed: 16/40
are 1-bar, only 9/40 full-3-bar), so bar-to-bar trend is undefined for the majority. Per-second within
the window is robust where per-bar is not. A1 isolates pre-entry context without the composition
confound; A2 is the clean in-trade run-up; B is the faithful live-screen window but length-confounded.

## Confound controls (decided BEFORE coding, from data)
- B is back-anchored with no floor => pre_entry_frac differs by group (reached ~0.70 / failed ~0.55;
  AUC of the fraction ALONE = 0.621, in the pre-registered direction). B therefore reports
  pre_entry_frac per trade and prints AUC stratified by a median split. A B signal only in the HIGH
  stratum = composition artifact, not book direction. B is exploratory-with-caveat.
- A1 "Design A" collapses to PRIMARY (fixed-length pre-entry window: no elapsed-time/survivorship
  confound; every reached trade is an eligible peer; per-cut AUC == pooled AUC). Reported as PRIMARY
  plus a cluster-bootstrap CI over the 40 failed (the only thing "Design A" adds pre-entry).
- Tripwire: a window is flagged + excluded if its in-window per-second snapshots have a gap > 120s
  (session/halt) or a mid jump > 40 ticks (roll discontinuity; series is unadjusted). Oct ESZ5 =
  single front month, intraday episodes => expected 0 flags (observed: 0).

## Designs / statistic
- PRIMARY 52/40 and excl-22 (30/40): pooled rank-AUC (P(reached feature > failed feature)), pure-numpy.
- CONTROL Design A (in-trade tau): each failed cut at elapsed tau=hold vs reached peers still open &
  pre-pt1 at the same tau, trailing W=60s window, oriented L1 LEVEL. Per-cut AUC + cluster-bootstrap
  95% CI over the 40 cuts (seed 0, 10000 resamples).
- Read = AUC + CI, NOT p-values at n~40/52. Standard to clear: CI excludes 0.5. Exploration screens.
- Orientation self-check: corr(mean oriented level, oriented mid change) over B; expect >0 if signal
  operating. Observed -0.05 => not operating at 180s (consistent with population decay).

## Reproduce
Deterministic, memory-safe: single streamed per-batch pass, downsampled to one snapshot/second
(~256k rows/month, ~70 grid-hours), filter-in-loop. Close edit of queue_imbalance_slope.py.
  python3 book_points_against_trade.py --config config.toml --wrb /path/to/wrb_1m.parquet
  (--depth L5 for the L1-5 dilution ride-along; --designA-window-seconds default 60.)
Outputs book_points_against_trade_results.csv (per-trade level/slope/n/midchg/flag for A1/A2/B +
pre_entry_frac). Validated off-data: grouping 52/40+22 and pre_entry_frac AUC 0.621 reproduce against
real episodes/wrb; orientation sign, slope direction, tripwire, AUC (separable/tied/NaN), bootstrap
determinism, 1-snapshot edge case all pass on synthetic book. The book-read path itself is only
exercisable on the SSD (not in a chat sandbox).

## Gate (unchanged)
05 + 06 (book_direction_change) both null => stop feature-hunting => re-target (isolate the 16 actual
losers) or expand data. A strategy decision, not feature #7. 05 is null. Next: 06, pre-registered blind.
