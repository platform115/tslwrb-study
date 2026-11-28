# FB REPORT — THE FAILED-BREAK EXIT (T-SR07-v2 RE-CHECK (post-F-36 universe))
STATUS: CLOSED | 2026-11-27 | Spec: FB_SPEC.md (frozen first) | controls exact (1541/1263; 750/+472.1; 102/+157.1) | mechanism-primary | TRAINING-ONLY context

| universe | cell | trades | per-trade | pooled | by month | stops | failbrk | captures | worst |
|---|---|---|---|---|---|---|---|---|---|
| 5W-full | baseline | 750 | +0.63 | +472.1 | +195/+278 | 353 | - | 237 | -2.00 |
| 5W-full | FB x=0.0 | 776 | +0.53 | +412.9 | +159/+254 | 7 | 522 | 163 | -2.00 |
| 5W-full | FB x=0.25 | 771 | +0.49 | +377.2 | +130/+248 | 11 | 481 | 179 | -2.00 |
| 5W-full | FB x=0.5 | 765 | +0.53 | +406.5 | +148/+259 | 27 | 427 | 198 | -2.00 |
| RWY[2,8] | baseline | 109 | +0.93 | +101.6 | +49/+52 | 46 | - | 41 | -2.00 |
| RWY[2,8] | FB x=0.0 | 112 | +0.63 | +70.8 | +40/+30 | 1 | 75 | 29 | -2.00 |
| RWY[2,8] | FB x=0.25 FROZEN | 111 | +0.67 | +74.0 | +36/+38 | 2 | 67 | 32 | -2.00 |
| RWY[2,8] | FB x=0.5 | 110 | +0.80 | +87.6 | +32/+55 | 6 | 54 | 36 | -2.00 |

## MECHANISM ACCOUNTING (twin-matched by fill; busy-freed reported separately)
| universe | x | changed trades | delta on changed (22-02/25-10/pooled) | rescued losses | killed winners | busy-freed add/drop (net pnl) |
|---|---|---|---|---|---|---|
| 5W-full | 0.0 | 501 | -34.0/-24.6/-58.6 | 346 | 119 | 28/2 (-0.6) |
| 5W-full | 0.25 | 463 | -61.1/-29.2/-90.4 | 342 | 95 | 23/2 (-4.5) |
| 5W-full | 0.5 | 415 | -45.1/-17.6/-62.8 | 326 | 65 | 16/1 (-2.9) |
| RWY[2,8] | 0.0 | 72 | -8.0/-20.6/-28.6 | 45 | 20 | 3/0 (-2.2) |
| RWY[2,8] | 0.25 | 66 | -12.5/-12.1/-24.6 | 45 | 16 | 2/0 (-3.0) |
| RWY[2,8] | 0.5 | 53 | -15.5/+2.8/-12.8 | 40 | 9 | 1/0 (-1.2) |

## VERDICT vs THE FROZEN LINES (RWY, x=0.25)
- controls exact: PASS
- mechanism delta > 0 pooled, >= 0 both months: FAIL (-24.6; -12.5/-12.1)
- full-cell pooled > +101.6: FAIL (+74.0)
- stop-count reduced (<46): PASS (2)
- worst >= -2.1: PASS (-2.00)
OVERALL: facts to J

Registry: T-SR07.
