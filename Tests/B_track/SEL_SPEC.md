# SEL SPEC — THE SELECTION ROUND: PER-TRADE QUALITY (pre-registered)
STATUS: FROZEN | 2026-11-26 | Registry: T-EN105
Goal (J): select more like him, or better. Target gap: our +0.49/trade
(G2-3) vs his +3.73.

## STEP 1 — DECOMPOSE THE GAP (measure before fixing)
On the G2-3 fill set (4A-v2 d1.25 x M7, training months): per-trade
P&L split caught-fills vs extras; winners-vs-losers shares; how
concentrated the +265.4 is (top-decile share); his per-trade on the
same caught trades for comparison.

## STEP 2 — FEATURES AT THE TRIGGER (all knowable <= t; R-1)
Per fill: movement ladder (mv15/mv60/mv300), flow1, vrate900,
consec-persistence, news clock + event name, time of day, triggering
band width, ROOM-TO-RUN = distance to the nearest computed multi-day
level AHEAD (the M7 detector, reused as an ENTRY feature), distance to
the level BEHIND, intensity composite. Labels (never features): traded
P&L under M7, near-his flag.

## STEP 3 — RANK, THEN RULE
Instrument: random forest + permutation importance, GroupKFold by
session (the T-IM46 protocol). SHIPPED RULE: explicit thresholds on the
top features, grid as RANGES. Two filter targets, both run:
(a) PROFIT filter (label = fill's own P&L > 0): the "or better" mode;
(b) HIS-LIKENESS filter (label = near-his): the replication mode.
ADOPTION BARS (pre-stated): a selection rule adopts only if, on the
filtered set: per-trade >= +1.00 (2x incumbent) AND catch >= 40 AND
pooled net >= +199 (0.75x incumbent) AND both months positive.
Checklist line 1: all verdicts in traded P&L. Line 3 (selection-free
result): a filter that merely drops random fills raises nothing - the
null comparison is random drops of equal size. Fourth stacked training
improvement if adopted - the purchased months arbitrate everything.
