# STRATEGY 1 (spec v10) — FROZEN (2026-11-15) · user's confirmation entry
> Named "Strategy 1" by the user (2026-11-16). Lineage: Group-A reverse
> engineering (news-burst signal shape), applied ungated. Scope for now:
> this arm only — Group B / fades parked.
> OOS (T-EN46, one shot): 2021-09 +62.5 pts (144 tr, 49%) · 2024-11 −7.2 pts
> (175 tr, 44%) · pooled +0.17/trade vs +0.84 in-sample.

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
