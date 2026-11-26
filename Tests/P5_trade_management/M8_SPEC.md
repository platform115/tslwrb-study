# M8 SPEC — HOLD-OR-SELL DISCOVERY (per-second continuation value)
STATUS: FROZEN | 2026-11-26 | Registry: T-MG15
Framing: optimal stopping, attacked the standard practical way - learn
the value of continuing from historical paths, then (gated) extract a
deterministic threshold/dead-band policy.
## STEP 1 — STATE-SECOND DATASET (policy-free)
Every second of: our 473 certified G2 fills (b2 candidates, d1.25) and
his 62 audited trades, to 1800s or data end. State features (knowable
at that second): t_in_trade, exc (current gain), peak, give_back
(peak-exc), slope10, slope30 (gain change over last 10/30s), dist to
nearest computed level AHEAD and BEHIND (shipped detector), mins since
the release, and the fill's static context (band width, tod).
## STEP 2 — LABELS (hindsight, label-side only, never features)
fut120 = exc(t+120) - exc(t); fut300 likewise; computed from the raw
path (policy-independent). Checklist line 3: states are serially
correlated within a trade - all splits are BY SESSION, and effect
sizes are reported per-trade-averaged as well as per-second.
## STEP 3 — DISCOVERY (this round's deliverable)
Rank state features for fut120/fut300 (RF + held-out permutation
importance, GroupKFold by session); show the top states' continuation
distributions vs base rate. REVIEW GATE: J sees the discovery before
any policy is extracted (step 4).
