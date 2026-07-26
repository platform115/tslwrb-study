#!/usr/bin/env python3
"""
test_combined_union.py — combined exit rule, UNION (OR): flag if ANY of S1 / S2 / z-VWAP fires
-------------------------------------------------------------------------------
The deferred winner-kill ledger. For each signal and their OR-union, on BOTH populations:
  COVERAGE  = of the CUT arm (losers / failed), how many the signal/union flags (loser-catching).
  WINNER-KILL = of the SPARED arm (reached), how many the signal/union FALSELY flags (cost).
Union maximizes coverage AND winner-kill — this shows whether the extra losers caught are worth the
extra winners clipped. Two populations side by side:
  clean = losing_trade(16) vs reached_target(47)   — loss-avoidance question
  pt1   = failed_trades(40) vs target_reached(52)  — target-reached question (diluted; expected weaker)

Signals @60s (still-open; trades cut before 60s -> S1/VWAP can't read, S2 from full path):
  S1 fire     = body_ratio@60 < 0.5
  S2 fire     = max adverse over [entry,exit] >= 2.5 pt   (path-based, not checkpoint)
  z-VWAP fire = vwap_z@60 (N=20) < 0
A trade that exited before 60s: S1/VWAP = NOT-fired (couldn't read); S2 still evaluated on its path.

Indicative thresholds (used throughout). SSD MOUNTED. October in-sample. Two-sided. Not advice.

RUN (from its subfolder)
  python3 test_combined_union.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups, read_per_second, S, M

import os as _os
INSTRUMENT_ID = int(_os.environ.get("TSLWRB_IID", "294973"))
MONTH = _os.environ.get("TSLWRB_MONTH", "2025-10")
SYMBOL = _os.environ.get("TSLWRB_SYMBOL", "ESZ5")
print(f"[env] MONTH={MONTH} SYMBOL={SYMBOL} INSTRUMENT_ID={INSTRUMENT_ID}", flush=True)
LO = pd.Timestamp(f"{MONTH}-01", tz="UTC"); HI = LO + pd.offsets.MonthBegin(1)
N = 20; TAU = 60; S1_THR = 0.5; S2_THR = 2.5; VW_THR = 0.0


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

    def prior_body_max(entry_ts):
        e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
        j = int(np.searchsorted(bsec, e_s, "left"))
        return float(np.abs(bclose[j-3:j] - bopen[j-3:j]).max()) if j >= 3 else np.nan

    print(f"[union] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    rows = []
    for _, r in g.iterrows():
        sgn = 1.0 if r.side == "long" else -1.0; pbm = prior_body_max(r.entry)
        e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000); x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000)
        open60 = x_s > e_s + TAU
        # S1 & VWAP @60 (only if still open at 60)
        s1 = vw = False
        if open60:
            cp = min(pd.Timestamp(r.entry) + S(TAU), r.exit); cps = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
            m = mid_at(cp)
            if not np.isnan(m):
                if pbm and pbm > 0:
                    s1 = (((m - r.entry_price) * sgn) / pbm) < S1_THR
                sg = at_idx(bsec, sigma, cps); vwv = at_idx(bsec, vwap, cps)
                if sg and sg > 0:
                    vw = ((((m - vwv) * sgn) / sg) < VW_THR)
        # S2 = max adverse over full path
        i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, x_s, "left")
        px = mid[i0:i1]
        adv = np.maximum(0.0, (r.entry_price - px) if r.side == "long" else (px - r.entry_price))
        s2 = bool(len(adv) and adv.max() >= S2_THR)
        rows.append(dict(uid=r.uid, is_loser=bool(r.is_loser), group=r.group,
                         S1=bool(s1), S2=s2, VWAP=bool(vw), union=bool(s1 or s2 or vw)))
    d = pd.DataFrame(rows)

    pops = {
        "clean (cut=losing16 / spared=reached47)": (d.is_loser, (d.group == "target_reached") & ~d.is_loser),
        "pt1   (cut=failed40 / spared=reached52)": (d.group == "failed_trades", d.group == "target_reached"),
    }
    for pop_name, (cutm, sparedm) in pops.items():
        cut = d[cutm]; spared = d[sparedm]
        print(f"\n================ {pop_name} ================")
        print(f"  {'signal':>8} | {'COVERAGE cut':>14} | {'WINNER-KILL spared':>20}")
        for s in ["S1", "S2", "VWAP", "union"]:
            cov = int(cut[s].sum()); wk = int(spared[s].sum())
            print(f"  {s:>8} | {cov:>3}/{len(cut)} ({cov/len(cut)*100:>3.0f}%)    | "
                  f"{wk:>3}/{len(spared)} ({wk/len(spared)*100:>3.0f}%)")
        cov = int(cut['union'].sum()); wk = int(spared['union'].sum())
        print(f"  NET (union): catches {cov}/{len(cut)} of the cut arm, clips {wk}/{len(spared)} winners "
              f"({wk/len(spared)*100:.0f}%).")

    print(f"\n[union] READ: union maxes loser-coverage AND winner-kill. The question is net value — is the")
    print(f"  extra coverage worth the clipped winners? Compare clean (loss-avoidance) vs pt1 (target).")
    print(f"  pt1 expected weaker/noisier (diluted by below_target_win). Indicative thresholds; in-sample.")


if __name__ == "__main__":
    main()
