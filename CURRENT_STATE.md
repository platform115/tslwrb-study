## **CURRENT MODE**

**This conversation is about EXPLORATION, not validation** If we find a sign that MBP-10 data shows promise of detecting a timing area where selling/holding/something else is a good move, we will validate it later in a different chat on different data. Do not focus on sample size etc.
**EXPLORATION, not validation.** Live channel = REALIZED TRADE FLOW (action=="T", aggressor side/size), NOT the resting book. Book-direction channel is CLOSED as null (03/04/05)" — the (03/04/05) is fine (those are test names, traceability, not results), but it's borderline. I'd keep it; pointing to which tests closed a channel is environment-level traceability, not a result value.


## MBP-10 Exit-Timing Research — Exiting to avoid non-runners



## It’s important to not get bogged down in semantics -

**using the word “prediction”** is not literal, it’s just referring to evidence of probabilities being stronger, similar concepts apply across the board.

**It is assumed that there is a way to measure MBP10 data to identify a good timing for entries and exits** And to roughly explain why wrbtrader made many / all of his moves, and that we can find this in the October data.



## The main tasks at hand of 2026.06.10

** Task 1 - Build deterministic baseline → align trades → flag deviations → compare distributions
** Task 2 - Build answers for Question 2 & 3 below.
**Question 1 - Separability** Main question right now - How can MBP-10 tell target-hitters apart from cuts? - Where would that signal exist in MBP-10 data?
**Question 2 - Trade Groupings** How should trades be grouped together for comparison? Decided that trades which reached their target (WRB pt1, defined below) are in one group - “target_reached” and trades which did not reach their target and were exited before WRB pt1 reached - “failed_trades”.
**Question 3 - Comparison Windows** For exits which should be compared to find the answers in terms of differences in patterns? This will primarily be two things in the beginning - Group 1; a number of 1 min bars before an exit on a failed_trades member. Group 2 - a number of 1 min bars before a WRB pt1 opens.
**Question 4 - Reproduction:** Can cuts *similar to* wrbtrader's be reproduced from MBP-10 data? *(Needs Q1-3 to work first)*




## Definitions

WRB / WHG - See file; WRB Definition.txt

WRB pt1, WRB pt2, WRB pt3 - See file; WRB Definition.txt

- failure_tag (behavioral relabel; single-source label behavioral_relabel_<month>.parquet):
  losing_trade = realized_pnl<0 ; reached_target = NOT losing AND pt1 reached ; below_target_win =
  NOT losing AND pt1 NOT reached. Losers take priority over pt1. October = 16 / 47 / 29.
- CLEAN EXIT CONTRAST = losing_trade(16) vs reached_target(47) (= the loser spine). Use this for
  exit-signal tests. Do NOT use 52/40 for exit work — it is diluted by below_target_win (profitable
  early-exits, ~0 adverse) which collapses exit-signal separation (shown in 06-9 / 2-b).
- body_ratio(τ) = favorable NET displacement by entry+τ ÷ max |close-open| of the 3 prior 1m bars.
  Forward progress toward a WRB. (S1.)
- adverse / MAE = max price excursion AGAINST entry, points. Reactive. (S2.)
- compression_ratio(τ) = developing per-second mid range ÷ mean range of 3 prior bars. (Tested null;
  kept as a definition only, not a live signal.)
- WHG geometry: WRB_Definition.txt §1.4 is the single source. bullish WHG=[prior_body_high, close];
  bearish=[close, prior_body_low]; fill (literal) = a bar's range covers the whole zone. Built by
  build_whg_series.py (1m from es_1m_front, 5m from es_5m_front — NOT wrb_1m).
- es_5m_front is now a DEPENDENCY: add config[paths][es_5m_front] (path to es_5m_front.parquet). Same
  11-col schema as es_1m_front; resolve front month by volume (Oct=294973 confirmed).
- traversal_frac (directional) = fraction toward the far edge price reached; >=1.0 = traversed. The
  both-edges coverage definition is WRONG for entered-mid-zone trades (label bug; see below).

## File Purposes and locations on disk

# tslwrb-study — Stage 0 config
# Read with stdlib tomllib. Hand-set the [paths] and [run] dials.
# The resolved contract is NOT set here by hand — script 02 writes it to a
# machine-readable sidecar (02_resolved_<month>.json) that 03 reads.
# (See note in 02_reduce_to_windows.py on why we don't have a script edit this file.)

[paths]
mbp10_dir   = "/Volumes/2TB-Lexar/GLBX-20260606-B8YDY9S86Q"      # raw .dbn.zst live here (read-only source)
episodes    = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/chatlogs/tsl_episodes_clean.parquet"  # <-- point at your processed/ copy
es_1m_front = "/Users/joshhall/Developer/Projects/es-trading-agent-v3/Data/processed/es/es_1m_front.parquet"         # <-- point at your processed/ copy
out_dir     = "/Volumes/2TB-Lexar/tslwrb_windowed"               # windowed parquet + summaries land here (gitignored)

[run]
month               = "2025-10"   # which month of MBP-10 we are reducing
pre_entry_min       = 60          # data kept before first entry  (pad reaches into Globex by design)
post_exit_min       = 5           # data kept after last exit
chunk_rows          = 1000000     # to_df(count=) streaming chunk size; lower this if RAM-pressured
resolve_sample_rows = 5000000     # early-exit cap for front-month resolution pass (per file)
tick                = 0.25        # ES tick
recon_tol_ticks     = 1           # reconciliation tolerance in ticks (revisit to 2 only if 03 says so)

[run.resolved]
contract = "ESZ5"
windowed_parquet = "/Volumes/2TB-Lexar/tslwrb_windowed/mbp10_ESZ5_2025-10_windowed.parquet"



## What was already tested 

Lenses tested to date — ALL October in-sample, holdout-pending, none a validated edge:
- Book-direction (03/04/05): CLOSED null.
- Trade-flow LEVEL (06 exhaustion / 06b confirmation): LIVE — two FROZEN candidates (ENTRY-flow, alive).
- Price-IMPACT Kyle/Amihud (06-2): CLOSED null — volume-normalized impact does not separate cuts from
  runners; RAW price movement does (the impact ratio launders the signal out).
- Behavioral adverse-excursion / MAE (06-5/06-6): REAL exit signal = "S2" (reactive risk).
- WRB body-progress, forward (06-7): REAL exit signal = "S1" (forward "is the move building").
- Signal redundancy (06-8): S1 and S2 are INDEPENDENT and complementary (different failure modes).
- Range-compression, forward (06-9): CLOSED null / redundant with S1 — raw volatility adds nothing.
Net exit picture: the action is in DISPLACEMENT (S1) and ADVERSE excursion (S2), not flow or raw range.
Two kept exit signals (see EXIT_SIGNALS_practical_guide):
  S1 = body-progress forward, owns SLOW-FLAT duds (the move never came).
  S2 = adverse stop reactive, owns FAST violent losses + LATE reversals (price went against).
- WHG fill / structure invalidation (06-10): the in-trade-fill framing was inconclusive-by-construction
  (timescale mismatch: WHGs fill over minutes-hours, trades last minutes). REFRAMED to gap-capture.
- WHG gap-capture (06-10, the real result): SETUP is real + distinct (see below). As an EXIT signal:
  NULL on early prediction — gap-capture trades start indistinguishably and diverge LATE. No early
  exit read. Moderate (+0.46-0.59), unresolved relation to S1.

## Notes

** Realistic role of MBP-10 here:** filtering out dead/adverse trades early. Operative channel = realized trade flow; book-direction channel is closed as a separator. Orient flow features against the trade-flow self-check, not the book-imbalance population diagnostic.
** It is noted that part of the edge of wrbtrader is exit/risk management and part is entry selection. We will deal with the latter in another conversation 
** Unless otherwise stated trade inside 8am - 4pm CT are to be included in analysis.


## Data Info
- realized_pnl is in POINTS (tick-granular), NOT dollars; reconciles with extracted entry/exit at corr 1.0.
- entry_prices / exit_prices are length-1 arrays in Oct (single-entry, unscaled; n_entries=n_exits=1).
- es_1m_front = COMPLETE 1-minute OHLC series — USE for bars / ATR / range / MAE / prior-body.
  wrb_1m = WRB-ONLY (sparse; every row is a WRB) — use ONLY for pt1 / WRB grouping, never for
  contiguous-bar features.
- session_date = the within-session boundary for bar features (TR / range reset; overnight Globex
  shares the next RTH morning's session_date).
- SSD DEPENDENCY: the MBP-10 windowed parquet (run.resolved.windowed_parquet) lives on the external
  SSD. Any PER-SECOND test (impact, reproduction, body/range via mid) needs it MOUNTED; pure-bar tests
  (08, MAE-bar) do not. Drive unmounted -> per-second tests FileNotFoundError while bar tests still run
  (useful diagnostic tell).

## Durable window / feature conventions (reuse across tests)
- FORWARD-checkpoint features: read at min(entry+T, exit) (causal guard). For honest magnitude use
  STILL-OPEN-only (drop trades exited before T) — truncating-to-exit leaks the outcome into the feature.
- HAZARD-CURVE format: evaluate the feature across a τ grid on still-open trades; reports WHEN a signal
  becomes readable + cut-survival shrinkage (doomed trades exit fast -> read early). Calibration =
  P(eventual cut | feature bin/quartile) at the primary τ.
- INSTRUMENT tradeoff: per-second MID = fine timing but under-reads the true extreme; 1m bar low/high =
  true extreme but minute timing + entry-bar inclusion. Truth is bracketed between. Use mid for
  TIMING questions, bars for MAGNITUDE / baseline-purity questions.
- COMPARISON construction: Design A (cut-time-matched) for EXIT-anchored features; entry-anchored
  population AUC with cluster-bootstrap over the cut arm for FORWARD features.
- horse_race_spine.py (06 folder root) = shared machinery (grouping, Design A windows, rank AUC,
  cluster-bootstrap CI, coherence). Subtest scripts in 06-N subfolders import it via a path bootstrap.

## Gap-capture SETUP (NOTE FOR THE FUTURE ENTRIES THREAD; full detail in SPEC_06-10)
- A real, identifiable ENTRY setup: trade entered at a LIVE WHG it is pointed to fill (price returns to
  a gap and is entered as it arrives). ~34 of 92 October trades. ONE setup among several (not all his
  trades are gap-arrivals; some are WRB-continuation alone).
- Distinct, higher-quality set: only 4 losers of 34 (~12% vs 17% baseline); skews to winners.
- Trades overwhelmingly traverse (29/34) and run PAST the gap (median 1.67x zone, ~62% >150%). The gap
  is a LAUNCH level, not a target. Winners run far (median 3.43x) vs stalls (1.67x).
- Replicable population rule (5m primary): live WHG (formed within validity window, unfilled at entry,
  dead on traversal) with entry INSIDE or NEAR (<=8 ticks) the zone AND pointed THROUGH it. Validity
  window window-insensitive (1/2/3d ~same; use 2d).
- This is ENTRY/selection knowledge, NOT an exit signal — the exit work (S1/S2) is separate and general.
  
## Standing notes
- 06-10 SUPERSEDED SCRIPT: test_gap_traverse_exit.py had a both-edges-coverage LABEL BUG (false 6/34);
  superseded by test_gap_capture_v2.py (directional, 29/34). All v1 results invalid. Kept for provenance.
- LESSON: run the DESCRIPTIVE distribution before the inferential test — gap_traverse_distribution.py
  exposed the v1 label bug that the test itself hid.

## (Keep) Next: HOLDOUT. The exit-signal exploration (S1, S2), the frozen entry-flow candidates, AND the
## gap-capture setup all now go to new-data validation, where n grows. De-Octoberize first (front month
## by volume; parametrize month/instrument; drop Oct count asserts).

## Latest Test Info
** Durable measurement facts (add):

** Queue-imbalance orientation: bid-heavy=up (continuation), sign +1; strongest at L1, ~1s-scale, decays to chance by ~60s. Book level/slope does NOT separate the groups (book-direction channel closed). Use for orientation only.
** Signed trade-flow convention: signed_flow = buy_vol(side=="B") - sell_vol(side=="A"), oriented x(+1 long/-1 short); >0 = pressure WITH the trade. Sizes uint32 -> int64 before arithmetic.
** Microprice (Stoikov 2018) = size-weighted mid; untested book-price-implication channel, distinct from raw imbalance.

** Orientation-check rule: validate any book-feature's sign on the per-second population at ~1s, not via window-mean-vs-window-change on the trade windows — that long-horizon/small-n stat is miscalibrated (it produced a spurious −0.357 in Test 03).
** MBP-10 book columns confirmed: bid_px_00 < ask_px_00 100%, spread 0.25; bid_sz_00..09/ask_sz_00..09 = per-level resting size (uint32→int64). Oct windowed file ≈ 73.7M snapshots; per-second grid ≈ 256k (~71 grid-hours).

** Standard window definitions (add — reuse across all feature tests):

** Anchor = pt1 bar (reached) / floor(exit) (failed or loser). Feature normalization: PER-SECOND (windows variable length). Per-bar collapse abandoned (most windows are 1 bar).
** 180s per-second windows (3 variants): A1 pre-entry [entry-180s, entry); A2 in-trade [max(entry,anchor-180s), anchor); B no-floor [anchor-180s, anchor). B is length-confounded -> always report pre_entry_frac median-split as the artifact check.
** EARLY entry-anchored FORWARD window: [entry, min(entry+60s, exit)) -- forward-predictive; causal guard min(...,exit) = never reads past trade close.
** CONTROL "Design A" (cut-time-matched): 60s trailing; each failed/loser cut vs reached peers still open & pre-pt1 at the same elapsed tau. Per-cut AUC + cluster-bootstrap CI.
** Validity rules: tripwire = flag/exclude a window if in-window gap >120s OR |mid jump| >40 ticks; firing floor = >=8 VALID firings (window <2s -> NaN, never a 1-snapshot value).
** Groupings (two; they answer different questions):
**   (a) Reading B inclusive pt1 -> 52 target_reached / 40 failed_trades (runner / non-runner) [OCT-2025 ONLY].
**   (b) Loser spine -> losers (realized_pnl<0) vs non-loser reached. MANDATORY DE-DUPE: losers that are also target_reached stay in the loser arm and are REMOVED from the comparison arm (else a trade is compared to itself and inflates AUC).
**   Pick by signal type: adverse/exit signals -> loser spine; runner-confirmation signals -> 52/40. (52/40 inverts for adverse signals: most failed_trades are profitable early-exits, not losers.)

## CURRENT Next recommended tests (OPEN candidates — suggestions, not constraints)
- WHG fill / structure invalidation: genuinely new mechanism (structural, not progress/adverse).
  CAUSAL HAZARD — WHG fill-status is forward-looking; the fill must be measured strictly BEFORE the
  exit decision or it reads the future.
- VWAP / session-reference: generic (non-WRB) baseline competitor — does an institutional default
  match the kept signals? Low fit, baseline role only.
- Combined-rule winner-kill: S1+S2 tested for loser-overlap (06-8) but NOT for combined FALSE-POSITIVE
  rate on winners — measure before treating "use both" as net-positive, not just complementary.
- Holdout / new-data validation of S1, S2, and the frozen entry-flow candidates (the real test).
Nothing above is a constraint on what may be explored next; findings are in-sample hypotheses and
high in-sample numbers fail out-of-sample most often.

## Standing debt
- OCTOBER-HARDCODE: spine self-test, relabel, behavioral baseline assert Oct counts; INSTRUMENT_ID /
  MONTH / SYMBOL hardcoded in trade_flow_exhaustion.py. Fail-loud off-October BY DESIGN. De-Octoberize
  (resolve front month by volume; parametrize month/instrument; drop the count asserts) before holdout.
- DOC DEBT: per-test SPECs for 06-6..06-9 not yet written; SPEC_06-2/06-3/06-5 + EXIT_SIGNALS guide not
  yet placed in their folders.
- Claude prediction-calibration note (meta): Across this session Claude repeatedly forecast murkier / more-redundant / more-deflated / null results than the data delivered — wrong ~5×, including on sign (e.g. predicted redundancy corr ≈ −0.4 to −0.6; actual +0.03). When Claude hedges toward "it's probably murkier than it looks," weight that against a demonstrated bias toward under-calling clean results. Let the numbers talk; treat Claude's magnitude/direction pre-guesses as near-uninformative.
## ADD to "lenses tested to date":
- VWAP / session-reference (06-11, baseline competitor — NOT his-method): DAILY anchor weak (~0.64,
  marginal). ROLLING anchor strong, stronger at SHORT N: z-scored, N~15-20, ~0.78 @60s clean, MONO
  calibration — as strong in-sample as S1, for a "low-fit" baseline. Momentum-flavored (favorable
  extension -> reached), not mean-reversion. Moderately correlated with S1 (+0.42 at N=30 raw) ->
  semi-independent, catches ~2 losers S1 misses. NOT a his-method signal; a candidate to BEAT in holdout.

## UPDATE the kept-signals picture:
There are now THREE in-sample "is-it-working" exit candidates (all ~60s, forward, clean population,
holdout-pending, none validated):
  S1 = body-progress (displacement vs prior-bar body) — owns slow-flat duds.
  S2 = adverse excursion (points against entry) — owns fast violent losses + late reversals.
  VWAP-dist = short-rolling, z-scored extension vs recent volume-weighted mean — momentum-flavored,
    semi-independent of S1. (Generic, not WRB-specific.)
They are partially independent (S1 vs S2 corr +0.03; S1 vs VWAP +0.42). Whether they survive and how
they combine is the holdout question.

## ADD — Definitions / data
- VWAP feature: vwap_dist = (mid - VWAP)*side_sign at tau; z = /rolling_sigma. Anchors: daily
  (session_date reset) and rolling-N (trailing N 1m bars). typical=(H+L+C)/3. N is a free parameter;
  short-N (~15-20) is the robust plateau. Built in 06-11 from es_1m_front + per-second mid.
- DISCIPLINE NOTE (overfitting): the N-sweep is a STABILITY diagnostic, not an optimizer. A monotone/
  plateau N-curve rules out single-N luck but NOT whole-sample luck (all N read on the same 13 losers).
  Any N for use = pre-registered from the plateau (not the in-sample peak) before holdout.

## ADD — Claude prediction-calibration note (extend existing): the "low-fit/weak/redundant" lean was
wrong AGAIN on VWAP (predicted correlate-at-best; got ~0.78, semi-independent). Now ~6 misses this
direction. Treat Claude's "probably weak/redundant" pre-guesses as near-uninformative; let numbers talk.

## (Keep/extend) Next: HOLDOUT now covers S1, S2, rolling-VWAP-dist, the frozen entry-flow candidates,
## AND the gap-capture setup. De-Octoberize first. Also still-unmeasured: COMBINED-rule winner-kill rate
## (S1+S2[+VWAP] together clip how many winners?) — needed before any "use together" is net-positive.
