# M5 SPEC — THE DECISION-FRAMEWORK EXIT ROUND (pre-registered)
STATUS: FROZEN | 2026-11-25 | Registry: T-MG11
Evidence base (T-MG09/10): his exit edge = TWO opposite behaviors done
correctly per trade - hold through pauses (+55.5/23 trades) AND take
the fast spike (+~35/14 trades). No fixed rule can do both; the rule
must switch on OBSERVED in-trade state. Documented precedents: the
parabolic SAR's accelerating stop (Wilder, 1978 - project source list);
ATR/Chandelier condition-scaled trails (LeBeau); state-dependent
barriers (Lopez de Prado, 2018). All candidates deterministic; grids
are ranges (J's rule); stop 3.75 and 900s cap on all.

## CANDIDATES
M5A ACCELERATING TRAIL (SAR-inspired): trailing arms once the trade
  reaches +1.5; initial trail distance 2.0 pts; each NEW favorable
  extreme (0.5-pt steps) tightens it: distance x decay, decay in
  {0.8, 0.9}, floored at 0.75. Fast spikes = many new extremes = trail
  snaps tight near the peak; grinds = trail stays loose. (2 cells)
M5B SPEED GATE (dual mode): measure the time to first +2.25.
  Fast (<= Tfast, Tfast in {20s, 40s}): spike-capture - exit at
  peak minus {0.75, 1.0}. Slow: patient mode = M3A's stall-60
  unchanged. (4 cells)
DIAGNOSTIC ONLY - DUAL ORACLE: per trade, the better of (M3A, exit at
  peak-0.75 within the first 120s) chosen WITH HINDSIGHT. Not a
  candidate; it is the measured ceiling of the dual-mode idea. If the
  oracle itself cannot approach his +231.2, the gap is not closable by
  any speed-switch and we say so.

## SCORING (two stages, bars corrected and pre-stated)
Stage 1 - his 62 fills: qualify = net > M3A's +123.9 (the correct M3A
  number; T-MG09's bar mislabel noted and fixed).
Stage 2 - joint on our Strategy 4A d1.25 fills: adopt = pooled >
  G2-1's +135.8, both months positive, extras >= 0, catch >= 39.
Adopted winner -> candidate G2-2, training-validated only (fresh
validation month to be purchased before any B5-style claim).
No qualifier -> round closes; M3A stands; findings feed the next shape.
