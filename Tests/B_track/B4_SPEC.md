# B4 SPEC — THE JOINT UNIT TEST: ENTRIES x MANAGEMENT (pre-registered)
STATUS: FROZEN | 2026-11-25 | Track B step B4 | Registry: T-BS05
The first full trading test of the G2 build. Training months only.

## NAMES (GLOSSARY entries land in this same commit, R-5)
Strategy 4 = the G2 entry rule (squeeze-band break inside the 5-45 min
post-release window; stop order at edge + displacement).
  4A = unfiltered trigger; 4B = trigger + move+flow filter.
  Displacement is a parameter: d1.25 / d2.50.
M3 = the G2-speed management family (from B3):
  M3A = stall 60s, stop 3.75, time 480s
  M3B = stall 90s, stop 3.75, time 480s
  M3C = fail-fast 1.5 in first 30s, target 4.5, stop 3.75, time 480s

## COMBOS
{4A, 4B} x {d1.25, d2.50} x {M3A, M3B, M3C} = 12, each on both months.

## SIMULATION RULES (stated, no silent choices)
Fills from the certified B2 scan (b2_candidates). One position at a
time; a candidate fill during an open trade is skipped; re-entry
allowed immediately after exit. Exits walked on per-second mids from
the fill price. MAE recorded per trade; max drawdown from the
chronological equity line per month.

## SCORING — THE FULL RESULTS DISPLAY STANDARD (R-7)
Per combo, per month and pooled, against HIS G2 same-period results:
his trades / fired (per day) / caught (share; his entry within 5 min of
our fill, direction-matched) / extras (time-based, not near any of the
62); both-column block: trades, win rate, points won/lost, net, avg
win/loss, worst single trade + MAE, max DD from start; extras net
points (the goal's extras-expectancy clause).

## WINNER RULE (pre-stated)
Winner = highest pooled net among combos positive in BOTH months with
extras net >= 0. None qualifying = honest fail; back to design, said
plainly. Only the winner may proceed to B5 (one shot, 2024-11).
