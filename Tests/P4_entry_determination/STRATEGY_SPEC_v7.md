# Strategy spec v7 — FROZEN before run (2026-11-15) · assistant recommendations, user-approved

Unit U = the PRIOR SESSION's median 1m WRB body, in points (yesterday's typical
WRB: Oct-2025 ~2.0 pts, Feb-2022 ~3.25). Every price parameter scales by U;
multipliers = v2B's winning numbers divided by pooled U (recorded derivation:
4.0->1.6U, 2.0->0.8U, 5.75->2.3U). No new fitted numbers.

## SETUP
- RTH 08:30–15:00 CT, force-flat at close · ES front month · v6 >= 6/10 at a 1m
  WRB completion · one position · 5-min cooldown

## ENTRY (two additions from the evidence)
- Trigger: qualifying WRB completes · fill: next bar's open
- Direction: BOTH must agree - sign of last 5-min net move AND sign of 5-min
  aggressor pressure; disagree, flat, or pressure unknown -> skip (recorded:
  stricter than v2-v6's move-only)
- NEW VETO: skip if 15-min pressure > 4.6 contracts/sec (his exhaustion
  ceiling, T-EN15 - the move already left)

## LOSS CUT (volatility-scaled v2B geometry)
- Base stop: 1.6 x U adverse · fast-fail: 0.8 x U during the first 2 bars
- WRB trail (kept from v4): 1st same-direction WRB mid-trade ratchets the stop
  to its body far side, next bar, never loosening; opposite WRBs ignored

## TARGET
- Fixed 2.3 x U

## TIME STOP — 9 bars (his winners' p75 hold)
## READINGS — standalone + imitation; results table now always: Configuration /
  Trades / Win rate / Avg win / Avg loss / Total, PLUS his same-month trades,
  win rate, avg win, avg loss (his P&L in units as parsed from chat)
## OUT OF SCOPE — sizing, commissions, slippage
