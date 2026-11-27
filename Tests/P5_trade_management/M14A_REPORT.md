# M14A REPORT — EARLY-ADVERSE EXIT (T-MG23)
STATUS: CLOSED | 2026-11-27 | Spec: M14A_SPEC.md (committed first) | R-9 CONTROL exact | verdict: MECHANISM-PRIMARY

| cell | trades | pooled net | by month | early exits | twin delta (changed trades) | months delta>0 | earners harmed | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 1517 | +483.2 | +138/+188/+119/+39 | 0 | - | - | - | (reproduced) |
| X1.25 | 1763 | +467.2 | +152/+145/+108/+63 | 647 | -57.9 on 479 changed | 1/4 | 28 | FAIL |
| X2.00 | 1652 | +483.5 | +166/+143/+118/+56 | 330 | -36.4 on 257 changed | 0/4 | 8 | FAIL |

Registry: T-MG23.

## READING — THE STOP IS ALREADY EFFICIENT
Both cells FAIL the mechanism-primary line: on the trades the rule
changed, exiting early LOST money vs letting M7 ride (-57.9 at
X1.25 on 479 changed trades; -36.4 at X2.00), positive in at most
1 of 4 months, and X1.25 harmed 28 earners. Why F-4's implication
fails in practice: the -3.75 stop already caps the tail, so an
early exit can save at most ~2.5 pts on eventual stop-outs - but it
forfeits every recovery, and enough early-breathers recover past
-1.25/-2.00 (to small stall losses or even spike wins) to outweigh
the savings. This is the SECOND independent vindication of the
plain stop (M9's distribution test was the first): the -345 stop
bill is the fair price of the recoveries, not an inefficiency.
Note the cell totals barely moved (+467/+484 vs +483) while trade
counts rose ~150-250 (early exits free the position clock, admitting
new entries) - cell-level numbers would have called this a wash;
the twin-matched mechanism called it correctly in one glance.
F-15 added to the register. D-24 part a: DONE (rejected). Parts b
(regime-conditioned stall) and c (spike-reach 12) remain queued.
