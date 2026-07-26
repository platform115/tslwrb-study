# Test 02 — favorable_aggression_cut_time_matched (REPRODUCTION SPEC)
Self-contained recipe to recreate this test in a fresh conversation. That chat has CURRENT_STATE.md
(bar OPEN-stamping, WRB completes at ts_event+60s, MBP-10 schema, side=="B"=buy/sign_mult=+1, size
uint32→int64, ESZ5 front, WRB pt1 definition). Mode: exploration. Status: COMPLETE — near-null.

## Purpose
Symmetric-anchor variant of Test 01 ("Design A"): does favorable aggression in the trailing window
before a cut differ from the same-elapsed-time trailing windows of trades that were still running?
Removes Test 01's asymmetric-anchor confound by matching on elapsed-time-since-entry.

## Result (headline)
AUC (per-cut, 40 cuts) = P(running peer's favorable_aggression > cut's) = **0.569**,
95% cluster-bootstrap CI **[0.459, 0.674]** (straddles 0.5). Pooled over 627 pairs: 0.599 (descriptive).
Median cut favorable_aggression −0.283. Sign self-check corr +0.631.
Verdict: near-null; CI includes 0.5 → not a carry-forward signal.

## Inputs (files)
- `tsl_episodes_clean.parquet` — side, first_entry_utc, last_exit_utc, source_file, episode_id, trading_date.
- `wrb_1m.parquet` — ts_event, symbol, timeframe, direction (for pt1).
- MBP-10 windowed parquet — action=="T" trade prints; ts_event, instrument_id(294973), side, size, price.

## Grouping (same as Test 01; Reading B, inclusive; P&L not used)
pt1 = first 1m WRB in trade direction with ts_event ≥ entry-minute. target_reached = exit ≥ pt1.ts_event+60s
(52); failed_trades = otherwise (40).

## Design A — risk-set / cut-time-matched
For each FAILED trade f (cut at elapsed τ = its hold, cut time = exit):
- cut window  = [max(entry_f, cut − W), cut).  feature_f = oriented signed-delta/sec.
- risk set    = TARGET_REACHED trades r with pt1_open_elapsed_r > τ  (still open AND pre-pt1-open at τ).
                NB: this auto-excludes the 22 entry-bar-pt1 trades (their pt1 opens before entry).
- per peer r: anchor = entry_r + τ; peer window = [max(entry_r, anchor − W), anchor); feature_r = oriented delta/sec.
- record pair (feature_f, feature_r) for all r in risk set.
Oct-2025: 40 cuts, median 16 peers/cut, 0 empty risk sets, 627 pairs. W = 60s (trailing; --window-seconds).

## Feature
oriented signed aggressor delta per second:
  signed_delta = Σ size·s in window (s=+1 buy / −1 sell); oriented = signed_delta·(+1 long / −1 short);
  feature = oriented / window_seconds. (Window floored at entry; same length within a risk set.)
Hypothesis (fixed before run): running peers > cuts ⇒ AUC > 0.5.

## Statistic
- AUC (per-cut) = mean over the 40 cuts of (fraction of that cut's peers with feature > the cut). Each
  cut = one observation (respects peer-reuse non-independence). 95% CI via cluster bootstrap over the 40
  cuts (10,000 resamples, --seed 0). HEADLINE.
- Pooled AUC over all 627 pairs = descriptive only (pairs overlap; no p-value leaned on).
- Sign self-check: corr(signed_delta, in-window price change) > 0.

## Reproduce
Deterministic (bootstrap seed fixed). Script: favorable_aggression_cut_time_matched.py; reads
config.toml [paths] + run.resolved.windowed_parquet, takes --wrb. Pure-numpy throughout.
