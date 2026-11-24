# A1 — FEATURE COVERAGE MATRIX + CANDIDATE ELICITATION
STATUS: LIVING | Version 1.4 | 2026-11-24 | Process: MASTER_PROGRAM Track A, step A1
Purpose (plain): the complete list of what we measure, what we could
measure, and where each candidate came from. OPEN list - J adds any time.
v1.1: vocabulary now CENSUSED from his 31,838 messages (counts shown),
not recalled; recent-bars family added and prioritized; KME family
expanded; level-anchored family expanded; full existing battery
enumerated as the baseline (J's corrections, 2026-11-24).

## SOURCE 1 — HIS WORDS, COUNTED (occurrences in his messages -> measurement)
| term (count) | candidate measurement | status |
|---|---|---|
| wrb (3328) | WRB flags/bodies/completion | BUILT |
| pt1/pt2/pt3 (1887) | WRB occurrence sequence in-trade | BUILT (exits) |
| | WRB formation CADENCE pre-entry (same/opposite dir per last N min) | ABSENT |
| kme (1325) / key kme (1068) | see KME family below | PARTIAL |
| volatility (1323) / contracting (358) | compression, squeeze episodes | BUILT |
| zone (1192) / s area (729) / r area (630) | zone bands + role edges | BUILT |
| range (402) | range measures, tight-range bands | BUILT |
| bounce (391) | REJECTION events at a level: size, speed of the bounce | ABSENT (his 4th most-used action word - never measured) |
| break/broke (317) | break events + follow-through shape | PARTIAL (interaction built; shape not) |
| signal (301) | score engine | BUILT |
| shadow (287) | shadow intervals | BUILT |
| squeeze (220) | squeeze bands | BUILT; squeeze-BREAK event anchoring ABSENT |
| retrace (128) | retracement depth/speed toward a level after a move | ABSENT |
| hidden gap (126) | gap zones + fill state | BUILT |
| alert (121) | approach events toward watched levels | PARTIAL |
| insync (99) / key markets (73) | cross-market agreement | ABSENT |
| support (94) / level (91) / test (87) / held (86) | per-level test count | BUILT |
| | per-level hold-vs-break HISTORY + rejection magnitudes per test | ABSENT |
| reaction high/low (81) | swing/zigzag levels | BUILT |
| lunch (72) | time-of-day regime anchor (he marks lunch explicitly) | ABSENT as feature |
| roll (42) | roll-day handling | BUILT (exclusion) |
| battle (37) / sticky (12) | prolonged dwell at a level: DWELL TIME per test | ABSENT |
| stall (30) | stall/alive-gap state | BUILT |
| approach (27) | approach velocity/acceleration INTO a level | ABSENT |
| runner (23) | trade-type label (management) | NOTED |
| sweep/stops (15) / take out (9) | liquidity sweep: pierce level then reverse | ABSENT |
| hesitation (15) | pre-break pause at level | ABSENT (= dwell) |
| flip role (12) | S<->R role-flip events | PARTIAL |
| clue (11) / confirmation (8) | staged-evidence sequencing | NOTED (labels) |
| momentum (8) / quiet (6) / grind (5) | tape-state words | BUILT (battery) |
| midpoint (3) | zone-midpoint coincidence | ABSENT |
| vtr (3) | second system | OPEN question |
(Zero-count checks: reject, defend, rip, thin - he does not use these;
my v1.0 list had invented emphasis. Corrected by the census.)

## SOURCE 2 — THE TRADED PRICE AREAS (measure the LEVEL'S OWN STORY)
| candidate | status |
|---|---|
| approach velocity/acceleration into the level | ABSENT |
| approach shape (weakening bounces into it) | ABSENT |
| dwell time within x pts, per test | ABSENT |
| rejection magnitude + speed per prior test | ABSENT |
| time between successive tests | ABSENT |
| first-touch vs later-touch behavior difference | ABSENT |
| volume at tests vs ambient; volume trend across tests | ABSENT |
| VOLUME-AT-PRICE / volume profile around the level (high-volume nodes) | ABSENT (standard: Steidlmayer market profile family; POC/value area) |
| order book at the level | ABSENT. v1.4 audit: held columns are top-of-book + 10-level totals (bid0/ask0/bid10/ask10, 2 months) - supports imbalance and thinning measures; pull/refill events would need raw MBP-10 reprocessing |
| large prints at the level | ABSENT |
| stacked-level ladder density (how many levels within y pts) | ABSENT |
| zone-midpoint coincidence | ABSENT |
| level formation session (RTH vs overnight) + formation time of day | ABSENT |
| virgin status (never touched since formation) | BUILT |
| gap-over-the-level events | ABSENT |
| confluence count | BUILT (no separation found) |
| round numbers | BUILT (no effect) |
| position in day structure (dist day hi/lo, day range %) | BUILT |
| prior-day levels (y'day H/L/C, overnight H/L) | ABSENT |
| VWAP distance/side | ABSENT |

## SOURCE 3 — RECENT BARS (last 1-20 bars, 1m and 1s scale) [J: this is
## where a trader actually looks - prioritized above generic anchors]
| candidate | status |
|---|---|
| per-bar body/wick ratios, sequence of last N bars | ABSENT |
| consecutive same-direction closes count | ABSENT |
| inside/outside bar flags, last N | ABSENT (NR-k BUILT) |
| bar-volume pattern last N bars (rising/falling) | ABSENT |
| last swing LEG stats (length, duration, speed) | PARTIAL |
| short-window continuation-vs-revert tendency | ABSENT |
| 1-second "bars": the same measures on 1s aggregation | ABSENT |
| the existing mv/rng/comp ladder (8s..30min) | BUILT |

## SOURCE 4 — KME FAMILY (expanded per J)
| candidate | status |
|---|---|
| in-45-min window flag + minutes-since | BUILT |
| KME TYPE (which report: CPI/FOMC/claims/...) | ABSENT (calendar holds it; never a feature) |
| KME importance tier | ABSENT |
| KME SURPRISE: actual vs forecast (the calendar already stores actual/forecast/previous - never used as a feature; macro-surprise is a standard, documented driver) | ABSENT - audit found the columns unused |
| window PHASE (0-5 min vs 5-45 min) | ABSENT |
| pre-KME state (quiet-before-news compression) | ABSENT |
| initial reaction: direction + size of first move after release | ABSENT |
| move/range/time SINCE the KME (event-anchored windows) | ABSENT |
| HIS-mentioned KMEs vs our calendar (coverage check - he says
  "0830am KME Report"; do our calendar rows match every one he names?) | ABSENT - audit task |
| day-regime flag (KME-day vs quiet day) | ABSENT as feature |

## SOURCE 5 — THE AREAS HE MARKED, WITH HIS OWN LABELS (J's catch, v1.3:
## this was built in the structure program and then LEFT OUT of this matrix)
What exists, verified against the data files:
- his parsed references: 5,155 marked areas with kind (wrb 1,912,
  key_kme_wrb 1,111, level_sr 513, contraction 310, shadow 268,
  hidden_gap 119, ...), role (S/R), relation, direction, TF, stated price.
- reference->object links: 7,533 matches of his references to specific
  chart objects, with distance and object age (s4_ref_links).
- his action labels: 5,207 entry messages, 5,174 exit messages, 21,457
  commentary messages - he labeled his own data for us.
- acted-vs-ignored edge properties (S6.4, one month): KME-window 42% vs
  10%; age/confluence/round-number/tested-count showed no separation.
- displacement (fill vs trigger edge): measured; the entry-price rule.
- lifetimes (S4): ordinary structures die intraday; stated Key zones
  live weeks-months.
| candidate measurement | status |
|---|---|
| was the entry inside/near an area HE had already named (same session or earlier)? talk->trade lag, count of prior mentions, which kind he called it | ABSENT. HONEST CAVEAT (v1.4 audit): only 146/5,155 refs carry an explicit stated price - the linkage must run refs->linked objects->edge prices (7,533 links exist), not stated prices alone |
| his own interaction labels: relation column - "reached" (1,270), "at/near" (416), "broken" (238), "squeeze" (211) - HE classified the interactions; compare against our detector's classification | ABSENT |
| his importance labels: tier column - "key" (1,092) vs "small" (292) | PARTIAL (key-zone work used stated prices only) |
| which TF he is working on at entry/exit moments (his_tf_mentions has ctx_entry/ctx_exit flags - never joined to trades) | ABSENT |
| areas he named and did NOT trade: what distinguishes them from named-then-traded (his own ignored set, vs our mechanical one) | ABSENT |
| his conditional plans - "if it ..." (60), "looking for" (22), "watching" (47): parse the stated condition, test whether his next action matched it | ABSENT - direct rule elicitation from his words |
| explicit negatives: "no trade" (98), "missed" (128), "waiting" (22) as labeled no-entry moments with full feature vectors | ABSENT |
| per-area mention count / emphasis / correction history as an importance score (vs the failed implied-list approach, S5b) | ABSENT |
| acted-vs-ignored properties on ALL months, not one | ABSENT (built 2025-10 only) |
| his chat-activity rate around entries | ANALYSIS-ONLY - explains misses; can never be a live entry input (not knowable without him) |
Assets: his_zone_refs, s4_ref_links, s4_objects (3.34M objects),
wrb_messages, his_kme_times (for the Source 4 audit), his_signal_stamps.

## SCOPE NOTE (v1.4 audit) — THE SAMPLE IS LARGER THAN THE PROGRAM ASSUMED
The episode file holds 4,842 of his trades across 60 months (2021-05 to
2026-05), and his messages span the same range. Per-second data exists
for only 4 months, but every Source 5 measurement (talk->trade linkage,
named-but-untraded, conditional plans, relation labels) needs only
message timestamps + 1m bars. DECISION FOR J (R-3, not taken silently):
do Source 5 analyses run on the full corpus, or does the training/
validation month discipline extend to them? Proposal: explore on all
months EXCEPT the quarantined validation months; any RULE fitted from
the findings still validates only on quarantined data.

## LABELS ARE NOT FEATURES (kept separate so X and y never mix)
This matrix lists candidate INPUTS (X). The OUTCOMES (y) live apart:
his realized P&L / exits / hold times (episodes), the M1-vs-his
dissection, and the triple-barrier outcomes B1 will compute. A feature
may never be computed from the trade's own outcome.

## APPENDIX — THE EXISTING BATTERY, DEFINED IN PLAIN LANGUAGE (all BUILT, <=t)
Price movement
- mv8..mv900: how far price moved over the last 8s / 10s / 15s / 20s /
  30s / 45s / 60s / 2min / 5min / 15min, in ticks; measured toward the
  trade's direction when one is given.
- rng30..rng1800: the distance between the highest and lowest price over
  the last 30s / 1 / 2 / 5 / 15 / 30 minutes.
- comp30..comp900: the current window's range compared with the typical
  recent range of the same width - below 1.0 means quieter than usual,
  above 1.0 wider than usual (the "contraction/expansion" measure).
- volr2, volr5: how jumpy second-to-second prices are in the last 2 / 5
  minutes relative to the last 30 minutes.
Volume and order flow
- vrate10..vrate900: contracts traded per second over the last 10s ... 15min.
- vratio60/120/300_30m: that trading rate compared with the last half
  hour's average (above 1.0 = busier than the recent norm).
- flow1, flow5, flow15: buying minus selling pressure per second over the
  last 1 / 5 / 15 minutes (positive = buyers hitting the offer harder).
Burst activity
- bursts5, bursts15: how many fast price bursts occurred in the last 5 /
  15 minutes (a burst = an 8-second move larger than a session-scaled
  threshold).
- burst_silence: seconds since the last burst.
- stall_5m_extreme: seconds since price last set a new extreme (in the
  relevant direction) within the past 5 minutes.
Day structure and context
- dist_day_hi, dist_day_lo, day_pos: distance to today's high and low,
  and where price sits inside today's range (0 = at the low, 1 = at the high).
- mins_open: minutes since the session open.
- atr10: the average size of the last 10 completed 1-minute bars (the
  bar-size yardstick).
- Cday, Rest: a session-scale multiplier learned from prior sessions, and
  Cday x atr10 = the expected movement scale for this session.
- kme_mins_since: minutes since the last scheduled news event.
Signals
- sig_samedir_5m, sig_best_score: whether a score>=6 signal in the trade's
  direction completed within the last 5 minutes, and its best score.
Structure-interaction flags and object ages (which level/zone was crossed
or rejected, how old it is) live in the resolver beside these.

## BUILD ORDER — RANKED BY A STATED RULE, NOT PREFERENCE
Ranking rule (standard research triage): expected relevance to HIS
behavior (from the census counts and prior findings) x how much we trust
the data, divided by build cost. Ratings shown so the order is auditable
and J can overrule any line.
| family (plain name) | what it measures, plainly | relevance | data trust | cost | order |
|---|---|---|---|---|---|
| HIS marked areas + his own labels | entries vs areas he named (talk->trade), named-but-untraded areas, his "if it" conditions vs his actions, explicit no-trade moments | HIGHEST (his own labels; 5,155 refs + 10,381 action messages already parsed) | HIGH | LOW | 1 |
| Recent bars + the level's story | how the last 1-20 bars behaved coming INTO a level: bounces, dwell, weakening tests, bar shapes | HIGH (bounce 391, break 317, battle/hesitation ~60) | HIGH | MED | 2 |
| News-event (KME) family | which report, its phase, pre-news quiet, first reaction, move-since-event; plus the audit: does our calendar contain every KME he names | HIGH (kme words ~2400; 4x enrichment already proven) | HIGH | LOW | 3 |
| Time-of-day regimes | open phases, lunch, event-anchored clocks instead of fixed windows | MED | HIGH | LOW | 4 |
| Cross-market agreement | are NQ/YM/VIX moving with or against ES ("insync" - his word, 99+73 uses) | HIGH (he names it) | MED (needs data alignment work) | MED | 5 |
| Standard price anchors | VWAP, yesterday's high/low/close, overnight range, volume-concentration prices | MED (field-standard; he never names them - census: 0) | HIGH | LOW | 6 |
| Order book + large trades | depth, pulls and refills at levels; big prints hitting them | HIGH as a hypothesis (the unexplained drift trades) | MED (held for 2 months only) | HIGH | 7 |
| Bar-shape sequences | encoding what the last few candles look like as repeatable patterns | MED | HIGH | HIGH (easy to fool ourselves; strict controls needed) | 8 |
Rank 1 is new in v1.3: his own labels are the only feature family where
relevance is not inferred - he wrote it down - and the parsing cost is
already paid. Note the honest tension at ranks 5-6: he names cross-market and never
names VWAP, so relevance puts insync first even though anchors are
cheaper. J may reorder any of this; the ratings are the argument, not
the verdict. Every family passes the truncation harness before entering
the measurement table (R-1).

## CHANGE LOG
- v1.4 2026-11-24: mechanical asset audit (ASSETS.md created). Found: KME
  surprise columns unused; his relation/tier labels unused; tf-mention
  entry/exit context unused; 60-month / 4,842-trade scope note + R-3
  decision for J; stated-price caveat (146/5,155); order-book holding
  corrected to what the columns actually support; labels-vs-features
  separation stated.
- v1.3 2026-11-24: SOURCE 5 added - his marked areas with his own labels
  (zone refs, ref->object links, entry/exit messages, no-trade census,
  conditional plans); was built in the structure program and omitted from
  this matrix (J's catch). Build order re-ranked: his-labels family = 1.
- v1.2 2026-11-24: battery appendix rewritten with plain-language definitions; build order rewritten with a stated ranking rule and auditable ratings (J's corrections).
- v1.1 2026-11-24: vocabulary censused (counts), bounce/retrace/dwell/
  sweep gaps surfaced, recent-bars family added + prioritized, KME family
  expanded, battery enumerated, zero-count terms corrected out.
- v1.0 2026-11-24: initial four-source elicitation.
