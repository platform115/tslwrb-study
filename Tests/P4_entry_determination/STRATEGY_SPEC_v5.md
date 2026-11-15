# Strategy spec v5 — FROZEN before run (2026-11-15) · user mods from v4

## SETUP (unchanged from v4)
- RTH 08:30–15:00 CT, force-flat at close · ES front month · v6 >= 6/10 at a 1m
  WRB completion · one position · 5-min cooldown

## ENTRY (unchanged)
- Trigger: qualifying WRB completes · direction: sign of last 5-min net move
  (flat -> skip) · fill: next bar's open

## LOSS CUT (replaced - user)
- Cut at bar close when an OPPOSITE-direction WRB completes mid-trade
- Cut at bar close when the entry's own speed measure (5-bar net move) flips
  SIGN against the position (interpretation recorded: the same quantity that
  chose the direction, evaluated each completed bar, nonzero opposite sign)
- NOTE, flagged: NO fixed price stop remains - worst case is bounded only by
  the time stop / the cut conditions firing
- (v4's 4.0 base stop, fast-fail arm: removed with this field)

## TARGET (replaced - user)
- 1st same-direction WRB mid-trade: trail ratchet to its body far side (from
  next bar, never loosening - as v4)
- 2nd same-direction WRB: EXIT at its close, no matter what
- (fixed 5.75 target: removed; an opposite WRB exits via LOSS CUT, so the
  "2nd WRB" count is same-direction by construction - recorded)

## TIME STOP (changed - user)
- 20 bars after fill

## READINGS / OUT OF SCOPE (unchanged)
- Standalone + imitation, both always · sizing/costs excluded
