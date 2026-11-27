# S5MF_SPEC — D-30: S5-MF, STRATEGY 5 ON THE FAMILY-EDGE UNIVERSE (T-SR02)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11
ONE variable changes vs Strategy 5: WHERE we listen for touches.
Everything else — trigger logic, risk, exits, single position — is
S-1's certified machinery verbatim (T-SR01). Tier-R.

## R-11 MONTHS-SPEND (mandatory section, first)
- Design has seen: 2022-02 + 2025-10, through T-BK02/03/04 (book
  studies), T-SR01 (Strategy 5), T-EN114/115 (family-edge evidence).
- This run newly spends: NOTHING. Both months already spent for
  surgical-line claims.
- Hold-out considered: none possible — these are the only two months
  with processed depth (OFI10 for the exits). Four flow-only months
  cannot run S5's exits.
- Consequence: verdict capped at TRAINING-ONLY by construction;
  judge = D-8 stage 2 (depth purchase). J gated this spend 2026-11-27
  ("D-30 (S5-MF) - Go").

## PART A (this run, container-only) vs PART B (deferred)
Part A runs the ANY arm only (enter every touch): it needs no 3s
book features — flow mids + OFI10 + levels are all banked. It prices
the UNIVERSE change. Part B (MF-ACTIVE: the F-21 3s read on the new
touches) requires device-side MBP-10 window extraction at the new
touch moments; the moment list is a Part A deliverable
(mf_touch_moments.csv). Part B gets a spec addendum before it runs;
no ACTIVE-arm thresholds are minted now.

## THE UNIVERSE (the one change)
Edges live at second t (knowability: resolver comps are minute-
aligned, verified T-EN115): resolver families SQZ, GAP, SHD, REA via
edges_at; 5m/15m WRB body edges (completion-time gated, G2-6
construction); prior-day RTH H/L/C. EXCLUDED: the raw W20 q0.8 band
— its box grows while active, so "touch" is ill-defined against a
moving boundary (stated limit; the SQZ family covers compression via
completed episodes). Edge identity = (family, round(E,2)).

## TOUCH CONSTRUCTION (T-BK03's mechanics, re-targeted)
Per day (RTH span, roll days excluded), per live edge E: approach =
mid enters |mid-E| <= 2.0 from outside (a far->near transition
OBSERVED after the edge's birth — a newborn edge with price already
near does NOT fire); dedupe 600s per edge key; approach direction
d = +1 if coming from below. Touch = first second |mid-E| <= 0.5
within 600s of the approach. No touch in 600s -> no event.

## TRADE (S-1 verbatim)
Entry: stop at E + 0.75*d, armed from touch+3 (ANY arm: every
touch), TTL 120s. Stop: E - 1.25*d. Exits: flow-fade (from 60s,
every 30s, trailing-30s OFI10 signed < 0 -> out), level-capture
(multi-day levels lf(di) UNCHANGED as capture targets — widening
targets is D-29, not this test), hard cap 900s. Single position via
busy clock; same-second touch order = family order SQZ, GAP, SHD,
REA, WRB, PDY (stable).

## CELLS
- CONTROL (R-9): universe = multi-day levels lf(di); builder must
  reproduce T-BK03's approach set EXACTLY (1541 approaches, 1263
  touches, by month/t/side/level) and the sim on the 693 covered
  touches must reproduce S1-ANY EXACTLY (422 trades, +216.5). Abort
  on any mismatch.
- LVL-ANY: incumbent universe, FULL RTH touch set (the fair
  baseline — MF-ANY is also full-RTH, while S1 ran covered-only).
- MF-ANY: the family-edge universe (the test).
Per-family attribution on MF-ANY (first-family tag, shared busy —
NOT additive); TOXIC flag = family negative in BOTH months.

## VERDICT (frozen flag-lines, R-4: they force discussion)
REGISTER S5-MF TRAINING-ONLY requires ALL of:
(a) both controls exact; (b) MF-ANY pooled > LVL-ANY pooled;
(c) MF-ANY per-trade >= +0.40; (d) both months > 0; (e) worst
trade >= -2.1 (stop bound + slip tick); (f) no unflagged toxic
family. Anything partial: facts to J, J decides. Registry: T-SR02.
