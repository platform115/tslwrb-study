# FB REPORT — THE FAILED-BREAK EXIT (T-SR07, D-33 ROUND 1)
STATUS: CLOSED | 2026-11-27 | Spec: FB_SPEC.md (frozen first) | controls exact (1541/1263; 750/+472.1; 102/+157.1) | mechanism-primary | TRAINING-ONLY context

| universe | cell | trades | per-trade | pooled | by month | stops | failbrk | captures | worst |
|---|---|---|---|---|---|---|---|---|---|
| 5W-full | baseline | 750 | +0.63 | +472.1 | +195/+278 | 353 | - | 237 | -2.00 |
| 5W-full | FB x=0.0 | 776 | +0.53 | +412.9 | +159/+254 | 7 | 522 | 163 | -2.00 |
| 5W-full | FB x=0.25 | 771 | +0.49 | +377.2 | +130/+248 | 11 | 481 | 179 | -2.00 |
| 5W-full | FB x=0.5 | 765 | +0.53 | +406.5 | +148/+259 | 27 | 427 | 198 | -2.00 |
| RWY[2,8] | baseline | 102 | +1.54 | +157.1 | +79/+78 | 32 | - | 46 | -2.00 |
| RWY[2,8] | FB x=0.0 | 105 | +1.18 | +123.4 | +64/+59 | 0 | 58 | 36 | -0.75 |
| RWY[2,8] | FB x=0.25 FROZEN | 104 | +1.21 | +125.6 | +65/+61 | 0 | 51 | 38 | -1.00 |
| RWY[2,8] | FB x=0.5 | 104 | +1.37 | +142.8 | +66/+76 | 3 | 40 | 42 | -2.00 |

## MECHANISM ACCOUNTING (twin-matched by fill; busy-freed reported separately)
| universe | x | changed trades | delta on changed (22-02/25-10/pooled) | rescued losses | killed winners | busy-freed add/drop (net pnl) |
|---|---|---|---|---|---|---|
| 5W-full | 0.0 | 501 | -34.0/-24.6/-58.6 | 346 | 119 | 28/2 (-0.6) |
| 5W-full | 0.25 | 463 | -61.1/-29.2/-90.4 | 342 | 95 | 23/2 (-4.5) |
| 5W-full | 0.5 | 415 | -45.1/-17.6/-62.8 | 326 | 65 | 16/1 (-2.9) |
| RWY[2,8] | 0.0 | 56 | -13.2/-21.4/-34.6 | 32 | 18 | 3/0 (+0.9) |
| RWY[2,8] | 0.25 | 50 | -13.1/-19.8/-32.9 | 32 | 15 | 2/0 (+1.4) |
| RWY[2,8] | 0.5 | 39 | -11.4/-4.1/-15.5 | 29 | 8 | 2/0 (+1.1) |

## VERDICT vs THE FROZEN LINES (RWY, x=0.25)
- controls exact: PASS
- mechanism delta > 0 pooled, >= 0 both months: FAIL (-32.9; -13.1/-19.8)
- full-cell pooled > +157.1: FAIL (+125.6)
- stop-count reduced (<32): PASS (0)
- worst >= -2.1: PASS (-1.00)
OVERALL: facts to J

Registry: T-SR07.
