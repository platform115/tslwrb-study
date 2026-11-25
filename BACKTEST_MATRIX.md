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
| Strategy 1 | M1 | 2025-10 RTH | 260 | 38% | +1.45/-1.59 | -113.2 | 114.1 | T-BS02 |
| Strategy 1 | M1 | 2022-02 RTH | 224 | 47% | +2.18/-1.72 | +24.2 | 12.0 | T-BS02 |
| Strategy 1 | M1A | 2025-10 RTH | 231 | 35% | +2.87/-2.25 | -104.6 | 121.6 | T-BS03 |
| Strategy 1 | M1A | 2022-02 RTH | 204 | 34% | +3.29/-2.82 | -147.2 | 147.2 | T-BS03 |
| Strategy 1 | M0 | 2025-10 RTH | 178 | 19% | +7.25/-2.56 | -131.6 | 151.4 | T-BS04 |
| Strategy 1 | M0 | 2022-02 RTH | 163 | 14% | +14.37/-2.55 | -26.6 | 97.6 | T-BS04 |
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

### Strategy 1 — all measured months
Activity (catch = his entry within +/-5 min of a fill, direction-matched;
definition adopted at T-BS02 for fill-based rules):
| | 2025-10 | 2022-02 |
|---|---|---|
| his trades | 92 | 221 |
| fills (per day) | 260 (10.4) | 224 (9.7) |
| his caught | 35 (38%) | 70 (32%) |

#### Strategy 1 | M1 | RTH (T-BS02 - full standard block, exact splits + MAE)
| metric | HIS 25-10 | OURS 25-10 | HIS 22-02 | OURS 22-02 |
|---|---|---|---|---|
| trades | 92 | 260 | 221 | 224 |
| win rate | 82% | 38% | 71% | 47% |
| points won / lost | +642.2 / -22.2 | +143.1 / -256.4 | +865.8 / -114.5 | +229.0 / -204.8 |
| net points | +620.0 | -113.2 | +751.2 | +24.2 |
| avg win / avg loss | +8.56 / -1.31 | +1.45 / -1.59 | +5.48 / -1.82 | +2.18 / -1.72 |
| worst single trade / worst MAE | -3.00 / - | -5.12 / 5.12 | -4.00 / - | -6.00 / 6.00 |
| max drawdown from start | ~0 | 114.1 | 10.5 | 12.0 |
Exits: ~93% stall - M1's clock closes Strategy 1's confirmation entries
before their pt-ladder targets can be reached. READ: entries and
management are COUPLED; M1 fits HIS entries, not Strategy 1's (native
stack earned +0.84/trade on these same months).

#### Strategy 1 | M1A | RTH (T-BS03)
| metric | OURS 25-10 | OURS 22-02 |
|---|---|---|
| trades | 231 | 204 |
| win rate | 35% | 34% |
| points won / lost | +232.2 / -336.9 | +230.1 / -377.4 |
| net points | -104.6 | -147.2 |
| avg win / avg loss | +2.87 / -2.25 | +3.29 / -2.82 |
| worst single trade / worst MAE | -6.38 / 6.38 | -4.88 / 5.38 |
| max drawdown from start | 121.6 | 147.2 |
READ: longer patience does NOT fix the fit - M1A matches M1's loss in
2025-10 and turns 2022-02 from +24.2 to -147.2 (wins grow to +2.87/+3.29
but losses grow faster). The coupling is not about clock speed: these
confirmation entries need their native structure (fast-fail 2.0 +
pt-ladder targets + 9-bar time), not a stall clock of any length.

#### Strategy 1 | M0 | RTH (T-BS04; single leg, reversal omitted as in T-MG02)
| metric | OURS 25-10 | OURS 22-02 |
|---|---|---|
| trades | 178 | 163 |
| win rate | 19% | 14% |
| points won / lost | +239.2 / -370.9 | +330.5 / -357.1 |
| net points | -131.6 | -26.6 |
| avg win / avg loss | +7.25 / -2.56 | +14.37 / -2.55 |
| worst single trade / worst MAE | -4.88 / 4.88 | -5.88 / 5.88 |
| max drawdown from start | 151.4 | 97.6 |
STRATEGY 1 M-SERIES EXPLORATION CLOSED: all three plans lose. M0's
fast-fail 1.5 kills ~55% of trades in two bars; the few survivors are
huge (avg win up to +14.4 - the 27-bar clock lets winners run past where
the pt-ladder would exit) but far too few. Bracketed precisely, the
native stack's value lies in: fast-fail at 2.0 not 1.5, time 9 bars not
27, pt-ladder targets, and the reversal leg (absent from all these
single-leg runs; native's +0.84/trade included it). Strategy 1 keeps its
NATIVE exit stack in the register; fill counts differ across plans
because the 5-min cooldown keys off each plan's own exit times.

#### Strategy 1 | native exit stack (historical era, thin record)
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
| Strategy 1 | (none - M-series complete) | M0/M1/M1A all tested (T-BS02..04), all poor; native stack stands |
| Strategy 1 | - | his 2024-11 comparison table still never built |
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

## STRATEGY 4 x M3 — THE G2 BUILD (T-BS05, 2026-11-25; training months pooled)
HIS G2 same period: 62 trades, 74% win, net +231.2, +5.71/-1.97, worst -3.75.
| combo | trades | win | net (22-02/25-10) | worst | maxMAE | maxDD | caught/62 | extras net |
|---|---|---|---|---|---|---|---|---|
| 4A d1.25 x M3A (WINNER) | 473 | 44% | +135.8 (+55.1/+80.6) | -3.75 | 5.62 | 35.1 | 39 | +47.0 |
| 4A d2.5 x M3C (runner-up) | 381 | 43% | +125.5 (+34.0/+91.5) | -3.75 | 7.88 | 48.8 | 47 | +105.5 |
| 4A d1.25 x M3C | 434 | 41% | +94.4 | -3.75 | 5.88 | 47.9 | 37 | +88.4 |
| 4B d1.25 x M3A | 287 | 44% | +61.8 | -3.75 | 5.62 | 34.6 | 38 | +1.2 |
| 4A d1.25 x M3B | 421 | 41% | +52.8 | -3.75 | 5.62 | 61.4 | 37 | +9.0 |
| others (7) | - | - | +44.4 .. -17.2 (B4 report) | - | - | - | - | - |
Winner rule (pre-stated): positive both months AND extras net >= 0, highest pooled net. 7/12 qualified.
Note: M3B (stall 90) - best on HIS fills in B3 - is WORST on OUR fills (extras punish patience): the entry-management coupling, measured again.

## B5 VALIDATION (T-BS06, 2024-11, first touch - QUARANTINE SPENT, look 1)
| combo | trades | win | net | worst | maxMAE | maxDD | caught | extras net | verdict |
|---|---|---|---|---|---|---|---|---|---|
| 4A d1.25 x M3A | 190 | 53% | +63.6 | -3.75 | 3.88 | 16.1 | 8/11 his G2-like (73%) | +61.9 | PASS (pre-stated rule) |
HIS 2024-11 G2-like: 11 entries, 91% win, +104.2. Note: our P&L that month came almost entirely from extras.
