# SEL REPORT — THE SELECTION ROUND (T-EN105)
STATUS: CLOSED | 2026-11-26 | Spec: SEL_SPEC.md (committed first)

## STEP 1 — GAP DECOMPOSITION (G2-3 fills, M7 exits)
- all fills: 542, net +265.4, per-trade +0.49
- near-his fills: 54, net +91.2, per-trade +1.69
- extras: 488, net +174.1, per-trade +0.36
- concentration: top 10% of fills hold 137% of net; losers 266 fills, -387.8

## RANKING — PROFIT (pnl>0) (held-out permutation importance)
- room_ahead: 0.055
- mv15: 0.020
- flow1: 0.013
- rng120: 0.008
- vrate900: 0.006

## RANKING — HIS-LIKENESS (held-out permutation importance)
- tod_min: 0.075
- mins_since_ev: 0.033
- mv15: 0.021
- mv300: 0.014
- lvl_behind: 0.010

## DETERMINISTIC RULES (grids; traded results; bars: per-trade >= +1.00, catch >= 40, net >= +199, both months > 0)
(null control: random half-drops give per-trade +0.50 - any rule must beat this trivially)

| rule | fills | per-trade | net (22-02/25-10) | caught | extras net | ADOPT? |
|---|---|---|---|---|---|---|
| room_ahead>= 3.0 | 432 | +0.48 | +209.4 (+104.4/+105.0) | 40 | +130.2 | no |
| room_ahead>= 4.5 | 349 | +0.44 | +152.2 (+84.0/+68.2) | 29 | +77.8 | no |
| room_ahead>= 6.0 | 288 | +0.44 | +128.1 (+69.5/+58.6) | 24 | +55.2 | no |
| room any | 542 | +0.49 | +265.4 (+140.5/+124.9) | 46 | +174.1 | no |
| mv15>=2.0 | 365 | +0.24 | +88.1 (+46.2/+41.9) | 41 | +48.9 | no |
| mv15>=4.0 | 299 | +0.20 | +60.2 (+38.8/+21.5) | 41 | +21.0 | no |
| mins_since_ev<=20.0 | 183 | +0.49 | +89.6 (+78.4/+11.2) | 19 | +62.2 | no |
| room>=4.5 & mv15>=2 | 238 | +0.06 | +14.5 (+10.6/+3.9) | 23 | -10.6 | no |
| room>=3 & mins<=20 | 157 | +0.53 | +83.0 (+68.2/+14.8) | 16 | +62.1 | no |

Registry: T-EN105. sel_fills.parquet saved (checksummed).
