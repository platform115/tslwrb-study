# S6.4 — ACCOUNTING + ACTED-vs-IGNORED EDGES + DAY MAP v2 (T-IM32)
> Status: AWAITING REVIEW. Script: p6_25_s6_4_accounting.py.

## 1. Daily accounting (2025-10)
89/92 caught by >=1 selector, 85/92 by >=2; 14 of 17 sessions fully
caught; 3 uncaught (listed in T-IM31; includes the 10-17 momentum runner).

## 2. Why THOSE edges — acted-on (89) vs ignored (600) interactions
| property | acted | ignored | verdict |
|---|---|---|---|
| KME-window (45 min) | **42%** | **10%** | THE discriminator |
| tested >=2 today | 90% | 98% | no separation (both high) |
| confluence >=1 family | 96% | 98% | no separation |
| round numbers | 8% | 8% | none |
| edge age q50 | 8 min | 7 min | none |
ATTRIBUTION CAVEAT (disclosed): the acted family mix (REA 79/89) and the
size row are biased by attribution order (first-firing selector claims the
entry; REA is checked first). The KME-window comparison is per-interaction
and not affected. The clean statement: among interacted edges, his
acted-on ones are 4x more likely to be inside a KME window; structural
properties (confluence, tested-count, roundness, age) do NOT separate -
the noise edges look like the traded edges, the TIMING differs.

## 3. Day map v2 (3 busiest sessions, full in run log)
Trigger objects are predominantly young 1m/5m reaction edges (age 0-27
min), tested 1-35x, confluence 0-9. 2025-10-01: nearly every entry inside
a KME window. 2025-10-17: none - a no-KME day traded on momentum. Day
regime (KME vs no-KME) shapes which machinery is active.

## Conjunction grid — PRE-REGISTERED, awaiting user check before running
Base: REA interaction, 15-min window, direction-aligned (86% catch,
299 fires/day). Conditions, from measured evidence only:
  C1: inside a KME window (45 min)             [42 vs 10]
  C2: volatility spike at the moment (battery: comp5 >= 1.39 or
      |mv120| >= 18 ticks - his own grounded "volatility spike")
  Grid: base x {C1, C2, C1 and C2, C1 or C2} - 4 cells, each scored on
  catch of his entries and fires/day. Target: tens of fires/day or fewer.
No other conditions; no cell added after seeing results.
