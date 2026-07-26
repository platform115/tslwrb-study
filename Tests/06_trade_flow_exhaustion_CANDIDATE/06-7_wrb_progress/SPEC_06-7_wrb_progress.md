# SPEC 06-7 — WRB body-progress, forward (exit signal "S1")
Status: COMPLETE. In-sample October, holdout-pending. Not a validated edge.

## Purpose
Test whether early FORWARD progress toward a wide-range bar predicts runner vs dud — the price/
structure signal (WRB) that survived where flow did not, read at the entry side.

## Feature
body_ratio(τ) = favorable NET displacement by entry+τ ÷ max |close-open| of the 3 prior 1m bars.
  favorable displacement = (mid_at[min(entry+τ, exit)] − entry_price) × side_sign  (net, not extreme:
  a spike-then-fade reads ~0 = correctly "no WRB body forming").
  denominator = the WRB-qualifying body to beat (largest of the 3 completed bars before entry).
High ratio = displaced ~a WRB's worth in favor by τ. Low/neg = flat or adverse.

## Populations
clean = losing_trade(16) vs reached_target(47) ; pt1 = failed_trades(40) vs target_reached(52).

## Design / causal handling
Entry-anchored FORWARD. Causal guard: read at min(entry+τ, exit). Honest magnitude uses STILL-OPEN-only
(drop trades exited before τ) — truncating-to-exit leaks the outcome. Entry-anchored population AUC,
cluster-bootstrap over the cut arm. Two-sided CI; expected direction reached>cut.

## Result (in-sample)
- Separation (still-open, 60s primary): clean AUC ~0.82, pt1 ~0.69. The signal is stronger on the
  loss-based contrast than on pt1 — i.e. NOT the pt1 label.
- Truncation: small inflation only. clean 60s ALL 0.852 -> OPEN 0.817; 90s ALL 0.901 -> OPEN 0.845.
  Truncation is cut-arm-heavy (pt1 60s trunc cut=8 vs spared=2) = fast cuts, as expected. Signal
  survives exclusion; not an artifact.
- Non-circularity (the central risk, since pt1 IS the first WRB): within-group spreads OVERLAP — some
  reached trades have ~0/neg early body (slow runners), some cuts have positive early body. Graded
  forward signal, not the label in disguise.
- Readable window ~45–90 s: AUC ~0.50 at 15 s, ~0.60 at 30 s (cleanest, zero truncation), strong by
  60 s. Doomed trades exit fast — about half the losers gone by ~105 s -> must read EARLY.
- Calibration (clean, 60 s): body_ratio <0 -> P(cut)~0.55 ; 0–0.5 -> ~0.33 ; 0.5–1.0 -> ~0.08 ;
  >1.0 -> ~0.05. Decision boundary ~0.5. pt1 calibration weaker (top two bins ~0.57, flat).

## Files (all three are the test — different views, none superseded)
- test_wrb_progress_A.py          — fixed-checkpoint separation + non-circularity spread.
- test_wrb_progress_A_trunccheck.py — ALL vs STILL-OPEN (de-confounded magnitude; per-arm truncation).
- test_wrb_progress_B_hazard.py   — hazard curve across τ + quartile/bin calibration (the live rule).

## Reproduce (06-7_wrb_progress/, SSD mounted)
  python3 test_wrb_progress_B_hazard.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet

## Caveats
16 losers, October, in-sample. Thresholds (~0.5 at 60 s) indicative, not tuned. Holdout-pending.
