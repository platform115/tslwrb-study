# S1_SPEC — D-25: STRATEGY S-1, THE SURGICAL LEVEL-BREAK (T-SR01)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 discipline
The first strategy DESIGNED from the findings rather than searched:
every element cites its evidence. Entries and exits born together
(F-18). Tier-R (depth feed). Registry family: surgical (T-SRxx);
designation S-1 (GLOSSARY row added this commit).

## THE DESIGN (element -> evidence)
WHERE: multi-day levels from the shipped detector (F-3: the engine).
SETUP: a T-BK03-style approach that TOUCHES (|mid-L| <= 0.5).
TRIGGER (F-21): in the 3s after first touch, the book is ACTIVE -
  churn3 (depl_3+repl_3) >= its touch-universe top-tercile (frozen
  from T-BK04: the t2 threshold) OR any sweep_3 > 0. Then place a
  stop entry at L + 0.75 in the BREAK direction (the approach
  direction; F-19: he is break-biased at levels), TTL 120s from
  touch+3. QUIET touches: NO TRADE (S-1 is break-only; fade = a
  possible S-2, not this round).
RISK: protective stop at L - 1.25 against the position (the level
  is the backstop; structural risk ~2.0 pts).
EXITS (the organism): (a) the stop; (b) FLOW-FADE (F-17): from 60s
  in, check each 30s - exit when trailing-30s OFI10 signed with the
  position < 0; (c) LEVEL CAPTURE (M7's validated component): next
  level ahead -> exit at peak-0.75 once peak comes within 1.0 of
  it; (d) hard cap 900s. Single position.

## CELLS (the mechanism must show its contribution)
- S1-ACTIVE: trigger as above (the strategy).
- S1-ANY: identical but entering on EVERY touch (signal ablated) -
  the control that prices F-21's contribution.
Months: 2022-02 + 2025-10 (depth coverage); covered touches only
(coverage stated; quiet-hours untested - stated limit).

## HIS-ALIGNMENT CHECK (J's question, answered directly)
His participation rate (T-BK03 tags) on ACTIVE vs QUIET touches -
does HIS selection align with the 3s signal?

## CONTROLS (R-9 analog for a new strategy)
Touch universe must reconcile with T-BK04 exactly (693 covered);
worst trade >= -2.1 (stop bound + slip tick); every cell non-empty
per month.

## VERDICT (frozen)
REGISTER S-1 TRAINING-ONLY requires ALL: pooled > 0; both months
> 0; per-trade >= +0.60; AND S1-ACTIVE beats S1-ANY on per-trade
(the signal must contribute). Anything less: the design returns to
the bench with its autopsy. Final judgment regardless: a FUTURE
depth purchase (stated now; these months built the parts).
