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
