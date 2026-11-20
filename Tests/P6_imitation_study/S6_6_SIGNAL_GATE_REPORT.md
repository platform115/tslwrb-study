# S6.6 — C3 SIGNAL-GATE GRID (T-IM34)
> Status: AWAITING REVIEW. Script: p6_27_s6_6_signal_gate.py.

| cell | catch | fires/day | fires per catch |
|---|---|---|---|
| base & KME (reference) | 36% | 40.7 | 28 |
| base & KME & signal | 25% | 11.0 | 11 |
| **base & signal (C3)** | **38%** | **18.6** | **12** |

## Reading
The score>=6 same-direction signal gate is the strongest conjunct found:
87 -> 12 fires per catch (7x concentration vs bare interaction) while
catch RISES slightly (36 -> 38%). At 18.6 alerts/day vs his ~4 trades and
1.5 catches/day, this is at plausible human-attention scale.

SELECTOR v1 (the first deliverable of the selection goal):
  REA-edge interaction (15 min, direction-aligned)
  AND a same-direction score>=6 signal completed within 5 min
  -> catches 38% of his training-month entries at 18.6 fires/day;
  entry price = edge + displacement (REA median +3.0 pts past the level).
Not yet run: base & (KME OR signal) - it was NOT in the registered cells;
flagged as the natural next cell but post-hoc. User decides.

## Registered-cell count (multiplicity ledger)
Round 1: 5 cells (T-IM33). Round 2: 3 cells (this). All declared before
their runs; no cell added after results within a round.
