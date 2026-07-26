# SPEC 06-3 — Volatility Compression price baseline (08-bar)

Status: RUN (Oct-2025 ESZ5 discovery). Result: SEPARATES (raw-range driven). The price-domain
baseline 07 had to beat. Recreatable from this doc + horse_race_spine.py + trade_flow_exhaustion.py.

## CLAIM TESTED
Would just watching the 1-minute bars stall do the job? If MBP-10 cannot separate cuts from runners
BEYOND this bar-only measure, the tick-data complexity is not necessary. Deliberately bar-domain.

## FEATURE FORMULA (Wilder 1978)
    compression = current_bar_true_range / ATR(5 of preceding in-session bars)
    TR = max(H-L, |H-prev_close|, |L-prev_close|);  first bar of a session_date: TR = H-L (no gapped
         overnight ref).  ATR(5) = mean TR of the 5 PRIOR bars within the same session_date; <5 -> NaN.
    compression < 1 = quieter than recent norm (coil); > 1 = expanding. DIRECTION-AGNOSTIC (side unused).
- Source = es_1m_front (COMPLETE minute series, OHLC), NOT wrb_1m (wrb_1m is WRB-only/sparse -> circular).
- Lookback MAY reach into overnight Globex bars (same session_date) by design; thin pre-open flagged
  via current-bar volume, not excluded.
- Window->bar map: bar CONTAINING window end `we` (largest bar ts_event <= we; a-asis, mild lookahead,
  symmetric under Design A). Gap >120s between we and bar start -> NaN.

## POPULATION & WINDOW
- 52 target_reached vs 40 failed_trades. TWO-SIDED. PRIMARY = Design A (W=60s), same as 06-2.
- Context: A1 (we=entry), anchor (we=anchor; A2==B collapse for a bar feature — keys on window END only).

## FILES / RUN
- es_1m_front from config[paths][es_1m_front]; wrb_1m for pt1; horse_race_spine.py; trade_flow_exhaustion.py.
    python3 test_08_bar_compression.py --config <cfg> --wrb <wrb_1m.parquet>

## RESULT (Oct-2025 ESZ5, 40 cuts, two-sided)
- Design A P=0.348 [0.267,0.431] SEPARATES. Direction: failed cuts have HIGHER compression (wider current
  bar) than mid-flight reached peers. Driver: TR (current-bar range), not the ATR5 baseline
  (failed TR med 3.00 vs reached 2.25; ATR5 ratio similar).
- Context A1=0.615, anchor=0.766 run reached>failed (OPPOSITE direction) = the pt1 coil confound
  (anchor windows end at/near the reached trade's expansion bar). Design A is the clean read; context is not.
- Interpretation: raw bar range separates cuts from runners. This + 07a numerator-only (per-second |Δmid|,
  P=0.242, same direction) = the price-MOVEMENT signal that the impact ratio (06-2) failed to beat.
  ATR5 medians ~2.5-3.1 points = plausible 1m ES; feature validated.

## CAVEAT
a-asis mild lookahead (forming bar at cut) is symmetric under Design A but not guaranteed perfectly
symmetric if arms differ in bar-offset; re-run a-strict (last COMPLETED bar before we) if 08 is ever
marginal. Here separation is large enough that this is not load-bearing.
