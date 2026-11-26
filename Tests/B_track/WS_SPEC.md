# WS_SPEC — WHICH-SIGNAL STUDY: WHY THE 1st/2nd/3rd CROSS? (T-EN109)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger (J, verbatim intent): "It's a fact that he enters on the
first, second, third, etc signal that we see. We need to figure out
why." STUDY ONLY — no strategy change comes out of this round; any
rule it suggests is a new spec presented to J first.

## HOW THIS DIFFERS FROM SEL (T-EN105, null-equivalent)
SEL asked GLOBALLY: among all our fills, do static features separate
his from ours? Null. This asks WITHIN-EPISODE: among the crosses of
the SAME edge in the SAME news window — one of which he took — what
distinguishes the taken cross from its passed siblings? The paired
design removes day/edge/window confounds SEL could not, and adds
SEQUENCE-HISTORY features (what the earlier crosses did) that were
not in the SEL feature set.

## POPULATION
The 50 matched entries from T-EN107 Part A (62 minus 12 unmatched;
unmatched counted in the report, not used). Episode = all deduped
crosses of the matched (edge,dir) key from 600s before the first
cross preceding his entry to his entry second, within the news
window. Episodes with only one cross (nothing to compare) are
reported as their own bucket and excluded from the paired analysis.

## FEATURES AT EACH CROSS (all live-computable at the cross second)
1. idx            — order of this cross within the episode (1,2,3..)
2. mins_since_rel — minutes since the news release
3. n_prior_fails  — earlier crosses of the key whose 300s max
                    excursion stayed < 1.0 pt
4. prior_max_exc  — max excursion beyond the edge since the first
                    cross of the episode (0 for the first)
5. room_ahead     — distance from edge to nearest shipped multi-day
                    level ahead in trade direction (none-> +inf cap 20)
6. level_within8  — room_ahead <= 8 (M7's arm condition)
7. flow_imb_30    — (buyv - sellv)*dir summed over last 30s, from
                    flow_per_sec
8. speed_30       — (mid_t - mid_{t-30}) * dir
9. dist_from_rel  — (mid_t - mid at release) * dir

## ANALYSIS (frozen)
- Raw fact first: distribution of taken idx (1st/2nd/3rd/4th+).
- Paired test per feature: within each multi-cross episode, the
  taken cross's rank among its siblings; null = taken cross is a
  uniform draw among the episode's crosses (10,000 within-episode
  permutations, pooled rank-sum). Report effect direction, median
  taken vs passed, and permutation p. 9 features -> Bonferroni-
  adjusted alpha 0.0056 for "finding", 0.05 flagged "suggestive".
- Power stated up front: ~50 episodes; only large effects can clear.
- No model, no fitting, no composite scores in this round.

## OUTCOME LINES (frozen)
- FINDING: any feature clearing adjusted alpha with consistent
  direction in both months -> candidate rule, spec to J.
- SUGGESTIVE: 0.0056 < p <= 0.05 -> parked in BACKLOG, retestable on
  validation months only.
- NULL: nothing clears -> "which signal" joins the six prior nulls
  as unpredictable with tape-side features; MBP-10 lane stands.
Registry: T-EN109.
