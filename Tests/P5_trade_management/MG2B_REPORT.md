# MG-2b — REFINEMENT CELL RESULTS (T-MG03)
> Status: AWAITING REVIEW. The one refinement round is now spent.

| plan | Win rate | Avg win / loss | Total |
|---|---|---|---|
| HIS ACTUAL (reference) | 82% | +8.56 / -1.31 | +620.0 |
| plain S=90 (reference, from MG-2) | 66% | +4.71 / -1.45 | +242.5 |
| L-1b structure breakeven | 41% | +7.94 / -2.69 | +156.5 |
| L-1c + reactivated stall | 65% | +4.20 / -1.27 | +211.1 |
| P+L S=90 + breakeven | 65% | +4.26 / -1.29 | +214.5 |

## Finding
All three cells LOSE to plain S=90 patience. The breakeven-at-the-edge
rule costs money on these entries: pulling back to the trigger edge is a
normal part of the path to his large wins, and a stop there surrenders
them (L-1c and P+L both land ~30 points below plain S=90). L-1b confirms
the MG-2 lesson from the other side: its win size nears his (+7.94) but
the win rate stays collapsed. Structure-anchored exits do not help on
these entries; TIME-based patience does.

## Where the management phase stands
Best mechanical rule found: M1 with the stall clock at S=90 (270 s on
overnight bars), every other dial unchanged. +242.5 vs M1's +200.0 on his
October entries (+21%). The remaining gap to his +620 is not closed by
any tested exit rule - his hold/fold choice inside the trade uses
information none of these rules have. That gap is recorded, not explained.

## MG-3 (needs approval)
1. Validate S=90 vs M1 on HIS entries in 2022-02 and 2021-09 (zero
   refitting).
2. Score S=90 vs M1 under the bounded-search entry rule ER-SIG (the
   deferred refinement of that program).
3. If validation holds, freeze as M2 (name, spec, charter entry);
   M0/M1 remain unchanged.
