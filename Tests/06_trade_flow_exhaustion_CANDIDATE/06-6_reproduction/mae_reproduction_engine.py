#!/usr/bin/env python3
"""
mae_reproduction_engine.py — adverse-excursion reproduction, parametrized
-------------------------------------------------------------------------------
Generalizes test_06-6 (the mid+clean run). Two switches:
  --instrument mid  : per-second MID adverse path. Fine TIMING (1s). Mid UNDER-reads the true
                      intra-second extreme a real stop triggers on. Starts at exact entry second
                      (no entry-bar contamination).
  --instrument bars : 1m bar LOW/HIGH adverse path from es_1m_front. TRUE extreme worst price, but
                      MINUTE-resolution timing AND entry-bar inclusion (the entry minute's low/high
                      includes pre-entry price -> can inflate adverse for both arms). Complementary
                      weakness to mid; the truth is bracketed between the two instruments.
  --grouping  clean : cut-arm = losing_trade (16, realized_pnl<0); spared-arm = reached_target (47).
  --grouping  pt1   : cut-arm = failed_trades (40); spared-arm = target_reached (52). The cut-arm here
                      is DILUTED (11 losers + 29 profitable early-exits ~0 adverse) -> expect weak
                      separation; that dilution is exactly why the relabel (06-4) exists.

ADVERSE EXCURSION (points, >=0) from entry:
  long  : max(0, entry_price - price);  short: max(0, price - entry_price). price = per-second mid, or
  bar low (long) / bar high (short). Running max over the window = MAE.
WINDOWS: cut-arm walks [entry, exit]; spared-arm walks [entry, pt1_completion] (= entry+pt1_open_el+60)
  -> "would a stop fire on this runner BEFORE it reached target".

REPORTS (decisive first):
  1. OVERLAP: cut-arm MAE distribution vs spared-arm pre-target MAE distribution. Reproduction lives
     or dies on whether runners dip into the band the cut-arm reaches. (Also: cut-arm EXIT-instant
     adverse = the loss/adverse actually accepted, distinct from MAE.)
  2. X-SWEEP (diagnostic, NOT a chosen X): sensitivity = cut-arm fires (MAE>=X); specificity =
     spared-arm spared (pre-target MAE < X). + loser timing gap (mid only; minute-coarse for bars).
PRE-REGISTERED read unchanged from 06-6: plausible if some X gives high sens AND high spec (AND tight
gap for mid); fails if sens & (1-spec) rise together or cut-arm adverse is scattered. No X selected.
n is small (clean cut-arm=16); October discovery. Not financial advice.

RUN (from 06-6_reproduction/)
  python3 mae_reproduction_engine.py --instrument bars --grouping clean --config ../../../config.toml --wrb ../../../wrb_1m.parquet
  python3 mae_reproduction_engine.py --instrument mid  --grouping pt1   --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    ep_path = cfg["paths"]["episodes"]
    windowed = cfg["run"]["resolved"]["windowed_parquet"]; es1m = cfg["paths"]["es_1m_front"]
    g = build_groups(ep_path, wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(ep_path)
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, windowed, es1m


def mid_series(windowed, t_min, t_max):
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    return sec, mid


def bar_series(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "high", "low"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.high.to_numpy(), d.low.to_numpy()


def adverse_path(kind, S1, S2, entry_ts, anchor_ts, side, ep):
    """Return (srel_sec, adv_per_step, run_cummax) over [entry, anchor) or None.
    kind 'mid': S1=sec, S2=mid.  kind 'bars': S1=bar_sec, S2=(hi,lo)."""
    e_s = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
    a_s = np.int64(pd.Timestamp(anchor_ts).value // 1_000_000_000)
    if a_s <= e_s:
        return None
    if kind == "mid":
        sec = S1; mid = S2
        i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, a_s, "left")
        if i1 <= i0:
            return None
        s = sec[i0:i1]; px = mid[i0:i1]
        adv = (ep - px) if side == "long" else (px - ep)
    else:  # bars: include the entry bar (bar starting > entry-60); minute resolution
        bar_sec = S1; hi, lo = S2
        i0 = np.searchsorted(bar_sec, e_s - 60, "left"); i1 = np.searchsorted(bar_sec, a_s, "left")
        if i1 <= i0:
            return None
        s = bar_sec[i0:i1]
        adv = (ep - lo[i0:i1]) if side == "long" else (hi[i0:i1] - ep)
    adv = np.maximum(0.0, adv)
    return (s - e_s).astype(float), adv, np.maximum.accumulate(adv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instrument", choices=["mid", "bars"], required=True)
    ap.add_argument("--grouping", choices=["clean", "pt1"], required=True)
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    args = ap.parse_args()

    g, windowed, es1m = load(args.config, args.wrb)
    if args.grouping == "clean":
        cut = g[g.is_loser].copy()
        spared = g[(g.group == "target_reached") & (~g.is_loser)].copy()
        cut_name, spared_name, exp = "losing_trade", "reached_target", "16 / 47"
    else:
        cut = g[g.group == "failed_trades"].copy()
        spared = g[g.group == "target_reached"].copy()
        cut_name, spared_name, exp = "failed_trades", "target_reached", "40 / 52"
    print(f"[repro] instrument={args.instrument}  grouping={args.grouping}  "
          f"cut={cut_name}({len(cut)})  spared={spared_name}({len(spared)})  (expect {exp})")

    if args.instrument == "mid":
        t_min = g["entry"].min(); t_max = g["exit"].max() + M(1)
        print(f"[repro] streaming per-second mid in [{t_min}, {t_max}) ...")
        S1, S2 = mid_series(windowed, t_min, t_max); print(f"[repro] per-second rows: {len(S1):,}")
    else:
        S1h, hi, lo = bar_series(es1m); S1, S2 = S1h, (hi, lo); print(f"[repro] es_1m bars: {len(S1):,}")
    kind = args.instrument

    # cut-arm: walk [entry, exit]
    cut_mae, cut_exit_adv, cut_paths = [], [], []
    for _, r in cut.iterrows():
        out = adverse_path(kind, S1, S2, r.entry, r.exit, r.side, r.entry_price)
        if out is None:
            continue
        srel, adv, run = out
        cut_mae.append(float(run[-1])); cut_exit_adv.append(float(adv[-1]))
        cut_paths.append((srel, run, float(srel[-1])))
    # spared-arm: walk [entry, pt1_completion]
    sp_mae = []
    for _, r in spared.iterrows():
        anchor = r.entry + S(float(r.pt1_open_el) + 60.0)
        out = adverse_path(kind, S1, S2, r.entry, anchor, r.side, r.entry_price)
        if out is not None:
            sp_mae.append(float(out[2][-1]))
    cut_mae = np.array(cut_mae); cut_exit_adv = np.array(cut_exit_adv); sp_mae = np.array(sp_mae)
    print(f"[repro] scored cut={len(cut_mae)}/{len(cut)}  spared={len(sp_mae)}/{len(spared)}")

    def qq(a): return np.round(np.percentile(a, [10, 25, 50, 75, 90]), 2)
    print(f"\n===== OVERLAP (points) =====")
    print(f"  {cut_name} MAE              p10/25/50/75/90 = {qq(cut_mae)}")
    print(f"  {cut_name} EXIT-instant adv p10/25/50/75/90 = {qq(cut_exit_adv)}  (loss actually accepted)")
    print(f"  {spared_name} MAX pre-pt1   p10/25/50/75/90 = {qq(sp_mae)}")
    print(f"  medians: cut MAE={np.median(cut_mae):.2f}  spared pre-pt1={np.median(sp_mae):.2f}")

    print(f"\n===== X-SWEEP (diagnostic; NOT a chosen threshold) =====")
    units = "1s" if kind == "mid" else "min-coarse"
    print(f"  {'X(pts)':>7} {'sens(cut fires)':>16} {'spec(spared spared)':>20} {'med gap('+units+')':>16}")
    for X in np.arange(0.5, 8.01, 0.5):
        sens = np.mean(cut_mae >= X); spec = np.mean(sp_mae < X)
        gaps = []
        for srel, run, exit_sec in cut_paths:
            if run[-1] >= X:
                gaps.append(exit_sec - srel[np.searchsorted(run, X, "left")])
        gap = np.median(gaps) if gaps else np.nan
        gap_disp = gap if kind == "mid" else (gap / 60 if not np.isnan(gap) else np.nan)
        print(f"  {X:>7.1f} {sens:>16.2f} {spec:>20.2f} {gap_disp:>16.0f}")

    print(f"\n  READ: sens AND spec both high (+ gap~0 for mid) => stop reproduces. sens & (1-spec) rise")
    print(f"  together => no clean X => overlap => NOT a simple stop.")
    if args.grouping == "pt1":
        print(f"  pt1 grouping: cut-arm is DILUTED by profitable early-exits (~0 adverse) -> expect LOW")
        print(f"  sensitivity / poor separation. Compare to --grouping clean to see the relabel's effect.")
    if args.instrument == "bars":
        print(f"  bars: true extreme price BUT entry-bar inclusion can inflate adverse (both arms);")
        print(f"  compare to --instrument mid (exact-entry-start, under-reads extreme) — truth is between.")
    print(f"\n[repro] DONE. Diagnostic only; no threshold selected.")


if __name__ == "__main__":
    main()
