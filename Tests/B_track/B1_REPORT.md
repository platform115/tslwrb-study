# B1 REPORT — ANATOMY OF G2 (squeeze + news window) (T-IM47)
STATUS: CLOSED | 2026-11-25 | Spec: B1_SPEC.md (committed first)

## 1. IS THE GROUP WORTH REPLICATING? (his own results)
| month | trades | win rate | points won / lost | net | avg win / loss | worst |
|---|---|---|---|---|---|---|
| 2022-02 | 40 | 70% | +109.5 / -24.0 | +85.5 | +3.91 / -2.00 | -3.75 |
| 2025-10 | 22 | 82% | +153.2 / -7.5 | +145.8 | +8.51 / -1.88 | -3.00 |
| BOTH | 62 | 74% | +262.8 / -31.5 | +231.2 | +5.71 / -1.97 | -3.75 |

## 2. ENTRY ANATOMY (all knowable at entry)
- trigger edge found for 62/62; DISPLACEMENT (fill past the band edge, pts): q25/50/75 = 1.25 / 2.62 / 5.19
- his side matches the band's break side: 100%
- minutes since the release: q25/50/75 = 8.39 / 12.01 / 20.75
- events he trades in G2: Crude Oil Inventories (13), Natural Gas Storage (5), RCM/TIPP Economic Optimism (5), Prelim UoM Consumer Sentiment (4), CB Consumer Confidence (4), Final Manufacturing PMI (3)
- movement mv15 at entry (ticks, his way): 2.62 / 4.50 / 7.00
- 10s persistence runs: 1.00 / 1.00 / 2.00
- flow toward side (contracts/s, 1 min): 0.35 / 2.99 / 7.35
- same-direction signal in last 5 min: 48% of entries

## 3. OUTCOME ANATOMY (labels - what the trades DID)
- MFE (best excursion, pts): q25/50/75 = 2.19 / 4.62 / 7.34
- MAE (worst excursion, pts): q50/75/90 = 0.75 / 2.56 / 3.82
- hold (seconds): q25/50/75 = 72.00 / 113.50 / 230.75
- scratch-vs-runner: 14 scratches (|P&L| <= 1 pt), 20 runners (> 4 pts)
- time to the trade's best point (seconds): q25/50/75 = 16.25 / 66.50 / 135.75 - the 'moves quickly' clause, measured

## 4. THE TRIPLE-BARRIER GRID (handed to B2; ranges, not picks)
| barrier | candidates (from his quantiles) |
|---|---|
| profit (pts) | 2.19 / 4.62 / 7.34 |
| stop (pts) | 0.75 / 2.56 / 3.82 |
| time (s) | 114 / 231 / 672 |

Registry: T-IM47.
