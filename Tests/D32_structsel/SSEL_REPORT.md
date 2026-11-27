# SSEL REPORT — STRUCTURAL SELECTORS, SURGICAL LINE (T-SR04, D-32)
STATUS: CLOSED | 2026-11-27 | Spec: SSEL_SPEC.md (frozen first) | control: banked 750/+472.1 reproduced | features 750/750 | TRAINING-ONLY context

Baseline: 750 trades, +0.63/trade; 353 stops (-2.00 each), 237 captures (+4.11 each).

## S1 room-to-level
| bucket | n | per-trade | median | win% | capture% | stop% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|---|---|
| b2-4 | 286 | +0.73 | +0.88 | 55% | 45% | 40% | +0.70 | +0.78 |
| c4-8 | 396 | +0.57 | -2.00 | 43% | 27% | 51% | +0.30 | +0.81 |
| d>8/none | 68 | +0.54 | -2.00 | 38% | 3% | 56% | +0.68 | +0.34 |

## S2 room-to-famedge
| bucket | n | per-trade | median | win% | capture% | stop% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|---|---|
| a<=2 | 647 | +0.53 | -1.12 | 45% | 30% | 49% | +0.40 | +0.68 |
| b2-4 | 61 | +1.49 | +2.12 | 62% | 48% | 31% | +1.64 | +1.37 |
| c4-8 | 17 | +2.51 | +2.62 | 82% | 53% | 18% | +2.62 | +2.44 |
| d>8/none | 25 | -0.22 | -2.00 | 36% | 16% | 60% | -0.95 | +0.06 |

## S3 stacked<=0.75
| bucket | n | per-trade | median | win% | capture% | stop% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|---|---|
| clean | 49 | +0.93 | +0.12 | 51% | 45% | 47% | +1.12 | +0.82 |
| stacked | 701 | +0.61 | -0.62 | 47% | 31% | 47% | +0.48 | +0.75 |

## S4 range-pos
| bucket | n | per-trade | median | win% | capture% | stop% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|---|---|
| t1_interior | 251 | +0.78 | -0.38 | 48% | 37% | 47% | +0.79 | +0.76 |
| t2_mid | 250 | +0.74 | -0.12 | 49% | 32% | 45% | +0.39 | +1.14 |
| t3_extension | 249 | +0.37 | -1.62 | 44% | 26% | 49% | +0.31 | +0.43 |

## S5 backstop
| bucket | n | per-trade | median | win% | capture% | stop% | 22-02 pt | 25-10 pt |
|---|---|---|---|---|---|---|---|---|
| b2-6 | 468 | +0.76 | -0.12 | 50% | 35% | 45% | +0.61 | +0.93 |
| c>6/none | 282 | +0.42 | -2.00 | 43% | 26% | 51% | +0.31 | +0.51 |

## TOP-vs-REST (BH-FDR q=0.10 across 5 lenses)
| lens | top bucket | n | per-trade | MW p | BH | both-dir | FINDING |
|---|---|---|---|---|---|---|---|
| S1 room-to-level | b2-4 | 286 | +0.73 | 0.1080 | fail | yes | - |
| S2 room-to-famedge | c4-8 | 17 | +2.51 | 0.0064 | PASS | yes | FINDING |
| S3 stacked<=0.75 | clean | 49 | +0.93 | 0.4533 | fail | yes | - |
| S4 range-pos | t1_interior | 251 | +0.78 | 0.3429 | fail | yes | - |
| S5 backstop | b2-6 | 468 | +0.76 | 0.0568 | fail | yes | - |

## PROMOTION RULE CHECK (monotone + FINDING + n>=150 + >=+0.85 + both months positive)
(no qualifier)

Banked: trades_5w_struct.parquet (750 trades + structural features). Registry: T-SR04.
