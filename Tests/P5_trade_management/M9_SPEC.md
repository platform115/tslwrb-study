# M9 SPEC — THE STATE-MACHINE EXIT POLICY (pre-registered)
STATUS: FROZEN | 2026-11-26 | Registry: T-MG16
Built from the four T-MG15 findings; every component explicit; grids
are ranges. J's framing: recognize the condition, switch modes.
## THE POLICY (per second, deterministic)
MODE BY CLOCK (finding 1 - the new regime switch): patience budget =
  S_early in {90, 120}s while within 15 min of the release;
  S_late in {45, 60}s after. (Replaces the fixed 60s.)
FADE-AWARE STALL (finding 2): when the budget expires, exit at once
  ONLY if not deep off peak (give_back < 1.5). In a deep fade, exiting
  sells the local low: wait for a bounce of r in {0.5, 0.75} from the
  trough, hard-capped at +120s (the cap stops this becoming
  hold-the-loser - finding-4 discipline).
LEVEL ARM (finding 3): M7's snap unchanged (arm at a computed level
  within 8 pts; exit at peak-0.75 once armed).
STOP (finding 4 - EXAMINED, NOT ACTED ON): stays 3.75. The +1.36
  recovery mean after -1.5 hides tail risk; the report SHOWS the full
  outcome distribution after first touch of -1.5 to justify deferral.
  Any stop change is its own future round with risk constraints.
Hard cap 900s. Cells: 2x2x2 = 8 + M7 baseline + dual oracle reference.
## EVALUATION (frozen two-stage bars, incumbent = current best)
Stage 1 - his 62 audited fills: qualify = net > M7's +146.0.
Stage 2 - joint on the certified fill universe (b2 candidates d1.25;
  incumbent on this universe = M7 +186.0 / caught 40 / extras +88.4):
  adopt = beat pooled net, both months positive, extras >= 0, catch
  >= 40. Scope note: porting an adopted policy to the v2 band set is
  mechanical and follows as a confirmation run.
Fifth stacked training improvement if adopted - the purchased months
arbitrate. Checklist: traded P&L only; oracle shown as ceiling; null
line = M7 baseline on identical fills.
