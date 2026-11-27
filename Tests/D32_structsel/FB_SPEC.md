# FB_SPEC — D-33 ROUND 1: THE FAILED-BREAK EXIT (T-SR07)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11 + R-12
J's directive: losses are the open surface - every loss in the
surgical line is a full -2.00 stop (353 of 750; 32 of 102 in RWY).
Mechanic under test: the FAILED-BREAK EXIT - a breakout entry whose
level is RECLAIMED against the position is exited at the reclaim,
not at the structural stop (standard failed-breakout handling;
Crabel 1990's breakout framework treats the failed break as its own
signal). ONE variable: the reclaim exit. No other change.

## R-11 MONTHS-SPEND
2022-02 + 2025-10, already spent (T-SR01..06 lineage); nothing new;
no hold-out exists; TRAINING-ONLY context; judge = D-8 stage 2.

## R-12 FINDINGS SWEEP
APPLIED: F-3/F-7 (capture exits untouched - they are the earnings),
F-11 (haircut stated), F-13 (controls below), F-15 (the -3.75 combo
stop law is G2-4's; S5's stop is L-1.25d - NOT covered by F-15, so
this test does not contradict it), F-17 (flow-fade retained),
F-21/F-22 (trigger side untouched), F-28/F-29 (run on the RWY cell
as the lead), F-20 (threshold tested as a RANGE, verdict frozen to
one value chosen for a stated mechanical reason).
NOT-APPLICABLE: F-1/2/4/5/6 (combo-line entry findings), F-8/9/10/12
(superseded), F-14/F-16 (combo-line management frontier - different
organism, and this is loss-side, not hold-side), F-18 (no his-rule
transplants), F-23..27 (entry/selection side - unchanged here).

## MECHANIC
In the certified S5 exit loop, add one check after the stop check:
exit at exc = -(0.75 + x) when exc[i] <= -(0.75 + x) - i.e., price
has come back through the level by x points against the position
(entry is at L + 0.75d, so exc -0.75 = the level itself). Fill at
the threshold, same convention as the stop. Stop (-2.00) keeps
priority within a second (conservative). No grace period, active
from the fill (one variable).
Range (per J's ranges directive): x in {0.0, 0.25, 0.5} -> exits at
-0.75 / -1.00 / -1.25.
FROZEN VERDICT VALUE: x = 0.25 (one tick beyond the level = the
level is genuinely reclaimed, not grazed by spread noise; stated
mechanical reason, not a fitted number).

## CELLS
Universes: 5W full-RTH (750 baseline) and RWY[2,8] (102 baseline).
Cells per universe: baseline + FB(x) for each x. Verdict on
RWY + x=0.25; everything else is reported evidence.

## R-9 CONTROLS + MECHANISM ACCOUNTING
Controls: builder 1541/1263; 5W 750/+472.1; RWY 102/+157.1 exact.
Mechanism-primary (T-MG21 law): twin-match trades by (month, fill
second); report (a) the delta on CHANGED trades only - the rule's
own effect; (b) busy-freed additions/removals separately - never
blended into the verdict; (c) rescued losses vs killed winners
counts (a trade exited at the reclaim that would have recovered
is a killed winner - the cost side).

## VERDICT (frozen flag-lines, RWY x=0.25)
ADOPT-AS-CANDIDATE (management variant of the S5 exit organism,
named only on adoption per R-3) requires ALL: (a) controls exact;
(b) twin-matched mechanism delta > 0 pooled AND >= 0 in both
months; (c) full-cell pooled > +157.1; (d) stop-count strictly
reduced; (e) worst trade >= -2.1. Partial -> facts to J.
Registry: T-SR07.
