# M14C_SPEC — SPIKE-CAPTURE REACH EXTENSION (D-24 part c) (T-MG25)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Basis: F-3 (spike-capture = the P&L engine, +679 of +483) and the
T-MG14 boundary flag (reach was monotone to the tested limit 8,
never tested beyond). This extends the WINNING mechanism - the only
family that ever beat a management incumbent (level-snap itself).
M14b is PRESERVED (rejected but helped the weakest month; revisit
only under a future regime framework - noted on the roadmap).

## MECHANIC (M14c = M7 with ONE constant changed)
M7 arms the capture when the nearest computed level ahead is
<= 8.0 pts. Cells raise that eligibility to <= 10.0 and <= 12.0
(arm threshold formula unchanged: max(level_dist - 0.75, 0.5)).
ISOLATION (stated): only trades whose nearest level ahead lies in
(8, reach] can change; they behave identically to M7 until price
approaches the far level. Cells: CONTROL | R10 | R12. Months: all 4.

## R-9 (abort on fail)
CONTROL reproduces 757/+325.1 and 760/+158.1 exactly; cells
non-empty per month; # newly-armed trades and # that reached arm
reported (the rule must visibly bind).

## VERDICT (mechanism-primary)
PRIMARY: twin-matched delta on changed trades > 0 pooled AND >= 3/4
months. SECONDARY: cell pooled > +483.2 AND 4/4 months positive.
Both -> REGISTER TRAINING-ONLY, final judge D-8. Earners harmed
reported. Registry: T-MG25.
