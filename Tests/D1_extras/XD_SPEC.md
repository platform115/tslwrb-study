# XD_SPEC — D-1 EXTRAS DECOMPOSITION: WHERE OUR MONEY COMES FROM (T-XD01)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 pre-registration
Trigger: J aimed D-1 (roadmap -> IN PROGRESS this commit). Constraint
(J): ONLY live-computable features - nothing from his feed; the
near-his tag appears as a descriptive column only, never tested.
STUDY ONLY: no filter is built; findings become inputs to D-2/D-3
specs, which J reviews first.

## POPULATION
All G2-4 trades on the 4 deep months (2022-02, 2025-10, 2023-05,
2024-05; the OOS months used as data for NEW work per
VALIDATION_PLAN's spent-per-claim rule). G2-4's validation verdict is
not re-judged here.

## R-9 CONTROL (abort on fail, before any decomposition number)
The trade generator must reproduce exactly:
- training pair: 757 trades, +325.1 (+137.6/+187.5)
- validation pair: 760 trades, +158.1 (+118.8/+39.4)

## DEFINITIONS (frozen)
- EARNERS = the top quartile of trades by P&L, pooled; everything
  else = REST. (Win/loss split also reported, not tested.)
- Direction consistency = the earner-vs-rest median difference has
  the same sign in >= 3 of 4 months.

## ANALYSES
1. CONCENTRATION: share of pooled net from the top 10% / 25% of
   trades, per month and pooled.
2. ENTRY-TIME FEATURES, 6 families, ~32 features, all computable at
   the entry second on live data:
   F1 entry mechanics: lane; edge source (resolver/band); band
      width; edge distance from release price; lane-2 pre-entry
      excursion; cross-to-fill seconds; signal index in window;
      our trades already taken today
   F2 news context: tier20; tier45; mins since release; first-5-min
      reaction |move|, range, volume; release hour; day of week
   F3 levels: room ahead to nearest level; level-within-8; levels
      within 10; room behind; mins since RTH open
   F4 flow/book at entry (top-of-book only, comparable all 4
      months): 30s and 120s signed aggressor imbalance; 30s volume;
      top imbalance; own-side size; broken-side size
   F5 path before entry: 60s and 300s signed momentum; distance
      from release price; inside prior day range; distance to
      nearest prior-day edge
   F6 regime: day range-so-far vs 14-session median full-day range;
      |1-min change| sum over the last 30 min
   Test: Mann-Whitney earners vs rest per feature; Benjamini-
   Hochberg FDR q=0.10 WITHIN each family; |rho|>0.9 pairs reported
   as one. FINDING = BH-pass AND >= 3/4 month consistency;
   suggestive = p<=0.05 without both; else null.
3. ANATOMY (path features, labeled NOT usable for selection): M7
   exit-type attribution (stop / spike-capture / stall / time-cap)
   with count and net share, earners vs rest; MFE/MAE medians.
4. Every table shows the 4 months separately. Distributions, never
   bare means, for any conditional claim.

## OUTCOME LINES
FINDINGs -> listed as candidate inputs for the D-2/D-3 specs (J
gates). No adoption, no parameter, no filter in this round.
Registry: T-XD01 (family: extras-decomposition).
