#!/usr/bin/env python3
"""
p6_8_term_grounding.py — IMITATION STUDY step 8 (queue item 1): HIS TERMS
measured on the tape at the moment he says them, vs ambient. Training months
messages only. (T-IM08; inline runs preserved here.)
Metrics at message second t: comp5 = 5-min range / median 5-min range of the
trailing hour; volratio = std(1s moves, 5min)/std(30min); |mv120| ticks.
CORRECTION LOGGED: pattern 'contract' matched 'contracts' (instruments) -
corpus count 295 was contaminated; proper 'contracting|contraction' n is
small (5-11/month).
RESULTS (vs ambient comp5 ~0.97-1.00, volratio ~0.97, |mv120| 6-7t):
- "volatility spike": comp5 1.39/1.50, volratio 1.16-1.21, |mv120| 18t in
  BOTH months (n=5/3) -> DETECTABLY REAL: when he says it, the 5-min range
  runs ~1.4-1.5x the trailing hour and the 2-min move ~2.5-3x ambient.
  First of his terms with an empirical, adapter-friendly definition.
- "contracting": weak but direction-consistent (volratio 0.91/0.92, comp5
  0.87 in 2022-02); n tiny in these months.
CAVEATS: message lag (he types after seeing); he sometimes discusses other
markets; n small throughout - grounded definitions are leads, not findings.
"""
