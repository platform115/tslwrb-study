# A2.2 REPORT — THE MEASUREMENT TABLE (T-IM41)
STATUS: CLOSED | 2026-11-24 | Spec: A2_2_SPEC.md (frozen) | harness PASS both months (0 honest mismatches; both planted bugs caught)

Rows: 307 of his trades with features (8 Feb-28 = NaN by design), 3070 matched nulls. 75 numeric features.

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

## FEATURE FAMILIES, GROUPED - SORTED BY HOW DIFFERENT HIS MOMENTS ARE
Difference score = Cliff's delta (Cliff, 1993): the chance a random
entry of his exceeds a random ordinary moment, minus the reverse.
0 = indistinguishable, +/-1 = completely separated. Flags = 
Mann-Whitney, Benjamini-Hochberg 5%; provisional, never gates (R-4).

| family | members flagged | strongest member | difference | his q50 | null q50 | unit |
|---|---|---|---|---|---|---|
| Directional movement (8s-15min ladder) | 10/10 | mv15 | +0.54 | 4.00 | 0.00 | ticks toward his side |
| Level story + recent bars (A2.3) | 6/12 | consec_10s | +0.44 | 1.00 | 0.00 | 10s steps, signed toward his side |
| Buy-sell flow | 3/3 | flow1 | +0.35 | 3.12 | 0.02 | net contracts/s toward his side |
| Bursts / time-since-extreme | 1/4 | stall_5m_extreme | -0.31 | 76.00 | 159.00 | seconds |
| Volume rate | 10/10 | vrate900 | +0.23 | 62.34 | 49.40 | contracts/s |
| Session scale (Cday/Rest prior-session-derived) | 2/3 | Rest | +0.21 | 346.05 | 299.71 | ticks |
| Our signal engine state | 2/2 | sig_best_score | +0.20 | 0.00 | 0.00 | score 0-10 |
| Recent range / compression | 11/13 | rng120 | +0.20 | 20.00 | 16.50 | ticks |
| Distance to structure edges | 6/8 | REA_int_dist | +0.18 | 3.44 | 2.75 | points |
| Position in the day / clock | 1/4 | mins_open | -0.17 | 100.00 | 127.00 | minutes |
| HIS LABELS: talked-about areas (A2.3) | 1/3 | mins_since_mention | -0.15 | 23.72 | 31.82 | minutes |
| News-event timing/surprise | 1/3 | kme_mins_since | -0.08 | 87.03 | 90.03 | minutes |

Flagged: 54 of 75 columns - but the ladder columns inside a family are one finding measured at several widths, so read this as ~12 family-level findings, not 54.

## FULL LIST, MOST-DIFFERENT FIRST (appendix)
| feature | difference | his q25/q50/q75 | null q50 | unit | flagged |
|---|---|---|---|---|---|
| mv15 | +0.54 | 2.00 / 4.00 / 7.00 | 0.00 | ticks toward his side | YES |
| mv20 | +0.52 | 2.00 / 4.00 / 8.00 | 0.00 | ticks toward his side | YES |
| mv10 | +0.52 | 1.00 / 3.00 / 6.00 | 0.00 | ticks toward his side | YES |
| mv30 | +0.49 | 2.00 / 4.00 / 9.00 | 0.00 | ticks toward his side | YES |
| mv45 | +0.48 | 2.00 / 6.00 / 11.00 | 0.00 | ticks toward his side | YES |
| mv8 | +0.48 | 1.00 / 2.50 / 5.00 | 0.00 | ticks toward his side | YES |
| mv60 | +0.46 | 2.00 / 6.50 / 13.00 | 0.00 | ticks toward his side | YES |
| mv300 | +0.46 | 4.00 / 14.00 / 26.00 | 0.00 | ticks toward his side | YES |
| consec_10s | +0.44 | 1.00 / 1.00 / 2.00 | 0.00 | 10s steps, signed toward his side | YES |
| mv120 | +0.43 | 1.75 / 8.00 / 20.00 | 0.00 | ticks toward his side | YES |
| flow1 | +0.35 | 0.07 / 3.12 / 7.23 | 0.02 | net contracts/s toward his side | YES |
| flow5 | +0.32 | -0.24 / 1.42 / 3.51 | -0.13 | net contracts/s toward his side | YES |
| stall_5m_extreme | -0.31 | 5.50 / 76.00 / 182.00 | 159.00 | seconds | YES |
| dwell120 | -0.23 | 0.12 / 0.31 / 0.54 | 0.45 | share 0-1 | YES |
| vrate900 | +0.23 | 42.59 / 62.34 / 82.13 | 49.40 | contracts/s | YES |
| vrate300 | +0.23 | 43.36 / 60.83 / 81.50 | 50.24 | contracts/s | YES |
| vrate10 | +0.23 | 39.90 / 60.50 / 101.85 | 47.60 | contracts/s | YES |
| vrate180 | +0.22 | 42.79 / 60.41 / 83.41 | 48.52 | contracts/s | YES |
| vrate120 | +0.22 | 41.88 / 61.27 / 81.56 | 47.95 | contracts/s | YES |
| vrate60 | +0.21 | 39.40 / 60.63 / 85.52 | 48.23 | contracts/s | YES |
| vrate30 | +0.21 | 39.15 / 60.87 / 84.95 | 47.42 | contracts/s | YES |
| Rest | +0.21 | 255.89 / 346.05 / 457.13 | 299.71 | ticks | YES |
| atr10 | +0.20 | 11.60 / 15.40 / 21.05 | 13.70 | ticks | YES |
| sig_best_score | +0.20 | 0.00 / 0.00 / 6.00 | 0.00 | score 0-10 | YES |
| rng120 | +0.20 | 13.00 / 20.00 / 28.00 | 16.50 | ticks | YES |
| last_bounce_ticks | +0.20 | 12.50 / 19.50 / 29.12 | 14.50 | ticks | YES |
| sig_samedir_5m | +0.19 | 0.00 / 0.00 / 1.00 | 0.00 | 0/1 | YES |
| approach120 | +0.19 | 3.00 / 9.00 / 19.00 | 6.00 | ticks (+=approaching) | YES |
| mv900 | +0.18 | -3.50 / 13.00 / 31.00 | 3.25 | ticks toward his side | YES |
| REA_int_dist | +0.18 | 1.88 / 3.44 / 5.12 | 2.75 | points | YES |
| rng60 | +0.18 | 9.00 / 13.00 / 20.50 | 11.00 | ticks | YES |
| mins_open | -0.17 | 41.00 / 100.00 / 231.00 | 127.00 | minutes | YES |
| consec_1m | +0.17 | -1.00 / 1.00 / 2.00 | 0.00 | bars, signed toward his side | YES |
| rng300 | +0.16 | 21.25 / 32.00 / 44.00 | 27.00 | ticks | YES |
| comp900 | +0.16 | 0.79 / 1.05 / 1.59 | 0.94 | ratio (1=typical) | YES |
| mins_since_mention | -0.15 | 4.96 / 23.72 / 105.00 | 31.82 | minutes | YES |
| rng30 | +0.15 | 6.00 / 9.00 / 13.00 | 7.50 | ticks | YES |
| comp300 | +0.15 | 0.81 / 1.05 / 1.50 | 0.94 | ratio (1=typical) | YES |
| SQZ_int_dist | +0.13 | 1.62 / 3.12 / 5.78 | 2.38 | points | YES |
| SHD_int_dist | +0.13 | 0.38 / 0.88 / 1.62 | 0.62 | points | YES |
| rng900 | +0.13 | 39.00 / 54.00 / 73.00 | 47.00 | ticks | YES |
| volr5 | +0.12 | 0.90 / 0.98 / 1.10 | 0.95 | ratio | YES |
| rng1800 | +0.12 | 55.00 / 76.50 / 103.75 | 69.00 | ticks | YES |
| vratio60_30m | +0.11 | 0.74 / 0.99 / 1.42 | 0.90 | ratio | YES |
| vratio120_30m | +0.11 | 0.78 / 0.98 / 1.33 | 0.91 | ratio | YES |
| flow15 | +0.10 | -0.63 / 0.36 / 1.60 | 0.08 | net contracts/s toward his side | YES |
| vratio300_30m | +0.10 | 0.84 / 0.96 / 1.25 | 0.94 | ratio | YES |
| GAP_near_dist | +0.10 | 0.12 / 0.38 / 1.12 | 0.38 | points | YES |
| volr2 | +0.09 | 0.86 / 0.97 / 1.12 | 0.94 | ratio | YES |
| comp120 | +0.09 | 0.80 / 1.03 / 1.42 | 1.00 | ratio (1=typical) | YES |
| GAP_int_dist | +0.09 | 0.38 / 0.75 / 1.62 | 0.62 | points | YES |
| mins_since_test | +0.09 | 4.54 / 9.43 / 17.74 | 7.79 | minutes | YES |
| REA_near_dist | -0.09 | 0.62 / 1.38 / 2.38 | 1.62 | points | YES |
| kme_mins_since | -0.08 | 17.93 / 87.03 / 264.01 | 90.03 | minutes | YES |
| SHD_near_dist | +0.06 | 0.12 / 0.38 / 0.88 | 0.38 | points | no |
| wick_opp_last | -0.06 | 0.12 / 0.24 / 0.37 | 0.25 | share 0-1 | no |
| edge_dist | +0.06 | 0.12 / 0.12 / 0.38 | 0.12 | points | no |
| kme_surprise_sign | +0.06 | -1.00 / 1.00 / 1.00 | 1.00 | +1/-1 | no |
| day_pos | -0.05 | 0.24 / 0.55 / 0.85 | 0.65 | 0=low 1=high | no |
| comp60 | +0.05 | 0.78 / 1.00 / 1.43 | 1.00 | ratio (1=typical) | no |
| bursts15 | +0.04 | 28.00 / 42.00 / 59.00 | 39.00 | count | no |
| burst_silence | -0.03 | 14.00 / 40.00 / 92.50 | 44.00 | seconds | no |
| dist_day_hi | +0.03 | 34.00 / 94.50 / 186.50 | 91.00 | ticks | no |
| SQZ_near_dist | +0.03 | 1.12 / 2.62 / 6.62 | 2.38 | points | no |
| n_tests_today | -0.03 | 2.00 / 4.00 / 8.00 | 5.00 | count | no |
| dist_day_lo | -0.03 | 57.50 / 121.00 / 217.75 | 122.00 | ticks | no |
| inside_last | -0.02 | 0.00 / 0.00 / 0.00 | 0.00 | 0/1 | no |
| kme_surprise | +0.02 | -5.50 / 0.01 / 580000.00 | 0.00 | native per report | no |
| mention_near_1pt | -0.01 | 0.00 / 0.00 / 0.00 | 0.00 | count (areas he named earlier today) | no |
| bursts5 | -0.01 | 7.00 / 13.00 / 20.00 | 13.00 | count | no |
| body_share3 | +0.01 | 0.35 / 0.45 / 0.55 | 0.46 | share 0-1 | no |
| volt3 | -0.01 | 0.76 / 0.91 / 1.21 | 0.93 | ratio | no |
| comp30 | +0.00 | 0.80 / 1.00 / 1.41 | 1.00 | ratio (1=typical) | no |
| mention_near_3pt | +0.00 | 0.00 / 0.00 / 1.00 | 0.00 | count (areas he named earlier today) | no |
| Cday | +0.00 | 21.53 / 22.06 / 22.73 | 22.06 | ratio | no |

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
