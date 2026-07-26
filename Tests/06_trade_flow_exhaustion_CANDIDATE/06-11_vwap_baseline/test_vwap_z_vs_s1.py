#!/usr/bin/env python3
"""
test_vwap_z_vs_s1.py — head-to-head: z-score VWAP-dist (N=20) vs S1 (body-progress)
-------------------------------------------------------------------------------
The strongest VWAP form (rolling, z-scored, N=20, ~0.78 @60s) vs S1 (body_ratio@60). Does sharpening the
VWAP signal make it MORE or LESS independent of body-progress than the N=30 raw baseline (+0.42)?
Pre-specified single config (N=20, z-score) — a clean comparison, not a sweep.

  vwap_z(60)  = (mid@60 - rolling_vwap_20) * side_sign / rolling_sigma_20   (still-open)
  body_ratio  = (mid@60 - entry) * side_sign / prior_3bar_max_body          (S1, still-open)

Reports: corr(vwap_z@60, body_ratio@60) over still-open trades (clean + pt1), AND a losers cross-tab
(S1 flag = body_ratio<0.5 ; VWAP flag = vwap_z<0): both / S1-only / VWAP-only / neither. VWAP-only>0 =>
catches losers S1 misses. High corr + no VWAP-only => redundant; low corr + VWAP-only => additive.

SSD MOUNTED. October in-sample (13 losers still-open @60s). Two-sided. Not financial advice.

RUN (from 06-11_vwap_baseline/)
  python3 test_vwap_z_vs_s1.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
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
N = 20; TAU = 60; S1_THR = 0.5


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

    print(f"[z-vs-s1] streaming per-second mid ... (N={N}, tau={TAU}s)")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    rows = []
    for _, r in g.iterrows():
        x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000); e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000)
        if not (x_s > e_s + TAU): continue
        sgn = 1.0 if r.side == "long" else -1.0; pbm = prior_body_max(r.entry)
        cp = min(pd.Timestamp(r.entry) + S(TAU), r.exit); cps = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
        m = mid_at(cp)
        if np.isnan(m): continue
        vw = at_idx(bsec, vwap, cps); sg = at_idx(bsec, sigma, cps)
        z = (((m - vw) * sgn) / sg) if (sg and sg > 0) else np.nan
        br = (((m - r.entry_price) * sgn) / pbm) if (pbm and pbm > 0) else np.nan
        rows.append(dict(uid=r.uid, is_loser=bool(r.is_loser), group=r.group, z=z, br=br))
    d = pd.DataFrame(rows).dropna(subset=["z", "br"])

    print(f"\n  CORRELATION corr(vwap_z@60, body_ratio@60):")
    for nm, mask in [("clean (loser+reached)", d.is_loser | ((d.group == 'target_reached') & ~d.is_loser)),
                     ("all still-open", pd.Series(True, index=d.index))]:
        sub = d[mask]
        if len(sub) >= 5:
            print(f"    {nm:>22}: {np.corrcoef(sub.z, sub.br)[0,1]:+.2f}  (n={len(sub)})")
    print(f"    [reference: N=30 RAW vwap_dist vs body_ratio was +0.42]")

    los = d[d.is_loser]
    s1 = los.br < S1_THR; vw = los.z < 0
    both = int((s1 & vw).sum()); s1o = int((s1 & ~vw).sum()); vwo = int((~s1 & vw).sum()); ne = int((~s1 & ~vw).sum())
    print(f"\n  LOSERS cross-tab (n={len(los)})  S1: body_ratio<{S1_THR} | VWAP: vwap_z<0:")
    print(f"    both={both}  S1-only={s1o}  VWAP-only={vwo}  neither={ne}")
    print(f"    (VWAP-only>0 => z-VWAP catches losers S1 misses; high corr + no VWAP-only => redundant)")

    print(f"\n[z-vs-s1] READ: vs the +0.42 raw baseline — higher corr => sharpening made it MORE like S1;")
    print(f"  similar/lower + VWAP-only losers => the z-form stays semi-independent and additive.")


if __name__ == "__main__":
    main()
