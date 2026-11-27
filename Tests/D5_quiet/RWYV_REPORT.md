# RWYV REPORT — THE RWY SELECTOR ON THE VOLUME LINES (T-EN117)
STATUS: CLOSED | 2026-11-27 | Spec: RWYV_SPEC.md (frozen first) | controls exact (all three baselines) | band [2,8] carried frozen from T-SR05 | TRAINING-ONLY

| cell | trades | per-trade | pooled | by month | catch-G3 |
|---|---|---|---|---|---|
| G3-2 baseline | 23941 | +0.24 | +5727.8 | +470/+1720/+833/+628/+768/+1308 | 150/151 |
| G3-2-RWY[2,8] VERDICT | 3843 | +0.51 | +1944.4 | +60/+750/+174/+209/+152/+599 | 88/151 |
| G3-2-RWY[1.5,8] | 7911 | +0.42 | +3288.0 | +167/+1274/+341/+254/+408/+843 | 120/151 |
| G3-2-RWY[2,10] | 3884 | +0.50 | +1958.8 | +59/+752/+172/+202/+156/+617 | 90/151 |
| G3-1 baseline | 19008 | +0.19 | +3689.4 | +357/+952/+593/+432/+528/+827 | 150/151 |
| G3-1-RWY[2,8] | 3159 | +0.38 | +1186.4 | -6/+486/+149/+113/+122/+321 | 82/151 |
| G2-6 baseline | 6252 | +0.27 | +1659.0 | +173/+324/+372/+219/+231/+340 | 5/151 |
| G2-6-RWY[2,8] | 1212 | +0.52 | +627.2 | +79/+112/+74/+101/+66/+194 | 1/151 |

## PER-FAMILY (G3-2-RWY)
| family | trades | net | per-trade | months net<0 |
|---|---|---|---|---|
| GAP | 1406 | +684.2 | +0.49 | 0/6 |
| PDY | 42 | +21.1 | +0.50 | 3/6 |
| REA | 123 | +97.9 | +0.80 | 0/6 |
| SHD | 1343 | +776.2 | +0.58 | 0/6 |
| SQZ | 256 | +114.6 | +0.45 | 0/6 |
| W20 | 132 | +26.4 | +0.20 | 2/6 |
| WRB | 541 | +223.9 | +0.41 | 0/6 |

## VERDICT vs THE FROZEN LINES (G3-2-RWY[2,8])
- controls exact: PASS
- per-trade >= +0.45: PASS (+0.51)
- n >= 500: PASS (3843)
- all six months > 0: PASS
- no unflagged toxic family: PASS
OVERALL: REGISTER QUALITY-VARIANT - J gates

Registry: T-EN117.
