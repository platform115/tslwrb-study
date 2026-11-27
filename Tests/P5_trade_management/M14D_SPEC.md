# M14D_SPEC — STRUCTURAL INVALIDATION EXIT (D-24 part d) (T-MG26)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Basis: J's "cut the trades that will not run" done the trader's way
(failed-breakout rule, Crabel/ORB tradition): the entry thesis is a
break of edge e; a 1-MINUTE BAR CLOSE back beyond e against the
position says the thesis failed. Distinct from T-MG23's rejected
rule in three ways: bar-close confirmation (noise wicks ignored),
referenced to the EDGE not the fill, active for the whole unarmed
life of the trade. Pre-stated risk: with the fill at e+1.25, a
close at e is exc<=-1.25 - if bar-close confirmation does not beat
raw touches, this collapses into the rejected tighter stop.

## MECHANIC (M14d = M7 + ONE rule)
Using the month's 1-minute bars: among bars whose OPEN time >= the
fill second, if a bar CLOSES beyond the edge against the position
(long: close <= e - y; short: close >= e + y), exit at the bar's
completion second. Once the spike-capture is ARMED, the rule is off
(the capture governs). Stop/stall/cap unchanged.
Cells: CONTROL | Y0 (close beyond e) | Y0.5 (close beyond e by 0.5).
Months: all 4.

## R-9 (abort on fail)
CONTROL reproduces 757/+325.1 and 760/+158.1 exactly; cells
non-empty per month; # invalidation exits reported.

## VERDICT (mechanism-primary)
PRIMARY: twin-matched delta on changed trades > 0 pooled AND >= 3/4
months. SECONDARY: cell pooled > +483.2 AND 4/4 months positive.
Both -> REGISTER TRAINING-ONLY (D-8 judges). Earners harmed
reported. WHATEVER the outcome, D-24 closes after this round with a
consolidated design-law F-entry. Registry: T-MG26.
