# WS REPORT — WHICH SIGNAL DOES HE TAKE, AND WHY (T-EN109)
STATUS: CLOSED | 2026-11-26 | Spec: WS_SPEC.md (committed first) | study only, no strategy change

Episodes: 21 multi-cross (paired analysis), 29 single-cross (he took the only signal), 12 unmatched (coverage ceiling).

## THE RAW FACT (J): WHICH CROSS IN THE SEQUENCE HE TAKES
| taken cross # | episodes |
|---|---|
| 2 | 14 |
| 3 | 4 |
| 4 | 2 |
| 5th+ | 1 |
Median crosses available per episode: 2.

## DESIGN VALIDITY (flagged before the table, Rule 3)
The taken cross is BY CONSTRUCTION the last cross of its episode (the episode ends at his entry). Any feature that is monotone in time within an episode is therefore guaranteed 'taken HIGHER' regardless of his behavior: idx, mins_since_rel, n_prior_fails, prior_max_exc are ARTIFACT-PRONE and their rows are labeled invalid-by-design, not findings. room_ahead and level_within8 are constant within an episode (paired design cannot test them). The design legitimately tests only market-state features: flow_imb_30, speed_30, dist_from_rel.

## PAIRED TEST: TAKEN CROSS vs ITS PASSED SIBLINGS (within-episode permutation, 10,000 draws)
| feature | taken med | passed med | direction | perm p | verdict (alpha .0056 / .05) |
|---|---|---|---|---|---|
| idx | 2.00 | 1.00 | taken HIGHER | 0.0000 | invalid-by-design |
| mins_since_rel | 32.10 | 20.78 | taken HIGHER | 0.0000 | invalid-by-design |
| n_prior_fails | 0.00 | 0.00 | taken HIGHER | 0.4818 | invalid-by-design |
| prior_max_exc | 4.88 | 0.00 | taken HIGHER | 0.0000 | invalid-by-design |
| room_ahead | 5.75 | 20.00 | taken LOWER | 1.0000 | untestable (constant in episode) |
| level_within8 | 1.00 | 0.00 | taken LOWER | 1.0000 | untestable (constant in episode) |
| flow_imb_30 | 172.00 | -81.50 | taken HIGHER | 0.2154 | null |
| speed_30 | 1.38 | -0.75 | taken HIGHER | 0.4238 | null |
| dist_from_rel | -2.75 | -1.75 | taken LOWER | 0.3708 | null |

Power note: ~21 paired episodes; only large effects can clear the adjusted alpha.
Registry: T-EN109.

## READING
- Structure of the fact first: in 29 of 50 matched entries (58%)
  there was only ONE signal of our stream to take — "which one" only
  arises in 21 episodes, and there he most often took the 2nd
  (14/21).
- The three features this design can legitimately test are all null
  at n=21. The flow direction is the one worth remembering (taken
  crosses sit on +172 median 30s aggressor imbalance, passed on
  -81.5) but the permutation test says noise-compatible at this
  sample size — it is NOT a finding, and per the distribution rule
  it is not carried forward as one.
- The time-shaped features (how long since release, what earlier
  breaks did) CANNOT be separated from "he entered when he entered"
  in any within-episode design — the first run of this script
  printed them as significant and that was the construction talking,
  caught and labeled before reporting.
- Where the question goes next: book state at taken vs passed
  crosses needs depth data — added to the MBP-10 standing trigger
  (J's drive). The purchased validation months are NOT used for this
  (they are quarantined for validation, not feature mining).

## IMPLEMENTATION NOTES (bugs caught before the clean run)
1. Duplicate news timestamps in the merged event list caused
   duplicate cross rows -> 19 episodes carried 2-3 "taken" rows
   (table summed 54 over 34 episodes — the inconsistency was the
   tell). Fixed: unique event times + cross-row dedupe. This
   duplication could NOT distort the trading runners (their fill
   dedupe and busy clock absorb copies; the control-arm exact
   reproduction confirms it).
2. First run reported mins_since_rel and prior_max_exc as FINDINGS;
   both are invalid-by-design (taken = last cross by construction).
   Labeled, not reported.
