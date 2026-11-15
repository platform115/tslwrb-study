# Strategy spec v6 — FROZEN before run (2026-11-15) · user mods

## SETUP (unchanged from v4)
- RTH 08:30–15:00 CT, force-flat at close · ES front month · v6 >= 6/10 at a 1m
  WRB completion · one position · 5-min cooldown

## ENTRY (unchanged)
- Qualifying WRB completes · direction = sign of last 5-min net move · fill next bar open

## LOSS CUT (user)
- Opposite-direction WRB completes at any point -> cut at its close
- Progress check ("not moving fast enough in the right direction"): at the close
  of the 5th bar after fill, favorable progress <= 0 -> cut. ANCHOR RECORDED:
  his winners' p25 progress at 5 min is exactly 0.0, so this floor keeps ~75%
  of his winners while catching stalls
- HARD FLOOR: fixed 2.5-pt maximum loss (intrabar price stop - restores the
  floor whose absence sank v5)

## TARGET (user)
- 1st same-direction WRB mid-trade: trail ratchet to its body far side (next
  bar, never loosening) · 2nd same-direction WRB: exit at its close, no matter what
- No fixed point target

## TIME STOP — 20 bars
## READINGS / OUT OF SCOPE — unchanged (standalone + imitation; sizing/costs excluded)
