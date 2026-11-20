#!/usr/bin/env python3
"""
p6_27_s6_6_signal_gate.py — C3 SIGNAL-GATE GRID. (T-IM34.)
===============================================================================
C3 = a same-direction score>=6 signal COMPLETED within the prior 5 min
(completion-stamped; the strongest measured separator, AUC 0.727, p6_3).
Cells (pre-registered): base&C1 | base&C1&C3 | base&C3.
base = REA interaction 15-min direction-aligned; C1 = KME window 45 min.
Scored: catch of his 92 entries; fires/day (30s grid, 5-min dedupe).

RUN: python3 Tests/P6_imitation_study/p6_27_s6_6_signal_gate.py       (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_22_s6_1_presence import Resolver, MONTH
from p6_24_s6_3_selectors import interact_edges
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p4_3_confluence_news import news_sets

GRID, DEDUP = 30, 300


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{MONTH}-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    P = prep(repo, MONTH)
    secs, mids = P["secs"], P["mids"]
    cx = P["cx"]
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    sg = cx.sig[cx.sig.score >= 6]
    ss = sg.comp_ns.to_numpy(np.int64) // 10**9
    sdir = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    oo = np.argsort(ss); ss, sdir = ss[oo], sdir[oo]

    def c1_at(t):
        t_ns = int(t.astype("datetime64[ns]").astype(np.int64))
        kk = np.searchsorted(ev, t_ns, "right") - 1
        return bool(kk >= 0 and (t_ns - ev[kk]) <= 45 * 60 * 10**9)

    def c3_at(t, d):
        t_s = int(t.astype("datetime64[s]").astype(np.int64))
        a, bb = np.searchsorted(ss, t_s - 300), np.searchsorted(ss, t_s, "right")
        return bool((sdir[a:bb] == d).any())

    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    CELLS = ["base&C1", "base&C1&C3", "base&C3"]

    def ok(c, c1, c3):
        return {"base&C1": c1, "base&C1&C3": c1 and c3, "base&C3": c3}[c]

    catch = {c: 0 for c in CELLS}; n = 0
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        side = 1 if r.side == "long" else -1
        sd0 = sec_sd(t)
        if sd0 is None: continue
        n += 1
        if not interact_edges(R, sd0, t, "REA", 15, secs, mids, side):
            continue
        c1, c3 = c1_at(t), c3_at(t, side)
        for c in CELLS:
            catch[c] += ok(c, c1, c3)
    fires = {c: 0 for c in CELLS}
    sds = sorted(set(sd1))
    for sd0 in sds:
        g = bm[bm.sd == sd0]
        t0 = np.datetime64(g.ts_event.iloc[0].tz_convert(None))
        t1 = np.datetime64(g.ts_event.iloc[-1].tz_convert(None))
        last = {(c, d): -10**12 for c in CELLS for d in (1, -1)}
        tt = t0
        while tt < t1:
            ts_ = tt.astype("datetime64[s]").astype(np.int64)
            need = [(c, d) for c in CELLS for d in (1, -1) if ts_ - last[(c, d)] > DEDUP]
            if need:
                c1 = c1_at(tt)
                for d in (1, -1):
                    if not any(dd == d for _, dd in need): continue
                    c3 = c3_at(tt, d)
                    pre = [c for c, dd in need if dd == d and ok(c, c1, c3)]
                    if pre and interact_edges(R, sd0, tt, "REA", 15, secs, mids, d):
                        for c in pre:
                            if ts_ - last[(c, d)] > DEDUP:
                                fires[c] += 1; last[(c, d)] = ts_
            tt = tt + np.timedelta64(GRID, "s")
        print(".", end="", flush=True)
    nd = len(sds)
    print(f"\n\n===== C3 SIGNAL-GATE GRID ({MONTH}, {nd} sessions, {n} entries) =====")
    print("| cell | catch | catch % | fires/day | fires per catch |")
    for c in CELLS:
        print(f"| {c} | {catch[c]}/{n} | {catch[c]/n:.0%} | {fires[c]/nd:.1f} | {fires[c]/max(1,catch[c]):.0f} |")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
