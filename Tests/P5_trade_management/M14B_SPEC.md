# M14B_SPEC — REGIME-CONDITIONED STALL (D-24 part b) (T-MG24)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Basis: F-2 ("in dead tape, stalls bleed"; rv30 = the energy factor).
Cites F-11, F-15. Thoroughness notes: regime is measured AT THE
STALL-FIRE MOMENT (decision-time, live-computable from the last 30
one-minute closes); the rule is ONE-SIDED (shorten in dead tape
only - lengthening is anti-evidenced by M3B); per-regime attribution
is mandatory in the output. D-24d (structural invalidation exit) is
registered as the untested cousin, after b/c.

## MECHANIC (M14b = M7 with ONE conditional)
When the stall condition (60s without a new peak) FIRES is unchanged
for active tape. In DEAD tape - rv30 at the stall-check moment < 36.0
(the corpus median, same frozen constant as T-EN113) - the stall
fires at S seconds without a new peak instead of 60.
Cells: CONTROL (M7) | S=30 | S=45. Months: all 4.

## R-9 (abort on fail)
CONTROL reproduces 757/+325.1 and 760/+158.1 exactly; cells
non-empty per month; # dead-tape stalls reported (rule must bind).

## VERDICT (mechanism-primary)
PRIMARY: twin-matched delta on changed trades > 0 pooled AND >= 3/4
months. SECONDARY: cell pooled > +483.2 AND 4/4 months positive.
Both -> REGISTER TRAINING-ONLY (judged on D-8). Output must show
deltas split dead-tape vs active-tape changed trades, and earners
(control pnl >= 1.38) harmed.
Registry: T-MG24.
