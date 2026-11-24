# A3 REPORT — GROUPING HIS TRADES (T-IM44)
STATUS: CLOSED | 2026-11-25 | Spec: A3_SPEC.md (committed before this script existed)

307 trades (training months). Hand taxonomy assigned first, deterministically; clustering ran blind to it.

## CHOICE OF k (both yardsticks, all k shown)
| k | mean silhouette | per-cluster stability (bootstrap Jaccard) | all >= 0.6? |
|---|---|---|---|
| 2 | 1.00 | 0.89 1.00 | YES |
| 3 | 0.73 | 0.94 1.00 0.98 | YES |
| 4 | 0.21 | 0.95 1.00 0.72 0.56 | no |
| 5 | 0.22 | 0.93 1.00 0.73 0.82 0.53 | no |
| 6 | 0.22 | 0.95 1.00 0.72 0.80 0.37 0.51 | no |
| 7 | 0.23 | 0.97 1.00 0.64 0.79 0.42 0.46 0.50 | no |
| 8 | 0.18 | 0.94 1.00 0.46 0.59 0.80 0.52 0.50 0.48 | no |

Picked k = 3 (largest k with every cluster >= 0.6, per spec).

## THE GROUPS (plain descriptions from median features)
| group | n | stability | strongest traits (vs the median trade) |
|---|---|---|---|
| 1 | 3 | 0.94 | mins_open high (+5262.6); vrate900 low (-1.4); Rest low (-0.9) |
| 2 | 14 | 1.00 | kme_mins_since high (+17.2); consec_10s high (+1.0); Rest low (-0.4) |
| 3 | 290 | 0.98 | kme_mins_since low (-0.0); Rest high (+0.0); flow1 high (+0.0) |

## GROUP x TAXONOMY CROSS-COUNTS

### ax_news
|   cluster |   news-burst |   news-window |   no-news |
|----------:|-------------:|--------------:|----------:|
|         1 |            0 |             1 |         2 |
|         2 |            0 |             0 |        14 |
|         3 |           21 |            87 |       182 |

### ax_struct
|   cluster |   open-tape |   reaction |   squeeze-break |   zone |
|----------:|------------:|-----------:|----------------:|-------:|
|         1 |           0 |          0 |               2 |      1 |
|         2 |           0 |          3 |              11 |      0 |
|         3 |           3 |         70 |             211 |      6 |

### ax_sess
|   cluster |   late |   midday |   open |
|----------:|-------:|---------:|-------:|
|         1 |      3 |        0 |      0 |
|         2 |      1 |        5 |      8 |
|         3 |     70 |       85 |    135 |

## AGREEMENT (Adjusted Rand Index: 0 = chance, 1 = identical)
| taxonomy axis | ARI vs clusters |
|---|---|
| ax_news | -0.05 |
| ax_struct | -0.01 |
| ax_sess | -0.00 |
| hand_label | -0.00 |

## OCCUPIED TAXONOMY CELLS (counts >= 5)
- no-news|squeeze-break|midday: 57
- no-news|squeeze-break|open: 49
- no-news|squeeze-break|late: 45
- news-window|squeeze-break|open: 43
- news-window|reaction|open: 17
- no-news|reaction|open: 16
- no-news|reaction|late: 15
- news-window|squeeze-break|midday: 12
- no-news|reaction|midday: 9
- news-burst|squeeze-break|open: 7
- news-window|squeeze-break|late: 7
- news-burst|reaction|open: 6
- news-window|reaction|midday: 5
(cells with <5 trades: 11, holding 19 trades)

## MANDATORY INVESTIGATION LIST (clustered together, taxonomy apart)
- cluster 3 (n=290) spans 24 taxonomy cells; largest: no-news|squeeze-break|midday (54), news-window|squeeze-break|open (43)

Labels appended to Data/inputs/a2_features.parquet. Registry: T-IM44.
