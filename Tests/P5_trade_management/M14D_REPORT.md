# M14D REPORT — STRUCTURAL INVALIDATION EXIT (T-MG26)
STATUS: CLOSED | 2026-11-27 | Spec: M14D_SPEC.md (committed first) | R-9 CONTROL exact | verdict: MECHANISM-PRIMARY | rule = 1-min bar CLOSE beyond the edge, off once armed

| cell | trades | pooled net | by month | early exits | twin delta (changed trades) | months delta>0 | earners harmed | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 1517 | +483.2 | +138/+188/+119/+39 | 0 | - | - | - | (reproduced) |
| Y0 | 1519 | +483.6 | +137/+193/+116/+38 | 40 | -1.9 on 40 changed | 2/4 | 0 | FAIL |
| Y0.5 | 1518 | +481.0 | +138/+188/+116/+39 | 21 | -1.1 on 21 changed | 2/4 | 0 | FAIL |

Registry: T-MG26.

## READING — THE STALL ALREADY IS THE INVALIDATION EXIT
The trader's failed-breakout rule barely binds (40 / 21 exits in
1,517 trades) and nets ~zero (-1.9 / -1.1, no earners harmed). The
reason is structural: for a bar to CLOSE back beyond the edge, the
trade must spend ~a minute going nowhere - and M7's stall-60 has
usually already exited it. The stall IS a faster invalidation exit:
"no new peak for 60s" catches thesis-failure before the bar does.
J's instinct was right and is ALREADY IN THE SYSTEM - that is the
finding.

## D-24 CLOSES — THE CONSOLIDATED DESIGN LAW (F-16)
Eleven challengers across five distinct families have now failed to
beat M7 on this information set (book-gated exits T-MG21, clock
extension T-MG22, loss-trimming T-MG23, regime patience T-MG24,
reach T-MG25-immaterial, structural invalidation T-MG26-immaterial;
plus the earlier M3B/M4/M5/M6 variants). M7's four rules already
occupy the efficient frontier of what 1-second mids + computed
levels can know: the stop prices the recovery distribution, the
stall is the fastest honest invalidation, the capture monetizes the
one validated structure. FURTHER PER-TRADE QUALITY CANNOT COME FROM
REARRANGING RULES ON THIS DATA - it requires new information
(event-level book, D-6) or new trade structures (fade-at-level
D-25, G3's class D-5).
