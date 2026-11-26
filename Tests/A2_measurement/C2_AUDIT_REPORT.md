# C2 AUDIT — TRIGGER-LEVEL COVERAGE (T-IM54)
STATUS: CLOSED | 2026-11-26 | Spec: C2 addendum (committed first)

Missed trades: 9.

## (a)+(b) TRIGGER SIMULATION + TRADED INCREMENTAL COST (M3A)
| cell | incr. fills | fills/day | of the 9 caught | caught P&L | extra fills | extras net | extras win |
|---|---|---|---|---|---|---|---|
| W20 q0.5 | 460 | 10.5 | 3 | +3.4 | 457 | -107.1 | 36% |
| W20 q0.8 | 595 | 13.5 | 5 | -26.5 | 590 | +239.8 | 43% |

## (c) UNION: 5 of the 9 caught by at least one cell.

## (d) THE STILL-UNCOVERED, WITH CAUSES
| month | time | side | nearest certified structure | fade anatomy (mv15<0 & dwell>0.45)? |
|---|---|---|---|---|
| 2025-10 | Thu 09:59 CT | S | SHD at 0.12 pts | False |
| 2025-10 | Wed 09:10 CT | L | GAP at 0.12 pts | False |
| 2022-02 | Tue 09:02 CT | S | GAP at 1.12 pts | False |
| 2022-02 | Tue 09:05 CT | S | GAP at 0.38 pts | False |

Adoption bar (pre-stated): >= 2 of 9 converted AND extras net >= 0. Registry: T-IM54.
