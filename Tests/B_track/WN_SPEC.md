# WN_SPEC — WINDOW SELECTION: WHICH NEWS WINDOWS DOES HE TRADE? (T-EN112)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J ordered the top of the decision tree ("be thorough, there
is almost definitely an answer"). Every prior round dissected WHICH
SIGNAL inside a window; this round asks WHICH WINDOWS he engages at
all. STUDY ONLY — any filter it suggests is a new spec to J.

## POPULATION & LABEL
All scanned news windows in both training months (unique release
times es passing the same RTH checks as every entry runner; the
5-45min post-release span). Label POSITIVE if >= 1 of his 62 G2
entries is assigned to the window (largest es with es+300 <= entry
sec <= es+2700). His entries assigned to no scanned window are
counted and reported, never silently dropped.

## FEATURES (all computable by es+300 — before the entry span opens)
Event:     tier20, tier45 (membership in the >=20tk / >=45tk event
           sets); hour_ct; dow; mins_since_open
Reaction:  react_abs_5m |mid(es+300)-mid(es)|; react_range_5m
           (max-min of mids in [es, es+300]); flow_net_abs_5m;
           flow_vol_5m (total contracts)
Structure: dist_level (|mid(es) - nearest active multi-day level|);
           n_levels_10 (levels within 10 pts); has_band (W20 q0.8
           squeeze band active at release); band_width (nan-safe);
           in_prior_range (mid(es) inside prior session RTH range);
           dist_pd_edge (min distance to prior-day RTH high/low)
Self-state: n_his_today (his earlier trades that session) — FLAGGED:
           in replication this becomes OUR trade count; reported in
           its own class, excluded from the model lane.

## ANALYSIS (frozen)
1. Base rate first: N windows, n positive, per month.
2. Univariate: Mann-Whitney (or exact proportion comparison for
   binaries) per feature; ~14 features -> Bonferroni alpha .0036
   FINDING, .05 suggestive; direction + medians both groups; month
   consistency (same direction in both months) required for any
   FINDING to stand.
3. Model lane (the "decision tree" J asked for): leave-one-day-out
   CV, pooled out-of-fold AUC, for (a) logistic on standardized
   features, (b) depth-2 decision tree. Null: 1000 label
   permutations WITHIN month. FINDING if perm p < 0.01. Tree
   structure is read out ONLY if its AUC clears; an unvalidated
   tree readout is overfit bait and is not shown.
4. Leak sweep: no feature may use data after es+300; missingness
   parity check between classes (>25pp flagged).
## OUTCOME LINES
FINDING -> candidate window filter, spec'd to J (would gate G2-3/
G2-4/G2-5 the same way). Suggestive -> BACKLOG, validation-only
retest. Null -> the tree top is not in these features; lanes left =
event-level book + cross-market.
Registry: T-EN112.
