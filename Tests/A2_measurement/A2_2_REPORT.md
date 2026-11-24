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

## FEATURES RANKED BY SEPARATION (Mann-Whitney, BH-corrected 5%)
Flags mark where A3/A4 should look. They are NOT gates (R-4).

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

Flagged features: 47 of 60 tested.

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
