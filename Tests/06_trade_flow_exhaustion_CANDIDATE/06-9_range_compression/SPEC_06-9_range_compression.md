# SPEC 06-9 — range-compression, forward (CLOSED: null / redundant)
Status: COMPLETE — CLOSED. In-sample October.

## Purpose
Test whether the trade going QUIET (or wild) in RANGE early predicts the outcome — volatility, distinct
from displacement (S1) and adverse (S2). Closes out the "volatility-contraction / stall" candidate.

## Feature
compression_ratio(τ) = developing per-second mid range (max mid − min mid over [entry, min(entry+τ,exit)))
                       ÷ mean (high−low) of the 3 prior 1m bars.
<1 = quieter than recent bars (compressed); >1 = wilder. Still-open-only (non-circular, truncation-free).
Instrument note: numerator = per-second mid range (understates true extreme), denominator = bar true
range -> absolute ratio biased LOW, but AUC (ranks) and quartile calibration are unaffected.

## Direction
TWO-SIDED, genuinely unknown a priori (coil-before-WRB vs going-dead; 08 showed losers EXPAND at the
cut). No pre-committed sign.

## Result (in-sample) — NULL / REDUNDANT
- clean @60 s: AUC 0.573, CI [0.388, 0.750] — straddles 0.5 widely. Not significant.
- pt1 @60 s: AUC 0.602, CI [0.500, 0.700] — lower bound on 0.5. Borderline at best, diluted population.
- Where it leans: reached MORE volatile (cut median compression ~0.72 vs reached ~0.95) — losers quieter
  early. Same DIRECTION as body-progress (flat/quiet early -> dud), so not independent of S1.
- Calibration: clean NON-MONOTONE across quartiles (0.33 / 0.14 / 0.21 / 0.20 = noise); pt1 weakly
  monotone (0.47→0.33, a 14-pt span vs body-progress's 55%→5%). No usable gradient.

## Verdict
Range-compression does not earn a place as a third signal: weak on its own AND redundant-direction with
S1. The exit action lives in displacement (S1) and adverse excursion (S2), not raw volatility. Retroactive
read: 08's exit-anchored range result was losers expanding INTO their adverse cut (= S2), not a
compression signal — range never had independent content.

## Files
- test_range_compression.py

## Reproduce (06-9_range_compression/, SSD mounted)
  python3 test_range_compression.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet

## Caveats
clean = 13–16 cuts, wide CI -> "no evidence of a usable signal," NOT "proof there is none." A faint true
effect could hide in the CI, but even if real it adds nothing over S1, so closed regardless.
