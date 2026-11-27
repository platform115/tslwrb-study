# GLOSSARY + COMBINABLE-COMPONENT REGISTER (2026-11-20, naming v2)
> CANONICAL NAMING (user 2026-11-20): entries are Strategy N (letters for
> variants in one family); management plans are M-N (letters for variants).
> Old names remain as aliases because registry history uses them.

## 1. ENTRY STRATEGIES (X axis) - canonical
| canonical | was | definition | status |
|---|---|---|---|
| Strategy 1 | Strategy 1 | score>=6 at a 1m WRB completion; direction = prior 5-min move; stop-fill at the signal bar's extreme; pt-ladder exits | CERTIFIED (T-EN102); record: +0.84/trade in-sample, +0.17/trade pooled OOS |
| Strategy 2A / 2B | same | adaptive-era rules | VOID (lookahead) - never reusable |
| Strategy 3A | S-A | reaction-edge interaction (break/reject, 15 min, direction = break side), no gate | tested; ~zero per trade under M1 |
| Strategy 3B | S-B | 3A + KME-window gate (45 min) | rejected under M1; retest only with new management |
| Strategy 3C | ER-SIG / S-C | 3A + same-direction score>=6 signal (5 min) | frozen; catch 38% train / 19-26% validation; 13-19 fires/day; entry at edge + displacement |
| Strategy 3D | ER-WIDE | 3A + (KME window OR signal) | frozen; 49% / 32-44%; 34-50 fires/day |
| HIS | - | his actual entries (replay) | benchmark row in every table |
(The whole Strategy 3 family shares one trigger - the reaction-edge
interaction - and differs only in the confirmation gate.)

## 2. MANAGEMENT PLANS (Y axis) - canonical
| canonical | was | definition | status |
|---|---|---|---|
| M0 | M0 | fast-fail 1.5 + stop 4 + time 27 + session (no stall) | frozen baseline |
| M1 | M1 | M0 dials + stall clock S=30 RTH / 90 ETH, fast-fail off | adopted working plan |
| M1A | "M1-S90" | M1 with stall S=90 RTH / 270 ETH | recorded variant, NOT frozen (best pooled +12%, high-vol fragile) |
| M2 | - | reserved for the next plan that passes a freeze criterion | does not exist yet |
(Failed MG candidates - breakeven rules, gap adapters, R-share stops -
are documented in T-MG02..07 and are not components.)

## 3. SLICES (Z axis)
RTH / ETH | KME-window vs not | volatility terciles | month-by-month.

## 4. COMBINATION RULES
- every backtest cell pre-registered before running; run once
- entry gates truncation-harness-passed first
- HIS same-period row in every table; results set per BACKLOG.md 3b

## 5. ID PREFIXES (registry, unchanged - historical)
T-EN## entry-era tests (T-EN99 lookahead discovery; T-EN101 harness)
T-EX## exit/management research (T-EX11 stall derivation)
T-IM## imitation study | T-BS## bounded search | T-MG## management design
P0..P7 phase folders | S0..S6 structure steps | G1..G4 generators
MG-1..MG-3d management-design steps | C2-S1..S3 imitation cycle-2 steps
D1/D2 shadow definitions | C1/C2/C3 conjunction conditions | Q dial set
ALIASES retired by naming v2: ER-SIG -> Strategy 3C, ER-WIDE -> 3D,
S-A/B/C -> 3A/3B/3C, M1-S90 -> M1A, V1/U -> 3C/3D (oldest).

## MASTER PROGRAM names (added 2026-11-24, same-commit rule R-3)
Track A = the map (breadth: measurement table + taxonomy + ranking).
Track B = the build (depth: one target to reliable; group mode or
single-trade case-study mode). A1..A4, B0..B5 = their steps.
R-1..R-7 = the standing rules in MASTER_PROGRAM.md.

## STANDING RULES (R-series) — MASTER_PROGRAM.md is the full text
There are exactly TWELVE. No R-13 without J's sign-off.
| id | plain meaning |
|---|---|
| R-1 | Lookahead prevention: the truncation harness applies to every script, mechanically |
| R-2 | Pre-registration: hypotheses and criteria written before any run |
| R-3 | Uncertainty is flagged to J, never resolved silently |
| R-4 | Plain language in everything J reads; numbers are provisional flag-lines, never silent gates |
| R-5 | Naming: GLOSSARY.md is the authority; new names land in the same commit |
| R-6 | Docs stay current: status headers, change logs, the living docs updated the same turn |
| R-7 | Results display: every entry test shown per RESULTS_DISPLAY_STANDARD.md |
| R-8 | Completeness pass: deliverables are diffed against ASSETS.md and the program doc mechanically, never from memory |
| R-9 | Prove the tool: engines reproduce certified controls exactly before any report is read; management verdicts are mechanism-primary |
| R-10 | Remainders get anatomies before being called ceilings |
| R-11 | Months-spend gate: every spec declares which months it spends and why no hold-out, before freezing; J gates the spend |
| R-12 | Findings sweep: every spec lists each standing F-finding as APPLIED or NOT-APPLICABLE before freezing; retroactive misses trigger follow-up rounds |

## TRACK STEPS (MASTER_PROGRAM)
A1 coverage matrix | A2 measurement table | A3 grouping | A4 ranking
B0 pick target | B1 anatomy | B2 entry rule | B3 paired management | B4 unit test | B5 quarantined validation

## STRATEGY STATUS VOCABULARY (closed list - no other status words)
Every strategy is exactly one of: TRAINING-ONLY (no out-of-sample test
yet) | VALIDATED (passed its frozen out-of-sample lines) | DORMANT
(OOS-profitable but its claim failed or it is dominated; kept, not
deployed) | DEAD (failed outright; never revisited).
Current: G2-1 TRAINING-ONLY (B5-passed on 2024-11 under old engine) |
G2-2 TRAINING-ONLY | G2-3 DORMANT (earns OOS; replication claim
failed; dominated by G2-4) | G2-4 VALIDATED | G2-5 DORMANT.

## DESIGNATION DISCIPLINE (added 2026-11-24, J: "these designations sprawl too easily")
1. The COMPLETE list of designation families is this file's table of
   contents. A designation not findable here is a naming bug - report it.
2. No new family (new prefix or numbering scheme) without J's approval.
3. First use of any designation in anything written for J carries its
   plain meaning inline, every time.

## TRACK B NAMES (added 2026-11-25, with B4)
| name | plain meaning |
|---|---|
| Strategy 4 | the G2 entry rule: squeeze-band break inside the 5-45 min post-release window, stop order at edge + displacement |
| Strategy 4A | unfiltered trigger |
| Strategy 4B | trigger + movement-and-flow filter |
| d1.25 / d2.50 | the displacement parameter (pts past the band edge) |
| M3 (family) | G2-speed management, built from his G2 exit anatomy (B3) |
| M3A | stall 60s + stop 3.75 + time 480s |
| M3B | stall 90s + stop 3.75 + time 480s |
| M3C | fail-fast 1.5 in first 30s + target 4.5 + stop 3.75 + time 480s |

## VALIDATED PAIRS (compact aliases, J-approved)
| alias | full designation | status |
| F-n | STANDING FINDING n (MASTER_PROGRAM findings register; append-only; must shape future strategy design) | family registered 2026-11-27 |
| D-n | ROADMAP direction item n (MASTER_PROGRAM roadmap table; append-only register of open work directions) | family registered 2026-11-26 |
| Q-n | OPEN DECISION n addressed to J (same roadmap block) | family registered 2026-11-26 |
|---|---|---|
| G2-1 | Strategy 4A d1.25 x M3A (squeeze-break entry, 5-45min post-release, unfiltered, displacement 1.25; stall-60 management) | VALIDATED (T-BS05 training, T-BS06 quarantine PASS) |
Convention: alias used alongside the long form, never replacing it in
specs. Future validated pairs: G<group>-<n>.

## M4 / M5 MANAGEMENT CANDIDATES (named per J, 2026-11-25; status shown)
| name | plain meaning | status |
|---|---|---|
| M4A | ratchet stall: patience budget grows with each k-pt new extreme | tested (T-MG09), not adopted |
| M4B | tiered stall: 60s/120s/longer by progress tier | tested (T-MG09), not adopted |
| M4C | event-keyed: exit on opposite-direction 1m WRB completion + safety stall | tested (T-MG09/10), not adopted; safety-180 on the REVISIT list (extras +59.5 beat G2-1's +47.0; lost on his-like fills) |
| M5A | accelerating trail (Wilder-SAR-inspired): trail tightens with each new extreme | in test (T-MG11) |
| M5B | speed gate: fast move -> spike-capture; slow -> M3A patience | in test (T-MG11) |

| M7 | level-snap management: M3A backstops (stall-60, stop 3.75, time 480) + spike-capture arming when price reaches a COMPUTED multi-day level within 8 pts of entry (MDL v3 detector) | ADOPTED on training (T-MG14) |
| G2-2 | Strategy 4A d1.25 x M7 | TRAINING-VALIDATED ONLY - awaits fresh pre-committed validation month |

| Strategy 4A-v2 | 4A with the band set widened: squeeze cells W10/W30 q0.67 PLUS W20 q0.8, one deduped trigger stream | adopted on training (T-EN104) |
| G2-3 | Strategy 4A-v2 d1.25 x M7 | TRAINING-VALIDATED ONLY - awaits the purchased months (2023-05, 2024-05). Corrected numbers under the fill-time engine (standard since T-EN108): +276.1 / 607 / catch 47 / extras +185.6. OUT-OF-SAMPLE (T-VL01): +144.4 (+137.6/+6.8), catch 50%; RE-REGISTERED AS TRACK-2 SYSTEM (J) - standalone earner, not a replication claim |
| G2-4 | Strategy 4A-v2 d1.25 two-lane (first-break + retest X1.0 pb0.75) x M7 | OUT-OF-SAMPLE PASS (T-VL02): +158.1 (+118.8/+39.4), all mode-2 lines - the program's first validated track-2 strategy |
| Strategy 4A-v3 | 4A-v2 with trigger edge-sources widened from {SQZ, W20} to the full price-computable vocabulary: + GAP, SHD, REA (resolver), 5m/15m WRB body edges, prior-day RTH H/L/C. Dedupe key unchanged - stacked structures dedupe together | adopted on training (T-EN115) |
| G2-6 | Strategy 4A-v3 d1.25 two-lane x M7 | TRAINING-ONLY, Tier-P (T-EN115, all six months, R-9 control exact): 6252/+1659.0, per-trade +0.27 = G2-4's, catch 59/62 (the F-23 ceiling reached), extras +1556.8, all months positive, no toxic family. Families chosen after seeing the unmatched entries, so ALL six months are training; judge = D-8 purchase |
| G2-7 | Strategy 4A-v2 d1.25 two-lane x M8 | TRAINING-ONLY, Tier-P (T-MG28, J-approved 2026-11-27): 2400/+824.8 on six months, per-trade +0.34, twin +143.6 vs G2-4xM7 (5/6 months). Judge = D-8 stage 1 |
| G2-8 | Strategy 4A-v3 d1.25 two-lane x M8 | TRAINING-ONLY, Tier-P (T-MG28, J-approved 2026-11-27): 8383/+2670.0 on six months, per-trade +0.32, twin +165.2 (4/6). Judge = D-8 stage 1 |
| M12 | M7 + imb10 gate at the stall exit | TESTED-REJECTED (T-MG21: mechanism-negative) |
| M13 | M7 + book-conditioned extension of the 480s cap | TESTED-STRUCTURALLY-EMPTY (T-MG22: 1/607 trades reach the cap) |
| Strategy 5 (alias S-1) | Surgical level-break: touch -> 3s ACTIVE book read -> break entry at L+0.75, stop L-1.25, flow-fade/level-capture exits. Named into the existing Strategy-N family (J, 2026-11-27: no new families without need) | TRAINING-ONLY, Tier-R (T-SR01: +119.6/198, +0.60/trade, worst -2.00; in-sample; judge = future depth months) |
| Strategy 5W (alias S1-ANY) | Strategy 5 with the 3s signal ablated - enters every touch | TRAINING-ONLY, Tier-R. Two measurements on record: covered touches (T-SR01: 422/+216.5, +0.51) and FULL RTH (T-SR02/03: 750/+472.1, +0.63 - the program's per-trade leader; the coverage restriction was hiding quality). T-SR03 anatomy: the +0.63 is flat across all flow/calendar/level lenses (null); upgrade path = Part B 3s book read. Trade tables banked in Tests/D30_s5mf/ |
| S5-MF | Strategy 5 with the touch universe widened from multi-day density levels to family edges (resolver SQZ/GAP/SHD/REA + WRB bodies + prior-day H/L/C; raw W20 band excluded - moving boundary). Part A = ANY arm only | TRAINING-ONLY, Tier-R (T-SR02: 4369/+1985.6, +0.45/trade, both months positive, worst -2.00; volume not quality - LVL-ANY full-RTH leads per-trade at +0.63). Part B (3s ACTIVE arm) awaits device extraction |
| 5W-RWY | Strategy 5W full-RTH gated by the RUNWAY selector: admit a touch only when the nearest family edge ahead of the would-be entry (F-23/24 vocabulary) is 2.0-8.0 pts away - room to run to a real target | TRAINING-ONLY, Tier-R (T-SR05: 102/+157.1, +1.54/trade, 63% win, stops 31%, months +79/+78; plateau across bands; the program's per-trade leader). Selection channel disclosed; judge = D-8 stage 2 |
| M8 | M7 with spike-capture targets widened to family edges >=2.0 ahead | SUPERSEDED-PENDING-J (T-MG29, F-33): its entire gain is reproduced by a fixed trail-arm (proposed M9) - the vocabulary was incidental; kept on record |
| M9 | Trail-arm management: the trail arms once the trade reaches +1.5 (A=1.5, mid of the tested 1.5-2.0 plateau, range-picked on training - disclosed); exit peak-0.75; stop -3.75, stall-60, cap-480 unchanged from M7. No targets, no resolver - one constant, Pine-trivial | MINTED (J, 2026-11-27; T-MG29, F-33): twin +173.4 vs M7 on G2-4, 5/6 months. TRAINING-ONLY; judge = D-8 |
| Tier-P / Tier-R | Deployment tiers: Tier-P = Pine-portable (price + public calendar only; G2-4 x M7). Tier-R = Python-runner + depth feed (Rithmic L2 live / Databento MBP-10 historical; Strategy 5 line, F-17/F-21 machinery). Book dependencies never enter Tier-P | families registered 2026-11-27 |
| G2-5 | G2-3 with cadence cap N=1 per news window | DORMANT (J, 2026-11-26): OOS-profitable (+38.9, both months positive, lowest maxDD) but its quality claim failed (+0.39 < +0.60) and it is dominated by G2-4 - not deployed, kept on record |
