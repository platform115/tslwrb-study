# A4 SPEC — CANDIDATE RANKING (pre-registered; committed before the run)
STATUS: FROZEN | 2026-11-25 | Track A step A4 | Registry: T-IM46
Input: the measurement table (T-IM41/42/43) + approved groups of record
(G1-G6). Output: ranked evidence per group; J picks Track B's target.

## (a) PER-GROUP SEPARABILITY
Each null moment inherits its trade's group (nulls were drawn per trade).
Per group: Cliff's delta for the 15 family-representative features,
group-trades vs group-matched-nulls. Summaries: how many features reach
|delta| >= 0.3, and the strongest three named with values.

## (b) MONTH STABILITY
The same deltas per month; a feature is STABLE for a group when its
sign agrees across both months. Report share of stable features per
group, with group-month sizes shown (G1 is 15/6, G5 is 34/6 - small
cells are reported, never hidden).

## (c) CEILING MODEL (instrument, never a strategy)
Question it answers: "given the same session and time of day, how well
do ALL current measurements together pick out his moments - and which
measurements carry it?"
- Model: random forest (Breiman, 2001), 500 trees, default depth.
- Features: every numeric knowable-at-entry column; excluded by name:
  identifiers, labels, group columns, side, raw time stamps. The two
  prior-session-derived columns (Cday, Rest) stay IN, flagged.
- Validation: 5-fold GroupKFold BY SESSION DATE - train and test never
  share a session, so session identity cannot leak (the matched-null
  design already removes date/time-of-day shortcuts).
- Scores: out-of-fold AUC overall and evaluated within each group.
  Plain reading: 0.5 = measurements add nothing, 1.0 = they fully
  pick his moments.
- Importance: permutation importance on held-out folds only
  (Lopez de Prado 2018 ch.8 discipline), top 10 named.

## (d) STACKING STUDY (J, 2026-11-24; conditions fixed here)
Six plain conditions, each tested OVER A RANGE (J's standing rule),
thresholds taken from the null distribution's 50/75/90th percentiles,
never hand-picked numbers:
  C-structure: any structure family interacting (the 9:1 avoidance)
  C-move: mv15 toward the trade side above the null p50/p75/p90
  C-persist: consec_10s >= 1 / 2 / 3 steps
  C-flow: flow1 toward side above null p50/p75/p90
  C-news: within 45 / 15 / 5 min of a release
  C-signal: a same-direction score>=6 signal in the last 5 min
For conjunction depths 1..4 (best combination at each depth by
capture x lift): his-capture % vs null-pass %, and the LIFT
(capture / null-pass). Fires-per-day costing stays with the selector
machinery (B-stage) - stated out of scope here, not forgotten.

## RANKING RUBRIC (pre-stated; an evidence table, not a magic score)
Groups ranked by: separability breadth (a), ceiling AUC (c), stability
(b), and size - all four shown side by side; ties broken toward the
group whose evidence is stable across months. J picks; the table argues.
