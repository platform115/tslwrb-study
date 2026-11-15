# Strategy spec v3 — FROZEN before run (2026-11-15) · user mods to v2

Changes from v2 (user, verbatim intent):
- SETUP: NO cooldown (re-entry allowed the bar after an exit)
- TARGET: exit when a NEW 1-minute WRB completes after the fill bar — exit at
  that bar's close. INTERPRETATION RECORDED: any direction counts (the literal
  reading); the readout splits exits by WRB-with-position vs WRB-against so the
  opposite-only variant can be judged without a new run. Fixed 5.75 dropped.
Everything else identical to v2: RTH, force-flat, v6>=6 entries, last-5-min-move
direction, next-bar-open fill, loss cut 4.0 (arm B fast-fail 2.0 first 2 bars),
time stop 9 bars, both readings, sizing/costs out of scope.
