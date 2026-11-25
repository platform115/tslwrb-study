# A4 REPORT — CANDIDATE RANKING (T-IM46)
STATUS: CLOSED | 2026-11-25 | Spec: A4_SPEC.md (committed first)

## (a)+(b) PER-GROUP SEPARABILITY AND MONTH STABILITY
| group | n (22-02/25-10) | features with diff >= 0.3 | top three (value) | stable-sign share |
|---|---|---|---|---|
| G1 news-burst | 21 (15/6) | 10/14 | mv15 +0.66; consec_10s +0.56; vrate900 +0.44 | n/a |
| G2 squeeze+news | 62 (40/22) | 5/15 | mv15 +0.58; kme_mins_since -0.56; consec_10s +0.40 | 100% of 12 |
| G3 squeeze quiet | 151 (108/43) | 4/15 | mv15 +0.51; consec_10s +0.42; flow1 +0.32 | 100% of 5 |
| G4 reaction+news | 25 (16/9) | 6/14 | sig_best_score +0.46; consec_10s +0.39; flow1 +0.39 | 80% of 10 |
| G5 reaction quiet | 40 (34/6) | 2/15 | mv15 +0.50; stall_5m_extreme -0.32; REA_int_dist +0.30 | n/a |
| G6 rare contexts | 8 (2/6) | 1/12 | consec_10s +0.35; mins_vs_open -0.23; kme_mins_since +0.20 | n/a |

## (c) CEILING MODEL (instrument only - never a strategy)
Overall out-of-fold AUC: 0.81 (0.5 = measurements add nothing; 1.0 = fully separate his moments from matched ordinary ones)

| group | AUC within group | n his / n null |
|---|---|---|
| G1 news-burst | 0.85 | 21 / 59 |
| G2 squeeze+news | 0.86 | 62 / 566 |
| G3 squeeze quiet | 0.77 | 151 / 1114 |
| G4 reaction+news | 0.81 | 25 / 244 |
| G5 reaction quiet | 0.75 | 40 / 589 |
| G6 rare contexts | 0.57 | 8 / 498 |

Top 10 measurements by held-out permutation importance:
- mv15: 0.016
- mv300: 0.013
- stall_5m_extreme: 0.010
- kme_mins_since: 0.010
- mv20: 0.010
- mv30: 0.008
- mv10: 0.007
- mins_since_mention: 0.007
- mv60: 0.005
- mv45: 0.005

## (d) STACKING STUDY (conditions from the frozen spec; thresholds = null percentiles, a range each)
| depth | best conjunction | capture (his) | null pass | lift |
|---|---|---|---|---|
| 1 | move>p50 | 87% | 45.2% | 1.9x |
| 2 | move>p50 AND flow>p50 | 68% | 27.2% | 2.5x |
| 3 | persist>=1 AND news15 AND signal | 10% | 0.4% | 29.1x |
| 4 | structure AND persist>=1 AND news15 AND signal | 10% | 0.3% | 35.6x |

Reading: capture = share of his 307 entries passing; null pass = share of matched ordinary moments passing; lift = concentration. Fires-per-day costing happens at the selector stage (B), as specified.

## THE RANKED EVIDENCE TABLE (rubric from the spec; J picks)
| group | n | sep. breadth (>=0.3) | ceiling AUC | stable share |
|---|---|---|---|---|
| G2 squeeze+news | 62 | 5 | 0.86 | 100% |
| G1 news-burst | 21 | 10 | 0.85 | n/a |
| G4 reaction+news | 25 | 6 | 0.81 | 80% |
| G3 squeeze quiet | 151 | 4 | 0.77 | 100% |
| G5 reaction quiet | 40 | 2 | 0.75 | n/a |
| G6 rare contexts | 8 | 1 | 0.57 | n/a |

Registry: T-IM46.
