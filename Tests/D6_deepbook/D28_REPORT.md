# D28 REPORT — ENTRY-SIDE BOOK AT THE DECISION SECONDS (T-BK04)
STATUS: CLOSED | 2026-11-27 | Spec: D28_SPEC.md (frozen first) | horizons 3/10/30s | certified extractor lineage | F-14/F-18 framing: design input, never a gate

Coverage: {'ma': 387, 'mb': 693} (of 757 fills / 1263 touches; news-window book coverage).
## M-A — OUR FILL SECONDS: EARNERS vs REST (n=103 vs 284)
| horizon | feature | earner med | rest med | p | BH | months same dir | verdict |
|---|---|---|---|---|---|---|---|
| 3s | depl_opp | 0.66 | 0.52 | 0.0074 | Y | 2/2 | FINDING |
| 3s | repl_opp | 0.45 | 0.35 | 0.0094 | Y | 2/2 | FINDING |
| 10s | depl_opp | 1.70 | 1.25 | 0.0035 | Y | 2/2 | FINDING |
| 10s | repl_opp | 1.35 | 1.01 | 0.0036 | Y | 2/2 | FINDING |
| 10s | sweep | 0.00 | 0.00 | 0.1928 | n | 2/2 | null |
| 30s | depl_opp | 4.53 | 3.41 | 0.0105 | Y | 2/2 | FINDING |
| 30s | repl_opp | 4.00 | 2.91 | 0.0098 | Y | 2/2 | FINDING |
| 30s | large_lot | 0.31 | 0.31 | 0.1279 | n | 2/2 | null |
| 30s | hidden | 6.00 | 4.00 | 0.0179 | Y | 2/2 | FINDING |
| 30s | sweep | 0.00 | 0.00 | 0.1112 | n | 1/2 | null |

## M-B — THE TOUCH AT LEVELS: HOLD vs BREAK (n=338 vs 327)
| horizon | feature | hold med | break med | p | BH | months same dir | verdict |
|---|---|---|---|---|---|---|---|
| 3s | depl_opp | 0.61 | 0.69 | 0.0063 | Y | 2/2 | FINDING |
| 3s | repl_opp | 0.42 | 0.52 | 0.0025 | Y | 2/2 | FINDING |
| 3s | hidden | 1.00 | 1.00 | 0.0124 | Y | 1/2 | suggestive |
| 3s | sweep | 0.00 | 0.00 | 0.0265 | Y | 2/2 | FINDING |
| 10s | depl_opp | 1.59 | 1.76 | 0.0693 | n | 1/2 | null |
| 10s | repl_opp | 1.30 | 1.37 | 0.0496 | n | 1/2 | suggestive |
| 10s | cancel_ratio | 0.88 | 0.88 | 0.0691 | n | 2/2 | null |
| 10s | hidden | 2.00 | 3.00 | 0.0077 | Y | 2/2 | FINDING |
| 10s | sweep | 0.00 | 0.00 | 0.0701 | n | 2/2 | null |
| 30s | depl_opp | 4.22 | 4.68 | 0.1101 | n | 1/2 | null |
| 30s | repl_opp | 3.58 | 3.87 | 0.1212 | n | 1/2 | null |
| 30s | hidden | 6.00 | 8.00 | 0.0748 | n | 2/2 | null |
| 30s | sweep | 0.00 | 1.00 | 0.0751 | n | 1/2 | null |

Non-null rows: M-A 7, M-B 6. Registry: T-BK04.

## READING — J'S DOM THESIS CONFIRMED AT THE PREDICTED HORIZON
M-B is the result of the round: AT THE TOUCH, the 50/50 hold/break
coin IS tilted - and exactly as the literature predicted, the signal
lives at the SHORTEST horizon and decays:
- 3s: breaks show HIGHER churn (depletion p=.006, replenishment
  p=.003) and MORE SWEEPS (p=.027) - all FINDINGs, both months.
- 10s: fading (hidden prints still separate); 30s: gone.
Interpretation: when price touches a multi-day level, the next ~3
seconds of book behavior say which way it resolves - hard churn +
sweeping INTO the level = the break is real; a quiet touch = the
level holds. T-BK03's pre-approach null is now EXPLAINED: wrong
moment, wrong horizon - the information exists but only at the
touch, at seconds. This is the program's FIRST entry-side book
discriminator.
M-A: profitable fills trigger into an actively CYCLING book (churn
elevated at every horizon, hidden prints at 30s) - the event-level
face of D-1's energy factor, at the fill second. Per F-14: design
input, not a gate.
## WHAT THIS ASSEMBLES (the D-25 design foundation is now complete)
Entries: level-touch -> 3s book read -> enter WITH the break on
churn/sweep confirmation (his-like per F-19: break-biased at
levels; DOM-fast per J's thesis). Exits: F-17's sustained-flow
fade. Both halves born together, as F-18 requires. Live: Rithmic
L2 via the Python runner (Tier-R), per the recorded architecture.
