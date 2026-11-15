# Strategy spec v4 — FROZEN before run (2026-11-15) · v2B + WRB trail (from v3's lesson)

## SETUP
- Session: RTH 08:30–15:00 CT; force-flat at the session's last bar close
- Instrument: ES front month (committed front-month series)
- Rule: v6 score >= 6 of 10 at a 1-minute WRB completion (frozen T-EN22 settings)
- Position: one at a time · 5-minute cooldown after any exit (restored - v3 showed
  removing it costs ~47 pts in burst-chasing re-entries)

## ENTRY
- Trigger: the moment a qualifying WRB completes
- Direction: sign of the last 5 minutes' net move (flat -> skip)
- Fill: next bar's open

## LOSS CUT
- Base: 4.0 points (his winners' p90 heat) · fast-fail arm B: 2.0 points during
  the first 2 bars after fill
- NEW - WRB TRAIL: when a SAME-direction WRB completes mid-trade, the stop
  ratchets to that WRB's body far side (long: its body bottom; short: its body
  top), applied from the NEXT bar (no lookahead), never loosening. Rationale:
  v3 showed with-direction WRBs mark profit happening but exiting there cashes
  early (-46 pts); the trail keeps the run and removes the risk instead.
  Opposite-direction WRBs are ignored (v3: exiting on them dumps recoverers).

## TARGET
- Fixed 5.75 points (his winners' median best run)

## TIME STOP
- 9 bars after fill (his winners' p75 hold)

## READINGS
1. Standalone: all system trades - P&L pts, win rate, win/loss sizes, worst
   stretch, exit mix (incl. trail-stop exits)
2. Imitation: system trades within 5 min of HIS entries vs his realized results

## OUT OF SCOPE
- Position sizing, commissions, slippage (standing instruction)
