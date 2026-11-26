# V3 REPORT — VALIDATION STEP 2b: G2-5 (ONE TRADE PER WINDOW) ON THE PURCHASED MONTHS (T-VL03)
STATUS: CLOSED | 2026-11-26 | Frozen lines: VALIDATION_PLAN.md addendum 1 (mode-2 quality line) | engine: v1 + T-EN110 cap, retro-controlled (its N=1 training cell: 98 / +88.0)

## HIS SIDE (B5 recipe: squeeze interact +-15, 5-45min window)
| month | his entries | G2-like | his net (stated) | per-trade |
|---|---|---|---|---|
| 2023-05 | 21 | 5 | +12.0 | +2.40 |
| 2024-05 | 42 | 9 | +53.2 | +5.92 |

## G2-5, FULL STANDARD
| trades | win | per-trade | net (23-05/24-05) | caught/HIS | extras net | worst | maxDD |
|---|---|---|---|---|---|---|---|
| 99 | 53% | +0.39 | +38.9 (+33.5/+5.4) | 1/14 (7%) | +31.9 | -3.75 | 17.8 |

## VERDICT vs THE FROZEN MODE-2 QUALITY LINE
- per-trade >= +0.60: FAIL (+0.39)
- each month > 0: PASS (+33.5 / +5.4)
- catch (reported): 1/14 (7%); extras (reported): +31.9
OVERALL: FAIL

Training reference (not a criterion): 98 trades / +88.0 / per-trade +0.90.
Registry: T-VL03.
