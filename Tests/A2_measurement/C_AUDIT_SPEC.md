# C AUDIT SPEC — SQUEEZE-DETECTOR COVERAGE (pre-registered)
STATUS: FROZEN | 2026-11-26 | Registry: T-IM53
Target: the 9 G2 trades where NO squeeze-band edge existed within 5 pts
at his entry (A5 decomposition, cause "edge_absent"). The shipped
generator uses the certified C2 cells (W=15 contraction / W=30 tight
range, q=0.67).
## QUESTIONS (fixed before the run)
1. For each of the 9: does ANY parameter cell of the SAME certified
   family (W in {10, 15, 20, 30, 45} x q in {0.5, 0.67, 0.8}) produce a
   qualifying band with an edge within 5 pts in the prior 15 minutes?
2. COST of any covering cell: its ambient qualification rate (share of
   RTH minutes carrying an active band) vs the shipped cells - more
   coverage is only worth having if it does not flood the trigger.
## OUTPUT
Per-trade coverage table + per-cell cost table + recommendation. ANY
adoption = a Strategy 4 revision requiring the full B2->B4 re-run and
fresh validation; that decision is J's, not this audit's.

## C2 PASS (pre-registered 2026-11-26; J: proximity is not the currency)
For candidate cells W20 q{0.5, 0.8}, inside the 5-45min post-release RTH
windows, both training months:
(a) TRIGGER SIMULATION on the 9 missed trades: per-second cross of the
    candidate band edges, stop fill at edge+1.25 (order TTL 300s),
    direction-matched within 5 min of his entry = CAUGHT; M3A P&L on
    each converted fill reported.
(b) INCREMENTAL COST: full per-second scan of the windows with the
    candidate bands alone - fires/day, and TRADED extras expectancy
    under M3A (the same yardstick as every adopted rule).
(c) UNION of caught trades across cells.
(d) CAUSE for each still-uncovered trade: nearest structure of any
    certified family at entry + whether the A5 fade anatomy (negative
    mv15, high dwell) fits - routing them to the G3/book lens if so.
Adoption bar (pre-stated): a cell earns the revision batch only if it
converts >= 2 of the 9 into caught fills AND its incremental extras are
non-negative under M3A.
