# D27_SPEC — SENSITIVITY AUDIT OF NEVER-RANGED CONSTANTS (T-SA01)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Purpose (J): the constants below are load-bearing and were never
range-tested. This audit perturbs each ONE AT A TIME and asks only
"does the conclusion survive?" - a ROBUSTNESS CHECK, never an
optimization: nothing is adopted from it, knife-edges are FLAGGED
(a knife-edge = hidden overfit risk; a flat response retires the
worry). Baseline = G2-4 on the training pair, R-9 control
(757/+325.1 exact) before any variant.

## PART A - exit-side constants (candidates reused; sim-only)
give-back 0.75 -> {0.5, 1.0}; arm floor 0.5 -> {0.25, 0.75};
stop 3.75 -> {3.0, 4.5, 5.25}; cap 480 -> {360, 720}.
Metric: pooled net + both-month nets vs baseline (+325.1).
## PART B - entry-side constants (regeneration per variant)
TTL 300 -> {150, 450}; dedupe 300 -> {150, 450};
lane-2 Wseq 600 -> {300, 900}. Same metric.
## PART C - analysis constants (conclusions, not P&L)
F-17's OFI trailing window 30s -> {15, 60}: does the exit-vs-hold
separation (within-pair delta direction, both months) survive?
(From the banked per-second OFI series; OFI10 only.)
T-BK03 outcome thresholds (zone 2.0 / touch 0.5 / move 1.5) ->
each +-50%: does the ~50/50 hold/break base rate and the all-null
book result survive?
## VERDICT (frozen)
Per constant: ROBUST (all variants within +-15% of baseline pooled
net, or conclusion direction unchanged) | SENSITIVE (beyond that,
flagged with direction) | KNIFE-EDGE (sign flip or conclusion
reversal - escalated to J). NOTHING is changed in any shipped
strategy regardless of outcome. Registry: T-SA01.
