# B3 SPEC — MANAGEMENT CANDIDATES FOR G2 (pre-registered; committed before run)
STATUS: FROZEN | 2026-11-25 | Track B step B3 | Registry: T-MG08
Method: each candidate is simulated ON HIS 62 AUDITED FILLS (his entry
second + fill price + side; our exits) and compared with HIS actual
results (+231.2 pts, 74% win, +5.71/-1.97, worst -3.75). This isolates
management quality from entry quality. B4 then pairs the survivors with
B2's entry variants on OUR fills. Per-second mids; forward walk from
the fill is label-side simulation (legal; R-1 untouched).

## WHERE THE CANDIDATES COME FROM (his G2 anatomy, B1)
Holds 72-231s; MAE q50/75/90 = 0.75/2.56/3.82; MFE q50 4.62; peak at
~66s; 14 scratches vs 20 runners; prior lessons: foreign management
loses on coupled entries; his exits ride WRB-pt events; breakeven
stops lose; stall-patience was his general-trade signature.

## CANDIDATES (all deterministic; parameters are RANGES)
M-G2-A "fail-fast + target": hard stop S in {2.5, 3.75}; fail-fast
  f=1.5 inside the first {30, 60}s; single target T1 in {2.25, 4.5};
  time stop in {240, 480}s. (16 cells)
M-G2-B "arm + trail": stop 2.5 until the trade reaches arm=2.25; then
  trail = peak minus {1.5, 2.0}; time 480s. (2 cells)
M-G2-D "stall mimic" (his signature, G2-speed): exit when {30, 60, 90}s
  pass without a new favorable extreme; stop {2.5, 3.75}; time 480s.
  (6 cells)
M1 BASELINE (stall 30 + stop 4 + time 27 min): the coupling check -
  expected to underperform; if it wins, the coupling lesson is wrong
  and gets said aloud. (1 cell)

## SCORING (per cell, on the 62)
Net points, win rate, avg win / avg loss, worst trade, MAE honored,
share of HIS +231.2 captured. SELECTION RULE (pre-stated): the top 3
cells by net points whose immediate parameter-neighbors are also
positive (no isolated spikes) go to B4. No cell added after results.
