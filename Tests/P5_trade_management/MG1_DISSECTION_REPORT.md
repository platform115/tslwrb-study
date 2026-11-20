# MG-1 — HIS MANAGEMENT vs M1, SAME 92 ENTRIES (T-MG01)
> Status: AWAITING REVIEW. Per-unit accounting; fill = his actual entry
> price (note: T-IM05 used per-second-mid fills, hence its lower M1 total).

| metric | HIS | M1 |
|---|---|---|
| total per-unit | +620.0 | +200.0 |
| win rate | 82% | 75% |
| avg win | +8.56 | +3.18 |
| avg loss | -1.31 | -0.85 |
| median holding | 183 s | 50 s |
| his winners' holding | 191 s | 54 s |
| capture of own-window MFE | 83% | 55% |
| MFE available to own exit | 5.12 | 2.62 |
| exits within 1 pt of an edge | 77% | 83% (edges dense - not discriminating) |
M1 exit reasons: stall 89/92. Adds/scale-outs in October: 0/92 - he
traded single-shot this month, so per-unit = his actual results.

## The mechanical finding
M1's stall clock (S=30) exits in ~50 seconds; he tolerates ~3x longer
stalls, which buys a 2x larger available move (5.12 vs 2.62) AND he
captures a larger share of it (83% vs 55%). His avg win is 2.7x M1's
while his avg loss grows only 1.5x. THE GAP IS PATIENCE STRUCTURED BY
SOMETHING - and the something is what MG-2 tests: is it just a longer
clock, or stall-tolerance conditioned on structure?

## MG-2 PRE-REGISTRATION (ranges, from this evidence; M0/M1 untouched)
On HIS entries (and later ER-SIG fires):
  P-grid: stall S in {30, 60, 90, 120, 180} s (RTH; ETH scaled 3x as in M1)
  L-1: no stall-exit while beyond the trigger edge AND no opposing
       structure interaction since entry (structure-conditioned patience)
  L-2: target = next structure edge in profit direction (exit there),
       stop beyond the trigger edge by {1, 2} pts
  L-3: trail anchored to the most recent same-direction swing level
  Baselines: M0, M1 (frozen). Metric: the standard table + capture ratio.
