# LVLR REPORT — 5W FULL-RTH ANATOMY (T-SR03, D-31)
STATUS: CLOSED | 2026-11-27 | Spec: LVLR_SPEC.md (frozen first) | controls exact (1541/1263; 422/+216.5; 750/+472.1) | TRAINING-ONLY context; promoted items are candidates only

Baseline: 750 trades, +0.63/trade, +472.1 (+195.3 / +276.8 by month).

## L1 news
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| a_burst<=5 | 39 | +0.32 | -2.00 | 46% | -0.04 | +0.59 |
| b_window5-45 | 177 | +0.49 | -2.00 | 42% | +0.50 | +0.49 |
| c_quiet>45 | 534 | +0.70 | -0.12 | 49% | +0.54 | +0.89 |

## L2 hour
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| a_0830-10 | 293 | +0.55 | -0.88 | 47% | +0.44 | +0.69 |
| b_10-12 | 220 | +0.75 | +0.00 | 50% | +0.47 | +1.00 |
| c_12-14 | 153 | +0.54 | -2.00 | 43% | +0.66 | +0.42 |
| d_14-15 | 84 | +0.75 | -2.00 | 46% | +0.56 | +1.02 |

## L3a score
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| hi>=6 | 642 | +0.68 | -0.88 | 47% | +0.56 | +0.80 |
| lo4 | 71 | +0.20 | -0.12 | 46% | -0.44 | +0.59 |
| mid5 | 37 | +0.64 | -0.12 | 49% | +0.82 | +0.34 |

## L3b first
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| first | 145 | +0.74 | +0.38 | 51% | +0.39 | +1.10 |
| repeat | 605 | +0.60 | -0.88 | 46% | +0.53 | +0.68 |

## L4a speed60
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| t1_lo | 263 | +0.59 | -0.12 | 49% | +0.55 | +0.63 |
| t2_mid | 237 | +0.69 | -0.12 | 50% | +0.51 | +0.85 |
| t3_hi | 250 | +0.62 | -2.00 | 43% | +0.46 | +0.82 |

## L4b vol10r
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| t1_lo | 250 | +0.83 | +0.12 | 52% | +0.65 | +1.06 |
| t2_mid | 250 | +0.42 | -1.00 | 46% | +0.41 | +0.43 |
| t3_hi | 250 | +0.64 | -2.00 | 43% | +0.44 | +0.79 |

## L5 fill_delay
| bucket | n | per-trade | median | win% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|
| t1_lo | 255 | +0.71 | -2.00 | 43% | +0.56 | +0.90 |
| t2_mid | 245 | +0.45 | -2.00 | 45% | +0.72 | +0.21 |
| t3_hi | 250 | +0.72 | +0.25 | 53% | +0.26 | +1.23 |

## L6 EXIT ANATOMY (where the money comes from)
| exit | n | net | per-trade | 22-02 net | 25-10 net |
|---|---|---|---|---|---|
| cap | 11 | +56.6 | +5.15 | +30.0 | +26.6 |
| capture | 237 | +973.2 | +4.11 | +437.1 | +536.1 |
| flowfade | 149 | +148.2 | +0.99 | +93.5 | +54.8 |
| stop | 353 | -706.0 | -2.00 | -366.0 | -340.0 |

## TOP-vs-REST TESTS (BH-FDR q=0.10 across the lens family)
| lens | top bucket | n | per-trade | MW p | BH | both-months dir | FINDING |
|---|---|---|---|---|---|---|---|
| L1 news | c_quiet>45 | 534 | +0.70 | 0.1918 | fail | yes | - |
| L2 hour | d_14-15 | 84 | +0.75 | 0.9518 | fail | yes | - |
| L3a score | hi>=6 | 642 | +0.68 | 0.4425 | fail | yes | - |
| L3b first | first | 145 | +0.74 | 0.6007 | fail | NO | - |
| L4a speed60 | t2_mid | 237 | +0.69 | 0.4439 | fail | yes | - |
| L4b vol10r | t1_lo | 250 | +0.83 | 0.1140 | fail | yes | - |
| L5 fill_delay | t3_hi | 250 | +0.72 | 0.1775 | fail | NO | - |

## PROMOTION RULE CHECK (frozen: monotone + FINDING + n>=150 + per-trade >= +0.85 + both months positive)
(none printed = no qualifier; the null is reportable per spec)

Banked: trades_s1any_covered / trades_5w_fullrth (with features) / trades_s5mf parquets. Registry: T-SR03.
