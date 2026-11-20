# MG-3b — ADAPTIVE STALL CLOCK RESULT: CRITERION FAILED (T-MG05)
> Pre-stated criterion: pooled win AND not worst in any month. Outcome:
> pooled +603.1 (below S=90's +657.5) and worst in 2025-10. FAIL - M1
> stands as the working management plan. No M2 is frozen.

| month | HIS | S=30 (M1) | S=90 | adaptive (S q50) |
|---|---|---|---|---|
| 2025-10 | +620.0 | +200.0 | +242.5 | +196.2 (37 s) |
| 2022-02 | +751.2 | +246.2 | +222.4 | +222.6 (24 s) |
| 2021-09 | +383.8 | +142.4 | +192.6 | +184.2 (42 s) |
| pooled | +1755 | +588.6 | +657.5 | +603.1 |

## Why it failed, stated plainly
The adapter produced 21-46 s clocks - it tightened correctly in the
high-volatility month (matching the best plan there) but stayed near 30 s
everywhere else, never reaching the 90 s patience that wins the other two
months. IMPLEMENTATION HONESTY: the measure used here is a PROXY (gaps
between new session-path extremes), not the original T-EX11 alive-gap
measure (gaps between favorable-extreme updates DURING trade excursions).
The chartered form was not what ran; the proxy was.

## Options at this gate
A. Accept the fail as-is: M1 stands; management round closes with the
   findings recorded (patience helps 2 of 3 months; no validated form).
B. One further run with the ORIGINAL T-EX11 alive-gap measure (from the
   excursion-anatomy code) before closing - testing what was actually
   chartered. Same freeze criterion, no other changes.
