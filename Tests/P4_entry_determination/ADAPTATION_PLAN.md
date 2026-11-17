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

## AMENDMENT 2 (2026-11-17, T-EN77): the thrust-window rule
Derivation measurements (P4.74, training months): post-burst drift crosses
zero at 74-169 s (mean ~2 min); directional 1-min run lengths median 1-2,
75th pct 2-3 min; variance ratio weakly peaks at 1-2 min (near-flat - weak
instrument). CONVERGENT BAND: minute-scale moves live ~1-3 minutes. No
measurement pins 2 min sharply (unlike the 8-9 s sweep duration for the
burst window) - recorded as a BAND, not a point.
FROZEN RULE: thrust window = the 75th-percentile directional run length of
1-min RTH returns over the trailing 21 sessions, clamped to [2, 3] minutes.
Bars-only, computable in every month and regime. Where per-second data
exists, the post-burst zero-crossing serves as the cross-check.
Thrust thresholds scale by sqrt(window/5) from the frozen 5-min shares
(the sqrt rule itself remains a flagged choice pending percentile-matched
recalibration).

## AMENDMENT 3 (2026-11-17, T-EN78): intraday-rolling thrust window
w(bar) = clamp(75th-pct length of directional runs COMPLETED in the last N
bars, lo..hi), fallback 2; thrust threshold scales sqrt(w/5). Training cost
~10-20%% of static-2min totals with quality intact (win rate holds, avg loss
shrinks, DD 0 in the INTRADAY10 lane); N (30/60/120) barely matters, clamp
[2,3] ~ [1,4]. FROZEN VARIANT for the next validation batch:
rolling N=30, w in [1,4] (most reactive, least constrained), alongside the
static w=2 and the 21-session rule (Amendment 2) for comparison.

## AMENDMENT 4 (2026-11-17, T-EN82): the firing-gap rule
Derivation (P4.79): burst crossings are heavily clustered - 68-75% of
inter-arrival gaps are under 5 s (within one sweep), with a clear valley at
5-30 s (3-5% per bin): an episode is OVER by ~10-30 s. The episode-count
curve shows NO clean knee (smooth decay - bursts cluster at all scales;
stated as a null for that instrument). Upper bound from the post-burst
drift life (T-EN77 A: positive for 74-169 s): the gap must stay below it
so re-fires still catch live moves. BRACKET: [~30 s, ~60-75 s] - exactly
where the P&L grid peaks (T-EN81).
FROZEN RULE: gap = half the post-burst drift zero-crossing, clamped to
[30, 60] s, recomputed monthly where per-second data exists; 45 s default
where it does not. (Training: Feb 37 s, Oct 60 s.) Wait-after-exit = 1 bar
rides along as the T-EN81 candidate. Both await the next validation batch.

## AMENDMENT 5 (2026-11-17, T-EN91/92): burst share derivation + lane adapters
BURST SHARE, INTRADAY10 LANE — DERIVED, static 0.022 justified:
q = |8-s move| / R_est is regime-INVARIANT in this lane (share 0.022 = 95.27%
/ 95.28% pct of q in 2025-10 and 2022-02; inverse share-at-pct matches to
~0.0005 across the two months). The adaptation lives in R_est (last-10-bars
TR); the share riding on it does not need to move. Same justification
pattern as C_N. The old 0.042 = 98.5th pct (2025-10 ATR scale) — a
transcription of the old top-~1.5% fixed-threshold era, now retired.

BURST THRESHOLD, ATR14D LANE — ADAPTIVE RULE (q NOT invariant there, T-EN91):
threshold(day) = 85th percentile of raw |8-s move| (ticks) over trailing
sessions. Tested form: expanding in-month, min 1 prior session (T-EN92:
+762.9, 64%/460 tr, months +411/+352 — matches static 0.018 at no derivation
cost; maximin worst-month +352 > static's +333). LIVE / VALIDATION FORM
(pre-registered here): trailing 14 sessions, matching the lane's lookback.
Justification: the P&L turn sits at the 82nd–91st pct of q in BOTH training
months; 85 is inside the band. Honest label: the pct value was picked from
{85, 90, 95} on training P&L — adaptive structure derived, exact value fitted.

SAVED SCHEME CANDIDATES (user decision 2026-11-17) — kept in the pool to be
narrowed later and included in a validation run; low-count/high-quality
profile (fewer trades = lower admin cost), thrust 0.15 as tested:
- (c) RTH60 share 0.014 — +452.9, 69%/237 tr, DD 0.4 — and share 0.018 —
  +414.2, 69%/234 tr, DD 3.0. R_est = C_N x mean TR of last min(60, so-far)
  RTH bars of today only (never crosses into ETH; min 10 bars).
- (b) DAYSOFAR share 0.014 — +380.2, 68%/185 tr, DD 1.0. R_est = C_N x mean
  TR of ALL of today's RTH bars so far (expanding, min 10 bars).
- (b) DAYSOFAR share 0.018 — +378.8, 66%/182 tr, DD 2.6. (User's earlier
  "0.028" confirmed 2026-11-17 as a typo for 0.018.)
Known caveats carried with these: C_N = 22.7 was calibrated on the 10-bar
window, so its reuse in (b)/(c) is approximate (the share absorbs the level
difference); their thrust axis was NOT swept (0.15 only).

## POST-BATCH-4 DECISION (user-confirmed 2026-11-17, T-EN93)
Two lanes kept, one config each; the rest parked, not deleted.
- VOLUME LANE: ATR14D, burst = trailing 85th pct of raw |8-s move|
  (live form: trailing 14 sessions), thrust 0.13. Validated +239.6/+272.6,
  worst-month best of the pool. FLAG: ~3.4 ticks/trade pre-cost -
  tradeable only if the management rebuild adds per-trade margin.
- QUALITY LANE: INTRADAY10, burst share 0.022 (derived), thrust 0.17.
  Validated +54.4/+116.1 at 66%/74% win; only adapter licensed overnight.
- PARKED (validated positive both months, same family as INTRADAY10 -
  window variants of "C_N x mean TR of a recent window"): RTH60 0.014 and
  0.018 / thrust 0.15; DAYSOFAR 0.014 and 0.018 / thrust 0.15. Re-examine
  on the purchase months; RTH60 outscored INTRADAY10 on validation totals
  but its shares are underived - first alternate if INTRADAY10 stumbles.
REPORTING RULE (user, 2026-11-17): every validation batch carries the prior
batch's adopted config as an explicit baseline row, so the delta from each
variable change is attributable run-over-run now that variables are no
longer static.
