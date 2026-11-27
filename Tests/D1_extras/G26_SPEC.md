# G26_SPEC — D-3: GATED G2-4 (CANDIDATE G2-6) (T-EN113)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Trigger: J's go on D-3 (roadmap -> IN PROGRESS this commit). Builds
on F-1..F-5; cites F-11 (shrinkage law) and F-13 (control-arm law).

## MECHANIC
G2-4 exactly, except a candidate fill is DECLINED at fill time unless
it passes the gate(s). Declining frees the position clock (a declined
fill admits later fills G2-4 skipped - the CD-round lesson; no subset
invariant is claimed). Gates, thresholds FROZEN from principled
sources, not optimized:
- E (energy): rv30 >= 36.0 pts (the corpus median over all 1,517
  G2-4 trades - the center of the distribution, not a searched value)
- P (proximity): nearest computed level ahead <= 8.0 pts (M7's own
  spike-arm condition, moved to the entry)
Cells: CONTROL (no gate) | E only | P only | E+P. Months: all 4.

## R-9 CONTROL (abort on fail)
CONTROL must reproduce exactly: training 757/+325.1, validation
760/+158.1. Checks: every cell non-empty per month; per-cell counts
of declined fills reported (gates must visibly bind).

## MECHANISM ACCOUNTING (the gate's work, not cell totals)
Per cell: the declined-fill set's would-have-been P&L (simulated
unmanaged through M7 at the same moments, position permitting -
approximated by CONTROL trades absent from the cell), reported as
"removed trades: n, net". A gate that works removes ~breakeven or
losing trades.

## CIRCULARITY DECLARED
The gates derive from the same 4 months they are tested on. Passing
here is NECESSARY, not sufficient: no adoption from this round. The
outcome line is REGISTER AS CANDIDATE G2-6 (TRAINING-ONLY), final
judgment on the D-8 fresh months per the dormant ride-along policy.

## OUTCOME LINES (frozen)
REGISTER AS G2-6 CANDIDATE: per-trade >= +0.48 (1.5x G2-4's +0.32)
AND pooled net >= +193 (40% of G2-4's +483.2) AND all 4 months
positive AND removed-trade net <= 0.
Otherwise: the gate(s) fail even in-corpus -> F-register annotated,
D-25 premise re-examined before any further gate work.
Catch vs his entries reported, not gated. Registry: T-EN113.
