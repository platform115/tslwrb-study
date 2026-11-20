# BACKTEST MATRIX — LIVING REPORT (v3)
> Layout: (1) compact summary matrix, one row per combo x period;
> (2) per-combo detail in the agreed standard display, months side by side
> where a combo ran on several; (3) management-only runs; (4) catch-only
> measurements; (5) untested grid; update rule at the end.
> "-" = never measured in that run (backfills on re-run). Costs/sizing out
> of scope. Last update: 2026-11-21.

## 1. SUMMARY MATRIX (every tested combo x period)
| entry | mgmt | period | trades | win | avg win/loss | net | maxDD | source |
|---|---|---|---|---|---|---|---|---|
| Strategy 1 | native | 2025-10+2022-02 (IS) | - | - | - | +0.84/tr | - | T-EN45 |
| Strategy 1 | native | 2021-09 (OOS) | 144 | 49% | - | +62.5 | - | T-EN46 |
| Strategy 1 | native | 2024-11 (OOS) | 175 | 44% | - | -7.2 | - | T-EN46 |
| Strategy 3A | M1 | 2025-10 RTH | 1644 | 41% | +1.76/-1.11 | +84.2 | 47.4 | T-BS01 |
| Strategy 3B | M1 | 2025-10 RTH | 428 | 40% | +1.84/-1.25 | -9.5 | 21.2 | T-BS01 |
| Strategy 3C | M1 | 2025-10 RTH | 373 | 42% | +1.79/-1.47 | -36.8 | 45.0 | T-BS01 |
| Strategy 3C | M1A | 2025-10 RTH | 326 | 42% | +2.97/-2.42 | -57.0 | 83.9 | T-MG04 |
| HIS | his own | 2025-10 | 92 | 82% | +8.56/-1.31 | +620.0 | ~0 | T-MG01 |
| HIS | his own | 2022-02 | 221 | 71% | +5.48/-1.82 | +751.2 | 10.5 | T-MG04 |
| HIS | his own | 2021-09 | 124 | 82% | +3.97/-0.95 | +383.8 | 0.8 | T-MG04 |
| HIS | M0 | 2025-10 | 92 | 30% | +8.96/-3.02 | +57.6 | 4.1 | T-MG02 |
| HIS | M1 | 2025-10 | 92 | 75% | +3.18/-0.85 | +200.0 | ~0 | T-MG01 |
| HIS | M1 | 2022-02 | 221 | 65% | +4.27/-4.67 | +246.2 | 4.1 | T-MG04 |
| HIS | M1 | 2021-09 | 124 | 73% | +1.84/-0.69 | +142.4 | ~0 | T-MG04 |
| HIS | M1A | 2025-10 | 92 | 66% | +4.71/-1.45 | +242.5 | ~0 | T-MG02 |
| HIS | M1A | 2022-02 | 221 | 56% | +5.94/-5.30 | +222.4 | 9.0 | T-MG04 |
| HIS | M1A | 2021-09 | 124 | 63% | +3.06/-1.01 | +192.6 | 2.1 | T-MG04 |

## 2. PER-COMBO DETAIL (standard display; months side by side)

### Strategy 3C | M1 (and M1A) — one trigger, all measured months
Activity:
| | 2025-10 | 2022-02 | 2021-09 |
|---|---|---|---|
| his trades | 92 | 223 | 176 |
| fires (per day) | 423 (18.6) | (18.0/day) | (13.0/day) |
| his caught | 35 (38%) | 58 (26%) | 34 (19%) |
Performance (P&L exists for 2025-10 only; validation months were
catch-only - P&L there is an untested cell):
| metric | HIS 25-10 | OURS M1 | OURS M1A |
|---|---|---|---|
| trades | 92 | 373 | 326 |
| win rate | 82% | 42% | 42% |
| points won / lost | +642.2 / -22.2 | - / - | - / - |
| net points | +620.0 | -36.8 | -57.0 |
| avg win / avg loss | +8.56 / -1.31 | +1.79 / -1.47 | +2.97 / -2.42 |
| worst single trade (MAE) | - | - | - |
| max drawdown from start | ~0 | 45.0 | 83.9 |

### Strategy 3A / 3B | M1 | 2025-10 RTH
Activity: his 92 | 3A caught 79 (86%), ~299 fires/day | 3B caught -, 428 taken
| metric | HIS | 3A OURS | 3B OURS |
|---|---|---|---|
| trades | 92 | 1644 | 428 |
| win rate | 82% | 41% | 40% |
| points won / lost | +642.2 / -22.2 | - / - | - / - |
| net points | +620.0 | +84.2 | -9.5 |
| avg win / avg loss | +8.56 / -1.31 | +1.76 / -1.11 | +1.84 / -1.25 |
| worst single trade (MAE) | - | - | - |
| max drawdown from start | ~0 | 47.4 | 21.2 |

### Strategy 1 | native exit stack — all measured months
Activity: catch-vs-HIS never measured (open cell); fires = trades taken.
| metric | HIS 21-09 | OURS 21-09 | HIS 24-11 | OURS 24-11 |
|---|---|---|---|---|
| trades | 124 | 144 | - | 175 |
| win rate | 82% | 49% | - | 44% |
| points won / lost | - / - | - / - | - | - / - |
| net points | +383.8 | +62.5 | - | -7.2 |
| avg win / avg loss | +3.97 / -0.95 | - / - | - | - / - |
| worst single trade (MAE) | - | - | - | - |
| max drawdown from start | 0.8 | - | - | - |
(In-sample reference: +0.84/trade on 2025-10+2022-02, T-EN45. His 2024-11
table never built - open cell.)

## 3. MANAGEMENT-ONLY RUNS (HIS entries under our plans, per-unit; months side by side)
| metric | his own 25-10 | M0 25-10 | M1 25-10 | M1A 25-10 | his own 22-02 | M1 22-02 | M1A 22-02 | his own 21-09 | M1 21-09 | M1A 21-09 |
|---|---|---|---|---|---|---|---|---|---|---|
| trades | 92 | 92 | 92 | 92 | 221 | 221 | 221 | 124 | 124 | 124 |
| win rate | 82% | 30% | 75% | 66% | 71% | 65% | 56% | 82% | 73% | 63% |
| pts won / lost | +642.2/-22.2 | -/- | +219.6/-19.6 | -/- | -/- | -/- | -/- | -/- | -/- | -/- |
| net | +620.0 | +57.6 | +200.0 | +242.5 | +751.2 | +246.2 | +222.4 | +383.8 | +142.4 | +192.6 |
| avg win/loss | +8.56/-1.31 | +8.96/-3.02 | +3.18/-0.85 | +4.71/-1.45 | +5.48/-1.82 | +4.27/-4.67 | +5.94/-5.30 | +3.97/-0.95 | +1.84/-0.69 | +3.06/-1.01 |
| maxDD | ~0 | 4.1 | ~0 | ~0 | 10.5 | 4.1 | 9.0 | 0.8 | ~0 | 2.1 |

## 4. CATCH-ONLY MEASUREMENTS (no P&L taken)
| entry | period | his trades | fires/day | caught | share | source |
|---|---|---|---|---|---|---|
| Strategy 3D | 2025-10 | 92 | 48.4 | 45 | 49% | T-IM35 |
| Strategy 3D | 2022-02 | 223 | 49.7 | 97 | 44% | T-IM36 |
| Strategy 3D | 2021-09 | 176 | 34.0 | 57 | 32% | T-IM36 |

## 5. UNTESTED COMBOS (the open grid)
| entry | management | note |
|---|---|---|
| Strategy 1 | M0 / M1 / M1A | only ever run with native exits |
| Strategy 1 | - | catch-vs-HIS never measured; his 2024-11 table never built |
| Strategy 3A / 3B | M0 / M1A | |
| Strategy 3C / 3D | M0 | |
| Strategy 3C | any mgmt, 2022-02 / 2021-09 / 2024-11 P&L | catch measured, P&L not |
| Strategy 3D | any management (P&L) | catch-only so far |
| all Strategy 3x | ETH slice | T-BS01 was RTH-only |
| all combos | 2024-11 | untouched by the Strategy 3 family |
| all combos | regime splits (vol terciles, KME days) | required by the standard |
| anything | M2 | does not exist yet |
| re-runs | points won/lost + MAE backfill | standard postdates these runs |

## UPDATE RULE
Every new run: add its summary row (1), extend its combo's detail block
(2) with the new month column, fill "-" cells it measures, remove its
combo from (5), cite its T-id.
