# FROZEN CANDIDATE — early_flow_confirmation (HOLDOUT SPEC)
Status: FROZEN 2025-10 (discovery). Pre-registered for out-of-sample holdout validation.
Self-contained: a fresh chat with this doc + CURRENT_STATE.md + WRB_Definition.txt can rebuild and
validate it with no other context. NOTHING below may be re-tuned on holdout data — that is the point
of freezing. If a parameter is changed, it is a NEW candidate and this record is void.

This is the CONFIRMATION face of the realized-trade-flow channel — the independent complement to the
FROZEN in_trade_flow_exhaustion candidate (which is exit-anchored, backward, loser-specific). The two
are pre-registered as CANDIDATE COMPLEMENTARY INDICATORS, to be tested separately AND combined ONLY on
the holdout — never composed/optimized on the discovery month. See §10.

===============================================================================
## 1. ONE-LINE CLAIM
Directional aggressor trade-flow BUILDING in the FIRST 60s of a trade confirms it will RUN to target.
Entry-anchored, FORWARD-looking (the only forward-predictive test in the project). Realized-trade
channel (action=="T", aggressor side, size) — the channel is live (self-check +0.72); the resting-book
channel (Tests 03/04/05) was null.

## 2. DISCOVERY RESULT (October 2025 ESZ5, 52 target_reached vs 40 failed_trades) — what froze it
- Channel LIVE: corr(mean oriented flow, oriented mid change) over B = +0.72.
- PRIMARY (frozen candidate): EARLY-ENTRY [entry, +60s) oriented LEVEL = 0.672, 95% CI [0.580, 0.759]
  — CI lower bound clears 0.5 by a comfortable margin (wider clearance than the exhaustion candidate).
  Median oriented early flow: reached +3.6 vs failed +0.8 (a location shift, not just tails).
- CONFIRMING: EARLY-ENTRY oriented SLOPE = 0.621 (same direction).
- INDEPENDENCE from the exhaustion candidate (why the two can compose): different WINDOW (entry-forward
  vs exit-backward), different POPULATION (52/40 vs loser spine), different DIRECTION (building vs fading).
- COHERENCE (evidence it is not a fluke): signal localizes to the early in-trade window. PRE-ENTRY A1
  INVERTS (0.377) and no-floor B INVERTS (0.357, both pre_entry strata <0.5 -> composition artifact
  ABSENT). A2 in-trade LEVEL also inverts (0.398) — the early window, not the run-up, is where the
  BUILDING signal lives (the run-up is where the exhaustion FADE lives; cf. the other candidate).
- WINDOW CONDITIONING: every trade has a usable early window (0 trades < 2s; only 10/92 truncated by a
  short hold, min span 31s). Best-conditioned window in the project — no degeneracy.
- CAVEATS carried into holdout:
  * In-sample, n=40/52. Treat as "CI-positive / promising", NOT "0.67".
  * FIRING MAGNITUDE adds little: confirmation flag (level>0) fires 40/52 reached vs 21/40 failed
    (runners fire more), BUT AUC on the FIRED subset is only 0.572 — the signal is WHETHER early flow
    builds, not HOW MUCH among those that build. A binary confirm-flag is weakly useful; do not sell magnitude.
  * LEVEL is the early-window statistic; SLOPE is the in-trade statistic (cross-test pattern: early reads
    favor level, in-trade reads favor slope). Keep them window-specific; do not bundle.

## 3. PRE-REGISTERED HOLDOUT DECISION RULE (frozen — declare before touching holdout data)
- PRIMARY statistic = EARLY-ENTRY [entry, +60s) oriented LEVEL, contrast 52 reached vs 40 failed.
  PASS if its 95% cluster-bootstrap CI lower bound > 0.5 on the holdout month.
  (Per-failed AUC vs all reached, cluster bootstrap over the failed arm; = the CONTROL line in §9.)
- CONFIRMING statistic = EARLY-ENTRY oriented SLOPE. Supportive if AUC > 0.5 same direction.
- Candidate VALIDATES only if PRIMARY passes. Confirming strengthens but cannot rescue a failed primary.
- Direction fixed: AUC(reached oriented flow > failed). No re-orientation post-hoc.
- A2 slope is NOT part of this candidate (different window/signal — it belongs to the exhaustion family).
- Freeze rule: a high AUC counts only on >= 8 VALID firings per arm (valid = defined feature; >=1 sec
  level / >=2 sec slope; <2s window -> NaN). Confirmation fire trigger = oriented level > 0 (building).

## 4. FEATURE DEFINITION (frozen formula — IDENTICAL to in_trade_flow_exhaustion; only window/direction differ)
Per snapshot keep trade prints only (action=="T"); aggregate to ONE row per SECOND:
    buy_vol_s  = sum(size where side=="B")       # buy-aggressor volume that second  (int64)
    sell_vol_s = sum(size where side=="A")       # sell-aggressor volume that second (int64)
    mid_s      = last (bid_px_00 + ask_px_00)/2 that second
Per-second signed flow, oriented to the trade:
    signed_flow_s = buy_vol_s - sell_vol_s
    oriented_s    = signed_flow_s * (+1 if side=="long" else -1)      # >0 = pressure WITH the trade
Per window (per-second series within [ws, we)):
    LEVEL = mean(oriented_s)                                          # PRIMARY statistic
    SLOPE = OLS slope of oriented_s on elapsed seconds (s - s[0])     # CONFIRMING statistic (n>=2 else NaN)
Pre-registered direction (both): AUC(reached > failed). Runners expected stronger / building.
Reference: OFI family — Cont, Kukanov, Stoikov (2014), "The price impact of order book events."

## 5. GROUPING (frozen; = CURRENT_STATE Reading B inclusive pt1)
pt1 = first 1m WRB (timeframe=="1m", symbol==holdout front month) in trade direction (bullish=long /
      bearish=short) with ts_event >= floor_min(entry). WRB completes at ts_event+60s.
reached = pt1 exists AND last_exit_utc >= pt1 + 60s.
anchor  = pt1 (reached) else floor_min(last_exit_utc).   # used by context windows A1/A2/B only
CONTRAST = target_reached (52) vs failed_trades (40). DISJOINT by construction — NO de-dupe.
  (Unlike the exhaustion candidate, the confirmation signal reads on 52/40; the loser-spine de-dupe
   does not apply here.)

## 6. WINDOWS (frozen; per-second)
  EARLY  [entry, min(entry+60s, exit))   PRIMARY. Entry-anchored, FORWARD. min(...,exit) = causal guard:
         never reads flow from after the trade closed (no lookahead; the predicted label is realized later).
         EARLY_W = 60s frozen.
  A2     [max(entry, anchor-180s), anchor)   secondary/context (in-trade run-up).
  A1     [entry-180s, entry)                 context (expected INVERTED — pre-entry).
  B      [anchor-180s, anchor)               context; report pre_entry_frac strata (composition control).
  CONTROL (gives EARLY a CI): per-failed EARLY-window AUC vs ALL reached EARLY-windows (identical
         construction both arms; no tau to match for an entry-anchored window), cluster-bootstrap CI
         over the 40 failed. This CONTROL line is the PRIMARY decision statistic in §3.

## 7. CONTROLS / INTEGRITY (frozen)
- Tripwire: flag+exclude any window with in-window gap > 120s (session/halt) or |mid jump| > 40 ticks
  (roll discontinuity; series unadjusted). Expected 0 on a single-front-month intraday month.
- Orientation self-check: corr(mean oriented level, oriented mid change) over B; must be > 0 (channel
  live). ~0 on holdout => channel not operating that month; report, do not force.
- B composition: pre_entry_frac differs by group; report AUC stratified by its median. A B signal only
  in the HIGH stratum is the length artifact, not flow. (EARLY is entry-anchored so it has no pre-entry
  composition issue — that is the point of the early window.)
- AUC = pure-numpy rank AUC. CI = cluster bootstrap (seed 0, 10000 resamples).

## 8. INPUTS / FILES
- config.toml: paths.episodes ; run.resolved.windowed_parquet (resolve the holdout front month /
  windowed file by traded volume as in Stage 0 — do NOT assume ESH2).
- tsl_episodes_clean.parquet: side, first_entry_utc, last_exit_utc, realized_pnl, source_file,
  episode_id, trading_date.
- wrb_1m.parquet: ts_event(UTC), symbol, timeframe, direction.   (--wrb arg)
- MBP-10 windowed parquet (holdout month): ts_event, instrument_id, action, side, size, bid_px_00,
  ask_px_00. Stream; ~73M rows; do not materialize. sizes uint32 -> int64.
- Script: trade_flow_confirmation.py (discovery script; holdout run is the SAME script pointed at the
  holdout config/windowed file — feature code unchanged).

## 9. RUN
  python3 trade_flow_confirmation.py --config <holdout_config.toml> --wrb <holdout_wrb_1m.parquet>
Read order: (1) self-check sign, (2) tripwire=0, (3) CONTROL EARLY per-failed AUC + CI lower bound
(the PASS/FAIL line), (4) EARLY level/slope primary block, (5) A1/B inversion + B strata (coherence),
(6) firing counts vs floor 8 (and remember fired-subset magnitude AUC was ~0.57 in discovery).

## 10. SEQUENCE / WHAT THIS IS NOT
- Two FROZEN trade-flow candidates now exist, independent (different window/population/direction):
    (a) in_trade_flow_exhaustion — exit-anchored, FADING, LOSER spine (adverse-exit detector).
    (b) early_flow_confirmation  — entry-anchored, BUILDING, 52/40 (runner-confirmation detector).
  They are pre-registered as CANDIDATE COMPLEMENTARY INDICATORS. On the holdout, test EACH on its own
  frozen rule, AND test the COMBINATION (e.g. confirm-at-entry + not-exhausted-in-trade) — but the
  combination is a HOLDOUT hypothesis ONLY. Composing/optimizing the two on October (the data that
  produced both halves) would be overfitting by aggregation and is forbidden.
- Independent of the earlier favorable_velocity candidate; does not replace it.
- Discovery screens; holdout confirms. PASS => promote; FAIL => the early-flow read was October-specific
  in-sample noise and only the exhaustion (loser-spine) candidate carries forward.
