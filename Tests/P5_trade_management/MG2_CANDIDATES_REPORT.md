# MG-2 — CANDIDATE RESULTS ON HIS 92 ENTRIES (T-MG02)
> Status: AWAITING REVIEW. Baselines frozen, run not modified. 13 episodes
> used the fallback trigger edge (no interacted REA edge at entry).

| plan | Win rate | Avg win / loss | Total | Max below start |
|---|---|---|---|---|
| HIS ACTUAL | 82% | +8.56 / -1.31 | **+620.0** | 0 |
| M0 (no stall; single leg, reversal omitted) | 30% | +8.96 / -3.02 | +57.6 | 4.1 |
| M1 (S=30) | 75% | +3.18 / -0.85 | +200.0 | 0 |
| P S=60 | 74% | +3.90 / -1.23 | +235.4 | 0 |
| P S=90 | 66% | +4.71 / -1.45 | +242.5 | 0 |
| P S=120 | 65% | +4.78 / -1.55 | +236.9 | 0 |
| P S=180 | 67% | +5.00 / -2.08 | +247.8 | 0 |
| L-1 conditional patience | 38% | +8.52 / -2.41 | +160.5 | 3.9 |
| L-2a edge target, stop edge-1 | 79% | +3.58 / -3.16 | +201.0 | 0 |
| L-2b edge target, stop edge-2 | 85% | +3.58 / -3.61 | +229.0 | 0 |
| L-3 swing trail | 45% | +6.71 / -2.93 | +126.0 | 2.5 |

## Reading
1. PATIENCE PLATEAU: S in {60..180} earns +235..+248 vs M1's +200 - a
   flat ~20% improvement across the whole range (a plateau, not a spike -
   robust, not fitted). Confirms MG-1: M1's 30 s clock is too impatient
   for HIS class of entries.
2. L-1's failure is INFORMATIVE: its avg win (+8.52) matches HIS (+8.56)
   exactly - unconditional hold-while-beyond-edge captures his WIN SIZE -
   but the win rate collapses to 38% because winners round-trip to losses.
   He gets his win size AND an 82% win rate; no candidate gets both.
3. Edge targets (L-2b, 85% win) buy win rate by capping winners - M1-like
   economics with structure dressing. Swing trail is the weakest.

## MG-2b PROPOSAL (one evidence-drawn refinement, pre-registered now)
Fix L-1's round-trip failure, keeping its win size:
  L-1b: as L-1, but once price has been beyond the trigger edge by >= 1
        pt, the stop moves TO the edge (structure breakeven).
  L-1c: as L-1b, plus the stall clock REACTIVATES (S=90) once beyond the
        edge - patience with a giveback cap.
  P+L : S=90 plain, plus the L-1b breakeven rule (no stall suppression).
Three cells, no further grid. Then MG-3 (freeze best as M2, validate).
