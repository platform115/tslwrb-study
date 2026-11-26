# M12_SPEC — STALL GATE: M7 + imb10 AT THE STALL EXIT (T-MG21)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J ordered both switch-rule shapes, (a) first, uncombined.
Basis: T-MG19/20 - imb10 (10-level depth imbalance toward the
position's support side) at his exits survives duration AND
excursion controls. Shape (a) monetizes it at M7's stall exit only.

## MECHANIC (M12 = M7 with ONE change)
M7 unchanged: stop -3.75, spike-capture arm/peak-0.75, time cap 480s.
CHANGED: when the stall-60 exit fires at in-trade time t,
- read imb10 at that second (book_per_sec, oriented by position
  side: (sup10 - opp10) / (sup10 + opp10));
- imb10 >= theta (liquidity to exit into) -> exit now, as M7 would;
- imb10 < theta -> grant ONE 60s extension (reset the stall clock
  once; the next stall fire exits unconditionally). Stop and 480s cap
  always bind regardless.
- book second missing (within 5s) -> behave exactly as M7 (exit) and
  COUNT the occurrence.
Grid: theta in {0.00, -0.02} (exit-median vs hold-median from
T-MG20). 2 cells + CONTROL.

## CELLS & MANDATORY CHECKS (abort on fail, as T-EN110)
- CONTROL: pure M7 through the same code path. MUST reproduce the
  corrected G2-3 line exactly: 607 trades / +276.1 / catch 47 /
  extras +185.6.
- Trade-set identity: all cells share identical entries (same fills);
  only exits may differ. Any cell whose entry set differs from
  CONTROL's aborts the run... except where a longer hold shifts the
  busy clock and later fills legally change - those trades are
  counted and listed as busy-shifted, and the entry-identity check
  applies only up to the first busy divergence per window.
- Mechanism accounting: per cell, # stall exits taken / # extensions
  granted / # missing-book stalls, and the P&L delta on extended
  trades specifically.

## VERDICT LINES (frozen; entries unchanged so catch is structural)
- ADOPT: pooled net > +276.1 AND both months positive AND worst
  single trade >= -3.75 (the stop must still bind).
- Otherwise REJECTED; M7 stands (and shape (b) is tested next
  regardless of this verdict, per J).
Full standard shown; registry T-MG21. Any outcome registers its
validation implications in VALIDATION_PLAN.md in the same commit
(depth data caveat already stands: imb10 is NOT testable on bbo-1s).
