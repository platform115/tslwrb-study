# GLOSSARY + COMBINABLE-COMPONENT REGISTER (2026-11-20)

## 1. ID PREFIXES (test registry, Tests/test_registry_rows.tsv)
T-EN##  entry-era tests (P4). Landmarks: T-EN99 = the thrust lookahead
        discovery; T-EN100 = honest baselines; T-EN101 = truncation harness.
T-EX##  exit/management research tests (P5, M0->M1 era). T-EX11 = stall
        derivation.
T-IM##  imitation-study tests (P6). T-IM05 = his entries under M0/M1;
        T-IM14..39 = structure program + selectors (this window).
T-BS##  bounded-search tests (P7). T-BS01 = S-A/B/C first backtest.
T-MG##  management-design tests (M2 phase). T-MG01..07 = MG-1..MG-3d.
(01..07 folders under Tests/ are the oldest candidate studies, pre-dating
the T- prefix scheme.)

## 2. PHASE / STEP NAMES
P0..P7   test phase folders: P0 audit, P4 entries, P5 management,
         P6 imitation, P7 bounded search (01-07 = older studies).
S0..S6   structure-program steps (P6): timeframes, parser, definitions,
         generators, lifetimes, resolver, entries-vs-structures.
G1..G4   structure generators: hidden gaps, shadows, reaction levels,
         compression ranges.
MG-1..MG-3d  management-design steps (the M2 phase). Not plans.
C2-S1..S3    imitation cycle-2 steps (drift remainder).

## 3. NAMED OBJECTS
M0 / M1 / M2   trade-management PLANS. M0 frozen incumbent; M1 adopted
               working plan; M2 not yet designed/frozen.
ER-SIG / ER-WIDE  frozen imitation entry selectors (formerly V1 / U).
S-A / S-B / S-C   bounded-search strategy candidates (entry rules + M1).
SEL-A'..SEL-F'    S6.3 event selectors (historical; superseded by ER-*).
D1 / D2        Long-Shadow definitions (ratio rule / prior-3 analogy).
C1 / C2 / C3   conjunction conditions: KME window / volatility spike
               (failed) / score>=6 signal.
L-1..L-3, L-1b/c, P+L   MG-2/2b management candidates (all failed).
Q              a management dial set {early, stop, time_bars, S}.
Strategy 1     earlier-era entry strategy (pre-adaptive era).
Strategy 2A/2B VOID - the lookahead-era strategies; never reusable.

## 4. BACKTEST COMPONENT REGISTER (what can be combined)
### Entry rules (X axis)
| id | status | note |
|---|---|---|
| ER-SIG | frozen, validated brackets | fires = entries; 13-19/day |
| ER-WIDE | frozen, validated brackets | 34-50/day |
| S-A (raw edge-break) | tested, negligible P&L under M1 | 300/day |
| S-B, S-C | tested, REJECTED under M1 | re-test only with new mgmt |
| HIS entries | benchmark replay | the comparison row |
| Strategy 1 | UNVERIFIED vs the T-EN99 audit scope | AUDIT BEFORE ANY USE |
| Strategy 2A/2B | VOID | never |
### Management plans (Y axis)
| id | status | note |
|---|---|---|
| M0 | frozen | baseline only |
| M1 | adopted working plan | default |
| M1-S90 | recorded variant, NOT frozen | best pooled, high-vol fragile |
| failed MG candidates | documented | not for reuse |
### Slices (Z axis)
RTH / ETH | KME-window vs not | volatility terciles | month-by-month.
### Rules of combination
- every cell pre-registered before running; run once
- entry gate must be truncation-harness-passed
- HIS same-period row in every table
- results set per BACKLOG.md 3b
