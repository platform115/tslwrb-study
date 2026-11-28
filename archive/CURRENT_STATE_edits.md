> STALE - ARCHIVED 2026-11-28 (Q-2, J). Superseded by MASTER_PROGRAM / OVERVIEW_TREE / SYSTEMS_MATRIX.

# CURRENT_STATE.md — edit list (apply these; general env/defs only, no per-test detail)

## REPLACE the "What was already tested" line
OLD: "...Next: 07 microprice_drift; see PHASE_B_test_plan_restructured.md."
NEW: "Test 06 folder split into subtests 06-1..06-5 (see their SPEC docs). Channels tested to date:
book-direction (03/04/05) CLOSED null; trade-flow LEVEL (06 exhaustion / 06b confirmation) LIVE, two
FROZEN candidates; price-IMPACT (Kyle/Amihud, 06-2) CLOSED null on Oct; price-MOVEMENT (06-3 bar
compression / 06-2 numerator) SEPARATES; behavioral MAE (06-5) SEPARATES. Next: 06-6 reproduction."

## ADD to "Definitions"
- failure_tag (behavioral relabel, single-source label = behavioral_relabel_<month>.parquet):
  losing_trade = realized_pnl<0 ; reached_target = NOT losing AND pt1 reached ; below_target_win =
  NOT losing AND pt1 NOT reached. Losers take priority over pt1. scratch_trade dropped (no pnl
  zero-cluster; may return as a behavioral def needing MAE). Oct = 16/47/29.
- CLEAN EXIT CONTRAST = losing_trade(16) vs reached_target(47) == the loser spine. Use this for
  exit-signal tests, NOT 52/40 (52/40 is diluted by below_target_win profitable early-exits).
- MAE (Sweeney 1996) = max adverse excursion from entry; bar-domain (es_1m_front lows/highs); points.

## ADD to "Data Info"
- realized_pnl is in POINTS (tick-granular), NOT dollars; reconciles with extracted entry/exit at corr 1.0.
- entry_prices/exit_prices are length-1 arrays in Oct (single-entry, unscaled, n_entries=n_exits=1).
- es_1m_front = COMPLETE 1m OHLC series (cols: ts_event, instrument_id, symbol, open, high, low, close,
  volume, is_roll_day, session, session_date; ~99.9% 60s gaps; has GLOBEX + RTH). USE FOR BARS.
- wrb_1m is WRB-ONLY (sparse; every row is a WRB) — do NOT use for ATR/contiguous-bar features; use
  it only for pt1/WRB grouping.
- session_date is the within-session boundary for bar features (TR reset; overnight Globex shares the
  next RTH morning's session_date).

## ADD to "Notes" (durable measurement facts)
- Window->bar mapping for bar features = bar CONTAINING window end (a-asis, mild lookahead, symmetric
  under Design A). For cumulative-from-entry features (MAE), window = [entry, anchor], NOT trailing-W.
- Impact (move-per-volume) does NOT separate on Oct because |Δmid| and volume co-scale on active bars;
  RAW movement does. Orient feature choice accordingly: flow LEVEL and adverse MOVEMENT separate;
  impact NORMALIZATION does not (this channel).
- Separability splits by LIFECYCLE: entry-anchored signals (flow level) live at trade start; exit-
  anchored microstructure is null/confounded; the exit is explained by adverse excursion (stop-like).
- horse_race_spine.py = shared machinery (grouping, Design A windows, rank AUC, cluster CI, coherence)
  for 06-2/06-3/06-5. Sits at folder root.

## OCTOBER-HARDCODE DEBT (add as a standing reminder)
spine self-test + relabel + behavioral baseline assert Oct counts; INSTRUMENT_ID/MONTH/SYMBOL hardcoded
in trade_flow_exhaustion.py. FAIL LOUD off-October by design. De-Octoberize before any holdout.

## RECOMMENDED NEXT TESTS (replace any stale "next" list)
1. 06-6 MAE REPRODUCTION (highest value): does ONE adverse-excursion threshold (and/or adverse-velocity
   rule) FIRE at his actual exit times — precision/recall vs real cuts, not group AUC. Decides "stop
   explains him" vs "losers merely have bigger MAE". Run on the clean 16/47 contrast.
2. MAE tighten to strict-from-entry-tick (remove entry-bar inclusion) before trusting the 3.0-pt magnitude.
3. De-Octoberization + holdout prep (front month by volume, parametrize month/instrument).
4. (Deferred, separate convo) entry-selection channel — the surviving entry-anchored flow-level signal.
