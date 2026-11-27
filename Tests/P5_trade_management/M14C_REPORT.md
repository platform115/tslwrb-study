# M14C REPORT — SPIKE-CAPTURE REACH EXTENSION (T-MG25)
STATUS: CLOSED | 2026-11-27 | Spec: M14C_SPEC.md (committed first) | R-9 CONTROL exact | verdict: MECHANISM-PRIMARY | isolation: only nearest-level-in-(8,reach] trades can change

| cell | trades | pooled net | by month | newly-eligible / reached-arm | twin delta (changed) | months delta>0 | earners harmed | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 1517 | +483.2 | +138/+188/+119/+39 | 0 | - | - | - | (reproduced) |
| R10 | 1517 | +486.1 | +140/+188/+119/+39 | 27 / 1 | +2.9 on 1 changed | 1/4 | 0 | FAIL |
| R12 | 1517 | +492.6 | +140/+194/+119/+39 | 41 / 2 | +5.8 on 2 changed | 2/4 | 0 | FAIL |

Registry: T-MG25.

## READING — THE BOUNDARY FLAG IS RESOLVED: IMMATERIAL, NOT BETTER
The extension is a free option that almost never binds: 27/41 trades
became newly eligible, but only 1-2 EVER ran far enough to arm - a
far level is rarely approached within a trade's ~8-minute life under
the stall clock. Every observed instance improved (+2.9/+5.8, zero
earners harmed), so the mechanic is harmless - but 2 changed trades
in 4 months cannot clear any evidence bar (frozen line: FAIL on
months-consistency; the honest word is IMMATERIAL). The old T-MG14
"monotone to the boundary" flag is hereby RESOLVED: the monotonicity
lived inside <= 8 where levels actually get reached; beyond 8 there
is nothing to collect at this trade duration. RECOMMENDATION: keep
M7 unchanged (parsimony - a constant that binds twice per 4 months
is spec churn, not improvement). If a future management regime holds
trades longer, revisit (noted).
