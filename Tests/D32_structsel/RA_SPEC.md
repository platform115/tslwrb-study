# RA_SPEC — D-33 ROUND 2: RECLAIM ANATOMY + FLOW-CONDITIONED EXIT (T-SR08)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11 + R-12
J's challenge to F-30: depth-only reclaim exits fail (T-SR07) - but
can the dips that DIE be told from the dips that RECOVER by richer,
documented discriminators? Methods on record: MAE/MFE path analysis
(Sweeney 1996), time stops (Tharp 1999), and our own F-17 deep-flow
machinery. No invented concepts; every lens cites its source.

## R-11 MONTHS-SPEND
2022-02 + 2025-10 only (OFI10 exists only there); already spent;
nothing new; no hold-out; TRAINING-ONLY; judge = D-8 stage 2.

## R-12 FINDINGS SWEEP
APPLIED: F-13 (controls), F-17 (OFI10 adverse-flow is THE tested
conditioner - his exit mechanism pointed at our loss side), F-20
(no fitted thresholds - the constructive rule is sign-based),
F-28/29 (RWY is the verdict universe), F-30 (depth-only is dead -
this round tests CONDITIONAL reclaims only), F-11 (haircut stated).
NOT-APPLICABLE: F-1..F-10/F-12 (combo-line/early findings),
F-14/15/16 (combo management frontier), F-18 (no his-rule
transplant - F-17 is a measured mechanism, not his rule), F-21..27
(entry/selection side, untouched here), F-6 noted: the retest-dip
being normal is WHY unconditional exits fail.

## OBJECT
The certified baseline trades (5W full-RTH 750; RWY[2,8] 102).
RECLAIM EVENT: first second after fill with exc <= -1.00 (price a
tick through the level against the position - T-SR07's frozen x).
Per reclaimed trade, computed AT that second (no lookahead):
A1 time-to-reclaim (secs since fill); A2 prior MFE (max exc before
the reclaim); A3 reclaim velocity (exc drop over the prior 10s);
A4 trailing-30s OFI10 signed with the position (F-17; None when no
book coverage -> excluded, counted).
OUTCOME: final certified pnl - STOPPED (-2.00) vs RECOVERED (>0)
vs other. Lenses: per-bucket stop-rate / mean final pnl, pooled +
by month; top-vs-rest MW, BH q=0.10 across the 4 lenses; FINDING =
BH-pass + both-months direction.

## THE ONE CONSTRUCTIVE RULE (frozen now, sign-based, no fitting)
FLOW-CONDITIONED RECLAIM EXIT: at the reclaim second, if trailing-
30s OFI10 signed with the position < 0, exit at -1.00; otherwise
hold (stop/exits unchanged). No coverage -> hold. Run as full cells
(5W-FCR, RWY-FCR) under the certified engine; twin-matched
mechanism accounting exactly as T-SR07 (changed trades' delta;
rescued/killed counts; busy-freed separate).

## R-9 CONTROLS
Builder 1541/1263; 5W 750/+472.1; RWY 102/+157.1 exact; and the
T-SR07 unconditional x=0.25 cell re-derived as a degenerate case
check (all-coverage, ignore-flow must reproduce 104/+125.6).

## VERDICT (frozen flag-lines; RWY-FCR)
ADOPT-AS-CANDIDATE requires ALL: (a) controls exact; (b) twin-
matched mechanism delta > 0 pooled AND >= 0 both months; (c) full-
cell pooled > +157.1; (d) worst >= -2.1. Lens FINDINGs register
regardless of the rule's fate. Partial -> facts to J.
Registry: T-SR08.
