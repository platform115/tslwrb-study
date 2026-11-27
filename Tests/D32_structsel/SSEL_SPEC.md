# SSEL_SPEC — D-32: STRUCTURAL SELECTORS FOR THE SURGICAL LINE (T-SR04)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11
J's push: T-SR03 tested flow/calendar lenses but NOT the structural
vocabulary of F-23/F-24/F-25/F-26 (family edges, stacking) or F-7's
room-to-target logic. The exit anatomy says 47% of trades die at the
full stop while captures earn +4.11 - so the question is whether
STRUCTURE AROUND THE TRADE, knowable at entry, separates captures
from stops. All features price-computable at the fill second.

## R-11 MONTHS-SPEND
Design has seen both depth months (T-SR01..03 lineage; this spec
exists because of T-SR03's exit anatomy - disclosed). Spends nothing
new; no hold-out exists; TRAINING-ONLY context; qualifiers are
follow-up-spec candidates only; judge = D-8 stage 2.

## OBJECT + R-9 CONTROL
The 750 certified 5W full-RTH trades (banked
trades_5w_fullrth.parquet). Features are ADDED; P&L is not re-
simulated. Control: row count 750 and pooled +472.1 reproduced from
the banked file before the look; feature join must cover 750/750.

## LENSES (structural, frozen; range-style buckets per J's directive)
S1 ROOM TO CAPTURE TARGET: distance from entry to the first multi-
   day level ahead (the M7-capture target). Buckets: <=2 / 2-4 /
   4-8 / >8-or-none. (F-7: his 1.61x targeting; F-3: capture is
   the engine. Mechanism: no reachable target = no capture exit.)
S2 ROOM TO NEAREST FAMILY EDGE AHEAD: same buckets, against the
   F-23/24 vocabulary (resolver SQZ/GAP/SHD/REA + WRB + prior-day
   H/L/C at the fill second, G2-6 construction). (F-25/26: family
   edges act as real structure; do they also act as magnets/brakes?)
S3 CONFLUENCE AT THE TOUCHED LEVEL: touched level stacked with a
   family edge within 0.75 (yes/no), and count of family edges
   within 1.5. (F-23: stacked structures; his entries sit on them.)
S4 POSITION IN DAY RANGE: entry's position in the day's range so
   far, signed by trade direction (breaking into new ground vs
   interior). Terciles. (Crabel 1990 range-extension context.)
S5 BACKSTOP QUALITY: distance from the level to the nearest level
   BEHIND (support under the stop). Buckets <=2 / 2-6 / >6-or-none.
Stats: per-bucket n / per-trade / median / win% / capture-rate /
stop-rate, by month + pooled; top-vs-rest Mann-Whitney per lens,
BH-FDR q=0.10 across the 5-lens family; FINDING = BH-pass + both-
months direction.

## PROMOTION RULE (frozen, same as T-SR03)
Monotone gradient + FINDING + pooled n >= 150 + per-trade >= +0.85
+ both months positive + live-computable. Qualifiers -> one-variable
follow-up specs, J gates. Null -> the structural surface is also
flat and selection moves wholly to Part B's book read. Registry:
T-SR04.
