# D4_CONSTANTS — EVERY NUMBER IN G2-4 (THE ONLY AUTHORITY ON VALUES)
STATUS: v1.0 FROZEN FOR HANDOFF | 2026-11-28
Pine code must reference these names; no number may exist only in
code. Certified source: the T-RH02 baseline machinery
(g26_remint_gen.py / remint_sims.py lineage), reproduced exactly by
the D-8 runners (T-VL05).

## Entry (EN-01)
| name | value | acts where |
|---|---|---|
| ENTRY_DISP | 1.25 | stop entry placed this far beyond the crossed edge (spec 4a) |
| ORDER_TTL_S | 300 | stop order expiry, seconds (4a, 4b) |
| SIGNAL_LOCKOUT_S | 300 | re-signal lockout per (edge, direction) (4a) |
| RETEST_WATCH_S | 600 | pullback-retest watch window after a cross (4b) |
| RETEST_EXTEND | 1.00 | excursion beyond edge that starts the retest setup (4b) |
| RETEST_PULLBACK | 0.75 | pullback-to level that re-arms the stop (4b) |
| EDGE_ROUND_DP | 2 | edge price rounding, decimals (2c, lockout key) |

## Filter (FL-WIN)
| name | value | acts where |
|---|---|---|
| WINDOW_START_S | 300 | window opens this many seconds after a release (spec 3) |
| WINDOW_END_S | 2700 | window closes this many seconds after a release (3) |
| RTH_START_CT | 08:30 | window must start inside RTH (1, 3) |
| RTH_END_CT | 15:15 | session close (1) |
| SESSION_OPEN_CT | 17:00 | structure reset, previous evening (1) |

## Structure (spec 2)
| name | value | acts where |
|---|---|---|
| W20_LEN | 20 | band window, 1m bars (2a) |
| W20_Q | 0.8 | band quietness: rng <= q * median (2a) |
| MED_LOOKBACK | 60 | bars in the median of ranges (2a, 2b) |
| MED_MIN_N | 10 | minimum defined values for the median (2a, 2b) |
| SQZ_W_FAST / SQZ_W_SLOW | 10 / 30 | squeeze episode windows (2b) |
| SQZ_Q | 0.67 | squeeze quietness threshold (2b) |
| KNOWABLE_LAG_S | 60 | 1m bar usable from close + 60s (2) |

## Exit (MP-7 / M7)
| name | value | acts where |
|---|---|---|
| STOP_PTS | 3.75 | fixed stop, points against (spec 5.2) |
| ARM_WINDOW | 8.0 | trail arms only if nearest level within this (5) |
| ARM_OFFSET | 0.75 | arm = best_distance - this (5) |
| ARM_FLOOR | 0.5 | minimum arm value (5) |
| GIVEBACK | 0.75 | trail exit: peak minus this (5.4) |
| STALL_S | 60 | exit after this long without a new peak (5.5) |
| CAP_S | 480 | hard time cap, seconds in trade (5.6) |
| LEVEL_MIN_AHEAD | 0.25 | levels closer than this (beyond entry) are ignored (5) |

## Level generation (research side; for reference - Pine only
## consumes the list)
| name | value | acts where |
|---|---|---|
| LVL_WINDOW_DAYS | 60 | sessions of structure memory (d4_levels_gen) |
| LVL_TOL | 2.0 | clustering tolerance, points |
| LVL_MIN_MEMBERS | 4 | minimum distinct days in a cluster |
| LVL_GRID | 0.25 | price grid (one tick) |
| LVL_NEWSBORN_S | 2700 | structure born within this of a release gets +1 score |
| LVL_MEMORY_KILL | 5.0 | level dropped if every close since its last member is farther than this |

## Simulation conventions (for the vector comparisons)
| name | value | acts where |
|---|---|---|
| TRADE_WATCH_S | 1800 | exit evaluation horizon from fill (engine array length; CAP_S ends trades long before) |
| CONTRACTS | 1 | always |
