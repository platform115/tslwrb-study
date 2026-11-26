# V1 REPORT — VALIDATION STEP 1: G2-3 ON THE PURCHASED MONTHS (T-VL01)
STATUS: CLOSED | 2026-11-26 | Frozen lines: VALIDATION_PLAN.md addendum 1 (committed before this run) | engine: the exact code path that reproduced +276.1/607/47/+185.6 on training | FIRST touch of the quarantined months

## HIS SIDE (B5 recipe: squeeze interact +-15, 5-45min window)
| month | his entries | G2-like | his net (stated) | per-trade |
|---|---|---|---|---|
| 2023-05 | 21 | 5 | +12.0 | +2.40 |
| 2024-05 | 42 | 9 | +53.2 | +5.92 |

## G2-3, FULL STANDARD
| trades | win | per-trade | net (23-05/24-05) | caught/HIS | extras net | worst | maxDD |
|---|---|---|---|---|---|---|---|
| 566 | 51% | +0.26 | +144.4 (+137.6/+6.8) | 7/14 (50%) | +141.1 | -3.75 | 25.2 |

## VERDICT vs THE FROZEN LINES (no post-hoc interpretation)
- pooled net > 0: PASS (+144.4)
- each month > 0: PASS (+137.6 / +6.8)
- catch >= 60% of his group: FAIL (7/14 = 50%)
- extras net > -20% of pooled: PASS (+141.1)
OVERALL: FAIL

Training reference (not a criterion): +276.1 / 607 trades / catch 47/62 / extras +185.6 / per-trade +0.45.
Registry: T-VL01.
