# TL_SPEC — TWO-LANE ENTRY: FIRST-BREAK + RETEST (T-EN108)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J ordered the combo while both parents are fresh (T-EN106/7).
Basis: T-EN107 Part A measured him DUAL-MODE on the same cross stream
(17 first-takes / 32 retest-takes of 50 matched, both profitable).
J's framing adopted: choosing WHEN to enter (first break vs confirmed
retest) is part of the entry strategy itself.

## MECHANIC
Per deduped cross of edge e, direction d, at t0 (same stream as
G2-3: resolver SQZ + W20 q0.8 bands, dedupe (round(e,2),d)/300s,
5-45min post-release RTH windows):
- LANE 1 (first-break, = G2-3): stop at e+1.25d, TTL 300s from t0.
- LANE 2 (retest, = T-EN107 mechanic): if mids reach >= e+X*d within
  600s of t0, then return to within pb of e (still within 600s), a
  stop at e+1.25d is placed at the touch, TTL 300s from the touch.
Each cross contributes at most one Lane-1 and one Lane-2 candidate
fill. Candidates are deduped on (fill second, edge key), pooled
across lanes, sorted by fill time, then the single-position rule is
applied in fill-time order (a candidate whose fill lands while a
position is open is discarded). Management: M7 exactly as shipped.

## CELLS (3; verdicts on TL cells only)
- CONTROL: Lane 1 only, through the SAME new engine. MUST reproduce
  T-EN104's G2-3 line (+265.4 net, 542 trades, catch 46, extras
  +173.0) within rounding. If it does not, the run STOPS, nothing is
  reported as a result, and the discrepancy is investigated first.
- TL-A: Lane 1 + Lane 2 (X=2.0, pb=0.25)  [best per-trade parent]
- TL-B: Lane 1 + Lane 2 (X=1.0, pb=0.75)  [highest catch parent]
Both training months; no costs; single position.

## HYPOTHESIS (both ways)
For: the union covers both of his measured modes, so catch should
rise toward/past 46 while Lane-2's higher-quality re-breaks add net.
Against: Lane-2 fills inside Lane-1's dedupe shadow may be the same
fills G2-3 already takes via re-cross, adding little but extra
exposure; extras could dilute per-trade back to ~+0.49.

## VERDICT LINES (same two as T-EN106/7, frozen)
- ADOPT: pooled net > +265.4 AND caught >= 46 AND extras net >= 0
  AND both months positive.
- QUALITY-ALTERNATE: per-trade >= +0.98 AND net >= +150 AND
  caught >= 30 AND both months positive.
- Otherwise REJECTED; G2-3 stands.
Full standard either way; his G2 line (+231.2 / 62 / +3.73) beside
it. Lane attribution (n, net per lane) reported for reading, not for
post-hoc cell surgery. Registry: T-EN108. Training-fitted knob #6;
freeze after this and the cadence round.
