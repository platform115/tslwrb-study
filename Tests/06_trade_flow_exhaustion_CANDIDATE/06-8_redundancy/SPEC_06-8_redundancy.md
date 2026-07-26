# SPEC 06-8 — signal redundancy (S1 body-progress vs S2 adverse stop)
Status: COMPLETE. In-sample October, holdout-pending.

## Purpose
Decide whether the two kept exit signals are COMPLEMENTARY (a two-part system) or REDUNDANT (one signal
twice). Tested on the 16 losers (the true positives).

## Method
Per loser, compute both readings:
  S1: body_ratio at 60 s (NaN if cut before 60 s -> S1 cannot fire on the fastest cuts).
  S2: max adverse excursion over [entry, exit], and the second it first crosses the zone.
Flags (indicative): S1 = open-at-60 AND body_ratio<0.5 ; S2 = max_adverse>=2.5 pt. Cross-tab + the
threshold-free correlation corr(body_ratio@60, max_adverse), plus threshold-robustness sweep.

## Result (in-sample)
- INDEPENDENT: corr(body_ratio@60, max_adverse) = +0.03 over the open-at-60 losers. How flat a trade is
  at 60 s tells you nothing about how far it eventually goes adverse — different things, and the sign is
  POSITIVE (not the negative redundancy would imply).
- DIFFERENT TRADES: of 16 losers — both=2, S1-only=8, S2-only=6, neither=0. They catch mostly different
  losers; together they flag all 16.
- DIVISION OF LABOR (from the per-loser table):
    S1 owns SLOW-FLAT DUDS (hold ~86–198 s, flat at 60 s, never reached the adverse zone — S2 misses).
    S2 owns FAST VIOLENT losses (cut <60 s, 3–5.6 pt adverse fired in 16–53 s — S1's checkpoint doesn't
      exist yet) AND LATE REVERSALS (built fine at 60 s so S1 cleared them, turned adverse minutes later).
- Threshold-robust: S1-only and S2-only both substantial across (0.0,3.0), (0.5,2.5), (0.5,2.0).

## Interpretation
"Use both" is now earned, not assumed. S1 = early warning on stalling trades; S2 = hard stop on
adverse/fast/late ones.

## Files
- test_signal_redundancy.py

## Reproduce (06-8_redundancy/, SSD mounted)
  python3 test_signal_redundancy.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet

## Caveats
16 losers split into a 2×2 cross-tab = small cells (both=2 is two trades); the CORRELATION (+0.03) and
the mechanistic pattern (S1 flat-dud / S2 fast+late) are the durable claims, not the exact 8/6/2 split.
NOT tested: combined FALSE-POSITIVE rate on winners (each signal clips some winners; combining may
stack) — measure before treating "use both" as net-positive. Holdout-pending.
