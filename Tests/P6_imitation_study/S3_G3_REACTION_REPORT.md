# S3 — GENERATOR 3 (Reaction highs / lows) REPORT (T-IM22)
> Status: AWAITING REVIEW. Script: `p6_15_g3_reaction.py` + inline refinement.

## Definition (documented)
Reaction high = swing high: a bar whose high exceeds the highs of the N
bars on each side (reaction low = mirror). "Reaction high/low" is Wilder's
(1978) term; the N-each-side swing form is the standard operational
version. No universal N exists — N ∈ {1,2,3} calibrated. LOOKAHEAD RULE: a
swing is knowable only after its N following bars complete; the completion
stamp carries that lag. Object: PRECISE LEVEL (the extreme price).

## The modeling step that mattered
Keeping the most recent swing per (TF, side) — 5 candidates — produced 60%+
ambiguity and NEGATIVE gaps vs null. His phrasing ("THE most recent
reaction low", stated in 70/76 refs) describes ONE object. Tested as a
single object — the most recent swing per side on ONE timeframe — the
metric becomes plain hit-or-miss, and the result is the strongest in the
program:

| config (TF, N) | his hit (within 3 pts) | fair null | gap |
|---|---|---|---|
| 5m N=2 | **67%** | 25% ± 5% | **+42%** |
| 5m N=3 | 63% | 21% | +42% |
| 15m N=1 | 61% | 18% | +44% |
| 1m N=1 | 77% | 60% | +18% (null high — weak levels everywhere) |
(57 relational ES refs, side stated in all; broken-relation window applied;
20-permutation fair null. Lookback beyond the current session changes
nothing — his reaction references are intraday objects.)

## Reading
When he says "most recent reaction high/low", price is within 3 pts of the
single most recent 5m-or-15m swing ~63–67% of the time, vs ~20–25% at
random times with the same wording (z ≈ 8). Unlike G1/G2's uniqueness
numbers, this is a direct hit test on one designated level — the strongest
correctness evidence available without gold anchors (none exist for this
object; no same-side reference pairs occur within 30 min, so consistency
pairs are empty).

## TF pattern across generators so far
Reaction objects live on 5m/15m; G1's KME-attached gaps verified on 5m;
G1's non-KME gaps skew 1m. His structures are NOT all on one chart — the
mid TFs carry the named objects more than the 1m execution chart.

## Proposal
Adopt: most recent swing per side, 5m, N=2 (primary; N=3 and 15m N=1 are
within noise — S4 re-reference evidence picks the final one, as with G2's
open questions). Misses (~33%) unexplained for now: tolerance, late typing,
or occasional different object — S4 can audit them.

---
# RIVAL-DEFINITION TEST (user challenge 2026-11-20: do not settle for the
# first/easiest reading of his words)
Two documented rival families run on the identical hit metric and null:
| family | his hit | null | gap |
|---|---|---|---|
| R1 swing 5m N=2 (original) | 67% | 25% | +42 |
| R3 zigzag pivot, 5-pt reversal | 65% | 29% | +36 |
| R3 zigzag, 3-pt reversal | 89% | 57% | +33 |
| R2 running session extreme | 18% | 18% | 0 - RULED OUT |
Findings: his reaction H/L is NOT the session extreme (consistent with his
separate "intraday high/low" vocabulary). Zigzag pivots are competitive and
largely co-locate with swings (both = last meaningful local extreme); the
swing form leads modestly and is scale-free (zigzag's point threshold has
the cross-regime flaw). SELECTION STANDS: swing, 5m, N=2 - with zigzag
recorded as the near-equivalent rival; S4 re-reference evidence arbitrates.
Also clarified for the record: N is the swing-prominence parameter (bars
each side), NOT the sample size; the sample is 57 usable references.
