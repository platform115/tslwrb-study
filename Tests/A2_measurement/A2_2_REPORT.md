# A2.2 REPORT — THE MEASUREMENT TABLE (T-IM41)
STATUS: CLOSED | 2026-11-24 | Spec: A2_2_SPEC.md (frozen) | harness PASS both months (0 honest mismatches; both planted bugs caught)

Rows: 307 of his trades with features (8 Feb-28 = NaN by design), 3070 matched nulls. 60 numeric features.

## STRUCTURE + KME STATE, HIS vs NULL (plain counts)
| state | his | null |
|---|---|---|
| REA interacting at the moment | 95% | 76% |
| SQZ interacting at the moment | 73% | 56% |
| GAP interacting at the moment | 97% | 80% |
| SHD interacting at the moment | 98% | 83% |
| inside 45-min KME window | 36% | 33% |
| KME phase 0-5 min | 7% | 2% |

## NAMES IN PLAIN WORDS (designation rule)
REA = reaction levels (recent swing highs/lows he reacts off); SQZ = squeeze bands (tight-range zones); GAP = hidden gaps; SHD = long-shadow zones. A null = an ordinary moment: same session, same 30-min time slot, >=10 min from any of his entries.

## FEATURE FAMILIES, GROUPED (one finding per family, not per column)
Flags = Mann-Whitney with Benjamini-Hochberg 5% correction. Provisional marks for A3/A4, never gates (R-4).

| family | members flagged | strongest member | his q50 | null q50 |
|---|---|---|---|---|
| Directional movement (8s-15min ladder) | 10/10 | mv15 | 4.00 | 0.00 |
| Recent range / compression | 11/13 | rng120 | 20.00 | 16.50 |
| Volume rate | 10/10 | vrate900 | 62.34 | 49.40 |
| Buy-sell flow | 3/3 | flow1 | 3.12 | 0.02 |
| Bursts / time-since-extreme | 1/4 | stall_5m_extreme | 76.00 | 159.00 |
| Position in the day / clock | 1/4 | mins_open | 100.00 | 127.00 |
| Session scale (Cday/Rest prior-session-derived) | 2/3 | Rest | 346.05 | 299.71 |
| Distance to structure edges | 6/8 | REA_int_dist | 3.44 | 2.75 |
| Our signal engine state | 2/2 | sig_best_score | 0.00 | 0.00 |
| News-event timing/surprise | 1/3 | kme_mins_since | 87.03 | 90.03 |

Flagged: 47 of 60 columns - but the ladder columns inside a family are one finding measured at several widths, so read this as ~10 family-level findings, not 47.

## FULL RANKED LIST (appendix)
| feature | his q25/q50/q75 | null q50 | flagged |
|---|---|---|---|
| mv15 | 2.00 / 4.00 / 7.00 | 0.00 | YES |
| mv20 | 2.00 / 4.00 / 8.00 | 0.00 | YES |
| mv10 | 1.00 / 3.00 / 6.00 | 0.00 | YES |
| mv30 | 2.00 / 4.00 / 9.00 | 0.00 | YES |
| mv45 | 2.00 / 6.00 / 11.00 | 0.00 | YES |
| mv8 | 1.00 / 2.50 / 5.00 | 0.00 | YES |
| mv60 | 2.00 / 6.50 / 13.00 | 0.00 | YES |
| mv300 | 4.00 / 14.00 / 26.00 | 0.00 | YES |
| mv120 | 1.75 / 8.00 / 20.00 | 0.00 | YES |
| flow1 | 0.07 / 3.12 / 7.23 | 0.02 | YES |
| sig_best_score | 0.00 / 0.00 / 6.00 | 0.00 | YES |
| sig_samedir_5m | 0.00 / 0.00 / 1.00 | 0.00 | YES |
| flow5 | -0.24 / 1.42 / 3.51 | -0.13 | YES |
| stall_5m_extreme | 5.50 / 76.00 / 182.00 | 159.00 | YES |
| vrate900 | 42.59 / 62.34 / 82.13 | 49.40 | YES |
| vrate300 | 43.36 / 60.83 / 81.50 | 50.24 | YES |
| vrate10 | 39.90 / 60.50 / 101.85 | 47.60 | YES |
| vrate180 | 42.79 / 60.41 / 83.41 | 48.52 | YES |
| vrate120 | 41.88 / 61.27 / 81.56 | 47.95 | YES |
| vrate60 | 39.40 / 60.63 / 85.52 | 48.23 | YES |
| vrate30 | 39.15 / 60.87 / 84.95 | 47.42 | YES |
| Rest | 255.89 / 346.05 / 457.13 | 299.71 | YES |
| atr10 | 11.60 / 15.40 / 21.05 | 13.70 | YES |
| rng120 | 13.00 / 20.00 / 28.00 | 16.50 | YES |
| mv900 | -3.50 / 13.00 / 31.00 | 3.25 | YES |
| rng60 | 9.00 / 13.00 / 20.50 | 11.00 | YES |
| mins_open | 41.00 / 100.00 / 231.00 | 127.00 | YES |
| REA_int_dist | 1.88 / 3.44 / 5.12 | 2.75 | YES |
| rng300 | 21.25 / 32.00 / 44.00 | 27.00 | YES |
| comp900 | 0.79 / 1.05 / 1.59 | 0.94 | YES |
| rng30 | 6.00 / 9.00 / 13.00 | 7.50 | YES |
| comp300 | 0.81 / 1.05 / 1.50 | 0.94 | YES |
| SHD_int_dist | 0.38 / 0.88 / 1.62 | 0.62 | YES |
| rng900 | 39.00 / 54.00 / 73.00 | 47.00 | YES |
| volr5 | 0.90 / 0.98 / 1.10 | 0.95 | YES |
| rng1800 | 55.00 / 76.50 / 103.75 | 69.00 | YES |
| SQZ_int_dist | 1.62 / 3.12 / 5.78 | 2.38 | YES |
| vratio60_30m | 0.74 / 0.99 / 1.42 | 0.90 | YES |
| vratio120_30m | 0.78 / 0.98 / 1.33 | 0.91 | YES |
| flow15 | -0.63 / 0.36 / 1.60 | 0.08 | YES |
| vratio300_30m | 0.84 / 0.96 / 1.25 | 0.94 | YES |
| GAP_near_dist | 0.12 / 0.38 / 1.12 | 0.38 | YES |
| volr2 | 0.86 / 0.97 / 1.12 | 0.94 | YES |
| comp120 | 0.80 / 1.03 / 1.42 | 1.00 | YES |
| GAP_int_dist | 0.38 / 0.75 / 1.62 | 0.62 | YES |
| REA_near_dist | 0.62 / 1.38 / 2.38 | 1.62 | YES |
| kme_mins_since | 17.93 / 87.03 / 264.01 | 90.03 | YES |
| SHD_near_dist | 0.12 / 0.38 / 0.88 | 0.38 | no |
| day_pos | 0.24 / 0.55 / 0.85 | 0.65 | no |
| kme_surprise_sign | -1.00 / 1.00 / 1.00 | 1.00 | no |
| comp60 | 0.78 / 1.00 / 1.43 | 1.00 | no |
| bursts15 | 28.00 / 42.00 / 59.00 | 39.00 | no |
| burst_silence | 14.00 / 40.00 / 92.50 | 44.00 | no |
| dist_day_hi | 34.00 / 94.50 / 186.50 | 91.00 | no |
| SQZ_near_dist | 1.12 / 2.62 / 6.62 | 2.38 | no |
| dist_day_lo | 57.50 / 121.00 / 217.75 | 122.00 | no |
| kme_surprise | -5.50 / 0.01 / 580000.00 | 0.00 | no |
| bursts5 | 7.00 / 13.00 / 20.00 | 13.00 | no |
| comp30 | 0.80 / 1.00 / 1.41 | 1.00 | no |
| Cday | 21.53 / 22.06 / 22.73 | 22.06 | no |

## KME SURPRISE (new field)
In-window trades: 109; surprise parsed: 72% (unparsed = speeches/no-forecast events, by design). Direction match (surprise sign == his side): 26% of in-window trades (28 trades).

## EVENTS HE TRADES AFTER (top, in-window trades)
- Crude Oil Inventories: 18
- Natural Gas Storage: 7
- 30-y Bond Auction: 7
- RCM/TIPP Economic Optimism: 7
- JOLTS Job Openings: 6
- CB Consumer Confidence: 6
- New Home Sales: 6
- Final Manufacturing PMI: 5

Output: Data/inputs/a2_features.parquet (checksummed). Registry: T-IM41.
