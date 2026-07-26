#!/usr/bin/env python3
"""
test_pnl_magnitude.py — does the union exit-overlay ADD POINTS, or clip more than it saves?
-------------------------------------------------------------------------------
The deciding net-value test. His recorded loss management is ALREADY disciplined (Oct losers: median
~-1.4pt, ceiling ~-3) — so the bar is high. Compares total points across all 92 October trades under:
  (A) HIS RECORDED management         = sum(realized_pnl)            [baseline]
  (B) SIGNAL OVERLAY (union)          = exit at next 1m bar close after the union flag (capped at his
                                        recorded exit; signal can only exit EARLIER), else his realized
  (C) FIXED -3pt STOP                 = -3 if adverse hit 3pt before his exit, else his realized
Union flag = S1(body_ratio@60<0.5) OR VWAP(vwap_z@60<0, N=20) OR S2(max adverse>=2.5pt). Flag time =
earliest fire (60s for S1/VWAP, adverse-cross for S2). Exit price = first 1m bar CLOSE after flag time.

HEADLINE: total points (A vs B vs C) AND the loser/winner SPLIT — points SAVED on losers (B-realized,
realized<0) vs points FORGONE on clipped winners (realized-B, realized>0). Net = saved - forgone.
If net <= 0, the overlay clips more than it saves (likely, given losses are already small & winners run).

CAVEAT: counterfactual uses bar-close as a proxy fill (his realized used his actual fills) — basis
approximation. Points only (sizing/costs handled separately). All 92, October, in-sample. Not advice.

RUN (from 06-12_combined_rule/)
  python3 test_pnl_magnitude.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
N = 20; TAU = 60; S1_THR = 0.5; S2_THR = 2.5; VW_THR = 0.0; STOP = 3.0


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["run"]["resolved"]["windowed_parquet"], cfg["paths"]["es_1m_front"]


def load_bars(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "open", "high", "low", "close", "volume"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    d["tp"] = (d.high + d.low + d.close) / 3.0; d["tpv"] = d.tp * d.volume
    vwap = (d.tpv.rolling(N, min_periods=5).sum() / d.volume.rolling(N, min_periods=5).sum()).to_numpy()
    sigma = d.tp.rolling(N, min_periods=5).std().to_numpy()
    sec = (d.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    return sec, vwap, sigma, d.open.to_numpy(), d.close.to_numpy()


def at_idx(bsec, arr, t_s):
    i = int(np.searchsorted(bsec, t_s, "right") - 1)
    return float(arr[i]) if i >= 0 else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    args = ap.parse_args()
    g, windowed, es1m = load(args.config, args.wrb)
    bsec, vwap, sigma, bopen, bclose = load_bars(es1m)
    bclose_t = bsec + 60   # close time of each 1m bar

    def prior_body_max(entry_ts):
        e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
        j = int(np.searchsorted(bsec, e_s, "left"))
        return float(np.abs(bclose[j-3:j] - bopen[j-3:j]).max()) if j >= 3 else np.nan

    print("[pnl] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    recs = []
    for _, r in g.iterrows():
        sgn = 1.0 if r.side == "long" else -1.0; pbm = prior_body_max(r.entry)
        e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000); x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000)
        realized = float(r.realized_pnl); open60 = x_s > e_s + TAU
        fires = []
        # S1 / VWAP @60
        if open60:
            cp = min(pd.Timestamp(r.entry) + S(TAU), r.exit); cps = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
            m = mid_at(cp)
            if not np.isnan(m):
                if pbm and pbm > 0 and (((m - r.entry_price) * sgn) / pbm) < S1_THR: fires.append(e_s + TAU)
                sg = at_idx(bsec, sigma, cps); vwv = at_idx(bsec, vwap, cps)
                if sg and sg > 0 and ((((m - vwv) * sgn) / sg) < VW_THR): fires.append(e_s + TAU)
        # S2 + 3pt stop from adverse path
        i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, x_s, "left")
        ss = sec[i0:i1]; px = mid[i0:i1]
        adv = np.maximum(0.0, (r.entry_price - px) if r.side == "long" else (px - r.entry_price))
        run = np.maximum.accumulate(adv) if len(adv) else np.array([])
        k2 = np.searchsorted(run, S2_THR, "left") if len(run) else 0
        if len(run) and k2 < len(run): fires.append(int(ss[k2]))
        k3 = np.searchsorted(run, STOP, "left") if len(run) else 0
        stop_hit = len(run) and k3 < len(run)

        # (B) signal overlay
        pnl_B = realized
        if fires:
            ft = min(fires)
            bi = int(np.searchsorted(bclose_t, ft, "right"))   # first bar CLOSING after flag
            if bi < len(bclose) and bclose_t[bi] < x_s:        # only if earlier than his exit
                pnl_B = (bclose[bi] - r.entry_price) * sgn
        # (C) fixed -3 stop
        pnl_C = -STOP if stop_hit else realized
        recs.append(dict(uid=r.uid, realized=realized, B=pnl_B, C=pnl_C,
                         flagged=bool(fires), early=(pnl_B != realized), is_loser=realized < 0))
    d = pd.DataFrame(recs)

    A = d.realized.sum(); B = d.B.sum(); C = d.C.sum()
    print(f"\n  ===== TOTAL POINTS, all {len(d)} trades =====")
    print(f"  (A) his recorded management : {A:+.1f}")
    print(f"  (B) union signal overlay    : {B:+.1f}   (delta {B-A:+.1f})   trades exited early: {int(d.early.sum())}")
    print(f"  (C) fixed -3pt stop         : {C:+.1f}   (delta {C-A:+.1f})")

    los = d[d.is_loser]; win = d[~d.is_loser]
    saved = (los.B - los.realized).sum()         # >0 = overlay reduced losses
    forgone = (win.realized - win.B).sum()        # >0 = overlay gave up winner points
    print(f"\n  ===== LOSER / WINNER SPLIT (overlay B vs his recorded) =====")
    print(f"  losers  (n={len(los)}): points SAVED   = {saved:+.1f}")
    print(f"  winners (n={len(win)}): points FORGONE = {forgone:+.1f}")
    print(f"  NET (saved - forgone) = {saved - forgone:+.1f}")
    print(f"  winners clipped early: {int(win.early.sum())}/{len(win)}  | losers exited early: {int(los.early.sum())}/{len(los)}")

    print(f"\n[pnl] READ: if NET <= 0, the overlay clips more winner-points than it saves on losers ->")
    print(f"  NOT net-positive (expected, since his losses are already small ~-1.4 and winners run).")
    print(f"  Bar-close proxy fill; points only; in-sample. The sign of NET is the answer to 'is it good'.")


if __name__ == "__main__":
    main()
