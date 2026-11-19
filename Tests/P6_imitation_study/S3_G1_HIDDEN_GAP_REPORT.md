# S3 — GENERATOR 1 (WRB Hidden GAP) CALIBRATION REPORT (T-IM17)
> Status: AWAITING REVIEW. Script: `p6_12_g1_hidden_gap.py`.

## What was built
The S2-approved WHG definition (WRB Definition.txt, unchanged), computed on
the decided TF set (1/2/3/5/15m), roll-day bars excluded, no session-seam
WRBs. ≤t by construction: a zone is a candidate only once its bar completed
(open+tf ≤ t); fill state uses only 1m bars completed by t; anchor price =
last completed 1m close. Calibration vs his 119 hidden-gap references (zero
explicit prices — all relational/mention) with a session-matched random-time
ambient null (n=400).

## Result 1 — the definition saturates (his anti-saturation rule vindicated)
~469 zones/session across 5 TFs. Price sits inside SOME zone ~90% of the
time at random. His refs vs null: indistinguishable (95% vs 88% within-0 at
same-session; identical at wider lookbacks). **Per-definition WHG zones are
NOT his watched set. Selection is where all the information is.**

## Result 2 — selectivity variants (his language: "most recent" 57/119, "Big" 47/119)
| variant | his within 1 pt | null within 1 pt | edge |
|---|---|---|---|
| most-recent per TF/dir (R) | 84% | 86% | −2% |
| size ≥ 6 pts (B6) | 72% | 65% | +7% |
| R & B≥2 | 83% | 75% | +8% |
| R & B≥4 | 71% | 62% | +9% |
| R single-TF (each of 1/2/3/5/15m) | — | — | −1% to −10% |
Best edges (+7–9%) sit at ~2σ for n=118 — directionally consistent with his
"Big + most recent" language, but marginal. Single-TF most-recent is
negative everywhere.

## Why the measurement itself is part of the problem (self-critique)
1. **Proximity-at-mention-time is a weak target.** 43/119 refs are bare
   mentions, many describing a gap AS IT FORMS ("volatility spike will
   produce a Big Down WRB Hidden GAP interval") — price is trivially at a
   just-formed gap, and null times are also near gaps because gaps are
   everywhere. The target can't discriminate on a saturated base rate.
2. **Absolute size grid (B≥x points) is flawed across 5 years** — 6 points
   in 2021 (ES ~4400, different vol regime) ≠ 6 points in 2026 (~6800).
   Size should be relative (vs trailing median gap size or session ATR).
3. Null times are uniform over whole sessions incl. overnight; his refs
   skew RTH. Secondary to 1–2.

## Proposal for the gate (G1 iteration 2)
Change the calibration TARGET from proximity to **object identification**:
for the 72 RELATIONAL refs (price interacting with a pre-existing gap:
retraced / testing / stuck / broke), ask — does a UNIQUE zone matching his
words (direction + most-recent + relative-Big) exist at that moment within
tolerance? Report identifiability: exactly-one-candidate %, multi-candidate
%, none %. That is the actual goal: reconstructing WHICH object he watches,
not whether any object is nearby. Plus: relative size measure; RTH-matched
null as hygiene. No definition change — selection layer only.

## Lookahead note
Zone candidacy and fill state depend only on completed bars ≤ t by
construction. A formal truncation-harness extension for generator outputs
is due before S4 consumes them (flagged, not yet written).

---
# ITERATION 2 — OBJECT IDENTIFICATION (T-IM18, p6_13)
User direction: saturation was known; the task is identifying THE gaps he
references; TF prior 1m/3m/5m unless he specifies otherwise.

## Identification result (71 relational refs, tol 3 pts, his own descriptors applied)
| TF set | miss / IDENTIFIED / ambiguous (med n) | null unique |
|---|---|---|
| 1/3/5 (prior) | 15% / 52% / 32% (med 2) | 47% |
| 1/2/3/5/15 | 14% / 46% / 39% | 50% |
| 2m only | 28% / 63% / 8% | 47% |
Descriptor-rich refs do better (most-recent stated: 63% identified; no
descriptors: 17%). Null uniqueness ~45-50% means UNIQUENESS ALONE is not
proof of correctness - correctness comes from spot-checks.

## Spot-check findings (12 hand-checked cases) - three matcher defects found
1. DIRECTION BINDING BUG: "retracing back DOWN below the S area of the most
   recent UP WRB Hidden GAP" - parser takes the FIRST up/down in the
   message; must bind to the (Up|Down) immediately preceding "WRB Hidden
   GAP" (his consistent syntax).
2. RELATION-AWARE GEOMETRY MISSING: "broke below the S area" means price is
   BEYOND the edge - the within-3-pts band test wrongly excludes the true
   object once price has followed through (verified on the 0948am case:
   the right 5m gap [4722.75, 4730.50], completed 14:50 UTC = the 0945-50
   ET bar, S=4722.75, px 4718.25 broke below it - excluded by the naive
   tolerance window; a wrong 3m gap was returned instead).
3. ROLE-AWARE EDGE MISSING: his "S area" = zone bottom, "R area" = zone top
   ("exit at the S area of the Up WHG interval"). Matching should measure
   to the NAMED edge, not the whole band - kills much of the n=2 ambiguity.
GOLD ANCHORS: refs where he timestamps the object ("of 0948am est") permit
exact verification - collect and use them as the correctness test set.

## Iteration 3 proposal (gate decision)
Fix the three matcher defects (direction binding in parser; relation-aware
and role-aware geometry in the matcher), build the gold-anchor set, re-run
identification, and hand-check again. No definition change.

---
# ITERATION 3 — MATCHER FIXES + GOLD ANCHORS (T-IM19)
Fixes applied: (1) parser v3.1 direction binds to the token adjacent to the
kind phrase (bug case verified flipped to Up; DB regenerated, checksum
updated); (2) relation-aware geometry (broken = price allowed beyond the
named edge, 2x tol on break side); (3) role-aware edges (his S area = zone
LO, R area = zone HI); (4) ES-only calibration set (a YM ref was found
contaminating the gold set - non-ES deferred per charter).

## Identification, ES-only relational refs (tol 3)
| TF set | miss / IDENTIFIED / ambiguous | null unique |
|---|---|---|
| 1/3/5 (prior) | 10% / 64% / 26% | 44% |
| 5m only | 30% / 62% / 8% | 49% |
(Iteration 2 baseline: 15/52/32.) Most-recent-stated refs: 70%.

## Gold anchors (7 refs where HE states the object's clock time or size)
- 2025-08-14 "Big Down WRB Hidden GAP interval of the 0830am KME Report":
  UNIQUE match, CLOCK-VERIFIED (5m bar 08:30-35 ET, 29.25-pt gap).
- 2021-11-22 "big Up WRB Hidden GAP of 0948am est": correct 5m object now
  IN the candidate set (iteration-2 fix validated); clock stamp
  disambiguates it from 1 wrong co-candidate.
- 2021-11-08 "of 0938am est": clock pins the exact 1m gap among 4.
- 2021-06-16 "KME @ 1030am produced a questionable WRB Hidden GAP": NOT
  matchable by price proximity - he is describing FORMATION, price had
  left; formation references need event-time matching, not proximity.
- 1 ref was YM (filter added), 2 have no decisive verifier.
OBSERVATION: the clock-verified objects live on 5m; KME-attached gaps may
be a 5m phenomenon (consistent with 5m-only's 62%/8% identification).

## Where G1 stands (gate)
Definition: unchanged (Perry-sourced). Matcher: v3 (role/relation/direction
aware). 64% of ES relational refs pin a unique object; clock stamps verify
correctness where available. Known limits: formation-references need
event-time matching; ~26% two-candidate ambiguity (clock/TF context would
resolve some); null uniqueness floor ~44% means the match set is a working
hypothesis to be validated by use (S4 lifetime + S6 entries), not ground truth.
