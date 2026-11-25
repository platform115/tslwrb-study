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
