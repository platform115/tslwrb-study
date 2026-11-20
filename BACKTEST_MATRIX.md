# BACKTEST MATRIX — LIVING REPORT (v2, standard-display blocks)
> One full block per tested combo, per RESULTS_DISPLAY_STANDARD.md.
> "-" = never measured in that run; such cells backfill when the combo
> re-runs. Costs/sizing out of scope. Last update: 2026-11-21.

=====================================================================
## Strategy 3A | M1 | 2025-10 | RTH          (T-BS01)
A: his trades 92 | fired ~299/day | caught 79 (86%) | extra fires: rest
| metric | HIS | OURS |
|---|---|---|
| trades | 92 | 1644 |
| win rate | 82% | 41% |
| points won / lost | +642.2 / -22.2 | - / - |
| net points | +620.0 | +84.2 |
| avg win / avg loss | +8.56 / -1.31 | +1.76 / -1.11 |
| worst single trade (MAE) | - | - |
| max drawdown from start | ~0 | 47.4 |

## Strategy 3B | M1 | 2025-10 | RTH          (T-BS01)
A: his trades 92 | fired 428 trades taken | caught - | extra -
| metric | HIS | OURS |
|---|---|---|
| trades | 92 | 428 |
| win rate | 82% | 40% |
| points won / lost | +642.2 / -22.2 | - / - |
| net points | +620.0 | -9.5 |
| avg win / avg loss | +8.56 / -1.31 | +1.84 / -1.25 |
| worst single trade (MAE) | - | - |
| max drawdown from start | ~0 | 21.2 |

## Strategy 3C | M1 | 2025-10 | RTH          (T-BS01 / T-IM34)
A: his trades 92 | fired 423 (18.6/day) | caught 35 (38%) | extra 388
| metric | HIS | OURS |
|---|---|---|
| trades | 92 | 373 |
| win rate | 82% | 42% |
| points won / lost | +642.2 / -22.2 | - / - |
| net points | +620.0 | -36.8 |
| avg win / avg loss | +8.56 / -1.31 | +1.79 / -1.47 |
| worst single trade (MAE) | - | - |
| max drawdown from start | ~0 | 45.0 |

## Strategy 3C | M1A | 2025-10 | RTH         (T-MG04)
A: as above (same entry rule, same period)
| metric | HIS | OURS |
|---|---|---|
| trades | 92 | 326 |
| win rate | 82% | 42% |
| points won / lost | +642.2 / -22.2 | - / - |
| net points | +620.0 | -57.0 |
| avg win / avg loss | +8.56 / -1.31 | +2.97 / -2.42 |
| worst single trade (MAE) | - | - |
| max drawdown from start | ~0 | 83.9 |

## Strategy 1 | native exit stack | 2021-09 OOS   (T-EN46)
A: his trades 124 | fired 144 trades taken | caught - (never measured) | -
| metric | HIS | OURS |
|---|---|---|
| trades | 124 | 144 |
| win rate | 82% | 49% |
| points won / lost | - / - | - / - |
| net points | +383.8 | +62.5 |
| avg win / avg loss | +3.97 / -0.95 | - / - |
| worst single trade (MAE) | - | - |
| max drawdown from start | 0.8 | - |

## Strategy 1 | native exit stack | 2024-11 OOS   (T-EN46)
A: his trades - (not tabulated for 2024-11) | fired 175 | caught - | -
| metric | HIS | OURS |
|---|---|---|
| trades | - | 175 |
| win rate | - | 44% |
| net points | - | -7.2 |
| all other rows | - | - |

=====================================================================
## MANAGEMENT-ONLY RUNS (HIS entries under our plans; per-unit)
| management | period | trades | win | pts won/lost | avg win/loss | net | maxDD | source |
|---|---|---|---|---|---|---|---|---|
| his own | 2025-10 | 92 | 82% | +642.2/-22.2 | +8.56/-1.31 | +620.0 | ~0 | T-MG01 |
| M0 | 2025-10 | 92 | 30% | -/- | +8.96/-3.02 | +57.6 | 4.1 | T-MG02 |
| M1 | 2025-10 | 92 | 75% | +219.6/-19.6 | +3.18/-0.85 | +200.0 | ~0 | T-MG01 |
| M1A | 2025-10 | 92 | 66% | -/- | +4.71/-1.45 | +242.5 | ~0 | T-MG02 |
| his own | 2022-02 | 221 | 71% | -/- | +5.48/-1.82 | +751.2 | 10.5 | T-MG04 |
| M1 | 2022-02 | 221 | 65% | -/- | +4.27/-4.67 | +246.2 | 4.1 | T-MG04 |
| M1A | 2022-02 | 221 | 56% | -/- | +5.94/-5.30 | +222.4 | 9.0 | T-MG04 |
| his own | 2021-09 | 124 | 82% | -/- | +3.97/-0.95 | +383.8 | 0.8 | T-MG04 |
| M1 | 2021-09 | 124 | 73% | -/- | +1.84/-0.69 | +142.4 | ~0 | T-MG04 |
| M1A | 2021-09 | 124 | 63% | -/- | +3.06/-1.01 | +192.6 | 2.1 | T-MG04 |

## CATCH-ONLY MEASUREMENTS (no P&L taken)
| entry | period | his trades | fires/day | caught | share | source |
|---|---|---|---|---|---|---|
| Strategy 3C | 2022-02 | 223 | 18.0 | 58 | 26% | T-IM36 |
| Strategy 3C | 2021-09 | 176 | 13.0 | 34 | 19% | T-IM36 |
| Strategy 3D | 2025-10 | 92 | 48.4 | 45 | 49% | T-IM35 |
| Strategy 3D | 2022-02 | 223 | 49.7 | 97 | 44% | T-IM36 |
| Strategy 3D | 2021-09 | 176 | 34.0 | 57 | 32% | T-IM36 |

## UNTESTED COMBOS (the open grid)
| entry | management | note |
|---|---|---|
| Strategy 1 | M0 / M1 / M1A | only ever run with native exits |
| Strategy 1 | - | activity-vs-HIS never measured; his 2024-11 table never built |
| Strategy 3A / 3B | M0 / M1A | |
| Strategy 3C / 3D | M0 | |
| Strategy 3D | any management (P&L) | catch-only so far |
| all Strategy 3x | ETH slice | T-BS01 was RTH-only |
| all combos | 2024-11 | untouched by the Strategy 3 family |
| all combos | regime splits (vol terciles, KME days) | required by the standard |
| anything | M2 | does not exist yet |
| re-runs | points won/lost + MAE backfill | standard adopted after these runs |

## UPDATE RULE
Every new run adds its full standard block, fills "-" cells it measures,
removes its combo from the untested grid, cites its T-id.
