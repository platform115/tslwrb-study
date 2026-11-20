#!/usr/bin/env python3
"""
p5_18_mg3c_intraday_adapter.py — MG-3c: INTRADAY STALL ADAPTER. (T-MG06.)
===============================================================================
USER CORRECTION (2026-11-20): the MG-3b adapter looked at prior sessions -
the same mistake made with management adapters before. The clock must read
the SHORT-INTERVAL RECENT PAST OF THE SAME SESSION.
Rule: at entry, measure alive gaps (time between successive new running
extremes of the per-second mid, highs and lows separately, capped 600 s)
over the LAST 60 MINUTES of the same session before the entry second.
S = the 80th percentile of those gaps, clipped to [20, 180]; fewer than 20
gaps -> S = 30 (the M1 default). ETH bars use 3x S. S is fixed per trade
at entry; everything else is M1 unchanged.
Freeze criterion (unchanged from MG-3b): pooled win over fixed S=30 AND
S=90, and not the worst plan in any month -> frozen as M2.

RUN: python3 Tests/P5_trade_management/p5_18_mg3c_intraday_adapter.py  (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p5_10_stall_stack_dials import leg
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds

CAP = 600.0


def entry_S(secs, mids, j, sd_sec):
    a = int(np.searchsorted(secs, secs[j] - 3600))
    while a < j and sd_sec[a] != sd_sec[j]:
        a += 1
    if j - a < 120:
        return 30.0
    gaps = []
    for sign in (1, -1):
        ext = None; last = None
        for i in range(a, j + 1):
            m = sign * mids[i]
            if ext is None or m > ext:
                if last is not None:
                    g = secs[i] - last
                    if 0 < g <= CAP:
                        gaps.append(g)
                ext = m; last = secs[i]
    if len(gaps) < 20:
        return 30.0
    return float(np.clip(np.percentile(gaps, 80), 20, 180))


def run(repo="."):
    months = ["2025-10", "2022-02", "2021-09"]
    pooled = {k: [] for k in ("HIS", "S=30", "S=90", "intraday")}
    worst = []
    for month in months:
        P = prep(repo, month, insample=(month == "2025-10"))
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        sd_sec = np.asarray(P["sd"])[np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1,
                                             0, len(cx.c) - 1)]
        ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                             ).dropna(subset=["first_entry_utc"])
        lo, hi = month_bounds(month)
        em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        res = {k: [] for k in pooled}
        Sused = []
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
            res["HIS"].append((exts.mean() - ents.mean()) * d)
            eth = not cx.rth[ib]
            j = int(np.searchsorted(secs, s0, "right")) - 1
            Sa = entry_S(secs, mids, j, sd_sec)
            Sused.append(Sa)
            for k, S in (("S=30", 30.0), ("S=90", 90.0), ("intraday", Sa)):
                q = dict(early=4.0, stop=4.0, time_bars=27, S=S * (3 if eth else 1))
                px, xs, xb, _ = leg(cx, ib, fill, s0, d > 0, q)
                res[k].append((px - fill) * d)
        print(f"\n===== {month} ({len(res['HIS'])} episodes) | per-entry S q25/50/75 = "
              f"{np.percentile(Sused,25):.0f}/{np.percentile(Sused,50):.0f}/{np.percentile(Sused,75):.0f} s =====")
        print("| plan | Win rate | Avg win / loss | Total |")
        tot = {}
        for k in ("HIS", "S=30", "S=90", "intraday"):
            a = np.asarray(res[k]); wn = a > 0
            tot[k] = a.sum()
            print(f"| {k} | {wn.mean():.0%} | +{a[wn].mean():.2f} / {a[~wn].mean():.2f} | {a.sum():+.1f} |")
            pooled[k] += list(a)
        mech = {k: tot[k] for k in ("S=30", "S=90", "intraday")}
        worst.append(min(mech, key=mech.get) == "intraday")
    print("\n===== POOLED =====")
    for k in ("HIS", "S=30", "S=90", "intraday"):
        a = np.asarray(pooled[k])
        print(f"| {k} | {(a>0).mean():.0%} | {a.sum():+.1f} |")
    win = (np.sum(pooled["intraday"]) > max(np.sum(pooled["S=30"]), np.sum(pooled["S=90"])))
    print(f"\nFREEZE CRITERION: pooled win = {win}; worst-in-a-month = {any(worst)}"
          f" -> {'PASS - freeze as M2' if win and not any(worst) else 'FAIL - M1 stands'}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
