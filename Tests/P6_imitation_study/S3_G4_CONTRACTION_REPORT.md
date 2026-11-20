# S3 — GENERATOR 4 (Contraction ranges) REPORT (T-IM23)
> Status: AWAITING REVIEW. Script: `p6_16_g4_contraction.py`.

## Definitions tested (documented families)
C1 — Crabel (1990) NR-7: most recent narrowest-range-of-7 bar; band = the
7-bar span. Tested on 5m and 15m.
C2 — rolling compression (same measure family as the p6_0 battery): W-bar
rolling range ≤ q × median of prior same-width windows (1-hour history)
marks active bars; an episode = a maximal run of active bars; band =
low/high of the episode so far. W ∈ {15, 30, 60} 1m bars, q ∈ {0.5, 0.67}.
Both ≤t. Selection: most recent episode at t — single object. Matching:
role-aware (S = band low, R = band high), relation-aware, tol 3.

## Results — his contraction references (95 relational ES)
| variant | his hit | null | gap |
|---|---|---|---|
| **C2 W=15 q=0.67** | **67%** | 53% | **+15** |
| C2 W=30 q=0.67 | 55% | 48% | +6 |
| C1 NR7 5m | 64% | 58% | +6 |
| C1 NR7 15m | 34% | 47% | −13 |
Sharper subset — refs that NAME the S or R area of the squeeze (n=34):
**C2 W=15 q=0.67: 59% vs 35% (+24, ~4σ)** — the best evidence. His squeeze
S/R talk tracks a SHORT (~15-minute) compression window at a mild
threshold. Nulls are high on the full set because condition-talk happens
while price is inside the squeeze, and squeezes are common — the
role-stated subset is the honest target.

## Merge test (S2 left open: contraction vs tight trading range)
The same C2 family scored against his tight/trading-range references
(n=41): **W=30 q=0.67: 61% vs 43% (+18)** — while W=30 is mediocre on
contraction refs (+6) and W=15 is the contraction winner. Reading:
**same family, different window** — "contracting volatility" tracks the
short window (~15 min), "tight trading range" the longer one (~30 min).
This matches the S2 hypothesis (contraction = process, tight range =
state). Proposal: keep them as two parameterizations of ONE generator
family, not merged into one object and not unrelated.

## Proposal at this gate
Adopt C2 (rolling compression): W=15 q=0.67 for contraction-range objects,
W=30 q=0.67 for tight-trading-range objects — both flagged provisional at
the same standard as G2 (S4 re-reference evidence refines). NR7 recorded
as tested and weaker; NR7 15m negative.
