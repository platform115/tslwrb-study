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
There are exactly EIGHT. No R-9 without J's sign-off.
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

## TRACK STEPS (MASTER_PROGRAM)
A1 coverage matrix | A2 measurement table | A3 grouping | A4 ranking
B0 pick target | B1 anatomy | B2 entry rule | B3 paired management | B4 unit test | B5 quarantined validation

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
| G2-3 | Strategy 4A-v2 d1.25 x M7 | TRAINING-VALIDATED ONLY - awaits the purchased months (2023-05, 2024-05) |
