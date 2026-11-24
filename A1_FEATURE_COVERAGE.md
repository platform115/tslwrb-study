# A1 — FEATURE COVERAGE MATRIX + CANDIDATE ELICITATION
STATUS: LIVING | Version 1.0 | 2026-11-24 | Process: MASTER_PROGRAM Track A, step A1
Purpose (plain): the complete list of what we measure, what we could
measure, and where each candidate idea came from - so "he sees something
we don't" is always a specific unbuilt row, never a vague worry.
Method: elicitation from four sources (no statistics in this step).
Review: J approves/edits the list and picks the build order.
This list is OPEN - J adds candidates at any time; nothing is removed,
only marked.

## SOURCE 1 — HIS OWN WORDS (each term -> a measurable)
| his term / behavior | candidate measurement | status |
|---|---|---|
| "volatility spike" | compression ratios, multi-window moves | BUILT (failed as an entry gate - T-IM33; still valid as a feature) |
| "contracting volatility" / "tight range" | squeeze episodes W=10/15/30 | BUILT |
| "most recent" (gaps, shadows, reaction levels) | object age at the moment | BUILT |
| Key zone "importance" (color tiers) | zone age, times re-referenced, multi-day persistence, size | PARTIAL (reference counts exist; persistence scoring not a per-moment feature yet) |
| "insync" with other key markets | NQ/YM/VIX direction agreement over several windows | ABSENT (data held, never built) |
| "WRB pt1/pt2/pt3" | WRB formation cadence before entry (how many WRBs in last N min, same/opposite direction) | ABSENT |
| price "testing / holding / breaking" an area | per-level test count today | BUILT (edge properties) |
| | per-level hold-vs-break HISTORY (how did the last k tests resolve) | ABSENT |
| hesitation at a level | DWELL TIME within x pts of the level per test | ABSENT |
| "follow through" after a break | post-break continuation over 1-5 min, retest-or-run shape | PARTIAL (displacement exists; shape does not) |
| his price alerts | level-approach event: crossing distance bands toward a watched level | PARTIAL |
| "early entry / poor entry" self-grades | label quality anchors for B-track labeling | NOTED (labels, not features) |

## SOURCE 2 — THE TRADED PRICE AREAS (point-centric: measure the LEVEL, not just the tape)
| candidate | plain meaning | status |
|---|---|---|
| approach velocity/acceleration INTO the level | how fast price came at it, speeding up or stalling | ABSENT (move ladder exists but is not level-anchored) |
| approach pattern shape | e.g. successively weaker bounces into support before the break | ABSENT |
| volume at tests vs ambient; volume trend across successive tests | is the defense thinning | ABSENT (volume rates exist, not level-anchored) |
| order book depth at/near the level; refills vs pulls | is the level real in the book | ABSENT (book data held 2 months, never used) |
| large prints at the level | who hit it | ABSENT (prints held, never used) |
| confluence count across structure families | BUILT (no separating power found so far - T-IM32) |
| round-number coincidence | BUILT (no effect found - T-IM32) |
| level's position in day structure (distance to day high/low, day range %) | BUILT |
| distance to VWAP | the most standard intraday anchor in the field - we have NEVER computed it | ABSENT |
| level vs prior-day levels (yesterday's high/low/close, overnight high/low) | standard floor-trader anchors - never computed | ABSENT |

## SOURCE 3 — STANDARD QUANT FEATURE FAMILIES NOT YET PRESENT
| candidate | source | status |
|---|---|---|
| VWAP + distance/side | standard practice | ABSENT |
| order flow imbalance from the book | Cont, Kukanov & Stoikov 2014 | ABSENT |
| signed trade flow | built already | BUILT |
| short-window trendiness (does the last move keep going or revert) | standard (autocorrelation) | ABSENT |
| event-anchored windows: move/range/time SINCE the KME, SINCE the squeeze break, SINCE session open | replaces fixed windows with his-style anchors | PARTIAL (mins-from-open, KME-minutes exist; move-since-event does not) |
| time-of-day seasonal baseline (is this volume/speed high FOR THIS TIME OF DAY) | standard seasonality normalization | ABSENT |
| swing-leg statistics (length/duration/speed of the last zigzag leg) | from our own G3 machinery | PARTIAL |
| bar-pattern sequences (what the last 3-5 candles look like, as a pattern) | he reads candles; standard pattern encoding | ABSENT |

## SOURCE 4 — OUR OWN FINDINGS, NOT YET TURNED INTO FEATURES
| candidate | origin | status |
|---|---|---|
| day-regime flag (KME-day vs quiet day) | the Oct-1 vs Oct-17 day maps (T-IM32) | ABSENT as a feature |
| his sequence context (time since his last trade, last trade's outcome) | attention realism work | ABSENT |
| signal score (>=6) | strongest separator found | BUILT |
| structure-interaction flags per family | S6.2 | BUILT |
| entry displacement from trigger level | T-IM31 | BUILT |
| stall/alive-gap state | M1 research | BUILT |

## COVERAGE MATRIX (summary view)
| data source \ measurement type | speed/range | volume | flow | structure/levels | event-anchored | sequence/pattern |
|---|---|---|---|---|---|---|
| 1m bars | BUILT | BUILT | - | BUILT | PARTIAL | ABSENT |
| per-second mids | BUILT | - | - | BUILT | PARTIAL | ABSENT |
| per-second volume/flow | BUILT | BUILT | BUILT | ABSENT (not level-anchored) | ABSENT | ABSENT |
| order book (2 months) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT |
| trade prints | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT |
| cross-market (NQ/YM/VIX) | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT | ABSENT |
| his messages | mined (structure refs) | - | - | BUILT (refs DB) | PARTIAL | PARTIAL |
| KME calendar | BUILT (window flag) | - | - | - | PARTIAL | - |

## PROPOSED BUILD ORDER (for J's decision - reasons stated, not bindings)
1. LEVEL-ANCHORED group (approach velocity, dwell, test-history, volume-
   at-level): directly serves the areas he trades around; uses data we
   already trust; most likely to create "detectable and unique patterns"
   at his points, per J's direction.
2. EVENT-ANCHORED windows (since-KME, since-break, seasonal baseline):
   cheap on existing data; his trading is visibly event-structured.
3. VWAP + prior-day levels: standard anchors, embarrassingly absent.
4. ORDER BOOK + PRINTS family: the biggest untouched data; candidate
   explanation for the drift remainder; most build effort.
5. CROSS-MARKET insync: his explicit vocabulary; needs data prep.
6. Bar-pattern sequences: hardest to do honestly; last.
Every new feature passes the truncation harness before entering the
measurement table (R-1).

## CHANGE LOG
- v1.0 2026-11-24: initial elicitation from four sources.
