# A1 — FEATURE COVERAGE MATRIX + CANDIDATE ELICITATION
STATUS: LIVING | Version 1.1 | 2026-11-24 | Process: MASTER_PROGRAM Track A, step A1
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
| order book depth/refills/pulls at the level | ABSENT (book held, unused) |
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
| window PHASE (0-5 min vs 5-45 min) | ABSENT |
| pre-KME state (quiet-before-news compression) | ABSENT |
| initial reaction: direction + size of first move after release | ABSENT |
| move/range/time SINCE the KME (event-anchored windows) | ABSENT |
| HIS-mentioned KMEs vs our calendar (coverage check - he says
  "0830am KME Report"; do our calendar rows match every one he names?) | ABSENT - audit task |
| day-regime flag (KME-day vs quiet day) | ABSENT as feature |

## APPENDIX — THE EXISTING BATTERY (the "35", enumerated; all BUILT, <=t)
moves: mv8 mv10 mv15 mv20 mv30 mv45 mv60 mv120 mv300 mv900 (ticks, signed
toward direction or absolute) | ranges: rng30 rng60 rng120 rng300 rng900
rng1800 | compression: comp30 comp60 comp120 comp300 comp900 (current
window vs median of prior same-width windows) | volatility ratios: volr2
volr5 | volume rates: vrate10 vrate30 vrate60 vrate120 vrate180 vrate300
vrate900 + vratio60/120/300_30m | signed flow: flow1 flow5 flow15 |
burst activity: bursts5 bursts15 burst_silence | stall_5m_extreme |
day structure: dist_day_hi dist_day_lo day_pos mins_open | context:
Rest(=Cday x atr10) atr10 Cday kme_mins_since | signals: sig_samedir_5m
sig_best_score. Structure-interaction flags and object ages live in the
resolver, alongside these.

## PROPOSED BUILD ORDER v1.1 (reordered per J; decision J's)
1. RECENT-BARS family + LEVEL-ANCHORED family together (they meet at
   "how did the last bars behave INTO this level" - his actual view).
2. KME family expansion incl. the his-mentions-vs-calendar audit.
3. Event-anchored windows + seasonal/lunch regime anchors.
4. Volume-at-price + prior-day levels + VWAP (anchors group).
5. Order book + prints family.  6. Cross-market insync.  7. Pattern n-grams.
All through the truncation harness before entering the table (R-1).

## CHANGE LOG
- v1.1 2026-11-24: vocabulary censused (counts), bounce/retrace/dwell/
  sweep gaps surfaced, recent-bars family added + prioritized, KME family
  expanded, battery enumerated, zero-count terms corrected out.
- v1.0 2026-11-24: initial four-source elicitation.
