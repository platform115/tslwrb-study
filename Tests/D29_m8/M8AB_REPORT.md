# M8AB REPORT — CAN M7'S DIALS REPRODUCE M8? (T-MG29)
STATUS: CLOSED | 2026-11-27 | Spec: M8AB_SPEC.md (frozen first) | control exact (2126/+565.9) | six months | G2-4 candidates

| cell | trades | per-trade | pooled | twin delta | months>=0 | busy add/drop (net) |
|---|---|---|---|---|---|---|
| M8 D=2.0 (incumbent) | 2400 | +0.34 | +824.8 | +143.6 | 5/6 | 331/57 (+115.2) |
| arm-window W=12 | 2126 | +0.27 | +575.2 | +5.8 | 6/6 | 1/1 (+3.6) |
| arm-window W=16 | 2126 | +0.27 | +575.2 | +5.8 | 6/6 | 1/1 (+3.6) |
| arm-window W=inf | 2126 | +0.27 | +575.2 | +5.8 | 6/6 | 1/1 (+3.6) |
| fixed-trail A=1.0 | 2505 | +0.31 | +774.2 | +69.6 | 4/6 | 469/90 (+138.8) |
| fixed-trail A=1.5 | 2370 | +0.36 | +858.1 | +173.4 | 5/6 | 358/114 (+118.9) |
| fixed-trail A=2.0 | 2261 | +0.36 | +814.4 | +154.4 | 5/6 | 260/125 (+94.1) |
| stall=90 | 1850 | +0.25 | +456.8 | -9.6 | 3/6 | 135/411 (-99.5) |
| stall=120 | 1653 | +0.27 | +450.9 | +13.2 | 3/6 | 142/615 (-128.2) |

## VERDICT (frozen: M8 stands unless an ablation matches its twin delta AND month-consistency)
- MATCHED BY SIMPLER DIAL: fixed-trail A=1.5 (+173.4, 5/6) - parsimony flag, J gates re-basing
- MATCHED BY SIMPLER DIAL: fixed-trail A=2.0 (+154.4, 5/6) - parsimony flag, J gates re-basing

Registry: T-MG29.
