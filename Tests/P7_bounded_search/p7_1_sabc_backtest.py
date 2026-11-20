#!/usr/bin/env python3
"""
p7_1_sabc_backtest.py — BOUNDED SEARCH: S-A/B/C FIRST BACKTEST. (T-BS01.)
===============================================================================
Hypotheses written first (BOUNDED_SEARCH_SPEC.md); parameters FIXED from
imitation-study measurements, no tuning:
  S-A: REA-edge interaction (union levels, 15-min window, direction = break
       side) -> enter at the per-second mid of the fire second; manage M1
       (frozen Q: early=4.0 stop=4.0 time=27 S=30; RTH-only this run,
       simq's rth gate).
  S-B: S-A gated by KME window (45 min).
  S-C: S-A gated by the score>=6 same-direction signal (5 min).
Fires: 30-s grid, 5-min dedupe per direction; entry components and M1
exits are harness-certified (T-IM28, E6, X1).
Report: Trades / Win rate / Avg win / Avg loss / Total / Max below start,
per strategy, 2025-10. ONE run; one refinement round allowed afterward.

RUN: python3 Tests/P7_bounded_search/p7_1_sabc_backtest.py             (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P6_imitation_study"))
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P5_trade_management"))
from p6_22_s6_1_presence import Resolver
from p6_24_s6_3_selectors import interact_edges
from p4_66_context_ablation import prep, row
from p4_3_confluence_news import news_sets
from p5_10_stall_stack_dials import simq

MONTH = "2025-10"
Q = dict(early=4.0, stop=4.0, time_bars=27, S=30)
DEDUP = 300


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
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    def c1_at(ts_):
        kk = np.searchsorted(ev, ts_ * 10**9, "right") - 1
        return bool(kk >= 0 and (ts_ * 10**9 - ev[kk]) <= 45 * 60 * 10**9)

    def c3_at(ts_, d):
        a, bb = np.searchsorted(ss, ts_ - 300), np.searchsorted(ss, ts_, "right")
        return bool((sdir[a:bb] == d).any())

    # fire generation: 30-s grid, both directions, 5-min dedupe (per strategy)
    fires = {"S-A": [], "S-B": [], "S-C": []}
    last = {(k, d): -10**12 for k in fires for d in (1, -1)}
    g30 = np.arange(4000, len(secs), 30)
    for j in g30:
        ts_ = int(secs[j])
        t = np.datetime64(ts_, "s")
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        for d in (1, -1):
            need = [k for k in fires if ts_ - last[(k, d)] > DEDUP]
            if not need:
                continue
            gates = {"S-A": True, "S-B": None, "S-C": None}
            if any(k in need for k in ("S-B",)):
                gates["S-B"] = c1_at(ts_)
            if any(k in need for k in ("S-C",)):
                gates["S-C"] = c3_at(ts_, d)
            cand = [k for k in need if gates[k]]
            if not cand:
                continue
            if interact_edges(R, sd0, t, "REA", 15, secs, mids, d):
                for k in cand:
                    fires[k].append((j, d)); last[(k, d)] = ts_
    print("fire events:", {k: len(v) for k, v in fires.items()}, flush=True)

    print(f"\n===== BOUNDED SEARCH S-A/B/C, {MONTH}, M1 management (RTH-only via simq) =====")
    print("| strategy | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for k in ("S-A", "S-B", "S-C"):
        pnl = simq(P, fires[k], Q)
        print(row(f"{k} [{len(fires[k])} fires]", {MONTH: pnl}))


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
