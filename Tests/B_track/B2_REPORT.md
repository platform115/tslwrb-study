# B2 REPORT — THE G2 ENTRY RULE (T-EN103)
STATUS: CLOSED | 2026-11-25 | Spec: B2_SPEC.md (committed first) | entries only; management = B3

Candidate fills scanned: 1818 across 44 sessions; his G2 targets: 62.

## DISPLACEMENT 1.25 pts
| filter | fills | fills/day | his caught (of 62) | extras | extras barrier win | extras avg barrier P&L |
|---|---|---|---|---|---|---|
| none | 1029 | 23.4 | 45 | 801 | 45% | +0.28 |
| move | 657 | 14.9 | 42 | 503 | 43% | +0.20 |
| flow | 559 | 12.7 | 42 | 425 | 44% | +0.17 |
| signal | 331 | 7.5 | 24 | 229 | 45% | +0.17 |
| move+flow | 501 | 11.4 | 40 | 376 | 44% | +0.18 |
| move+signal | 219 | 5.0 | 19 | 158 | 41% | -0.05 |
| flow+signal | 194 | 4.4 | 19 | 130 | 39% | -0.14 |
| all | 171 | 3.9 | 17 | 116 | 36% | -0.42 |

## DISPLACEMENT 2.5 pts
| filter | fills | fills/day | his caught (of 62) | extras | extras barrier win | extras avg barrier P&L |
|---|---|---|---|---|---|---|
| none | 789 | 17.9 | 47 | 581 | 43% | +0.17 |
| move | 505 | 11.5 | 40 | 366 | 42% | +0.01 |
| flow | 425 | 9.7 | 41 | 306 | 41% | -0.03 |
| signal | 259 | 5.9 | 22 | 168 | 38% | -0.41 |
| move+flow | 384 | 8.7 | 38 | 274 | 42% | +0.04 |
| move+signal | 163 | 3.7 | 16 | 111 | 42% | -0.18 |
| flow+signal | 147 | 3.3 | 16 | 93 | 35% | -0.48 |
| all | 129 | 2.9 | 14 | 83 | 35% | -0.52 |

## PER-EVENT SPLIT (J's check: oil vs the rest; filter move+flow, both displacements)
- Crude Oil Inventories: 59 fills, barrier win 51%, avg +0.62 pts
- all other events: 826 fills, barrier win 43%, avg +0.16 pts

## BARRIER SENSITIVITY (filter move+flow, disp 1.25)
- center (P 4.5 / S 2.5 / T 240s): win 45%, avg +0.24
- profit 2.25: win 60%, avg +0.34
- profit 7.25: win 41%, avg +0.21
- stop 0.75: win 27%, avg +0.40
- stop 3.75: win 49%, avg +0.02
- time 120: win 49%, avg +0.21
- time 660: win 41%, avg +0.28

Candidates saved to Data/inputs/b2_candidates.parquet. Registry: T-EN103.
