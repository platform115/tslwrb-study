# PRE-REGISTERED ADAPTATION PLAN — Strategy 2 entry thresholds
> Frozen 2026-11-17 (T-EN72), BEFORE any validation-month run of these variants.
> Purpose: when validation shows the expected quality reduction, the response
> is to execute THIS plan, not to improvise.

## Design assumption (user)
The burst WINDOW is near-universal: fixed at 7 seconds everywhere.
Only the TICK thresholds adapt. Direction = burst sign. No old-signal
requirement, no session cut, 120 s clustering, 5-bar cooldown.

## The frozen formulas
burst threshold = 0.042 x R_est        thrust threshold = 0.17 x R_est
(shares from T-EN71: daily top-0.5% cutoff = 4.2% of day range; 50tk = ~17%)

## The seven variants (constants frozen from training months)
FIXED      13 tk burst / 50 tk thrust (baseline)
PRIORDAY   R_est = previous session's RTH range
EWMA       R_est_d = 0.7 R_est_(d-1) + 0.3 R_(d-1)
ATR14D     R_est = mean RTH range, trailing 14 sessions (Wilder 1978)
TRAIL21    R_est = mean RTH range, trailing 21 sessions
OVERNIGHT  R_est = 0.98 x overnight ETH range (Crabel 1990 lineage)
OPEN30     R_est = 2.62 x first-30-min RTH range; trades only after 30 min

## Training-month results (the in-sample cost of adaptivity; T-EN72)
FIXED +214.6 | PRIORDAY +143.8 | EWMA +132.9 | OPEN30 +120.4 | ATR14D +119.0
| OVERNIGHT +99.4 | TRAIL21 +91.5  — all positive; adaptivity costs 33-57%
of fixed's total in SAME-regime months (expected; the payoff is cross-regime).

## The validation protocol (to execute when user authorizes)
1. Run all seven variants UNCHANGED on 2021-09 and 2024-11 (and later the
   four purchased months: 2023-02, 2023-07, 2025-04, 2026-03).
2. Record per variant per month: total, per-trade avg, max-below-start DD,
   trades, his-matched.
3. DECISION RULE (pre-registered): rank variants by their WORST-month total
   (maximin). Adopt the maximin winner for the Strategy 2 v1 spec.
   - If FIXED wins maximin even across regime shifts, the conclusion is
     "fixed numbers per regime + periodic manual recalibration" and the
     adaptive question closes for now.
4. NO new estimators, coefficient changes, or share changes after seeing
   validation results. Any new idea starts over on training months and must
   then be validated on months not yet used for it.
5. The v11 management is a sketch; when management is rebuilt, this plan's
   entry-threshold comparison re-runs unchanged under the new management.

## AMENDMENT 1 (2026-11-17, T-EN73 — before any validation run)
Added to the pre-registered battery after P4.70:
  INTRADAY10  R_est = 22.7 x mean true range of the last 10 COMPLETED 1-min
              bars, recomputed every bar (user's reversed rolling estimator)
  INTRADAY20  same with 20 bars (c = 22.7)
  WINDOW RULE (replaces "7 s assumed"): window = the trailing 99th-percentile
              duration of one-sided signed-flow runs, recomputed monthly
              (= 8-9 s in both training months; the only measurement found
              that independently yields the working window; price memory is
              not it - 1-s autocorrelation dies at lag 1 - and extreme 20-s
              moves show NO time concentration, B3 null).
Which estimator GENERATES the fixed numbers: ATR14D (daily burst median 12.9
vs 13; thrust 52 vs 50; lowest RMS miss with TRAIL21). Training P&L of the
new variants: INTRADAY10 +149.1 (32 trades, 78% win, never below start),
INTRADAY20 +133.6 - the best adaptive results so far.
Decision rule unchanged: maximin on worst-month total, all variants frozen.

## AMENDMENT 1a (clarification, 2026-11-17 — still before any validation run)
The window rule applies to variants 2-9 (all adaptive variants); FIXED (variant
1) keeps the 7 s window and 13/50 ticks unchanged as the pure control. The
window rule adapts the WINDOW only (slowly, monthly); the estimators adapt the
TICK thresholds only. Nothing adapts the 0.042 / 0.17 shares, the 5-min thrust
window, the clustering, or the cooldown - those stay fixed in every variant.

## POST-VALIDATION DECISIONS (user, 2026-11-17, after T-EN75)
- ATR14D adopted per the maximin rule (battery winner: worst month +26.2).
- INTRADAY10 RETAINED as a second lane by user decision: the project runs
  multiple clean entry strategies, each allowed to be low-frequency in some
  periods; a lane that signals rarely but cleanly is acceptable by design.
- Detector-side maximin: D6-accel + thrust 30.
