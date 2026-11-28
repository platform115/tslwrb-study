# degenerate fb25 cell on corrected universe (minted): 111/+74.0
# RA REPORT — RECLAIM ANATOMY + FLOW-CONDITIONED EXIT (T-SR08-v2 RE-CHECK (post-F-36 universe))
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

## RECLAIM ANATOMY — RWY[2,8] (95 reclaimed trades; 46 ended stopped)
### L_ofi_sign
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| against | 27 | 19% | +0.71 | 33% | 7% |
| no-book | 38 | 71% | -0.26 | 60% | 78% |
| with/flat | 30 | 47% | +1.01 | 52% | 29% |

### L_time
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| t1_fast | 32 | 69% | -0.55 | 72% | 64% |
| t2_mid | 31 | 58% | -0.55 | 64% | 53% |
| t3_slow | 32 | 19% | +2.32 | 17% | 21% |

### L_mfe
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| mfe0.5-1 | 14 | 71% | -1.07 | 89% | 40% |
| mfe<0.5 | 21 | 67% | -0.45 | 67% | 67% |
| mfe>=1.0 | 60 | 37% | +1.07 | 34% | 39% |

### L_vel
| bucket | n | stop-rate | mean final | 22-02 stop% | 25-10 stop% |
|---|---|---|---|---|---|
| v1_slow | 36 | 44% | +0.50 | 50% | 38% |
| v2_mid | 27 | 52% | +0.14 | 47% | 60% |
| v3_fast | 32 | 50% | +0.56 | 54% | 47% |

### BH (q=0.10, RWY[2,8])
| lens | top | n | mean final | p | BH | both-dir | FINDING |
|---|---|---|---|---|---|---|---|
| L_ofi_sign | with/flat | 30 | +1.01 | 0.2955 | fail | yes | - |
| L_time | t3_slow | 32 | +2.32 | 0.0000 | PASS | yes | FINDING |
| L_mfe | mfe>=1.0 | 60 | +1.07 | 0.0031 | PASS | yes | FINDING |
| L_vel | v3_fast | 32 | +0.56 | 0.8181 | fail | NO | - |

## FLOW-CONDITIONED RECLAIM EXIT (the one frozen rule)
| universe | cell | trades | per-trade | pooled | by month | stops | failbrk | worst |
|---|---|---|---|---|---|---|---|---|
| 5W-full | baseline | 750 | +0.63 | +472.1 | +195/+278 | 353 | - | -2.00 |
| 5W-full | FCR | 753 | +0.62 | +463.4 | +199/+265 | 271 | 140 | -2.00 |
| RWY[2,8] | baseline | 109 | +0.93 | +101.6 | +49/+52 | 46 | - | -2.00 |
| RWY[2,8] | FCR | 109 | +0.76 | +83.2 | +44/+39 | 40 | 19 | -2.00 |

## MECHANISM (twin-matched; busy-freed separate)
| universe | changed | delta (22-02/25-10/pooled) | rescued | killed | busy add/drop (net) |
|---|---|---|---|---|---|
| 5W-full | 138 | +6.1/-12.4/-6.2 | 84 | 31 | 4/1 (-2.5) |
| RWY[2,8] | 19 | -4.8/-13.6/-18.4 | 6 | 8 | 0/0 (+0.0) |

## VERDICT vs THE FROZEN LINES (RWY-FCR)
- controls exact: PASS
- mechanism delta > 0 pooled, >= 0 both months: FAIL (-18.4; -4.8/-13.6)
- full-cell pooled > +101.6: FAIL (+83.2)
- worst >= -2.1: PASS (-2.00)
OVERALL: facts to J

Registry: T-SR08.
