# M8S5 REPORT — M8 ON THE S5 LINE (T-MG28)
STATUS: CLOSED | 2026-11-27 | Spec: Tests/D29_m8/M8_SPEC.md (frozen first) | controls exact (750/+472.1; 102/+157.1) | mechanism-primary

| universe | cell | trades | per-trade | pooled | by month | captures | capture avg | stops | worst |
|---|---|---|---|---|---|---|---|---|---|
| 5W-full | baseline (M-S5) | 750 | +0.63 | +472.1 | +195/+278 | 237 | +4.11 | 353 | -2.00 |
| 5W-full | M8 D=2.0 FROZEN | 803 | +0.65 | +519.8 | +260/+260 | 507 | +1.90 | 232 | -2.00 |
| 5W-full | M8 D=1.0 | 815 | +0.62 | +509.4 | +230/+280 | 722 | +0.88 | 69 | -2.00 |
| 5W-full | M8 D=3.0 | 783 | +0.66 | +518.4 | +277/+241 | 368 | +2.94 | 310 | -2.00 |
| 5W-full | M8 naive D=0.5 | 817 | +0.62 | +504.9 | +235/+270 | 767 | +0.73 | 32 | -2.00 |
| RWY[2,8] | baseline (M-S5) | 102 | +1.54 | +157.1 | +79/+78 | 46 | +4.21 | 32 | -2.00 |
| RWY[2,8] | M8 D=2.0 FROZEN | 105 | +1.47 | +154.2 | +74/+80 | 77 | +2.48 | 19 | -2.00 |
| RWY[2,8] | M8 D=1.0 | 105 | +1.50 | +157.1 | +77/+80 | 80 | +2.35 | 16 | -2.00 |
| RWY[2,8] | M8 D=3.0 | 103 | +1.46 | +150.4 | +75/+76 | 55 | +3.61 | 31 | -2.00 |
| RWY[2,8] | M8 naive D=0.5 | 105 | +1.45 | +152.1 | +73/+79 | 87 | +2.00 | 12 | -2.00 |

## MECHANISM (twin-matched; busy-freed separate)
| universe | D_min | changed | delta (22-02/25-10/pooled) | busy add/drop (net) |
|---|---|---|---|---|
| 5W-full | 2.0 | 364 | +48.4/-41.2/+7.1 | 55/2 (+40.5) |
| 5W-full | 1.0 | 592 | +16.0/-35.5/-19.5 | 65/0 (+56.8) |
| 5W-full | 3.0 | 194 | +66.8/-44.5/+22.2 | 35/2 (+24.0) |
| 5W-full | 0.5 | 637 | +23.8/-45.2/-21.5 | 67/0 (+54.2) |
| RWY[2,8] | 2.0 | 51 | -6.0/+2.1/-3.9 | 3/0 (+1.0) |
| RWY[2,8] | 1.0 | 54 | -3.1/+2.1/-1.0 | 3/0 (+1.0) |
| RWY[2,8] | 3.0 | 23 | -2.0/-2.8/-4.8 | 1/0 (-2.0) |
| RWY[2,8] | 0.5 | 62 | -6.9/+0.9/-6.0 | 3/0 (+1.0) |

## VERDICT vs THE FROZEN LINES (S5 line: RWY-M8, D=2.0)
- controls exact: PASS
- twin delta > 0 pooled, >= 0 both months: FAIL (-3.9; -6.0/+2.1)
- full cell > +157.1: FAIL (+154.2)
- worst >= -2.1: PASS (-2.00)
S5-LINE VERDICT: facts to J

Registry: T-MG28 (S5 arm).
