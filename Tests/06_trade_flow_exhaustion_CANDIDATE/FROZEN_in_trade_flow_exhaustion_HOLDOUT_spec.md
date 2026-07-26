# FROZEN CANDIDATE — in_trade_flow_exhaustion (HOLDOUT SPEC)
Status: FROZEN 2025-10 (discovery). Pre-registered for out-of-sample holdout validation.
Self-contained: a fresh chat with this doc + CURRENT_STATE.md + WRB_Definition.txt can rebuild and
validate it with no other context. NOTHING below may be re-tuned on holdout data — that is the point
of freezing. If a parameter is changed, it is a NEW candidate and this record is void.

===============================================================================
## 1. ONE-LINE CLAIM
Directional aggressor trade-flow IN-TRADE FADES before adverse (losing) ES trades and HOLDS for
trades that run to target. Measured on the realized-trade channel (action=="T", aggressor side,
size) — the resting-book channel (Tests 03/04/05) was null; this channel is live (self-check +0.72).

## 2. DISCOVERY RESULT (October 2025 ESZ5, 16 losers vs 47 non-loser reached) — what froze it
- Channel is LIVE: corr(mean oriented flow, oriented mid change) over B = +0.72 (book channel was -0.05).
- PRIMARY (frozen candidate): Design A, in-trade tau, level = 0.712, 95% CI [0.555, 0.844] — CI clears 0.5.
- CONFIRMING: A2 in-trade-run-up slope = 0.718 (on 11 valid losers vs 28 reached; 8/11 losers fire).
- COHERENCE (evidence it is not a fluke): signal concentrates in-trade; PRE-ENTRY (A1) null/inverted
  (level 0.492, slope 0.318); no-floor B null (0.542) with both pre_entry_frac strata ~0.5 (composition
  artifact ABSENT). A noise hit would scatter across windows; this one sits only where the mechanism predicts.
- CAVEAT carried into holdout: n is small (16 losers). Treat as "CI-positive / promising", NOT "0.71".
  A2-slope alone is on 11 trades — it does NOT stand alone; it only corroborates the all-16 Design A read.
  Firing magnitude adds nothing beyond the binary: AUC on the FIRED subset was 0.438 (the signal is
  WHETHER flow fades, not HOW far among those that faded).

## 3. PRE-REGISTERED HOLDOUT DECISION RULE (frozen — declare before touching holdout data)
- PRIMARY statistic = Design A (cut-time-matched, in-trade tau, W=60s) on oriented LEVEL.
  PASS if its 95% cluster-bootstrap CI lower bound > 0.5 on the holdout month.
- CONFIRMING statistic = A2 in-trade-run-up oriented SLOPE. Supportive if AUC > 0.5 same direction.
- Candidate VALIDATES only if PRIMARY passes. Confirming strengthens but cannot rescue a failed primary.
- Direction is fixed: AUC(reached oriented flow > loser oriented flow). No re-orientation post-hoc.
- Freeze rule unchanged: a high AUC counts only on >= 8 VALID loser firings (valid = window has a
  defined feature; >=1 sec level / >=2 sec slope; <2s window -> NaN, never a 1-snapshot value).

## 4. FEATURE DEFINITION (frozen formula)
Per book/trade snapshot, keep trade prints only (action == "T"); aggregate to ONE row per SECOND:
    buy_vol_s  = sum(size where side=="B")      # buy-aggressor volume that second  (int64)
    sell_vol_s = sum(size where side=="A")      # sell-aggressor volume that second (int64)
    mid_s      = last (bid_px_00 + ask_px_00)/2 that second
Per-second signed flow, oriented to the trade:
    signed_flow_s = buy_vol_s - sell_vol_s
    oriented_s    = signed_flow_s * (+1 if side=="long" else -1)     # >0 = pressure WITH the trade
Per window (per-second series within [ws, we)):
    LEVEL = mean(oriented_s)                                          # PRIMARY statistic
    SLOPE = OLS slope of oriented_s on elapsed seconds (s - s[0])     # CONFIRMING statistic
            (Cov(x,y)/Var(x); requires n>=2 else NaN)
Pre-registered direction (both): AUC(reached > loser). Losers expected weaker / fading.
Reference: OFI family — Cont, Kukanov, Stoikov (2014), "The price impact of order book events."

## 5. GROUPING (frozen; = CURRENT_STATE Reading B inclusive pt1)
pt1 = first 1m WRB (timeframe=="1m", symbol==holdout front month) in trade direction
      (bullish=long / bearish=short) with ts_event >= floor_min(entry). WRB completes at ts_event+60s.
reached = pt1 exists AND last_exit_utc >= pt1 + 60s.
anchor  = pt1 (reached) else floor_min(last_exit_utc).
LOSER group  = episodes with realized_pnl < 0.
COMPARISON   = target_reached AND realized_pnl >= 0  (non-loser reached).
  CRITICAL DE-DUPE: losers that are themselves in target_reached (tagged pt1 then lost) STAY in the
  loser arm and are REMOVED from the comparison arm — else a trade is compared to itself and inflates
  the AUC. October: 5 such overlap losers -> 16 losers vs 47 non-loser reached.
  (October loser uids, for exact reproduction of the discovery set:
   t1282.html::7, t1284.html::1, t1284.html::2, t1284.html::4, t1284.html::5, t1287.html::2,
   t1288.html::4, t1288.html::5, t1294.html::0, t1294.html::5, t1294.html::8, t1299.html::2,
   t1299.html::4, t1302.html::0, t1303.html::2, t1304.html::2 — discovery month only; holdout
   resolves its own losers from realized_pnl.)

## 6. WINDOWS (frozen; per-second; anchor as in 5)
  A1 pre-entry      [entry-180s, entry)                 fixed 180s  (expected NULL — control)
  A2 in-trade       [max(entry, anchor-180s), anchor)   entry-floored, anchor excluded  (CONFIRMING slope)
  B  no-floor       [anchor-180s, anchor)               live-screen; report pre_entry_frac strata (control)
  Design A          cut-time-matched: each loser at elapsed tau=hold vs non-loser-reached peers with
                    pt1_open_el > tau, trailing W=60s window ending at entry+tau; oriented LEVEL.
                    PRIMARY statistic lives here.

## 7. CONTROLS / INTEGRITY (frozen)
- Tripwire: flag+exclude any window whose in-window per-second rows have gap > 120s (session/halt)
  or |mid jump| > 40 ticks (roll discontinuity; series unadjusted). Expected 0 on a single-front-month
  intraday month.
- Orientation self-check: corr(mean oriented level, oriented mid change) over B; must be > 0 (channel
  live). If it comes back ~0 on holdout, the channel is not operating that month — report, do not force.
- B composition: pre_entry_frac differs by group; report AUC stratified by its median. A B signal only
  in the HIGH-pre_entry stratum is the length-composition artifact, not flow.
- AUC = pure-numpy rank AUC. Design A CI = cluster bootstrap over the loser cuts (seed 0, 10000 resamples).

## 8. INPUTS / FILES
- config.toml: paths.episodes ; run.resolved.windowed_parquet (+ resolve holdout front month / windowed
  file for the holdout month — do NOT assume ESH2; resolve by traded volume as in Stage 0).
- tsl_episodes_clean.parquet: side, first_entry_utc, last_exit_utc, realized_pnl, source_file,
  episode_id, trading_date.
- wrb_1m.parquet: ts_event(UTC), symbol, timeframe, direction.  (--wrb path arg)
- MBP-10 windowed parquet (holdout month): ts_event, instrument_id, action, side, size,
  bid_px_00, ask_px_00. Stream; ~73M rows; do not materialize. sizes uint32 -> int64.
- Script: trade_flow_exhaustion.py  (Round-1 discovery script; the holdout run is the SAME script
  pointed at the holdout config/windowed file with its own resolved losers — feature code unchanged).

## 9. RUN
  python3 trade_flow_exhaustion.py --config <holdout_config.toml> --wrb <holdout_wrb_1m.parquet>
Read order on output: (1) self-check sign, (2) tripwire=0, (3) Design A level AUC + CI lower bound
(the PASS/FAIL line), (4) A2 slope (confirming), (5) A1/B nulls + B strata (coherence check),
(6) valid-firing counts vs floor 8.

## 10. SEQUENCE / WHAT THIS IS NOT
- This freeze is the LOSER-spine (16 vs 47) discovery. ROUND 2 (still to run, same frozen params, NO
  de-dupe because target_reached vs failed_trades are disjoint) tests 52 reached vs 40 failed — to learn
  whether the signal is LOSER-SPECIFIC or generalizes to non-runners. Round 2 is corroboration, not part
  of this holdout decision.
- Independent of the earlier favorable_velocity candidate; does not replace it.
- Discovery screens; holdout confirms. A pass here = promote; a fail = the signal was October-specific
  small-n noise and the loser-spine re-target continues without it.
