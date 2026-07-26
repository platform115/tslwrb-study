#!/usr/bin/env python3
"""
test_combined_ladder.py — the full combination ladder: singles / pairs / majority / unanimous
-------------------------------------------------------------------------------
Extends the union test across the whole permissive->strict surface. For each combination, on BOTH
populations: COVERAGE (of the cut arm = losers/failed) vs WINNER-KILL (of the spared arm = reached).
Question: does a stricter rule (AND-pairs, 2-of-3 majority) hold loser-coverage while cutting the
union's high winner-kill? More signals required to fire => fewer false positives but less coverage.

Combinations (by increasing strictness):
  union (any of 3)  >  OR-pairs (any of 2)  >  singles  >  majority (>=2 of 3)  >  AND-pairs (both of 2)  >  unanimous (all 3)

Signals @60s (same defs as test_combined_union.py):
  S1 = body_ratio@60 < 0.5 ; S2 = max adverse over path >= 2.5pt ; VWAP = vwap_z@60 (N=20) < 0.
Trades cut before 60s: S1/VWAP cannot read (NOT-fired); S2 from full path.
Indicative thresholds. SSD MOUNTED. October in-sample. Counts only (no P&L). Not advice.

RUN (from 06-12_combined_rule/)
  python3 test_combined_ladder.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
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

    print("[ladder] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    rows = []
    for _, r in g.iterrows():
        sgn = 1.0 if r.side == "long" else -1.0; pbm = prior_body_max(r.entry)
        e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000); x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000)
        s1 = vw = False
        if x_s > e_s + TAU:
            cp = min(pd.Timestamp(r.entry) + S(TAU), r.exit); cps = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
            m = mid_at(cp)
            if not np.isnan(m):
                if pbm and pbm > 0: s1 = (((m - r.entry_price) * sgn) / pbm) < S1_THR
                sg = at_idx(bsec, sigma, cps); vwv = at_idx(bsec, vwap, cps)
                if sg and sg > 0: vw = ((((m - vwv) * sgn) / sg) < VW_THR)
        i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, x_s, "left")
        px = mid[i0:i1]
        adv = np.maximum(0.0, (r.entry_price - px) if r.side == "long" else (px - r.entry_price))
        s2 = bool(len(adv) and adv.max() >= S2_THR)
        rows.append(dict(is_loser=bool(r.is_loser), group=r.group, S1=bool(s1), S2=s2, VWAP=bool(vw)))
    d = pd.DataFrame(rows)

    combos = {
        "S1 alone":            lambda x: x.S1,
        "S2 alone":            lambda x: x.S2,
        "VWAP alone":          lambda x: x.VWAP,
        "S1 OR S2":            lambda x: x.S1 | x.S2,
        "S1 OR VWAP":          lambda x: x.S1 | x.VWAP,
        "S2 OR VWAP":          lambda x: x.S2 | x.VWAP,
        "union (any of 3)":    lambda x: x.S1 | x.S2 | x.VWAP,
        "majority (>=2 of 3)": lambda x: (x.S1.astype(int) + x.S2.astype(int) + x.VWAP.astype(int)) >= 2,
        "S1 AND S2":           lambda x: x.S1 & x.S2,
        "S1 AND VWAP":         lambda x: x.S1 & x.VWAP,
        "S2 AND VWAP":         lambda x: x.S2 & x.VWAP,
        "unanimous (all 3)":   lambda x: x.S1 & x.S2 & x.VWAP,
    }
    pops = {
        "clean (cut=losing16 / spared=reached47)": (d.is_loser, (d.group == "target_reached") & ~d.is_loser),
        "pt1   (cut=failed40 / spared=reached52)": (d.group == "failed_trades", d.group == "target_reached"),
    }
    for pop_name, (cutm, sparedm) in pops.items():
        cut = d[cutm]; spared = d[sparedm]
        print(f"\n================ {pop_name} ================")
        print(f"  {'combination':>20} | {'COVERAGE cut':>14} | {'WINNER-KILL spared':>19}")
        for nm, fn in combos.items():
            cov = int(fn(cut).sum()); wk = int(fn(spared).sum())
            print(f"  {nm:>20} | {cov:>3}/{len(cut)} ({cov/len(cut)*100:>3.0f}%)    | "
                  f"{wk:>3}/{len(spared)} ({wk/len(spared)*100:>3.0f}%)")

    print(f"\n[ladder] READ: scan for a combination that holds high COVERAGE while dropping WINNER-KILL")
    print(f"  vs the union. Majority (>=2) is the prime candidate. Counts only — net P&L value unmeasured.")
    print(f"  Indicative thresholds; in-sample; ~16 losers (cells small — read patterns, not exact n).")


if __name__ == "__main__":
    main()
