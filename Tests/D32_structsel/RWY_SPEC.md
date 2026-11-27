# RWY_SPEC — D-32b: THE RUNWAY SELECTOR AS A STRATEGY (T-SR05)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11
T-SR04's FINDING (S2): per-trade rises monotonically with room to
the nearest family edge ahead, peaking at 2-8 pts of runway. A lens
on filled trades is NOT a strategy (busy-clock reshuffle, T-MG21
lesson), so the selector is now run constructively: 5W full-RTH
with touches REQUIRED to have family-edge runway in a frozen band.

## R-11 MONTHS-SPEND
Both depth months already spent (T-SR01..04); spends nothing new;
no hold-out exists. TRAINING-ONLY cap; judge = D-8 stage 2. The
band [2,8] was chosen after seeing T-SR04's gradient on these same
months - the selection channel is disclosed and is exactly why the
verdict is capped.

## MECHANIC (one change vs 5W full-RTH)
At the TOUCH second t (before entry exists), compute the would-be
entry E = L + 0.75*d and the family-edge set (G2-6 vocabulary:
resolver SQZ/GAP/SHD/REA at t, WRB bodies completed <= t, prior-day
H/L/C). Runway R = min over edges p of (p - E)*d restricted to
(p - E)*d > 0.5; R = inf if none. ADMIT the touch only if
2.0 <= R <= 8.0. Everything else is the certified 5W machinery
verbatim (touch universe, +3s stop entry, TTL 120, stop L-1.25d,
M7-capture/flow-fade/900s cap, busy single-position).

## CELLS
- CONTROL: unrestricted 5W full-RTH - must reproduce 750/+472.1
  exactly (abort otherwise), after the builder reproduces T-BK03
  (1541/1263).
- RWY[2,8]: the frozen candidate cell (verdict applies here only).
- Sensitivity ranges (reported, no verdict, per J's ranges
  directive): RWY[1.5,8], RWY[2,6], RWY[2,10], RWY[3,8].

## VERDICT (frozen flag-lines)
REGISTER "5W-RWY" TRAINING-ONLY requires ALL on RWY[2,8]:
(a) controls exact; (b) pooled n >= 100; (c) per-trade >= +1.00;
(d) both months positive; (e) worst trade >= -2.1; (f) stop-rate
< the baseline's 47%. Partial -> facts to J, J decides. The
sensitivity table must show the band is a plateau, not a knife-edge
(F-20 discipline) - a lone-band result is reported as fragile
regardless of (a)-(f). Registry: T-SR05.
