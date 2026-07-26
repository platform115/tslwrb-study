#!/usr/bin/env python3
"""
test_08_bar_compression.py  — 08-bar: the PRICE-DOMAIN BASELINE (not a candidate)
-------------------------------------------------------------------------------
PURPOSE
  The honest "would just watching the bars do this?" control. If 07's MBP-10
  impact features cannot separate failed from reached BEYOND what this bar-only
  compression does, the tick-data complexity has not earned its keep. This is
  the necessary-vs-sufficient probe, kept deliberately on 1-minute bars so it is
  genuinely the cheap thing a screen-watcher could compute.

FEATURE (frozen for this run)
  compression = current_bar_true_range / ATR(5 of the preceding in-session bars)
    - True range (Wilder, 1978): max(H-L, |H-prev_close|, |L-prev_close|).
    - Within-session reset: prev_close is the prior bar's close ONLY within the
      same session_date; the first bar of a session_date uses TR = H-L (no gapped
      overnight reference). Uses es_1m_front's session_date column directly.
    - ATR(5) = mean TR of the 5 bars immediately preceding the current bar, within
      the same session_date. Fewer than 5 prior in-session bars -> NaN (floor).
    - Lookback MAY reach into overnight Globex bars (same session_date), by design:
      the genuinely-preceding minutes are the honest baseline. Thin pre-open bars
      are flagged (low-volume lookback), not excluded.
  compression < 1 = quieter than recent norm (coiling); > 1 = expanding.
  Direction-agnostic: volatility has no long/short orientation (side is ignored).

WINDOW -> BAR MAPPING (confirmed: a-asis)
  The bar CONTAINING the window end `we` (largest bar ts_event <= we). This bar may
  still be forming at the cut instant -> mild lookahead, accepted because under
  Design A both arms are mapped identically, so it does not bias the CONTRAST.
  (A data gap of >120s between `we` and the bar start -> NaN, tripwire-consistent.)

PRE-REGISTRATION
  Two-sided (direction NOT pre-committed: the pt1 coil confound could push either
  way; Design A defuses it by anchoring reached peers mid-flight, pre-pt1, not on
  the pt1 expansion bar). Read = does the 95% CI exclude 0.5, and in which direction.
  PRIMARY window = Design A (52/40). A1/anchor = context. Exploration screens.

POPULATION: 52 target_reached vs 40 failed_trades.
Deterministic (bootstrap seed=0). Read-only on all source data.

RUN
  python3 test_08_bar_compression.py --config ../../config.toml --wrb ../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---
import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import S

INSTRUMENT_ID = 294973            # ESZ5 (verified Oct front month)
LO = pd.Timestamp("2025-10-01", tz="UTC")
HI = pd.Timestamp("2025-11-01", tz="UTC")
GAP_TRIPWIRE_S = 120


def load_bars(es1m_path):
    """Complete ESZ5 October minute series with TR / ATR(5) / compression precomputed."""
    cols = ["ts_event", "instrument_id", "open", "high", "low", "close",
            "volume", "session", "session_date"]
    d = pd.read_parquet(es1m_path, columns=cols)
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)

    # True range with within-session reset (prev_close only within same session_date)
    prev_close = d.groupby("session_date")["close"].shift(1)
    hl = (d.high - d.low)
    hc = (d.high - prev_close).abs()
    lc = (d.low - prev_close).abs()
    tr = hl.copy()
    m = prev_close.notna()
    tr[m] = np.maximum(np.maximum(hl[m], hc[m]), lc[m])
    d["tr"] = tr.values

    # ATR(5) = mean TR of the 5 PRIOR in-session bars (exclude current); <5 -> NaN
    d["atr5"] = d.groupby("session_date")["tr"].transform(
        lambda s: s.rolling(5, min_periods=5).mean().shift(1))
    d["compression"] = d["tr"] / d["atr5"]
    return d


def make_feature_fn(bars):
    """Closure: window end -> compression of the containing bar (a-asis)."""
    bar_sec = (bars["ts_event"].astype("int64") // 1_000_000_000).to_numpy()
    comp = bars["compression"].to_numpy()
    tr = bars["tr"].to_numpy()
    atr5 = bars["atr5"].to_numpy()
    vol = bars["volume"].to_numpy()

    def feature_fn(side, ws, we):
        we_s = pd.Timestamp(we).value // 1_000_000_000
        i = int(np.searchsorted(bar_sec, we_s, "right") - 1)   # largest bar start <= we
        if i < 0:
            return {"value": np.nan}
        if we_s - int(bar_sec[i]) > GAP_TRIPWIRE_S:            # we fell in a data gap/halt
            return {"value": np.nan}
        # expose components for the driver check; value is the compression ratio
        return {"value": float(comp[i]), "tr": float(tr[i]),
                "atr5": float(atr5[i]), "vol": float(vol[i])}
    return feature_fn


def driver_report(failed, reached, feature_fn, W):
    """Is any compression separation driven by current-bar TR or by the ATR(5) baseline?
    Reports median TR / ATR5 / compression per Design-A arm, plus lookback-thinness."""
    def collect(windows):
        c, t, a, v = [], [], [], []
        for w in windows:
            f = feature_fn(w["side"], w["ws"], w["we"])
            if f and not np.isnan(f.get("value", np.nan)):
                c.append(f["value"]); t.append(f["tr"]); a.append(f["atr5"]); v.append(f["vol"])
        return np.array(c), np.array(t), np.array(a), np.array(v)

    cut_w = spine.designA_cut_windows(failed, W)
    peer_w = []
    for _, f in failed.iterrows():
        peer_w += spine.designA_peer_windows_for(f, reached, W)
    cc, ct, ca, cv = collect(cut_w)
    pc, pt, pa, pv = collect(peer_w)
    print("\n  [driver] median per Design-A arm (what moves the compression ratio?)")
    print(f"    {'arm':14s} {'n':>4} {'compression':>12} {'TR(tk?)':>10} {'ATR5':>8} {'cur-bar vol':>12}")
    print(f"    {'failed cut':14s} {len(cc):>4} {np.median(cc):>12.3f} {np.median(ct):>10.2f} "
          f"{np.median(ca):>8.2f} {np.median(cv):>12.0f}")
    print(f"    {'reached peer':14s} {len(pc):>4} {np.median(pc):>12.3f} {np.median(pt):>10.2f} "
          f"{np.median(pa):>8.2f} {np.median(pv):>12.0f}")
    print("    (TR is in PRICE units, not ticks; ratio = TR/ATR5. Compare cols across arms: a gap in")
    print("     compression with similar TR means the baseline ATR5 shifted; a TR gap means current-bar")
    print("     range differs. Low cur-bar vol = thin/pre-open lookback context, flagged not excluded.)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--W", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    failed, reached, g, ep_path, windowed = spine.load_and_group(args.config, args.wrb)
    print(f"[08-bar] target_reached={len(reached)}  failed_trades={len(failed)}  (expect 52 / 40)")

    es1m = tomllib.load(open(args.config, "rb"))["paths"]["es_1m_front"]
    bars = load_bars(es1m)
    n_comp = int(bars["compression"].notna().sum())
    print(f"[08-bar] es_1m_front ESZ5 Oct bars: {len(bars):,}  "
          f"({bars.ts_event.min()} .. {bars.ts_event.max()})  "
          f"compression defined on {n_comp:,} bars (rest = first-5-of-session floor)")

    feature_fn = make_feature_fn(bars)
    W = S(args.W)

    # NaN-floor diagnostic on the actual windows we will score
    cut_w = spine.designA_cut_windows(failed, W)
    nan_cut = sum(1 for w in cut_w if np.isnan(feature_fn(w["side"], w["ws"], w["we"])["value"]))
    print(f"[08-bar] failed cut-windows with NaN compression (insufficient lookback or gap): "
          f"{nan_cut}/{len(cut_w)}")

    # ---- PRIMARY: Design A, two-sided ----
    res = spine.designA_perCut(failed, reached, feature_fn, W, seed=args.seed)
    spine.report_designA("08-bar  compression = TR / ATR(5)", res)

    # ---- driver check (TR vs ATR5) ----
    driver_report(failed, reached, feature_fn, W)

    # ---- CONTEXT: A1 (we=entry) and anchor (we=anchor). A2==B for a bar feature. ----
    print("\n  [context] population-level two-sided AUC (bar feature keys on window END):")
    for label, ws_col, we_col in [("A1 pre-entry (we=entry)", "a1_s", "a1_e"),
                                   ("anchor (we=anchor)", "a2_s", "a2_e")]:
        r = spine.population_auc(failed, reached, feature_fn, ws_col, we_col)
        spine.report_population(label, r)
    print("  NOTE: A2 and B collapse to the same value here (both end at anchor; bar feature ignores")
    print("        window start). Anchor-context inherits the pt1 coil confound — Design A is the clean read.")

    print("\n[08-bar] DONE. This is the BASELINE. 07 must separate the arms BEYOND this to justify MBP-10.")


if __name__ == "__main__":
    main()
