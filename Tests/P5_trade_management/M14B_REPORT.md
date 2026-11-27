# M14B REPORT — REGIME-CONDITIONED STALL (T-MG24)
STATUS: CLOSED | 2026-11-27 | Spec: M14B_SPEC.md (committed first) | R-9 CONTROL exact | verdict: MECHANISM-PRIMARY | regime measured at the stall-check moment

| cell | trades | pooled net | by month | dead-stalls | twin delta (changed) | dead-tape delta | active delta | months delta>0 | earners harmed | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| CONTROL | 1517 | +483.2 | +138/+188/+119/+39 | 0 | - | - | - | (reproduced) |
| S=30 | 1687 | +471.6 | +138/+173/+110/+50 | 850 | -17.0 on 680 | -17.0 | +0.0 | 2/4 | 61 | FAIL |
| S=45 | 1591 | +476.5 | +138/+179/+108/+51 | 740 | -6.2 on 658 | -6.2 | +0.0 | 2/4 | 46 | FAIL |

Registry: T-MG24.

## READING
Both cells FAIL mechanism-primary, but the texture matters:
- The deltas are small (-17.0 and -6.2 across ~660-680 changed
  trades, ~-0.02/trade) - a wash trending negative, not a disaster.
- The per-regime split confirms the ATTRIBUTION was right and the
  FIX was wrong: all the delta sits in dead-tape stalls (active
  untouched, +0.0, as designed). Dead-tape trades ARE low-value
  (F-2 stands as description), but their cost is not the extra
  15-30 seconds of patience - they are simply low-EV trades, and
  cutting patience occasionally beheads one that was about to reach
  a level (46-61 earners harmed - spike captures that never armed).
- Pattern: F-4's implication died the same way (true description,
  rejected fix). The decomposition findings describe WHERE outcomes
  happen, not WHAT to change - every "trim the bad side" tweak has
  now lost to M7's recoveries.
M7 survives its 9th challenger. Remaining D-24 parts attack the
WINNING side instead: (c) extend spike-capture reach to 12 (the one
family that ever beat a management incumbent - level-snap itself);
(d) structural invalidation exit. If c and d also fail, a
consolidated design-law F-entry closes the simple-tweak management
lane at this resolution.
