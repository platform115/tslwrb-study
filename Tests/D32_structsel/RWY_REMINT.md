# RWY REPORT — THE RUNWAY SELECTOR AS A STRATEGY (T-SR05, D-32b)
STATUS: CLOSED | 2026-11-27 | Spec: RWY_SPEC.md (frozen first) | controls exact (builder 1541/1263; S1-ANY 422/+216.5; 5W full-RTH 750/+472.1) | TRAINING-ONLY cap

| cell | touches | trades | win | per-trade | pooled | by month | worst | stop% | capture% |
|---|---|---|---|---|---|---|---|---|---|
| 5W full-RTH baseline | 1264 | 750 | 47% | +0.63 | +472.1 | +195/+278 | -2.00 | 47% | 32% |
| RWY[2,8] (FROZEN) | 179 | 109 | 51% | +0.93 | +101.6 | +49/+52 | -2.00 | 42% | 38% |
| RWY[1.5,8] | 312 | 194 | 49% | +0.74 | +142.6 | +65/+78 | -2.00 | 45% | 38% |
| RWY[2,6] | 166 | 102 | 51% | +0.97 | +99.4 | +48/+51 | -2.00 | 42% | 38% |
| RWY[2,10] | 188 | 114 | 51% | +0.93 | +105.6 | +53/+52 | -2.00 | 43% | 38% |
| RWY[3,8] | 88 | 52 | 62% | +1.36 | +70.5 | +26/+44 | -2.00 | 31% | 46% |

## VERDICT vs THE FROZEN LINES (RWY[2,8] only)
- controls exact: PASS
- n >= 100: PASS (109)
- per-trade >= +1.00: FAIL (+0.93)
- both months positive: PASS
- worst >= -2.1: PASS (-2.00)
- stop-rate < 47%: PASS (42%)
OVERALL: PARTIAL - facts to J

Registry: T-SR05.
