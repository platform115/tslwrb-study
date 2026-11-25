# A5 REPORT — GAP AUTOPSY (T-IM48)
STATUS: CLOSED | 2026-11-25 | Spec: A5_SPEC.md (committed first)

## HALF 1.1 — THE BLIND SET
His trades the model scores below the typical ordinary moment: 24/307 (8%).

| axis | blind set | the rest |
|---|---|---|
| grp | {'G3': 0.46, 'G5': 0.29, 'G6': 0.12, 'G1': 0.04, 'G4': 0.04, 'G2': 0.04} | {'G3': 0.49, 'G2': 0.22, 'G5': 0.12, 'G4': 0.08, 'G1': 0.07, 'G6': 0.02} |
| np_ | {'none': 0.88, 'window': 0.08, 'burst': 0.04} | {'none': 0.63, 'window': 0.3, 'burst': 0.07} |
| month | {'2022-02': 0.67, '2025-10': 0.33} | {'2022-02': 0.7, '2025-10': 0.3} |

What blind trades lack vs the rest (difference score, blind vs seen):
- mv15: -0.78 (blind q50 -0.50 vs 4.50)
- consec_10s: -0.66 (blind q50 -0.50 vs 1.00)
- dwell120: +0.58 (blind q50 0.59 vs 0.27)
- rng120: -0.53 (blind q50 11.00 vs 21.00)
- flow1: -0.52 (blind q50 -1.25 vs 3.42)
- vrate900: -0.48 (blind q50 37.06 vs 63.87)

## HALF 1.2 — WHY THE TRIGGER MISSED 17 G2 TRADES (mechanical causes)
- caught: 45
- edge_absent: 9
- no_cross: 5
- window_miss: 2
- order_unfilled: 1

## HALF 2 — THE EXIT GAP, DISSECTED (his P&L minus M3A's, same fills)
Total gap: +107.4 pts over 62 trades.
| cause | trades | gap points |
|---|---|---|
| OTHER | 16 | +51.8 |
| SMALL | 21 | +1.0 |
| STALL-EARLY | 23 | +55.5 |
| STOP | 1 | +1.2 |
| TIME | 1 | -2.1 |

Conditioning evidence - do big-gap trades differ at ENTRY (knowable)?
- mv15: big-gap q50 4.00 vs rest 5.00 (difference -0.08)
- vrate900: big-gap q50 62.64 vs rest 61.94 (difference -0.02)
- sig: big-gap q50 1.00 vs rest 0.00 (difference +0.06)

## VERDICT (for J's pick - nothing built here)
Written in the summary message with the evidence above.

Registry: T-IM48.
