# B2 SPEC — THE G2 ENTRY RULE (pre-registered; committed before the run)
STATUS: FROZEN | 2026-11-25 | Track B step B2 | Registry: T-EN103
Target: replicate G2 entries (squeeze break, 5-45 min after a release).
Months: training only. ENTRIES ONLY - management is B3; the full
paired unit test with P&L display standard is B4.

## THE CANDIDATE TRIGGER (from B1 anatomy, mechanical)
Scan every second of every 5-45-min post-release window (RTH), both
directions:
1. BREAK EVENT: per-second price crosses a selected squeeze-band edge
   (certified resolver objects); break side = direction.
2. ENTRY ORDER: stop order at edge + DISPLACEMENT x direction;
   displacement grid {1.25, 2.50} pts (his q25/~q50 - a RANGE, J's
   rule). Order lives 5 minutes; untouched = no trade.
3. DEDUPE: one candidate per (edge, direction) per 5 minutes.

## FILTERS (deterministic, from the stacking conditions; the ceiling
## model only RANKS them - the shipped rule is explicit conditions)
At the trigger second (all knowable <= t): movement mv15 above the
ambient median toward the break side; persistence consec_10s >= 1;
flow1 toward side > 0; same-direction signal in last 5 min.
Filter sets tested: none; each alone; the pairs; all. No filter added
after seeing results.

## LABELS (triple-barrier, Lopez de Prado 2018 ch.3)
Center cell: profit 4.50 pts, stop 2.50, time 240 s (B1 medians,
rounded to tick); sensitivity rows at profit {2.25, 7.25}, stop
{0.75, 3.75}, time {120, 660}. First barrier hit decides the label,
at 1-second resolution, from the fill second.

## SCORING (per candidate rule: the entry-quality scoreboard)
- catch: his G2 entries with a fill within +/-5 min, direction-matched
  (same definition as every prior catch number);
- fires/day inside the windows; extras = fills not near his entries;
- extras quality: barrier-label win rate + average barrier P&L of
  extras (the goal's clause: extras acceptable if also profitable);
- PER-EVENT SPLIT (J, 2026-11-25): oil-inventory windows vs all other
  events, same scoreboard - a distinct oil profile = a named sub-group
  (G2a), never a hidden confounder.

## HONEST LIMITS (stated now)
Entry-quality only: no management, no P&L claim beyond barrier labels;
fills at mid-price crossing (stop-order realism priced at B4); n=62
target, oil concentration 13/62.
