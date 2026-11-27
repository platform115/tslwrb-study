# RA REPORT — RECLAIM ANATOMY + FLOW-CONDITIONED EXIT (T-SR08, D-33 R2)
STATUS: CLOSED | 2026-11-27 | Spec: RA_SPEC.md (frozen first) | controls exact (incl. T-SR07 degenerate 104/+125.6) | TRAINING-ONLY context

## RECLAIM ANATOMY — 5W-full (657 reclaimed trades; 353 ended stopped)
### L_ofi_sign
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| against | 189 | 35% | +0.21 | 37% | 32% |
| no-book | 280 | 66% | +0.06 | 68% | 65% |
| with/flat | 188 | 54% | +0.23 | 56% | 52% |

### L_time
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| t1_fast | 220 | 77% | -0.84 | 76% | 78% |
| t2_mid | 218 | 61% | -0.51 | 58% | 64% |
| t3_slow | 219 | 24% | +1.81 | 25% | 22% |

### L_mfe
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| mfe0.5-1 | 125 | 68% | -0.66 | 65% | 72% |
| mfe<0.5 | 143 | 72% | -0.81 | 71% | 73% |
| mfe>=1.0 | 389 | 42% | +0.77 | 43% | 42% |

### L_vel
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| v1_slow | 307 | 50% | +0.07 | 48% | 51% |
| v2_mid | 161 | 61% | -0.04 | 54% | 71% |
| v3_fast | 189 | 54% | +0.45 | 60% | 50% |

### BH (q=0.10, 5W-full)
| lens | top | n | mean final | p | BH | both-dir | FINDING |
|---|---|---|---|---|---|---|---|
| L_ofi_sign | with/flat | 188 | +0.23 | 0.8487 | fail | NO | - |
| L_time | t3_slow | 219 | +1.81 | 0.0000 | PASS | yes | FINDING |
| L_mfe | mfe>=1.0 | 389 | +0.77 | 0.0000 | PASS | yes | FINDING |
| L_vel | v3_fast | 189 | +0.45 | 0.2803 | fail | NO | - |

## RECLAIM ANATOMY — RWY[2,8] (85 reclaimed trades; 32 ended stopped)
### L_ofi_sign
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| against | 25 | 4% | +1.81 | 0% | 7% |
| no-book | 36 | 61% | +0.32 | 54% | 65% |
| with/flat | 24 | 38% | +1.35 | 41% | 29% |

### L_time
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| t1_fast | 29 | 59% | +0.10 | 62% | 54% |
| t2_mid | 28 | 36% | +1.07 | 30% | 39% |
| t3_slow | 28 | 18% | +2.02 | 7% | 29% |

### L_mfe
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| mfe0.5-1 | 8 | 62% | -0.55 | 75% | 50% |
| mfe<0.5 | 18 | 56% | +0.24 | 62% | 50% |
| mfe>=1.0 | 59 | 29% | +1.51 | 21% | 35% |

### L_vel
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| v1_slow | 35 | 37% | +0.75 | 39% | 35% |
| v2_mid | 25 | 40% | +0.96 | 31% | 50% |
| v3_fast | 25 | 36% | +1.56 | 33% | 38% |

### BH (q=0.10, RWY[2,8])
| lens | top | n | mean final | p | BH | both-dir | FINDING |
|---|---|---|---|---|---|---|---|
| L_ofi_sign | against | 25 | +1.81 | 0.0496 | fail | yes | - |
| L_time | t3_slow | 28 | +2.02 | 0.0267 | fail | yes | - |
| L_mfe | mfe>=1.0 | 59 | +1.51 | 0.0295 | fail | yes | - |
| L_vel | v3_fast | 25 | +1.56 | 0.2865 | fail | yes | - |

## FLOW-CONDITIONED RECLAIM EXIT (the one frozen rule)
| universe | cell | trades | per-trade | pooled | by month | stops | failbrk | worst |
|---|---|---|---|---|---|---|---|---|
| 5W-full | baseline | 750 | +0.63 | +472.1 | +195/+278 | 353 | - | -2.00 |
| 5W-full | FCR | 753 | +0.62 | +463.4 | +199/+265 | 271 | 140 | -2.00 |
| RWY[2,8] | baseline | 102 | +1.54 | +157.1 | +79/+78 | 32 | - | -2.00 |
| RWY[2,8] | FCR | 103 | +1.37 | +140.6 | +72/+68 | 30 | 12 | -2.00 |

## MECHANISM (twin-matched; busy-freed separate)
| universe | changed | delta (22-02/25-10/pooled) | rescued | killed | busy add/drop (net) |
|---|---|---|---|---|---|
| 5W-full | 138 | +6.1/-12.4/-6.2 | 84 | 31 | 4/1 (-2.5) |
| RWY[2,8] | 12 | -6.5/-12.4/-18.9 | 2 | 7 | 1/0 (+2.4) |

## VERDICT vs THE FROZEN LINES (RWY-FCR)
- controls exact: PASS
- mechanism delta > 0 pooled, >= 0 both months: FAIL (-18.9; -6.5/-12.4)
- full-cell pooled > +157.1: FAIL (+140.6)
- worst >= -2.1: PASS (-2.00)
OVERALL: facts to J

Registry: T-SR08.
