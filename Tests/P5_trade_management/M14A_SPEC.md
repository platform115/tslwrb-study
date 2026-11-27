# M14A_SPEC — EARLY-ADVERSE EXIT (D-24 part a) (T-MG23)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Trigger: J's go. Basis: F-4 (winners don't breathe: earner MAE med
0.12 vs rest 1.12) and the -345 stop bill (F-3 anatomy). Cites F-11
(shrinkage law), F-14 (this is a management lever, not selection -
it changes handling of kept trades, discards no entries).

## MECHANIC (M14a = M7 + ONE rule)
If, within the first N=120 seconds of a trade, excursion reaches
<= -X, exit immediately (before the -3.75 stop). All other M7 rules
unchanged. X derived (not searched) from the earner MAE
distribution, tick-rounded: X = 1.25 (q90 = 1.12) and X = 2.00
(q95 = 1.81) - by construction these rules would have touched at
most ~10% / ~5% of earners. Cells: CONTROL (M7) | X1.25 | X2.00.
Months: all 4.

## R-9 (abort on fail)
CONTROL reproduces 757/+325.1 and 760/+158.1 exactly. All cells
non-empty per month.

## VERDICT (mechanism-primary, the T-MG21 standard)
PRIMARY: on common entries (same month, tf, key), the changed
trades' twin-matched delta vs M7 must be > 0 pooled AND >= 3/4
months. SECONDARY: cell pooled net > +483.2 AND 4/4 months positive.
REGISTER AS TRAINING-ONLY M14a requires BOTH; judged finally on D-8.
Mechanism accounting: # early exits, their pnl vs twin pnl,
# earners (pnl >= 1.38 under control) harmed.
Registry: T-MG23.
