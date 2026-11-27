# SYSTEMS_MATRIX — THE WIRING AUTHORITY
STATUS: LIVING | v1.0 | 2026-11-27 | This page is the single source
for how every trading system is composed. Legacy names stay canonical
everywhere (nothing renamed); formulas here are additive metadata.
Mechanically checked by scripts/taxonomy_audit.py (R-8 pass).

## TERMS (industry-standard; Tharp 1999, Kaufman, Davey 2014)
SETUP = conditions that must be true (structure exists, knowable).
ENTRY SIGNAL = the event that fires the order (cross / touch-break).
ENTRY TECHNIQUE = how the order goes in (breakout stop-order;
pullback-retest). FILTER = a rule that rejects signals (event filter,
structure filter, microstructure filter). TRADE MANAGEMENT PLAN =
stop, trailing stop + arm, profit capture, time exits. TRADING
SYSTEM = entry x filters x management plan. The word "Strategy" is
RETIRED as a component word - it survives only inside legacy aliases.

## REGISTER: ENTRIES (EN-)
| id | definition | used by |
|---|---|---|
| EN-01 | 4A-v2 edge-cross (SQZ W10/W30 + W20 bands), two techniques: breakout stop-order + pullback-retest X1.0 pb0.75; d=1.25, dedupe 300s, TTL 300s | G2-4, G2-7, G2-9 |
| EN-02 | 4A-v3 edge-cross: EN-01 with edge sources widened to GAP/SHD/REA (resolver) + 5m/15m WRB bodies + prior-day RTH H/L/C | G2-6, G2-8, G2-10, G2-11, G3-1, G3-2, G3-3, G3-4 |
| EN-03 | Multi-day-level touch-break: approach, touch (<=0.5), stop entry at L+0.75*d from touch+3, TTL 120s | Strategy 5, Strategy 5W, 5W-RWY |
| EN-04 | Family-edge touch-break: EN-03 with the touch universe = family edges (raw W20 band excluded - moving boundary) | S5-MF |
| EN-05 | 4A-v2 edge-cross, breakout-only (single-technique; historical, pre two-lane) | G2-3, G2-5 |
| EN-06 | 4A edge-cross (original band set; historical, pre v2) | G2-1, G2-2 |

## REGISTER: FILTERS (FL-)
| id | definition | kind |
|---|---|---|
| FL-WIN | news window: 5-45 min after a scheduled economic release | event filter |
| FL-QT | quiet market: > 45 min since the last scheduled release | event filter |
| FL-ALL | all RTH (no time filter) | event filter |
| FL-RWY | runway: admit only when the nearest family edge ahead of entry is 2.0-8.0 pts away (frozen T-SR05 band) | structure filter |
| FL-3S | 3s ACTIVE book read at the touch: churn3 >= T2 OR sweep_3 > 0 | microstructure filter |
| FL-CAD | cadence cap N=1 per news window (historical) | event filter |

## REGISTER: TRADE MANAGEMENT PLANS (MP-)
| id | alias | definition |
|---|---|---|
| MP-7 | M7 | stop -3.75, stall-60, cap-480, trail armed by a multi-day level <=8 ahead (arm = best-0.75, floor 0.5), exit peak-0.75 |
| MP-8 | M8 | MP-7 with arming targets widened to family edges >=2.0 ahead (structure-armed) |
| MP-9 | M9 | MP-7 with the arm replaced by a constant: armed once +1.5; exit peak-0.75 |
| MP-10 | M10 (the S5 exit organism) | stop L-1.25*d, level-capture (arm when peak within 1.0 of next level, exit peak-0.75), flow-fade (from 60s, 30s steps, trailing-30s OFI10 < 0), hard cap 900s |
RETIRED (kept in GLOSSARY, not re-registered): M0-M6 generations,
M12/M13/M15 rejected, M14a-d campaign outcomes.

## SYSTEMS
| system | formula | tier | status | headline (training unless noted) | judge |
|---|---|---|---|---|---|
| G2-1 | EN-06 x FL-WIN x MP-7 | P | TRAINING-ONLY | legacy engine; B5-passed 2024-11 | Q-3 pending |
| G2-2 | EN-06 x FL-WIN x MP-7 | P | TRAINING-ONLY | legacy engine | Q-3 pending |
| G2-3 | EN-05 x FL-WIN x MP-7 | P | DORMANT | OOS +144.4 but claim failed; dominated | kept on record |
| G2-4 | EN-01 x FL-WIN x MP-7 | P | VALIDATED | OOS PASS +158.1 - the D-4 port target | done (extend at D-8) |
| G2-5 | EN-05 x FL-WIN x FL-CAD x MP-7 | P | DORMANT | OOS +38.9; dominated | kept on record |
| G2-6 | EN-02 x FL-WIN x MP-7 | P | TRAINING-ONLY | 6252/+1659.0, catch 59/62 | D-8 stage 1 |
| G2-7 | EN-01 x FL-WIN x MP-9 | P | TRAINING-ONLY | 2370/+858.1, twin +173.4 | D-8 stage 1 |
| G2-8 | EN-02 x FL-WIN x MP-8 | P | TRAINING-ONLY | 8383/+2670.0, twin +165.2 | D-8 stage 1 |
| G2-9 | EN-01 x FL-WIN x MP-8 | P | TRAINING-ONLY | 2400/+824.8, twin +143.6 | D-8 stage 1 |
| G2-10 | EN-02 x FL-WIN x MP-9 | P | TRAINING-ONLY | 8153/+2644.0, twin +139.5 | D-8 stage 1 |
| G2-11 | EN-02 x FL-WIN x FL-RWY x MP-7 | P | TRAINING-ONLY | 1212/+627.2 at +0.52 | D-8 stage 1 |
| G3-1 | EN-02 x FL-QT x MP-7 | P | TRAINING-ONLY | 19008/+3689.4, catch 150/151 | D-8 stage 1 |
| G3-2 | EN-02 x FL-QT x MP-9 | P | TRAINING-ONLY | 23941/+5727.8 at +0.24 | D-8 stage 1 |
| G3-3 | EN-02 x FL-QT x FL-RWY x MP-9 | P | TRAINING-ONLY | 3843/+1944.4 at +0.51 | D-8 stage 1 |
| G3-4 | EN-02 x FL-QT x FL-RWY x MP-7 | P | TRAINING-ONLY | 3159/+1186.4 at +0.38 | D-8 stage 1 |
| Strategy 5 | EN-03 x FL-ALL x FL-3S x MP-10 | R | TRAINING-ONLY | 198/+119.6 at +0.60 (covered-touch scope) | D-8 stage 2 |
| Strategy 5W | EN-03 x FL-ALL x MP-10 | R | TRAINING-ONLY | covered 422/+216.5; full-RTH 750/+472.1 at +0.63 | D-8 stage 2 |
| 5W-RWY | EN-03 x FL-ALL x FL-RWY x MP-10 | R | TRAINING-ONLY | 102/+157.1 at +1.54 - per-trade leader | D-8 stage 2 |
| S5-MF | EN-04 x FL-ALL x MP-10 | R | TRAINING-ONLY | 4369/+1985.6 at +0.45 | D-8 stage 2 |
PRE-SPLIT LEGACY (no formulas; predate the component split): the
Strategy 1 / 2A / 3A-3D / 4A generation - see GLOSSARY.

## IMPLEMENTATION ANCHORS (component -> canonical code + proof)
The LINEAGE CONVENTION: every runner COPIES its machinery from the
canonical source named here (declared in its docstring) and must
reproduce that source's certified numbers (R-9) before any look -
the control number, not the filename, is the proof of identity.
| id | canonical source (file :: anchor) | certified proof |
|---|---|---|
| EN-01 | Tests/D11_unmatched/g26_round.py :: cand_{tag}_ | reproduces 757/+325.1 and 760/+158.1 (T-EN115 control) |
| EN-02 | Tests/D11_unmatched/g26_round.py :: tail_edges | T-EN115; quiet-span variant: Tests/D5_quiet/g31_round.py (engine set-equal control) |
| EN-03 | Tests/D30_s5mf/s5mf_round.py :: BUILDER A | reproduces T-BK03 1541 approaches / 1263 touches key-for-key |
| EN-04 | Tests/D30_s5mf/s5mf_round.py :: BUILDER B | mf_touch_moments.csv (45,454) banked |
| EN-05 | historical - see T-EN106..110 registry rows | fill-time corrections certified at T-EN108 |
| EN-06 | historical - old-engine era, Q-3 pending | B5 quarantine records |
| FL-WIN | Tests/D11_unmatched/g26_round.py :: evm window loop | T-EN115 |
| FL-QT | Tests/D5_quiet/g31_round.py :: day_spans | T-EN116 (engine control + G2-6 sim control) |
| FL-ALL | no code (absence of a time filter) | - |
| FL-RWY | Tests/D32_structsel/rwy_round.py :: runway | T-SR05 controls; volume-line form: Tests/D5_quiet/g3rwy_round.py :: run_cell2 |
| FL-3S | Tests/D25_surgical/s1_round.py :: churn3 | T-SR01 (universe reconciled 693) |
| FL-CAD | historical - cadence round (T-EN110) | G2-5 record |
| MP-7 | Tests/P5_trade_management/m15_round.py :: def m7tag | the certified pair numbers, reproduced by every copy |
| MP-8 | Tests/D29_m8/m8g2_round.py :: run_cell_m8 dmin | T-MG28 controls |
| MP-9 | Tests/D29_m8/m8ab_round.py :: def m7_var | T-MG29 control + the G2-7/G2-10 cells |
| MP-10 | Tests/D25_surgical/s1_round.py :: def sim | 422/+216.5 (S1-ANY), reproduced by every copy since |
