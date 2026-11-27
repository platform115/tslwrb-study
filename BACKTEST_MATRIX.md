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
| 4A d1.25 x M3A (WINNER = G2-1) | 473 | 44% | +135.8 (+55.1/+80.6) | -3.75 | 5.62 | 35.1 | 39 | +47.0 |
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
| G2-1 (4A d1.25 x M3A) | 190 | 53% | +63.6 | -3.75 | 3.88 | 16.1 | 8/11 his G2-like (73%) | +61.9 | PASS (pre-stated rule) |
HIS 2024-11 G2-like: 11 entries, 91% win, +104.2. Note: our P&L that month came almost entirely from extras.

## G2-2 CANDIDATE (T-MG14, 2026-11-26; training months pooled)
| combo | trades | win-side | net (22-02/25-10) | caught/62 | extras net | status |
|---|---|---|---|---|---|---|
| G2-2 = 4A d1.25 x M7 (level-snap reach8) | 500 | - | +186.0 (+84.6/+101.4) | 40 | +88.4 | TRAINING ONLY - validation month to be pre-committed & purchased |
| 4A d1.25 x M7-reach5 | 500 | - | +154.9 | 40 | +57.2 | qualifier, not selected |
vs G2-1 +135.8 / catch 39 / extras +47.0. Flag: reach monotone to the tested boundary (8).

## G2-3 CANDIDATE (T-EN104, 2026-11-26; training months pooled)
| combo | trades | net (22-02/25-10) | caught/62 | extras net | status |
|---|---|---|---|---|---|
| G2-3 = 4A-v2 d1.25 x M7 | 542 | +265.4 (+140.5/+124.9) | 46 (74%) | +173.0 | TRAINING ONLY |
| 4A-v2 d1.25 x M3A | 515 | +244.6 (+108.0/+136.6) | 46 | +158.6 | qualifier |
vs G2-2 +186.0/40 and G2-1 +135.8/39. Third stacked training improvement - validation months arbitrate.

## RT ROUND — BREAK-AND-RETEST ENTRY (T-EN106, 2026-11-26; training months pooled)
Entry timing only; everything else = exact G2-3 config. Spec RT_SPEC.md, frozen first.
| cell | trades | per-trade | net (22-02/25-10) | caught/62 | extras net | verdict |
|---|---|---|---|---|---|---|
| Wr120 pb0.25 | 521 | +0.48 | +250.4 (+134.6/+115.8) | 43 | +163.8 | no |
| Wr120 pb0.75 | 540 | +0.50 | +269.6 (+158.2/+111.4) | 45 | +177.0 | no (baseline replica) |
| Wr300 pb0.25 | 525 | +0.50 | +265.0 (+148.4/+116.6) | 43 | +177.5 | no |
| Wr300 pb0.75 | 540 | +0.50 | +269.6 (+158.2/+111.4) | 45 | +177.0 | no (baseline replica) |
REJECTED on both pre-stated lines. Design hole found post-run (median cross
overshoot 0.12pt -> pb0.75 "retest" instantly satisfied on 94.5% of crosses;
pb0.25 on 68.6%): hypothesis only weakly tested. A true retest needs a minimum
excursion beyond the edge before the pullback counts (RT v2 = new spec, J's
call vs training freeze). G2-3 stands. Untested grid: excursion-gated retest.

## RT2 ROUND — EXCURSION-GATED RETEST (T-EN107, 2026-11-26; training months pooled)
Gate: price must extend >= X beyond the edge, pull back to within pb, then re-break (stop e+1.25d, TTL 300s). Else exact G2-3.
| cell | trades | per-trade | net (22-02/25-10) | caught/62 | extras net | verdict |
|---|---|---|---|---|---|---|
| X1.0 pb0.25 | 383 | +0.60 | +228.4 (+137.5/+90.9) | 34 | +157.1 | no |
| X1.0 pb0.75 | 439 | +0.52 | +228.4 (+114.0/+114.4) | 37 | +171.5 | no |
| X2.0 pb0.25 | 300 | +0.80 | +240.8 (+165.2/+75.5) | 32 | +162.9 | no |
| X2.0 pb0.75 | 342 | +0.52 | +176.4 (+153.1/+23.2) | 38 | +151.0 | no |
REJECTED as replacement (catch structurally capped: Part A shows he retest-takes only 32/50 matched entries, first-takes 17). First entry-side lever to move per-trade quality (+0.80 best vs +0.49). Untested grid: two-lane (first-break + retest) = combo, awaiting J.

## TL ROUND — TWO-LANE ENTRY (T-EN108, 2026-11-26) — CONTROL GATE TRIPPED, PENDING J
The round's control arm exposed an engine convention defect in ALL prior combo
backtests: single-position applied in cross order, not fill order (not
executable; not lookahead; reproduction of G2-3 to the decimal confirms it is
the only difference). Numbers below use the REALISTIC (fill-time) engine and
are provisional until J rules on re-baselining:
| cell | trades (L1/L2) | per-trade | net (22-02/25-10) | caught/62 | extras net |
|---|---|---|---|---|---|
| lane1-only = "G2-3 corrected" | 607 | +0.45 | +276.1 (+111.8/+164.4) | 47 | +185.6 |
| TL-A (+retest X2.0 pb0.25) | 760 (490/270) | +0.36 | +272.2 (+108.9/+163.4) | 47 | +207.4 |
| TL-B (+retest X1.0 pb0.75) | 757 (517/240) | +0.43 | +325.1 (+137.6/+187.5) | 48 | +246.8 |
NO ADOPTION DECLARED. Decisions to J: (1) re-baseline on fill-time engine,
(2) TL-B adopt/alternate/reject (clears corrected incumbent on net/catch/extras;
lane2 quality +0.28/trade dilutes per-trade).

## ENGINE CONVENTION (standard as of T-EN108, J-approved 2026-11-26)
Single-position is applied in FILL-TIME order (executable convention). All
rows above this line were produced under the old cross-order convention and
are kept for traceability; the corrected incumbent line is G2-3 = +276.1 /
607 / catch 47 / extras +185.6, and G2-4 (two-lane TL-B) = +325.1 / 757 /
catch 48 / extras +246.8 is REGISTERED AS QUALITY-ALTERNATE. Both go to the
purchased validation months; those months arbitrate.

## CD ROUND — CADENCE CAP PER NEWS WINDOW (T-EN110, 2026-11-26; fill-time engine)
| cell | trades | per-trade | net (22-02/25-10) | caught/62 | extras net | verdict |
|---|---|---|---|---|---|---|
| CONTROL (= G2-3 corrected) | 607 | +0.45 | +276.1 (+111.8/+164.4) | 47 | +185.6 | incumbent reproduced exactly |
| N=3 | 262 | +0.55 | +144.8 (+62.4/+82.4) | 30 | +93.1 | no |
| N=2 | 184 | +0.70 | +128.5 (+44.5/+84.0) | 25 | +68.5 | no |
| N=1 | 98 | +0.90 | +88.0 (+41.8/+46.2) | 14 | +28.1 | no |
ALL REJECTED as replacement. Monotone quality gradient (never reaches +0.98);
later fills per window carry ~2/3 of net; his sparseness is selection, not
earliness. Entry-side pre-freeze program COMPLETE (retest line + cadence closed).
POST-GATE (J, 2026-11-26): N=1 cell REGISTERED as G2-5, the high-contract-size
quality variant (+0.90/trade) - saved for validation testing beside G2-3/G2-4,
not adopted.

## M12/M13 ROUNDS — BOOK-GATED EXITS (T-MG21/22, 2026-11-26; fill-time engine)
| cell | trades | net (22-02/25-10) | extras | mechanism (twin-matched delta) | verdict |
|---|---|---|---|---|---|
| CONTROL (M7) | 607 | +276.1 (+111.8/+164.4) | +185.6 | - | incumbent reproduced (both rounds) |
| M12 stall-gate th0.00 | 578 | +274.9 | +216.2 | -5.8 on 96 extended | REJECTED |
| M12 stall-gate th-0.02 | 581 | +280.8 | +209.2 | -5.2 on 84 extended | REJECTED (cell ADOPT line met by busy-reshuffle confound; mechanism negative) |
| M13 clock-ext th0.00/-0.02 | 607 | +276.1 | +185.6 | n=0 (1/607 trades reach 480s) | STRUCTURALLY EMPTY |
Standing lesson (institutionalized in specs from T-MG22 on): management verdicts
are MECHANISM-PRIMARY (twin-matched delta per month), cell totals secondary.
imb10 (T-MG20) stands as description of HIS exits; both monetization shapes
failed on our fills. M7 stands.

## VALIDATION STEP 1 — G2-3 OUT OF SAMPLE (T-VL01, 2026-11-26; 2023-05 + 2024-05, FIRST TOUCH)
| strategy | trades | win | per-trade | net (23-05/24-05) | caught/his | extras | worst | maxDD | frozen verdict |
|---|---|---|---|---|---|---|---|---|---|
| G2-3 | 566 | 51% | +0.26 | +144.4 (+137.6/+6.8) | 7/14 (50%) | +141.1 | -3.75 | 25.2 | FAIL (catch 50% < 60%; all 3 financial lines PASS) |
His same-group line: 14 entries, +65.2 total (+2.40 and +5.92/trade by month).
Shrinkage realized: per-trade +0.45 -> +0.26. 2024-05 nearly flat (+6.8).
Original program goal (30-50% replication) met; the frozen 60% line was not.
POST-GATE (J, 2026-11-26): G2-3 RE-REGISTERED AS A TRACK-2 (MODE-2) SYSTEM -
failed as a replication claim, validated as a standalone earner (all financial
lines passed; no losing month in 4 tested: +111.8/+164.4 training,
+137.6/+6.8 out of sample; the +6.8 month is the recorded robustness caveat).

## VALIDATION STEP 2 — G2-4 OUT OF SAMPLE (T-VL02, 2026-11-26; mode-2 lines)
| strategy | trades | win | per-trade | net (23-05/24-05) | caught/his | extras | worst | maxDD | frozen verdict |
|---|---|---|---|---|---|---|---|---|---|
| G2-4 | 760 | 51% | +0.21 | +158.1 (+118.8/+39.4) | 7/14 (50%) | +154.6 | -3.75 | 28.5 | PASS (all mode-2 lines) |
First full out-of-sample PASS. Holds up in 2024-05 (+39.4) where G2-3 went
nearly flat (+6.8) - the retest lane earned where first-break-only thinned.

## VALIDATION STEP 2b — G2-5 OUT OF SAMPLE (T-VL03, 2026-11-26; mode-2 quality line)
| strategy | trades | win | per-trade | net (23-05/24-05) | caught/his | extras | worst | maxDD | frozen verdict |
|---|---|---|---|---|---|---|---|---|---|
| G2-5 | 99 | 53% | +0.39 | +38.9 (+33.5/+5.4) | 1/14 (7%) | +31.9 | -3.75 | 17.8 | FAIL (per-trade +0.39 < +0.60) |
Engines retro-controlled before the look: v1 -> 607/+276.1, v2 -> 757/+325.1,
v3 -> 98/+88.0, all exact. G2-5's quality edge was mostly training-fit
(+0.90 -> +0.39); dies per the plan's rule. G2-4 remains the sole OOS PASS.

## T-EN115 — G2-6: MULTI-FAMILY EDGES (4A-v3) x M7, SIX MONTHS (2026-11-27)
Spec: Tests/D11_unmatched/G26_SPEC.md (frozen first). R-9 control exact:
restricted-family engine reproduced 757/+325.1 AND 760/+158.1 before the look.
All six months are TRAINING for this claim (families chosen after seeing the
12 unmatched entries) — judge = D-8 purchased months.

| cell | trades | per-trade | pooled | by month (21-09/22-02/23-05/24-05/24-11/25-10) | catch/62 | extras |
|---|---|---|---|---|---|---|
| CONTROL (G2-4) | 2126 | +0.27 | +565.9 | +59/+138/+119/+39/+24/+188 | 48 | +487.5 |
| G2-6 | 6252 | +0.27 | +1659.0 | +173/+324/+372/+219/+231/+340 | 59 | +1556.8 |

Per-family (shared busy clock — attribution = which source fired first, NOT
additive value): GAP 2174/+470.2, SHD 1885/+491.0, WRB 1480/+565.9,
SQZ 379/+34.0, W20 184/+54.5, REA 106/+27.0, PDY 44/+16.4. No family TOXIC
(none negative in >=4/6 months). Frozen verdict: ALL FIVE LINES PASS ->
REGISTER TRAINING-ONLY. Note: same per-trade (+0.27) at 3x the volume —
G2-6 widens the book and closes the catch gap (59/62 = exactly the F-23
ceiling); it does not raise per-trade quality.

## T-SR02 — S5-MF PART A: FAMILY-EDGE TOUCH UNIVERSE, ANY ARM (2026-11-27)
Spec: Tests/D30_s5mf/S5MF_SPEC.md (frozen first, R-11 section included).
R-9 dual controls exact: builder reproduced T-BK03 (1541 approaches /
1263 mb touches, key-for-key) and S1-ANY (422/+216.5). Depth months
(2022-02 + 2025-10); TRAINING-ONLY cap by construction.

| cell | touches | trades | per-trade | pooled | by month | worst |
|---|---|---|---|---|---|---|
| S1-ANY control (693 covered) | 693 | 422 | +0.51 | +216.5 | +134/+82 | -2.00 |
| LVL-ANY (full RTH) | 1264 | 750 | +0.63 | +472.1 | +195/+278 | -2.00 |
| MF-ANY (family edges) | 45454 | 4369 | +0.45 | +1985.6 | +1031/+955 | -2.00 |

All five frozen lines PASS -> S5-MF REGISTERED TRAINING-ONLY. Two
secondary facts, stated plainly: (1) LVL-ANY full-RTH at +0.63 beats the
covered-only S1-ANY (+0.51) - the incumbent universe UNRESTRICTED is the
per-trade quality leader of the surgical line so far, before any 3s
filter; (2) the family widening adds ~6x trades and ~4x pooled P&L at
DILUTED per-trade (+0.45 < +0.63) - volume, not quality, exactly as in
T-EN115. GAP+SHD again dominate (3051 trades, +1515.5 of +1985.6).
PDY tiny and negative (26, -2.8) - watch, not toxic by the frozen rule.
Part B (MF-ACTIVE, the F-21 3s read) needs device-side extraction at the
new touch moments: 45,454 moments is ~36x the prior extraction volume,
so the Part B addendum must choose a restriction (e.g., traded-touch
subset or stratified sample) before any extraction runs.

## T-SR03 — 5W FULL-RTH ANATOMY: CAN THE +0.63 GET SURGICAL? (2026-11-27)
Spec: Tests/D30_s5mf/LVLR_SPEC.md (frozen first; promotion rule frozen
before the look). Controls exact (builder 1541/1263; S1-ANY 422/+216.5;
5W full-RTH 750/+472.1). Six lenses, BH-FDR q=0.10, both-months required.

RESULT: ZERO qualifiers - the reportable null. No live-computable flow,
calendar, or level-state lens separates the +0.63 at FINDING level.
Directional (non-FINDING) facts: quiet>45min +0.70 vs news-window +0.49
vs burst +0.32 (both months same direction - F-24 flavor); LOW pre-touch
10s volume is the best single cell (+0.83, p=0.114, BH fail); first
touch of a level today +0.74 vs repeat +0.60 (months disagree). Exit
anatomy (F-3 echo): capture exits carry the book - +973.2 on 237 trades
(+4.11 each) vs stops -706.0; flow-fade only +148.2 on 149.
Conclusion on record: the surgical upgrade is NOT in 1s flow or
calendar structure; it waits on the 3s BOOK read (Part B / F-21),
consistent with T-BK04 (the discriminator lives in the book and decays
within seconds). Banked assets: trades_s1any_covered.parquet,
trades_5w_fullrth.parquet (with lens features), trades_s5mf.parquet,
mf_touch_moments.csv.

## T-SR04 — STRUCTURAL SELECTORS ON THE SURGICAL LINE (2026-11-27)
Spec: Tests/D32_structsel/SSEL_SPEC.md (frozen first). Control: banked
750/+472.1 reproduced. Five structural lenses (F-7/F-23..26 vocabulary).
ONE FINDING (BH q=0.10, both months): S2 room-to-family-edge-ahead is
monotone — edge within 2 pts ahead (647 trades, 86%) +0.53; runway 2-4
(61) +1.49; runway 4-8 (17) +2.51; no edge ahead (25) -0.22. Supporting
same-direction gradients (non-FINDING): room-to-level 2-4 best (+0.73,
capture 45%); backstop 2-6 behind +0.76 (p=0.057); range-extension
trades worst (+0.37). Promotion correctly refused (top-cell n=17) ->
constructive strategy test T-SR05. Banked: trades_5w_struct.parquet.

## T-SR05 — THE RUNWAY SELECTOR AS A STRATEGY: 5W-RWY (2026-11-27)
Spec: Tests/D32_structsel/RWY_SPEC.md (frozen first; band [2,8] frozen,
selection channel disclosed). Controls exact (1541/1263; 422/+216.5;
750/+472.1). Admit a touch only when the nearest family edge ahead of
the would-be entry is 2.0-8.0 pts away.

| cell | trades | win | per-trade | pooled | by month | stop% | capture% |
|---|---|---|---|---|---|---|---|
| 5W full-RTH baseline | 750 | 47% | +0.63 | +472.1 | +195/+278 | 47% | 32% |
| RWY[2,8] FROZEN | 102 | 63% | +1.54 | +157.1 | +79/+78 | 31% | 45% |
| sensitivity [1.5,8]/[2,6]/[2,10]/[3,8] | 183/94/105/50 | 57-76% | +1.20/+1.53/+1.52/+2.03 | - | - | 37/32/32/18% | 43-56% |

ALL frozen lines PASS -> 5W-RWY REGISTERED TRAINING-ONLY, Tier-R.
Plateau confirmed (no knife-edge; per-trade rises monotonically with
required runway - a volume/quality dial, NOT to be optimized further per
F-20 discipline). This is the program's per-trade leader (+1.54, 2.4x
G2-4's line) and the first selection gate that ever worked - it is
mechanism-linked (capture needs a reachable target), where every
flow/calendar/grid gate failed (F-14, F-27). At one tick of round-trip
friction the edge is ~+1.29 - robust where +0.27-class strategies are
not. Caveats: band chosen after seeing T-SR04's gradient on these same
months; n=102; F-11 expects a per-trade haircut on fresh months.
