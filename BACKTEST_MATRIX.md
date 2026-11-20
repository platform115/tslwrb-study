# BACKTEST MATRIX — LIVING REPORT
> Updated with every run. One row per tested combo; untested combos listed
> at the bottom. Full tables follow RESULTS_DISPLAY_STANDARD.md; cells
> never measured show "-" (points won/lost split and per-trade MAE were
> added to the standard 2026-11-21 and backfill only when a combo re-runs).
> Costs/sizing out of scope throughout. Last update: 2026-11-21 (T-EN102).

## 1. TESTED COMBOS — summary matrix
| entry | management | period/slice | trades | win | avg win/loss | net | maxDD | source |
|---|---|---|---|---|---|---|---|---|
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
| Strategy 1 | native exit stack | 2025-10+2022-02 (in-sample) | - | - | - | +0.84/trade | - | T-EN45 |
| Strategy 1 | native exit stack | 2021-09 (OOS) | 144 | 49% | - | +62.5 | - | T-EN46 |
| Strategy 1 | native exit stack | 2024-11 (OOS) | 175 | 44% | - | -7.2 | - | T-EN46 |
| Strategy 3A | M1 | 2025-10 RTH | 1644 | 41% | +1.76/-1.11 | +84.2 | 47.4 | T-BS01 |
| Strategy 3B | M1 | 2025-10 RTH | 428 | 40% | +1.84/-1.25 | -9.5 | 21.2 | T-BS01 |
| Strategy 3C | M1 | 2025-10 RTH | 373 | 42% | +1.79/-1.47 | -36.8 | 45.0 | T-BS01 |
| Strategy 3C | M1A | 2025-10 RTH | 326 | 42% | +2.97/-2.42 | -57.0 | 83.9 | T-MG04 |

## 2. ACTIVITY STATS vs HIS (where measured; catch = his trades flagged)
| entry rule | period | his trades | fires (per day) | caught | share |
|---|---|---|---|---|---|
| Strategy 3A | 2025-10 | 92 | ~299/day | 79 | 86% |
| Strategy 3C | 2025-10 | 92 | 423 (18.6/day) | 35 | 38% |
| Strategy 3C | 2022-02 | 223 | 18.0/day | 58 | 26% |
| Strategy 3C | 2021-09 | 176 | 13.0/day | 34 | 19% |
| Strategy 3D | 2025-10 | 92 | 48.4/day | 45 | 49% |
| Strategy 3D | 2022-02 | 223 | 49.7/day | 97 | 44% |
| Strategy 3D | 2021-09 | 176 | 34.0/day | 57 | 32% |
(Strategy 1 catch-vs-his: never measured - listed untested below.)

## 3. UNTESTED COMBOS (the open grid)
| entry | management | note |
|---|---|---|
| Strategy 1 | M0 / M1 / M1A | only ever run with its native exit stack |
| Strategy 1 | - | activity-vs-HIS (catch/fires) never measured |
| Strategy 3A / 3B | M0 / M1A | |
| Strategy 3C / 3D | M0 | |
| Strategy 3D | any management as P&L | only catch-tested, never traded |
| all Strategy 3x | ETH slice | T-BS01 was RTH-only |
| all combos | 2024-11 | month never touched by Strategy 3 family |
| all combos | per-regime splits (vol terciles, KME days) | standard asks for them |
| anything | M2 | does not exist yet |

## UPDATE RULE
Every new run: add its row(s) to section 1 (and 2 where applicable) in
the standard display, remove the combo from section 3, cite the T-id.
