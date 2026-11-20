# MG-3 — S=90 VALIDATION RESULT: MIXED, NO FREEZE (T-MG04)
> Status: AWAITING REVIEW. Zero refitting anywhere.

## A. His entries, per-unit
| month | HIS | M1 (S=30) | S=90 | verdict |
|---|---|---|---|---|
| 2025-10 (training) | +620.0 | +200.0 | +242.5 | S=90 wins |
| 2022-02 | +751.2 | +246.2 | +222.4 | M1 wins |
| 2021-09 | +383.8 | +142.4 | +192.6 | S=90 wins |
| pooled | +1755 | +588.6 | +657.5 | S=90 +12% |

## B. ER-SIG fires (bounded-search entries), 2025-10
S=30: -36.8 | S=90: -57.0 (drawdown 84). Longer patience makes the
mechanical entry rule WORSE - patience only pays on entry quality it
cannot create. The bounded-search entry rules stay unprofitable under
both exits; that program's problem is the entries, not the clock.

## Decision
S=90 is NOT frozen as M2. The validation is regime-dependent: 2022-02 is
the high-volatility month (average losses ~3x the other months) and
longer patience is punished there. A fixed stall number is the wrong
form - which the M1 research already anticipated: the stall dial's
natural form is the ALIVE-GAP BAND rule (session-adaptive S measured
from that session's own quiet-gap distribution; the mechanism that set
30/90 for RTH/ETH in the first place).

## MG-3b PROPOSAL (pre-registered; the chartered adapter, not new search)
Compute S per session from the alive-gap band (p75..p90 of same-session
favorable-extreme gaps, as in T-EX11), apply to his entries in all three
months, compare against fixed S=30 and S=90. If the adaptive form wins
pooled AND is not worst in any month, freeze THAT as M2.
