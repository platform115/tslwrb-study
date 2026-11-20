#!/usr/bin/env python3
"""
p5_13_mg1_dissection.py — MG-1: HIS MANAGEMENT vs M1, SAME ENTRIES. (T-MG01.)
===============================================================================
His 2025-10 episodes. Per-unit accounting (mean entry price vs mean exit
price) so his scaling does not confound the comparison. M1 run from HIS
first fill (frozen Q; S=30 RTH / S=90 ETH per p5_12). Dissection:
  1. per-unit P&L his vs M1 (totals, win rate, by win/loss)
  2. holding time his vs M1, split winners/losers
  3. capture: his exit vs the max favorable excursion up to his exit time;
     same for M1 (did he capture more of the move or just a longer move?)
  4. adds (n_entries>1) and scale-outs (n_exits>1): frequency + per-unit
     P&L vs single-shot episodes
  5. LEVEL-AWARE: distance of his exit price(s) and M1's exit price to the
     nearest live structure edge (reaction level / gap edge) at exit time
     (user directive: carry the identified levels into management testing)
RUN: python3 Tests/P5_trade_management/p5_13_mg1_dissection.py         (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P6_imitation_study"))
from p5_10_stall_stack_dials import leg
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p6_22_s6_1_presence import Resolver
from p6_23_s6_2_interaction import edges_at

Q_RTH = dict(early=4.0, stop=4.0, time_bars=27, S=30)
Q_ETH = dict(early=4.0, stop=4.0, time_bars=27, S=90)


def run(repo="."):
    P = prep(repo, "2025-10")
    cx = P["cx"]
    secs, mids = P["secs"], P["mids"]
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= "2025-10-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    def nearest_edge_dist(t, px):
        sd0 = sec_sd(t)
        if sd0 is None:
            return np.nan
        best = np.inf
        for fam in ("REA", "GAP"):
            for e in edges_at(R, sd0, np.datetime64(t), fam):
                best = min(best, abs(px - e))
        return best

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds("2025-10")
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    rows = []
    for _, r in em.iterrows():
        s0 = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        xT = int(pd.Timestamp(r.last_exit_utc).value // 10**9)
        d = 1 if r.side == "long" else -1
        ib = int(np.searchsorted(cx.bts, s0 * 10**9, "right")) - 1
        if ib < 60:
            continue
        ents = np.atleast_1d(r.entry_prices).astype(float)
        exts = np.atleast_1d(r.exit_prices).astype(float)
        ents = ents[np.isfinite(ents)]; exts = exts[np.isfinite(exts)]
        if not len(ents) or not len(exts):
            continue
        his_pu = (exts.mean() - ents.mean()) * d
        fill = float(ents[0])
        q = Q_RTH if cx.rth[ib] else Q_ETH
        px, xs, xb, reason = leg(cx, ib, fill, s0, d > 0, q)
        m1_pu = (px - fill) * d
        # MFE up to HIS exit time (per-second mids)
        j0 = int(np.searchsorted(secs, s0, "right")) - 1
        j1 = int(np.searchsorted(secs, xT, "right")) - 1
        mfe_his = np.nan
        if j1 > j0 >= 0:
            seg = mids[j0:j1 + 1]
            mfe_his = (seg.max() - fill) if d > 0 else (fill - seg.min())
        j2 = int(np.searchsorted(secs, int(xs), "right")) - 1
        mfe_m1 = np.nan
        if j2 > j0 >= 0:
            seg = mids[j0:j2 + 1]
            mfe_m1 = (seg.max() - fill) if d > 0 else (fill - seg.min())
        ex_t = pd.Timestamp(r.last_exit_utc).tz_convert(None)
        rows.append(dict(
            his_pu=his_pu, m1_pu=m1_pu, d=d,
            hold_his=xT - s0, hold_m1=int(xs) - s0,
            mfe_his=mfe_his, mfe_m1=mfe_m1,
            cap_his=(his_pu / mfe_his if mfe_his and mfe_his > 0 else np.nan),
            cap_m1=(m1_pu / mfe_m1 if mfe_m1 and mfe_m1 > 0 else np.nan),
            adds=int(r.n_entries) > 1, scaled_out=int(r.n_exits) > 1,
            exit_edge_his=nearest_edge_dist(ex_t, float(exts[-1])),
            exit_edge_m1=nearest_edge_dist(pd.Timestamp(int(xs), unit="s"), float(px)),
            reason=reason))
    D = pd.DataFrame(rows)
    n = len(D)
    print(f"===== MG-1: {n} episodes, per-unit accounting =====\n")
    print(f"TOTAL per-unit: HIS {D.his_pu.sum():+.1f} | M1 {D.m1_pu.sum():+.1f}")
    print(f"win rate: HIS {(D.his_pu>0).mean():.0%} | M1 {(D.m1_pu>0).mean():.0%}")
    print(f"avg win: HIS +{D.his_pu[D.his_pu>0].mean():.2f} | M1 +{D.m1_pu[D.m1_pu>0].mean():.2f}")
    print(f"avg loss: HIS {D.his_pu[D.his_pu<=0].mean():.2f} | M1 {D.m1_pu[D.m1_pu<=0].mean():.2f}")
    print(f"\nholding (median s): HIS {D.hold_his.median():.0f} | M1 {D.hold_m1.median():.0f}")
    w = D[D.his_pu > 0]; l = D[D.his_pu <= 0]
    print(f"  his winners: HIS {w.hold_his.median():.0f}s vs M1 {w.hold_m1.median():.0f}s")
    print(f"  his losers : HIS {l.hold_his.median():.0f}s vs M1 {l.hold_m1.median():.0f}s")
    print(f"\ncapture of MFE-to-own-exit (median): HIS {D.cap_his.median():.0%} | M1 {D.cap_m1.median():.0%}")
    print(f"MFE available (median): to his exit {D.mfe_his.median():.2f} | to M1 exit {D.mfe_m1.median():.2f}")
    print(f"\nadds: {D.adds.sum()}/{n} episodes | per-unit with adds {D[D.adds].his_pu.mean():+.2f} vs without {D[~D.adds].his_pu.mean():+.2f}")
    print(f"scale-outs: {D.scaled_out.sum()}/{n} | per-unit scaled {D[D.scaled_out].his_pu.mean():+.2f} vs single {D[~D.scaled_out].his_pu.mean():+.2f}")
    print(f"\nexit distance to nearest structure edge (median pts): HIS {D.exit_edge_his.median():.2f} | M1 {D.exit_edge_m1.median():.2f}")
    print(f"HIS exits within 1 pt of an edge: {(D.exit_edge_his<=1).mean():.0%} | M1: {(D.exit_edge_m1<=1).mean():.0%}")
    print(f"\nM1 exit reasons: {dict(D.reason.value_counts())}")
    D.to_parquet(os.path.join(repo, "Data/inputs/mg1_dissection.parquet"))


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
