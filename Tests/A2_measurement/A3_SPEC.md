# A3 SPEC — GROUPING HIS TRADES (pre-registered; committed BEFORE any clustering runs)
STATUS: FROZEN | 2026-11-25 | Track A step A3 | Registry: T-IM44
Rows: his 307 training-month trades with features (T-IM41/42/43 table).
Nulls are not grouped - A3 asks how HIS trades differ among themselves.

## PART 1 — HAND TAXONOMY (declared here, before any cluster is seen)
Three axes, from evidence already closed (S6, A2), not from clusters:
AXIS 1 - NEWS PHASE: "news-burst" = entry 0-5 min after a scheduled
  release; "news-window" = 5-45 min; "no-news" = else.
AXIS 2 - STRUCTURE CONTEXT, by priority (most specific first, from A2
  interact rates: squeeze 73%-vs-56% is rarest, gaps/shadows 97/98%-vs-
  80/83% are near-ambient so least specific):
  "squeeze-break" if a squeeze band is interacting at entry;
  else "reaction" if a reaction edge is interacting;
  else "zone" if a gap or shadow is interacting;
  else "open-tape".
AXIS 3 - SESSION PHASE: "open" = first 90 min of RTH; "midday" =
  90-240; "late" = after 240; "overnight" = ETH entries.
A trade's hand label = the triple. Occupied cells reported with counts.

## PART 2 — CLUSTERING (Ward, 1963), blind to the taxonomy
Features (one per A2 family, the strongest by difference score - chosen
from the CLOSED A2 report, fixed here): mv15, flow1, stall_5m_extreme,
vrate900, Rest, sig_best_score, rng120, REA_int_dist, mins_open,
kme_mins_since, consec_10s, dwell120, last_bounce_ticks, approach120,
mins_since_mention.
Preparation: robust standardization ((x - median) / IQR, pooled over the
two training months - both are training, so no leakage). NaN (no edge
nearby / no prior mention) -> 0 after standardization (= the median),
plus a 0/1 was-missing flag for edge-story and mention-recency fields.
Method: Ward hierarchical clustering; k examined from 2 to 8.
Choice of k - by two pre-stated yardsticks, not taste:
  (a) mean silhouette (cohesion vs separation);
  (b) STABILITY (Hennig, 2007): 100 bootstrap resamples, recluster,
      best-match Jaccard per cluster; >=0.75 strong, >=0.6 moderate.
  Pick the largest k whose every cluster reaches 0.6; report the table
  for all k so the choice is auditable.

## PART 3 — AGREEMENT AND DISAGREEMENT
Adjusted Rand Index (Hubert & Arabie, 1985) between cluster labels and
each taxonomy axis and the full triple. Plain reading: 0 = no relation
beyond chance, 1 = identical grouping.
MANDATORY INVESTIGATION LIST: the largest sets of trades that clustering
puts together but the taxonomy splits (and the reverse) - listed
verbatim, they are A4's first candidates, not failures.

## OUTPUT
Group table (size, plain one-sentence description per group from its
median features), ARI table, stability table, investigation list.
Columns hand_label and cluster appended to the trade rows of the
feature table. Registry T-IM44. Review gate: J sees groups before A4.
