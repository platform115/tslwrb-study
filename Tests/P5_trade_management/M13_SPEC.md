# M13_SPEC — CLOCK EXTENSION: HOLD PAST 480s WHILE THE BOOK SUPPORTS (T-MG22)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J ordered shape (b) after (a). Targets the long-hold
remainder directly (his unexplained holds beyond the clock; Analysis
B: holders at 480s sit on thicker support).

## MECHANIC (M13 = M7 with ONE change)
All M7 rules unchanged (stop -3.75, spike-capture, stall-60). CHANGED:
at the 480s time cap, instead of exiting unconditionally:
- read imb10 (oriented, 10-level); imb10 >= theta -> HOLD ON, with
  every M7 rule still live, re-checking imb10 every 60s (540, 600,
  ...); exit at the first re-check with imb10 < theta, or when
  stop/spike/stall fires, or at the HARD CAP 900s.
- imb10 < theta at 480s, or book second missing -> exit at 480s as
  M7 would (missing counted).
Grid: theta in {0.00, -0.02}. CONTROL = pure M7, must reproduce
607 / +276.1 / 47 / +185.6 exactly or the run aborts.

## VERDICT LINES (frozen — the T-MG21 lesson applied)
PRIMARY (mechanism): the extended trades' twin-matched delta vs their
identical-entry M7 twins must be > 0 pooled AND > 0 in each month.
SECONDARY (cell): pooled net > +276.1 AND both months positive AND
worst trade >= -3.75.
ADOPT requires BOTH. Primary passes but secondary fails (busy
reshuffle unlucky) -> REGISTER AS MECHANISM-VALIDATED, J aims.
Primary fails -> REJECTED regardless of cell totals.
Mechanism accounting mandatory (extensions granted / re-check exits /
hard-cap exits / no-book; twin deltas with distribution, worst
included). Registry: T-MG22. Depth caveat stands (imb10 not testable
on bbo-1s).
