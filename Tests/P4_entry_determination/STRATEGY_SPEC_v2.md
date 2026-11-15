# Strategy spec v2 — FROZEN before run (2026-11-15) · supersedes v1 (T-EN25 FAIL)

This file doubles as THE TEMPLATE: every spec is these fields; amendments change
field values, say why, and become v3, v4... committed before their run.
All derived numbers below were measured from his 4,789 bar-covered episodes
(3,680 winners / 1,109 losers) BEFORE this spec was frozen.

## SETUP (conditions that must be true — unchanged from v1)
- Session: RTH 08:30–15:00 CT; force-flat at the session's last bar close
- Instrument: ES front month (per committed front-month series)
- Rule: v6 score >= 6 of 10 at a 1-minute WRB completion (frozen T-EN22 settings)
- Position: one at a time · 5-minute cooldown after any exit

## ENTRY (the trigger and the fill)
- Trigger: the moment a qualifying WRB completes
- Direction: sign of the last 5 minutes' net move (flat -> skip)
- Fill: next bar's open (conservative primary)

## LOSS CUT
- v2: 4.0 points adverse — his WINNERS' 90th-percentile heat (a stop that lets
  90% of his winning trades breathe; v1's 2.5 was his LOSERS' end-state and
  killed 25% of would-be winners)
- Comparison arm B ("fast-fail", mirrors his 1.5-min loser dumps): 2.0 points
  during the first 2 bars after fill, then 4.0 — his losers are >=3.25 pts
  adverse by minute 1.5 while his winners' median heat is only 1.5

## TARGET
- v2: fixed 5.75 points — his winners' MEDIAN best favorable move (v1's ~2-pt
  targets cashed tickets his winners ran far past)
- (far-edge target parked after v1; may return as an arm in v3+)

## TIME STOP
- v2: 9 bars after fill (his winners' 75th-percentile hold, 9.3 min; v1's
  3 bars was the all-trade median, dominated by his fast loser dumps)

## READINGS (what gets reported, both always)
1. Standalone: all system trades — P&L pts, win rate, win/loss sizes, equity
   path, worst stretch, exit mix
2. Imitation: system trades within 5 min of HIS entries — same stats vs his
   realized results on those months

## OUT OF SCOPE (standing instruction)
- Position sizing, commissions, slippage
