# A5 SPEC — GAP AUTOPSY (pre-registered; committed before the run)
STATUS: FROZEN | 2026-11-25 | Track A step A5 | Registry: T-IM48
Input: everything closed through B5. Training months only. Purpose:
turn the two measured gaps into named build targets - no narratives,
every miss gets a mechanical classification.

## HALF 1 — THE ENTRY GAP (ceiling 0.81 -> what the measurements miss)
1. Rerun the T-IM46 ceiling model protocol unchanged; take each of his
   307 trades' out-of-fold score. The BLIND SET = his trades scoring
   below the null median (the model finds them indistinguishable from
   ordinary tape). Profile the blind set vs the rest: group, event,
   month, session phase, intensity, every A2 family - differences
   shown with the standard difference score.
2. B2-UNCAUGHT DECOMPOSITION (the 17 G2 trades no trigger caught,
   separate from the 6 busy-skips already explained): for each, four
   mechanical checks at the entry second -
   (a) was a selected squeeze edge within 5 pts? (detector coverage)
   (b) did price CROSS such an edge within the prior 5 min? (he may
       enter on rejection, not break)
   (c) was the moment inside a scan window? (clock/window mismatch)
   (d) did a stop order at edge+1.25 simply go unfilled? (mechanics)
   Output: counts per cause. Each cause maps to a different fix.

## HALF 2 — THE EXIT GAP (his +231.2 vs M3A's +135.0 on HIS fills)
Per trade (62): gap = his stated P&L minus M3A's simulated P&L on the
same fill. Mechanical causes, checked in order:
  STOP: M3A hit -3.75 where he tolerated more and won;
  STALL-EARLY: M3A's 60s-stall exit fired, and price went on to reach
    his exit level before his actual exit time (premature patience cut);
  TIME: the 480s cap bound;
  SMALL: |gap| <= 1 pt (noise band, not dissected).
Then: do the big-gap trades share knowable entry-time conditions
(event, intensity, movement, signal)? Shown with difference scores -
this is the EVIDENCE BASE for excursion-conditioned management
candidates. No candidate is designed in this step (R-2: that is the
next round's spec).

## OUTPUT
One report: blind-set profile, uncaught-cause counts, exit-gap cause
counts + conditioning evidence, and a VERDICT section naming (a) the
next data/feature build for entries, (b) the management-candidate
shapes the evidence supports. Review gate: J picks what gets built.
