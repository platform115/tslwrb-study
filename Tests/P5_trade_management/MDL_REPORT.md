# MDL REPORT — MULTI-DAY LEVEL DETECTOR (T-IM50)
STATUS: CLOSED | 2026-11-25 | Spec: MDL_SPEC.md (committed first) | evidence = completed sessions only (screening-legal)

Evidence records: 505,730 over 1293 sessions ({'wrb': 212006, 'gap': 175866, 'swing': 117858})

Recovery targets: key-tier priced mentions 55; all priced mentions 146.

## RECOVERY CHECK (his-families detector, all parameter cells)
| window | tol | min days | key-tier recovered | all-priced recovered | levels active (median/day) |
|---|---|---|---|---|---|
| 20 | 2.0 | 3 | 16/54 (30%) | 44/139 (32%) | 18 |
| 20 | 2.0 | 4 | 13/54 (24%) | 36/139 (26%) | 10 |
| 20 | 3.0 | 3 | 15/54 (28%) | 44/139 (32%) | 13 |
| 20 | 3.0 | 4 | 13/54 (24%) | 35/139 (25%) | 13 |
| 40 | 2.0 | 3 | 18/54 (33%) | 47/139 (34%) | 25 |
| 40 | 2.0 | 4 | 16/54 (30%) | 43/139 (31%) | 23 |
| 40 | 3.0 | 3 | 18/54 (33%) | 48/139 (35%) | 17 |
| 40 | 3.0 | 4 | 16/54 (30%) | 43/139 (31%) | 16 |

## GENERIC CONTROL ARM (prior-day H/L/C + 5-day H/L)
key-tier recovered: 9/54 (17%); all-priced: 18/139 (13%); levels/day = 5 by construction

## INDEPENDENT-VALUE CHECK (best cell W40 tol2.0 m3; SCREENING tier: 1m bars, completed-bar rule)
touched-level reactions (>=1.5 pt away within 30 min): levels 87% (n=2189) vs random prices 85% (n=4062)

Saved 30,712 level-days (best cell) to Data/inputs/mdl_levels.parquet. Registry: T-IM50.
