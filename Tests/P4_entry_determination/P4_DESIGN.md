# P4 — Entry Determination: design record
**Status:** active · discovery on Oct-2025 (ESZ5) + Feb-2022 (ESH2) · updated 2026-11-14

Plain-language terms used in this phase:
- **signal** — a completed 1-minute WRB (per WRB_Definition.txt)
- **zone** — an unfilled WRB Hidden Gap (WHG) that no bar has fully traded through yet
- **news event / KME** — a scheduled economic release from the committed calendar
  (`Data/inputs/kme_calendar.parquet`); "event size" = its measured typical market move
  (`kme_event_impact.csv`, median ticks moved from 1 min before to 5 min after release)
- **at his desk** — the window from 60 minutes before his first trade of the day to his
  last exit of the day (user-confirmed: he was usually at the desk 30–60 min before trading)
- **passed on** — a signal during his desk window while he was not in a trade

## Decisions on record (2026-11-14, user-approved)
1. **Desk window: 60 min before first trade** is the primary definition; 30 min is the
   cross-check. Basis: user's direct statement, not inference. Counts barely differ
   (720 vs 769 vs 797 free signals in Oct), so this choice cannot drive results.
2. **Standing caveat — "passed on" includes "possibly away".** Some skipped signals are
   absences (stepped away), not decisions. This dilutes skipped-side patterns; it cannot
   fabricate them. A stricter "definitely seen" variant (signals close in time to his
   actual order activity) is available later if needed.
3. **News importance — three-width test (approach A), user's reading leads.** The impact
   ranking showed nearly every scheduled event moves the market well beyond quiet minutes
   (user: "most if not all should be considered important" — matching Perry's own wording).
   So probes test news-proximity at three widths, side by side:
   ALL timestamped events · events ≥20 ticks median move · the biggest cluster ≥45 ticks
   (jobs/CPI/Fed). Widths were chosen after seeing the ranking — recorded as such; testing
   several widths side by side is the control for that.
   Approach C stays open: if Perry's material names specific events, that list becomes a
   fourth width. (His material is hit-and-miss on this — no dependency.)
4. **Sample for discovery:** the two months above only (both fully quality-gated). The
   full 5-year history (4,842 trades) is reserved for later validation and is UNEVEN —
   1,710 trades in 2022 vs 398 in 2023 — so validation must not assume his behavior was
   constant across years.

## Order of work
P4.2 entry characterization (descriptive — this folder's `p4_2_entry_context.py`)
→ P4.3 lock the taken-vs-skipped definitions from its output (pre-registration checkpoint)
→ P4.4 probes (one registry row each; news-width grid per decision 3)
→ P4.5 entry-rule synthesis → validation on reserved years → P&L test in the backtester.

## Zone fill rule — RESOLVED 2026-11-14 (user decision)
- The 2x disagreement was traced to one rule: WHEN a zone counts as filled. The written
  definition (WRB_Definition.txt 1.5) says ONE bar's range must sweep the whole zone;
  the October probe's CODE instead killed a zone once price had touched above the top
  and below the bottom in different bars. Evidence: swapping only that rule reproduced
  the probe's numbers from this script (1m: 61% -> 29% inside).
- User (trader knowledge): the fill rule is real, but he sometimes still trades zones
  that are already filled. DECISION: single-bar sweep is the canonical fill definition,
  and fill status is a RECORDED PROPERTY (unfilled / partial / filled at entry), never
  a filter on which zones count. Boundary case: top and bottom touched in different
  bars with no single-bar sweep = partial, by the letter of the definition.
- Provenance footnote (not a retraction): SPEC_06-10's gap-arrival population and
  T-DF22's holdout verdict were computed under the stricter cumulative rule,
  consistently in both months - they stand as findings about that construction.
- Open residual (low priority): 5m counts don't fully reconcile even under the
  cumulative rule; chase only if 5m zone work becomes load-bearing.

## Known measurement limits (recorded before any probe runs)
- "Inside some zone formed in the last 2 days" is true for ~93% of his entries at 1m -
  and very likely for most random moments too (zones form ~200+/day; nearest-zone age
  median is 12 min). Zone PRESENCE is near-universal and discriminates nothing by
  itself; only zone PROPERTIES compared taken-vs-skipped (fill state, age, timeframe,
  pointed-through) can carry signal.
- Being inside a zone mechanically raises the chance it is already "partial" (price had
  to travel into it). Taken-vs-skipped comparisons are fair because the same mechanics
  apply to both sides; absolute fill-state shares are not evidence by themselves.

## Multi-timeframe zone result (2026-11-14, p4_2b)
- User: the trader alternates 1/3/5/10/15-minute charts for zones -> all five measured.
- Convention set: fill state for every zone timeframe is judged on completed 1-minute
  bars (strictest reading of "a bar's range covers the whole zone").
- FINDING: nearest-zone presence and fill state are AMBIENT at every timeframe.
  Entries vs 4,000 random flat desk-window moments: inside-or-near 99/95/92/90/85%
  (entries) vs 98/95/93/88/86% (baseline) across 1/3/5/10/15m; fill-state splits
  nearly identical too. His entry moments do not differ from random moments on these
  measures. Consequence for P4.4 and for any strategy signal: nothing can be built on
  "a zone exists" or "the zone is filled/unfilled" alone. Candidate signals must be
  RELATIVE: properties of the specific triggering WRB/zone (size, news-proximity,
  cross-timeframe confluence, direction agreement) compared taken-vs-skipped.
- CAUTION, flagged before P4.3 locks anything: the WRB-timing nomination (61% of
  entries within 5 min of a same-direction WRB completing) has NOT yet had the same
  baseline check - same-direction WRBs complete every ~7-8 min, so a random moment
  may also often be "within 5 min". Run the identical baseline on it before treating
  timing as a trigger.

## Baseline verdicts on the candidate factors (2026-11-14, p4_3)
All measured identically for 313 entries vs 4,000 random flat desk-window moments.
- WRB timing, any direction: AMBIENT (78% vs 75% within 5 min of a completion) - dead.
- WRB timing, direction-matched: REAL BUT MODEST - 61% of entries within 5 min of a
  same-direction completion vs 46% at random moments (random side). Survives as a
  trigger component, downgraded from "strong".
- Cross-timeframe confluence BY COUNTING (inside a zone on how many of 1/3/5/10/15m):
  NULL - mean 4.25 vs 4.23; direction-matched 1.96 vs 2.11. Counting presence across
  timeframes inherits the ambience of presence. The user's confluence intuition gets
  its fair test at SIGNAL level instead (the triggering WRB's zone vs higher-TF zones,
  taken vs skipped) - presence-counting was the wrong operationalization, and this
  null does not close that question.
- NEWS-FORMED ZONES: the clearest positive gap so far. Share of points whose nearest
  1m zone formed within 30 min AFTER a >=20-tick event: entries 7% vs baseline 2%
  (3m: 4% vs 1%; all-events width 1m: 26% vs 19%; >=45tk too rare to read; 5-15m no
  gap). Minority behavior (~22 trades) but the largest relative enrichment measured.
  Directly supports the trader's stated KME-weighting of zones, at short timeframes
  and the >=20tk width. Units bug (parquet us vs ns) was found and fixed in this
  pipeline before these numbers; fix verified by selftest + manual probe.

## P4.3 locked + first taken-vs-skipped readout (2026-11-14, p4_3b)
- LOCKED: signal = flat, desk-window 1m WRB completion; taken = same-direction entry
  within 5 min (15-min cross-check kept). 1,865 signals: 179 taken, 1,686 skipped;
  60-62% of his entries are matched by a signal (the rest recorded, not dropped).
- Descriptive splits (formal tests pending): KME-born signals (completed within
  minutes after ANY scheduled event - the user's reading that effectively all events
  matter is what carries it; the >=20tk width is too thin here) are taken at roughly
  DOUBLE the base rate: e.g. within-15-min-of-event signals ~17% taken vs ~9% for the
  rest. Higher-timeframe zone overlap of the signal's own zone leans positive
  (3.27 vs 2.86 of 4 TFs; direction-matched 2.85 vs 2.52) - the user's confluence
  intuition shows daylight at SIGNAL level where presence-counting showed none.
  Body size mild (13 vs 11 ticks). "At an older KME-born level" null AS DEFINED
  (>=20tk-born levels only; may deserve the all-events width before closing).
- Next: pre-registered probes with AUC + confidence intervals, one registry row each:
  kme_born (all-events width, W grid 5/15/30), n_htf_overlap(_dir), body_tk.

## Trader-stated mechanism #2 + taken-trade anatomy (2026-11-14, p4_5a)
- USER (citing the trader's own repeated claims, clarified 2026-11-14): a KME occurs
  -> a WRB forms DURING or minutes after it -> the TOP and BOTTOM of that WRB's body
  become the price levels where his interest concentrates — **mostly on the 1-minute
  chart, sometimes 3-minute, mostly 1-minute**. ("During" is covered by the code: any
  WRB whose bar completes after the event moment counts, including the bar the event
  lands inside.) Consequence: 1m is the PRIMARY chart for this mechanism, 3m the
  secondary; 5m/15m kept only as context.
- Anatomy of all 313 taken trades (taken-only template BY DESIGN; the test is applying
  it to matching non-entered moments + reserved years):
  * 73% of entries have a 1m reaction WRB (formed <=30 min after an event) before them,
    but in AGGREGATE entries sit far from it (median 71 min later, 36 ticks from the
    nearest body edge, mostly beyond the range) - old reaction bars are not where he
    enters.
  * The FRESH subset carries the template: entries within 30 min of the reaction WRB
    (n=84, ~27% of all entries): median 9 ticks from a body edge; at 4-tick tolerance
    30% sit AT an edge (bottom 23% / top 7%) and 13% inside - and on the 5m reaction
    bar (n=40) 66% are in or at the body. Side matches the reaction WRB 60%.
  * 3m chart (added after the user's clarification): a 3m reaction WRB exists before
    81% of entries, but in aggregate entries sit far from it too (median 34 ticks);
    the fresh 3m subset is small (n=56) and shows more "inside the body" (33-43%)
    than at-edge behavior. 1m remains the carrier, matching the user's "mostly 1min".
  * SIDE-SPLIT CHECK (fresh 1m subset, 4-tick tolerance): the bottom-edge preference
    holds on BOTH sides — longs: 26% AT-bottom vs 11% AT-top (n=35); shorts: 20%
    AT-bottom vs 4% AT-top (n=49). So it is NOT just long/short composition. Caveat:
    n is small; treated as a template detail, not a cleared finding.
- TEMPLATE (draft, for forward application): event -> 1m WRB completing within 30 min
  (during or after) -> entry within ~30 min of that WRB, at/inside its body, favoring
  the lower edge, side agreeing with the WRB. PRE-REGISTERED as T-EN05 (edge distance,
  taken vs skipped, 1m primary / 3m secondary) and T-EN06 (forward application: firing
  rate, his take rate vs base rate, untaken matches described) in the registry before
  any taken-vs-skipped statistic on these quantities is computed. Honest provenance,
  recorded in both rows: the hypotheses were sharpened by looking at the taken trades
  (p4_5a), so same-months results are internal-consistency checks; the reserved years
  are the real test.

## Terminology settled + two further pre-registered tests (2026-11-15, user)
- VOCABULARY (user asked for the right collective term; documented precedent used, no
  invented words): per Tharp (1999), the simultaneous state items — event occurred,
  reaction WRB exists, zone presence, price speed — are SETUP CONDITIONS; the single
  event that times the entry (a signal WRB completing) is the TRIGGER; several
  conditions true at once is CONFLUENCE (already in use here).
- User (2026-11-15), three additions: (a) he sometimes enters INSIDE a WRB zone
  expecting a traverse to its edge and/or beyond -> T-EN07, registered on BOTH
  readings of "zone" (WHG gap zone and reaction-WRB body; user chose both since his
  usage may blur them); (b) post-KME WRBs on 1m/3m are the most interesting objects
  to him — already covered by T-EN01 (cleared) + T-EN05/06, nothing new registered;
  (c) the exit work's speed-type attributes may be part of the entry signal ->
  T-EN08, TRAILING speed only (the holdout-confirmed exit feature fav_net_vel is
  post-entry — reusing it for entries would be lookahead), read jointly with the
  already-cleared body-size cell T-EN03.
- STATUS: T-EN07/T-EN08 rows are in the registry with directions fixed; the RUN is
  held for user review (user decision 2026-11-15).

## Exit-confirmed patterns re-aimed at the time BEFORE entry (2026-11-15, user)
- USER: the patterns the exit work confirmed should be measured in the time leading
  up to his entries - taken trades first, skipped pool as yardstick only. A registry
  sweep (prompted by the user catching an incomplete keyword search) found these
  exit-side survivors beyond plain speed:
  * oriented order flow - T-DF10 0.805 / T-DF11 0.683 on holdout (best of program)
  * z-VWAP stretch - T-DF23 0.633 confirmed-weak
  * WRB body progress (T-DF21 0.871) + gap capture (T-DF22) - traverse behavior,
    already encoded in T-EN06/T-EN07, not re-registered
  * Hurst persistence sign (T-SR08 0.657, candidate-weak, never holdout-tested) -
    NOT registered; weak pedigree, revisit only if the flow/speed cells disappoint.
- Registered: T-EN09 (trailing oriented flow, 5-min primary; real aggressor-signed
  flow from the windowed tick extracts, NOT a bar proxy) and a vwap_z cell amended
  into the still-unrun T-EN08. Lookahead guard stated in both: only trailing windows
  ending at the entry/signal moment; nothing measured after it.
- DATA: the windowed extracts keep 60 min before first entry -> 5 min after last
  exit, so they cover the desk-window signals. They live on the user's Mac drive;
  Feb-2022 extract existence is verified at run time, not assumed.

## T-EN05..08 results (2026-11-15, p4_6_template.py)
- T-EN05 (distance to reaction-WRB body edge): NULL at the rule's letter — 1m primary
  0.553 [0.500,0.606], CI lower edge exactly 0.500. Direction right (taken median
  19 tk from an edge vs 30 tk skipped) but does not clear; 3m null. The LEVELS claim
  survives only as a weak lean, not a cleared trigger component.
- T-EN06 (template forward application): CANDIDATE. Template minutes (event ->
  reaction WRB -> price at/inside its body) are 5.5% of flat desk minutes, and his
  entry rate on them is 23.0% vs 10.8% elsewhere — 2.13x, holding in both months.
  90 distinct opportunities, 70% entered. BUT side agreement with the reaction WRB
  is only 57%: the template says WHEN AND WHERE he engages, not WHICH WAY. By
  construction this is internal consistency (template came from his trades);
  reserved years are the test.
- T-EN07 (room ahead inside zone/body): NULL both cells (0.511 / 0.535). Room-ahead
  is not how he selects. Secondary descriptive, kept for the exit linkage: once IN
  a matched trade, the far edge of the interval was reached 84% (zone) / 83% (body)
  of the time — consistent with his stated traverse EXPECTATION, but it shows up as
  trade management/outcome, not entry selection.
- T-EN08 (trailing tape speed): CANDIDATE, the cleanest support for the user's
  speed intuition. 60s path 0.609, 5m path 0.620 (best entry cell so far), 5m net
  0.584 — all clear. Speed-since-event and absolute VWAP stretch null. 5m path
  clearing above single-bar measures says surrounding speed adds beyond the signal
  bar's own size; joint read with body_tk (T-EN03) still owed.
- Measurement choice recorded pre-stats (p4_6 docstring): both arms use the signal
  WRB's own direction as the side (it IS the trade side for taken signals by
  construction) — supersedes the "seeded random side" wording in the T-EN07 row.
- Current cleared entry picture: KME-born timing (T-EN01) + trailing speed (T-EN08)
  + the T-EN06 template + HTF overlap (T-EN02, weak) + body size (T-EN03). Levels
  AT edges (T-EN04, T-EN05) and room-ahead (T-EN07) do not separate taken from
  skipped. What remains open before synthesis: trailing flow (T-EN09).

## Open items
- Perry-named event list (approach C) — pending user finding it in source material.
- "Definitely seen" strict variant of the skipped label — build only if needed.
- Zone tables (`whg_*_2025-10/2022-02.parquet`) are derived files present in the working
  tree but not in git (parquet rule); regenerate with `06-10_whg_fill/build_whg_series.py`.
