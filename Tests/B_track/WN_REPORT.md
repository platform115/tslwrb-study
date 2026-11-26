# WN REPORT — WHICH NEWS WINDOWS DOES HE TRADE (T-EN112)
STATUS: CLOSED | 2026-11-26 | Spec: WN_SPEC.md (committed first) | study only

Population: 105 scanned windows (40 / 65 per month); he traded 33 ({'2022-02': 19, '2025-10': 14}); 3 of his entries assigned to no scanned window (reported, not dropped). Base rate 31%.

## LEAK SWEEP
missingness parity: clean (no gap > 25pp). All features end at es+300 by construction.

## UNIVARIATE (Mann-Whitney; Bonferroni alpha .0036, suggestive .05; FINDING also needs same direction both months)
| feature | his med | other med | p | both-months same dir | verdict |
|---|---|---|---|---|---|
| tier20 | 0.00 | 0.00 | 0.0019 | yes | FINDING |
| tier45 | 0.00 | 0.00 | 0.1452 | yes | null |
| hour_ct | 9.58 | 10.46 | 0.0978 | yes | null |
| dow | 3.00 | 2.00 | 0.1778 | NO | null |
| mins_since_open | 60.00 | 112.50 | 0.0978 | yes | null |
| react_abs_5m | 4.25 | 3.56 | 0.4790 | NO | null |
| react_range_5m | 8.75 | 6.62 | 0.0673 | NO | null |
| flow_net_abs_5m | 852.00 | 611.00 | 0.1560 | yes | null |
| flow_vol_5m | 22695.00 | 18625.50 | 0.0496 | yes | suggestive |
| dist_level | 2.25 | 2.88 | 0.6964 | NO | null |
| n_levels_10 | 2.00 | 2.00 | 0.7072 | NO | null |
| has_band | 1.00 | 1.00 | nan | yes | null |
| band_width | 7.75 | 7.62 | 0.5548 | NO | null |
| in_prior_range | 1.00 | 1.00 | 0.8394 | yes | null |
| dist_pd_edge | 10.38 | 11.44 | 0.6611 | NO | null |

## SELF-STATE (flagged class, excluded from model)
n_his_today: his-window med 1 vs other 1 (p=0.6651) — in replication this becomes OUR trade count; context, not a market feature.

## MODEL LANE (leave-one-day-out CV; 1000 within-month label permutations)
- logistic: out-of-fold AUC 0.615 (null median 0.501, perm p=0.089)
- depth-2 tree: out-of-fold AUC 0.519 (null median 0.426, perm p=0.178)
- FINDING threshold: p < 0.01. Tree readout only if the tree clears; otherwise withheld (overfit bait).

Registry: T-EN112.

## THE FINDING, IN PLAIN RATES (tier20 was binary; medians hid it)
tier20 = the event TYPE's historical median reaction is >= 20 ticks
(CPI/FOMC-class). This is CALENDAR knowledge — known before the
release, no lookahead (it is the "high-impact" flag every economic
calendar publishes).
- Share of his windows on tier20 events: 21% vs 3% of untraded
  windows (2025-10: 29% vs 2%; 2022-02: 16% vs 5% — same direction
  both months).
- Read as engagement: when a tier20 event fired, he traded the
  window 78% of the time (7/9). On everything else: 27% (26/96).
  Nearly a 3x engagement jump, from information that costs nothing.
- The branch is real but PARTIAL: 26 of his 33 windows are minor
  events — the big-event flag explains why he is ALWAYS there for
  CPI/FOMC-class releases, not how he picks among the minor ones.
  That remainder is consistent with the model lane's failure to
  clear (logistic AUC 0.615, p=0.089): after the calendar branch,
  the rest of the tree top is not in these features.
- Second thread, suggestive only: flow_vol_5m (first-5-min total
  volume) higher in his windows (p=0.0496) -> BACKLOG,
  validation-only retest.
- Caveat stated: the per-event-type impact table was built from the
  corpus; event-type importance is stable public knowledge, but the
  threshold's exact calibration has in-sample flavor. The validation
  months retest it for free (the flag is a calendar constant).

## CANDIDATE RULE (per the frozen outcome line; spec to J, not built)
Not a hard filter — gating to tier20-only would keep ~9 windows and
discard 79% of his trades. The defensible uses: (a) an engagement
PRIOR: tier20 windows are near-certain engagement, minor windows
need additional confirmation (the within-window selection problem,
still open); (b) at higher contract counts, trade tier20 windows
with the full strategy and minor windows with the G2-5-style
selective variant. Both are combos; J aims.
