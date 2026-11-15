# Strategy spec v10 — FROZEN (2026-11-15) · user's confirmation entry

## SETUP — RTH, force-flat at close · ES front month · v6 score >= 6 at a 1m WRB
   completion (PRIMARY: ungated; news<=15min variant kept as the concentrated arm)
   · one position · 5-min cooldown
## ENTRY (changed - user's mechanism, first try, no grid searched)
- Direction: sign of the last 5-min net move (flat -> skip)
- FILL: stop order at the SIGNAL BAR'S MOMENTUM-SIDE EXTREME - its high when the
  move is up, its low when down - valid for 5 bars; if price never returns to
  that level, NO TRADE. Gap-through fills at the bar's open. Exits evaluated
  from the bar after the fill.
- Rationale: the next-bar-open fill bought climax points ("our losers are the
  hottest bursts"); requiring the momentum-side re-break of the trigger bar
  validates continuation and silently drops never-confirming flags.
## LOSS CUT — stop 4.0 · fast-fail 2.0 first 2 bars · REVERSE once on fast-fail
## TARGET — his pt ladder (pt1; hold to pt2/pt3 when the pt's body >= 2x prior-
   session median WRB; always out at pt3)
## TIME STOP — 9 bars
## READINGS — standard table + his stats · OUT OF SCOPE — sizing, costs
