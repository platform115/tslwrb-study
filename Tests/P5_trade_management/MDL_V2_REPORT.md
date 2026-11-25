# MDL V2 REPORT — DETECTOR v2 + REVEALED-PREFERENCE TARGET (T-IM51)
STATUS: CLOSED | 2026-11-25 | Spec: MDL_SPEC.md + V2 addendum

Market evidence v2: 298,688 deduped (sd,px) records (shadows/gaps/swings corpus-wide + 5m/15m WRB bodies; news-born 16%).
Revealed teaching set: 17,435 action records -> 48 revealed key regions (median member-days 6, median span 72 sessions).
Sanity: 3/55 of his priced KEY mentions fall inside an active revealed region.

## V2 RECOVERY (primary = revealed regions; secondary = 55 priced keys)
| window | tol | min score | revealed regions recovered | priced keys recovered | levels/day |
|---|---|---|---|---|---|
| 40 | 2.0 | 4 | 25/48 (52%) | 18/54 (33%) | 29 |
| 40 | 2.0 | 5 | 22/48 (46%) | 16/54 (30%) | 24 |
| 40 | 3.0 | 4 | 25/48 (52%) | 17/54 (31%) | 15 |
| 40 | 3.0 | 5 | 22/48 (46%) | 16/54 (30%) | 21 |
| 60 | 2.0 | 4 | 26/48 (54%) | 18/54 (33%) | 25 |
| 60 | 2.0 | 5 | 24/48 (50%) | 16/54 (30%) | 25 |
| 60 | 3.0 | 4 | 26/48 (54%) | 18/54 (33%) | 17 |
| 60 | 3.0 | 5 | 24/48 (50%) | 16/54 (30%) | 17 |

Best cell: W60 tol2.0 score>=4 -> revealed recovery 54%. Verdict bands: >=50% fit / 25-50% partial / <25% unfit (frozen).
Registry: T-IM51.
