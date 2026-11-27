# DB2_SPEC — D-6 DEFERRED HALF: LEVEL-APPROACH + G3 EVENT FEATURES (T-BK03)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 lineage
Purpose: the raw material for D-25 (surgical fade/level-approach
entries) and D-5 (G3), extracted while the drive is connected.
STUDY/EXTRACTION ONLY - descriptive tables; any rule is a D-25 spec.

## E1 — LEVEL-APPROACH EVENTS (the fade candidate universe)
Population: both depth months, RTH. A level-approach = the first
second where |mid - L| <= 2.0 after having been > 2.0, for each
active multi-day level L (the shipped detector, lf(di)), deduped
600s per (level, approach direction). Approach direction = the side
price comes FROM (below -> resistance test; above -> support test).
Per approach: the 8 certified book features (trailing 30s at the
approach second) + frozen OUTCOME from per-second mids over the
next 600s:
- HOLD (fade pays): mid reverses >= 1.5 pts away from the level
  without first trading >= 1.0 beyond it
- BREAK: mid trades >= 1.5 beyond the level before reversing 1.5
- CHOP: neither within 600s
HIS TAG: any of his audited entries within +-300s and within 2.5 pts
of L, with his side recorded (fading or breaking).

## E2 — G3 ENTRY FEATURES
His quiet-squeeze entries (ctx = squeeze, outside the 45-min news
window) in the depth months: the same 8 features at entry seconds -
banked for the D-5 cycle (no analysis this round beyond counts).

## ANALYSIS (E1 only, frozen)
Base rates first (HOLD/BREAK/CHOP, per month). Then holds-vs-breaks
compared on the 8 features (approach-direction-signed where
applicable): BH q=0.10, both-months direction for FINDING - these
findings are D-25 DESIGN INPUTS (which book states mark a level
likely to hold), explicitly allowed to inform the D-25 spec since
D-25's final judgment is on future months + future depth (D-8).
His-tagged approaches summarized beside (which outcomes he trades).
Extractor: certified T-BK02 lineage (same feats code). Registry: T-BK03.

## ADDENDUM 1 (2026-11-27, before any analysis - caught by base rates)
The outcome definition was flawed: price enters the 2.0 zone already
~2 pts from the level, so "reverses >= 1.5 from the level" could
fire instantly -> 96% HOLD. Corrected (frozen): an approach must
TOUCH the level (|mid - L| <= 0.5) before HOLD can count; HOLD =
after the touch, mid reverses >= 1.5 from L with max penetration
< 1.0; BREAK unchanged (>= 1.5 beyond, before or after touch);
never touches within 600s -> NO_TEST (excluded, counted). No
analysis had been run on the flawed labels.
