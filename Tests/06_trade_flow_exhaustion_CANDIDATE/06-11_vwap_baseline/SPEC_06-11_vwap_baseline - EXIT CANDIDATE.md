# SPEC 06-11 — VWAP / session-reference baseline competitor
Status: COMPLETE for October exploration. In-sample, holdout-pending. NOT a his-method signal — a
generic baseline competitor to S1/S2. Surprisingly strong in its short-rolling, z-scored form. Not advice.

## 0. Why this exists
VWAP is the institutional reflex; nothing in WRB methodology points to it. Run as a BASELINE: does an
off-the-shelf distance-from-VWAP rule separate cuts as well as the WRB-derived body-progress (S1)? It
did better than its "low-fit" billing suggested — recorded as a candidate to BEAT in holdout, not a found edge.

## 1. Feature
vwap_dist(tau) = (mid_at[min(entry+tau,exit)] - VWAP_at[checkpoint]) * side_sign  (still-open).
  Positive = price on the favorable side of VWAP for the trade. Two-sided (no pre-committed direction).
Anchors tested:
  DAILY   VWAP = sum(typical*vol)/sum(vol) cumulative within session_date (resets at session boundary).
  ROLLING VWAP = same over trailing N 1m bars. typical = (H+L+C)/3.
z-score variant: vwap_z = vwap_dist / rolling_sigma_N (sigma = rolling std of typical price = VWAP-band units).
Price from per-second mid (same instrument as S1, for clean comparison); VWAP/sigma from 1m bars.
Populations: clean (losing16 vs reached47) primary; pt1 (52/40) = NULL throughout (dilution, as elsewhere).

## 2. Results (clean, in-sample, honest 60s horizon — 13 losers still-open)
- DAILY VWAP: weak. ~0.64 @60s, CI barely excludes 0.5; calibration only weakly monotone. The session-
  level anchor mostly does not separate.
- ROLLING VWAP: strong, and STRONGER at SHORT lookback. N-sweep @60s (raw): N=10..120 ->
  0.768/0.761/0.764/0.744/0.696/0.668/0.665/0.663 — a smooth MONOTONE DECAY with N (not a single spike =
  not the cheap overfit signature). Short N (~10-30 = ~10-30min) best; long N decays toward the weak
  daily result. Interpretable: short rolling VWAP = "price vs its recent ~15min mean" = short-horizon
  extension; long VWAP washes out.
- z-SCORE (volatility-normalized) is CLEANER than raw: peak ~0.781 @60s at N=20, MONO calibration across
  the short-N cluster (N=10-30), bottom-quartile P(cut)=0.00 at every N. Normalizing by sigma sharpens it.
- SIGMA-BANDS (N=20, discrete levels <=0/0-1/1-2/>2 sigma): P(cut) steps 0.41/0.33/0.11/0.00. The >2sigma
  band had 0 losers of 10 (i.e. 0/10 in October — NOT a law). Clean monotone, BUT: with ~3 losers/band the
  level-vs-smooth question is UNTESTABLE (not falsified) — the table is consistent with both a discrete
  level effect AND the continuous z re-binned (simpler). Bands are useful as a READABLE operating-point
  expression of z (below VWAP ~40% cut; >2sigma ~0%), not demonstrated as a distinct mechanism.

## 3. Honest interpretation
Strongest form: short-N (~15-20), volatility-normalized rolling VWAP-distance, ~0.78 @60s clean, MONO
calibration. As strong (in-sample) as S1 (~0.82) — for a "low-fit" baseline. Direction is momentum-
flavored (favorable extension -> reached), NOT mean-reversion. Likely a member of the "is-it-working"
signal family (S1 displacement, S2 adverse, this = extension-vs-recent-mean), not WRB-specific.
CAUTION: all 8 N's read on the SAME 13 losers — correlated views, not independent tests; the monotone
N-curve rules out single-N luck but NOT whole-sample luck. Only holdout settles generalization.

## 4. Relationship to S1 (from 06-11 head-to-head; see that result if run)
N=30 raw: corr(vwap_dist@60, body_ratio@60) = +0.42 (moderate; semi-independent). Daily = +0.19.
Losers cross-tab (N=30 raw, S1<0.5 vs VWAP-dist<0): both~6-7, S1-only~6-7, VWAP-only=2, neither=0 ->
VWAP catches ~2 losers S1 misses (additive, not redundant). [z-score N=20 head-to-head: pending/see result.]

## 5. Files (in 06-11_vwap_baseline/)
- test_vwap_baseline.py        CANONICAL — daily + rolling(N=30), exit AUC + calibration + S1 head-to-head.
- test_vwap_rolling_sweep.py   CANONICAL — N-sweep DIAGNOSTIC (raw + z), stability/plateau read. NOT an optimizer.
- test_vwap_sigma_bands.py     CANONICAL — sigma-band P(cut) table (N=20), descriptive (n-limited).

## 6. Reproduce (06-11_vwap_baseline/; SSD mounted; per-second mid)
  python3 test_vwap_baseline.py        --config ../../../config.toml --wrb ../../../wrb_1m.parquet
  python3 test_vwap_rolling_sweep.py   --config ../../../config.toml --wrb ../../../wrb_1m.parquet
  python3 test_vwap_sigma_bands.py     --config ../../../config.toml --wrb ../../../wrb_1m.parquet

## 7. Caveats / parameters
13 losers @60s, October, in-sample. N (lookback) is a free parameter — short-N plateau (~15-20) is the
robust region; any N chosen for use must be PRE-REGISTERED from the plateau (not the peak) before holdout.
Late-tau AUCs (90s+) inflated by cut-survival shrinkage (cut arm -> ~5-10) — trust the 60s figures.
ROLL_N, the z-score, and sigma window are all OOS-confirm items. pt1 null. Not a validated edge.
