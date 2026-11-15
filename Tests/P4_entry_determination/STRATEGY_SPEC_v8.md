# Strategy spec v8 — FROZEN before run (2026-11-15) · reverse-on-fast-fail (his mechanism)

Basis: T-EN33 - 37% of his losers are flipped within minutes and the flipped leg
wins 80%. v8 mechanizes it on BOTH co-leading configs; nothing else changes.

## SETUP / ENTRY — exactly as the base config of each arm
- Arm A base = v2B: fixed geometry, direction = 5-min move only
- Arm B base = v7: volatility-scaled (U), both-agree direction + exhaustion veto,
  WRB trail

## LOSS CUT — NEW REVERSAL MECHANIC (both arms)
- When the FAST-FAIL stop hits (the tight stop inside the first 2 bars - his
  90-second loser-dump window), the position REVERSES: flip side, fill at the
  stop price, fresh exit stack of the same arm oriented to the new side
  (reversed leg's exits evaluated from the next bar; time counted from the
  reversal bar). ONE flip maximum - the reversed leg's own fast-fail exits flat.
- The full (wide) stop after the early window exits flat, as before.

## TARGET / TIME / READINGS / OUT OF SCOPE — unchanged per arm
