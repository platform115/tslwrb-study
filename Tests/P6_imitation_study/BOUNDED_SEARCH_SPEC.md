# BOUNDED SEARCH — STRATEGY HYPOTHESES (written BEFORE any backtest, Rule 2)
> Program part 2: our own entries, built from imitation-study harvest.
> P&L is in scope HERE (unlike the imitation study). Position sizing,
> commissions, transaction costs out of scope per project instructions.

## Pre-registered strategy candidates (parameters FIXED from measured
## imitation numbers - no tuning before the first backtest)
S-A "Edge-break": enter on REA-edge interaction (union definition,
    15-min window, direction = break side) at market; manage with M1
    (frozen). Hypothesis: structure-triggered entries + M1 management are
    net positive because the edge break marks initiative flow.
S-B = S-A gated by KME window (45 min). Hypothesis: the 3x concentration
    carries into P&L via higher post-KME follow-through.
S-C = S-A gated by the score>=6 same-direction signal (5 min).
    Hypothesis: the 7x concentration selects the follow-through subset.
Stopping rule: these three run ONCE on 2025-10 with M1 as-is; results
reported with the standard table (trades, win rate, avg win/loss, total,
max-below-start). One refinement round allowed only from reported
evidence; then holdout months. Entry gates must pass the truncation
harness before any run counts (components already certified: interaction
edges T-IM28, signals E6, M1 exits X1).
