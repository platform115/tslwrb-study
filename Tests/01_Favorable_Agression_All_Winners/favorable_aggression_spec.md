# Test Spec — favorable_aggression_all_winners_included
Frozen 2026-06-11. Mode: EXPLORATION (signal-hunting, not validation). Single pre-registered
feature, fully deterministic, re-runnable to identical output.

## Objective
Does MBP-10 order flow in the final window of an active ES trade separate **runners**
(reached the WRB pt1 target) from **non-runners** (exited before it), via *favorable
aggression*?

## Data
- Contract: **ESZ5** (Oct-2025 front month, resolved by traded volume — not assumed).
- Universe: 92 single-fill episodes in `tsl_episodes_clean` with `trading_date` in 2025-10,
  8am–4pm CT inclusion. All 92 are single entry / single exit (no scaling in October).
- Bars: `wrb_1m` / `es_1m_front` are **OPEN-stamped** (`ts_event` = interval start; verified
  via CME maintenance-gap edges 20:59→22:00 UTC and the 13:30 UTC cash-open volume jump).
  A 1m WRB **completes at `ts_event + 60s`**.
- Order flow: MBP-10 windowed parquet (`mbp10_ESZ5_2025-10_windowed.parquet`); trade prints
  carrying aggressor `side`.

## Grouping — Reading B, INCLUSIVE (P&L is NOT used)
- `pt1` = first 1m WRB in the trade's direction (bullish for long, bearish for short) with
  `ts_event >= entry-minute` (the entry bar itself may qualify — "inclusive").
- `target_reached` (n=52): trade still active at pt1 completion, i.e. `exit_utc >= pt1.ts_event + 60s`.
- `failed_trades` (n=40): exited before the first same-direction 1m WRB completed.

## Window — per trade; anchor EXCLUDED; entry-bar fallback
- Anchor = the `pt1` bar (reached) or the `exit` bar (failed).
- Window = up to **3 contiguous 1m bars strictly before the anchor**, floored at the entry minute.
- If that set is empty (pt1 == entry bar, or exit within the entry minute) → window = the
  **entry bar** (fallback). Applied to BOTH groups.
- Window time span = `[min(window_bar.ts_event), max(window_bar.ts_event) + 60s)`;
  `window_seconds = n_bars * 60` (60 / 120 / 180).

## Feature — single, pre-registered
`favorable_aggression` = **oriented signed aggressor delta, per second**:
1. `signed_delta` = Σ over trade prints in the window of `size * s`, where `s = +1` for a
   buy-aggressor print, `-1` for a sell-aggressor print. (The buy/sell encoding is
   **self-verified** at run time, expected `sign_mult = +1`; see self-checks.)
2. `oriented = signed_delta * (+1 if long else -1)`.
3. `feature = oriented / window_seconds`.
- Zero-trade windows → `feature = 0`, flagged and counted.

## Hypothesis — direction FIXED before running
`target_reached` shows **higher** `favorable_aggression` than `failed_trades`.
One feature, one direction, no parameter sweep (guards against multiple-testing / backtest
overfitting — Bailey & López de Prado, 2014).

## Comparison
- **Primary:** target_reached (52) vs failed_trades (40). Mann-Whitney U (one-sided, per the
  fixed direction) + **AUC** = P(a random reached trade > a random failed trade). Report
  median / IQR and the two distributions. In exploration the p-value is descriptive, not a gate.
- **Stratification (NOT artifact removal):** repeat with the 22 entry-bar-pt1 trades removed
  (30 vs 40), to locate where any signal lives — *immediate entry confirmation* (the 22) vs
  *run-up across an active hold* (the other 30).

## Determinism / audit
- Fixed contract, universe, window rule, feature formula; no randomness or sampling → identical
  re-run. Inputs pinned by file; outputs are CSVs.
- Self-checks (script asserts / reports): ESZ5 only; every window strictly before its anchor
  (causal — no event-bar leakage, except the intentional 22 fallback bars); `size` cast to int64
  before arithmetic; **sign convention verified** by `corr(signed_delta, in-window price change) > 0`.
- Outputs: `windows_table.csv` (Part 1, grouping + windows) and `favorable_aggression_results.csv`
  (Part 2, per-trade feature + group + flags) plus printed summary stats.

## Known caveats (documented, accepted, non-blocking)
- The 22 reached windows ARE the entry/pt1 WRB bar (contain pre-entry flow and the favorable
  move itself) — intended here as the real-time "this is working" confirmation signal; isolated
  via the stratification, not discarded.
- Anchors are asymmetric (pt1 vs exit). Accepted: this is descriptive analysis of data on hand,
  not a deployable rule. A real-time-observable anchor is required before the separate validation chat.
- Window duration differs by group (reached median 60s, failed 120s); per-second normalization
  mitigates. If the result tracks duration rather than flow, treat as a confound.
- A few windows fall in the 08:00–08:30 CT pre-cash-open Globex period (thinner book); surfaced
  via per-window trade count.

## Queued after this test
- Segregate pass (option C) as its own analysis of the 22 entry-bar-pt1 trades.
- Matched time-since-entry control test (symmetric anchor).
- Second feature: Order Flow Imbalance (Cont, Kukanov & Stoikov, 2014) and/or volume-normalized
  aggressor imbalance ratio.

---

## Outcome log

### 2026-06-11 — favorable_aggression_all_winners_included (RESULT)
Run on ESZ5 windowed MBP-10 (3,702,549 trade prints). Sign self-check: corr(signed_delta,
in-window price change) = **+0.755** -> buy-aggressor encoding `side=="B"` confirmed empirically.

- PRIMARY (52 vs 40): median reached **+2.939** / failed **+1.728**; **AUC 0.576**, one-sided p 0.107.
- STRATIFIED, 22 entry-bar-pt1 removed (30 vs 40): median reached **-0.275** / failed **+1.728**;
  **AUC 0.359**, one-sided p 0.978 (points the OPPOSITE way).

Read: pre-registered hypothesis (reached > failed) NOT supported.
1. PRIMARY's mild positive is largely label-coupling — the 22 entry-bar trades are runners *because*
   a same-direction WRB formed at entry, and their window IS that WRB bar (large favorable move);
   feature partly restates the label. Removing them drops reached median +2.94 -> -0.28.
2. Among genuine run-up cases, favorable aggression is LOWER in runners and the contrast reverses.

Caveat / status: the reversal is **confounded by the asymmetric anchor** (reached anchored on
pt1-formation, failed on discretionary exit — flagged at design time). So this is a **design
negative, not yet a feature negative**. Disambiguated by the matched-time control below before any
conclusion about the feature. Pending: outlier check on the stratified reached group (describe()).

### Matched-time control — favorable_aggression_matched_time (QUEUED/RUN)
Symmetric anchor. Window = [entry, entry+T) from the exact entry timestamp (causal, post-entry only;
removes entry-bar contamination). Same grouping as primary. T = 60s (pre-registered single value).
Sample = trades open at entry+T: **50 reached / 32 failed** (drops 2 reached, 8 failed with hold<60s
-> cannot speak to sub-60s cuts). Same feature, same Mann-Whitney/AUC.
Disambiguation rule:
- AUC ~0.5 here  -> original reversal was the anchor; feature simply doesn't separate (feature ~null).
- reached > failed -> original result was a design artifact; favorable early flow favors runners.
- reached < failed -> reversal persists under symmetric anchor; would need a real economic story + replication.
