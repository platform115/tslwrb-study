#!/usr/bin/env python3
"""
p5_16_mg3_validation.py — MG-3: VALIDATE S=90, THEN FREEZE AS M2. (T-MG04.)
===============================================================================
A. HIS entries, 2022-02 and 2021-09 (signals not needed): M1 (S=30) vs the
   candidate (S=90), both from his actual fills, ETH bars use 3x the stall
   seconds, every other dial unchanged. Zero refitting.
B. ER-SIG fires, 2025-10 (the bounded-search deferred refinement): the
   same fire list as T-BS01's S-C cell, managed with S=30 vs S=90.
RUN: python3 Tests/P5_trade_management/p5_16_mg3_validation.py         (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P6_imitation_study"))
from p5_10_stall_stack_dials import leg, simq
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p4_3_confluence_news import news_sets
from p6_22_s6_1_presence import Resolver
from p6_24_s6_3_selectors import interact_edges


def table(name, pnl):
    a = np.asarray(pnl); wn = a > 0
    dd = -min(0.0, float(np.min(np.cumsum(a)))) if len(a) else 0.0
    aw = a[wn].mean() if wn.any() else np.nan
    al = a[~wn].mean() if (~wn).any() else np.nan
    print(f"| {name} | {len(a)} | {wn.mean():.0%} | +{aw:.2f} / {al:.2f} | {a.sum():+.1f} | {dd:.1f} |")


def his_month(repo, month):
    P = prep(repo, month, insample=False)
    cx = P["cx"]
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(month)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    out = {30: [], 90: []}
    his = []
    for _, r in em.iterrows():
        s0 = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        d = 1 if r.side == "long" else -1
        ib = int(np.searchsorted(cx.bts, s0 * 10**9, "right")) - 1
        if ib < 60:
            continue
        ents = np.atleast_1d(r.entry_prices).astype(float)
        exts = np.atleast_1d(r.exit_prices).astype(float)
        ents, exts = ents[np.isfinite(ents)], exts[np.isfinite(exts)]
        if not len(ents) or not len(exts):
            continue
        fill = float(ents[0])
        his.append((exts.mean() - ents.mean()) * d)
        eth = not cx.rth[ib]
        for S in (30, 90):
            q = dict(early=4.0, stop=4.0, time_bars=27, S=S * (3 if eth else 1))
            px, xs, xb, _ = leg(cx, ib, fill, s0, d > 0, q)
            out[S].append((px - fill) * d)
    print(f"\n===== A. HIS entries {month} ({len(his)} episodes, per-unit) =====")
    print("| plan | Trades | Win rate | Avg win / loss | Total | Max below start |")
    table("HIS ACTUAL", his)
    table("M1 (S=30)", out[30])
    table("candidate S=90", out[90])


def ersig_fires(repo):
    month = "2025-10"
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    P = prep(repo, month)
    secs, mids = P["secs"], P["mids"]
    cx = P["cx"]
    sg = cx.sig[cx.sig.score >= 6]
    ss = sg.comp_ns.to_numpy(np.int64) // 10**9
    sdir = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    oo = np.argsort(ss); ss, sdir = ss[oo], sdir[oo]
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    fires = []
    last = {d: -10**12 for d in (1, -1)}
    for j in np.arange(4000, len(secs), 30):
        ts_ = int(secs[j]); t = np.datetime64(ts_, "s")
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        for d in (1, -1):
            if ts_ - last[d] <= 300:
                continue
            a, bb = np.searchsorted(ss, ts_ - 300), np.searchsorted(ss, ts_, "right")
            if not (sdir[a:bb] == d).any():
                continue
            if interact_edges(R, sd0, t, "REA", 15, secs, mids, d):
                fires.append((j, d)); last[d] = ts_
    print(f"\n===== B. ER-SIG fires {month} ({len(fires)} fires, RTH via simq) =====")
    print("| plan | Trades | Win rate | Avg win / loss | Total | Max below start |")
    for S in (30, 90):
        q = dict(early=4.0, stop=4.0, time_bars=27, S=S)
        table(f"S={S}", simq(P, fires, q))


if __name__ == "__main__":
    repo = "." if len(sys.argv) < 2 else sys.argv[1]
    his_month(repo, "2022-02")
    his_month(repo, "2021-09")
    ersig_fires(repo)
