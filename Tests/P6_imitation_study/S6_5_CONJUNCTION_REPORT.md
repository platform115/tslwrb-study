# S6.5 — CONJUNCTION GRID RESULTS (T-IM33)
> Status: AWAITING REVIEW. Script: p6_26_s6_5_conjunction.py.

| cell | catch | fires/day | fires per catch |
|---|---|---|---|
| base (REA interaction) | 79/92 (86%) | 299 | 87 |
| base & KME window | 33/92 (36%) | 41 | **28** |
| base & vol-spike | 34/92 (37%) | 128 | 86 |
| base & both | 15/92 (16%) | 22 | 34 |
| base & either | 52/92 (57%) | 146 | 64 |

## Reading
- The KME filter triples efficiency (87 -> 28 fires per catch) at 36%
  catch - it concentrates his entries relative to its own volume.
- The volatility-spike condition as formulated adds NOTHING: 86 fires per
  catch, same as base. Its fires scale with the market being active, and
  his entries within it at the same rate - it measures motion, not his
  selection. The grounded "volatility spike" vocabulary described his
  COMMENTARY moments; at entry seconds it does not discriminate. Recorded
  as a failed condition.
- Best efficiency cell still fires ~41/day for ~1.4 catches/day. Remaining
  gap to human scale ~28x. Part of that gap may be irreducible discretion
  (moments he saw and declined); the floor is not necessarily 1.

## Proposed next round (one condition, from measured evidence)
C3 = same-direction score>=6 signal completed within 5 min - the
strongest separator the typology phase measured (AUC 0.727, T-IM/p6_3),
not yet used in any selector. Grid: {base&C1} x {C3, no C3} and
{base} x {C3} for reference. Awaiting user check before running.
