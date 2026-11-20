#!/usr/bin/env python3
"""
p5_17_mg3b_adaptive.py — MG-3b: SESSION-ADAPTIVE STALL CLOCK. (T-MG05.)
===============================================================================
The stall seconds S computed per session from data, not fixed:
  For each session, pool the ALIVE GAPS of the 5 STRICTLY PRIOR sessions -
  an alive gap is the time between successive new running extremes of the
  per-second mid (highs and lows tracked separately, gaps capped at 600 s,
  reset each session). S = the pooled 80th percentile, clipped to
  [20, 180] s; ETH bars use 3x S as before. <=t: only prior sessions feed
  a session's S.
Compared against fixed S=30 (M1) and S=90 on HIS entries, all three
months. FREEZE CRITERION (stated in advance): adaptive wins pooled AND is
not the worst plan in any single month -> frozen as M2.

RUN: python3 Tests/P5_trade_management/p5_17_mg3b_adaptive.py          (repo root)
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


def alive_gaps_of_session(secs, mids, a, b):
    gaps = []
    for sign in (1, -1):
        ext = None; last = None
        for i in range(a, b):
            m = sign * mids[i]
            if ext is None or m > ext:
                if last is not None:
                    g = secs[i] - last
                    if 0 < g <= CAP:
                        gaps.append(g)
                ext = m; last = secs[i]
    return gaps


def session_S(P):
    """Map session_date -> adaptive S from 5 prior sessions' alive gaps."""
    secs, mids = P["secs"], P["mids"]
    cx = P["cx"]
    sd_sec = np.asarray(P["sd"])[np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1,
                                         0, len(cx.c) - 1)]
    sess = list(dict.fromkeys(sd_sec))
    bounds = {s: (int(np.searchsorted(sd_sec, s, "left") if False else 0), 0) for s in sess}
    # contiguous spans
    spans = {}
    start = 0
    for i in range(1, len(sd_sec) + 1):
        if i == len(sd_sec) or sd_sec[i] != sd_sec[start]:
            spans[sd_sec[start]] = (start, i)
            start = i
    gaps_by = {s: alive_gaps_of_session(secs, mids, a, b) for s, (a, b) in spans.items()}
    S_of = {}
    for k, s in enumerate(sess):
        prior = [g for s2 in sess[max(0, k - 5):k] for g in gaps_by.get(s2, [])]
        S_of[s] = float(np.clip(np.percentile(prior, 80), 20, 180)) if len(prior) >= 50 else 30.0
    return S_of


def run(repo="."):
    months = ["2025-10", "2022-02", "2021-09"]
    pooled = {k: [] for k in ("HIS", "S=30", "S=90", "adaptive")}
    worst_flags = []
    for month in months:
        P = prep(repo, month, insample=(month != "2021-09") and (month != "2022-02"))
        cx = P["cx"]
        S_of = session_S(P)
        Ss = np.array(list(S_of.values()))
        ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                             ).dropna(subset=["first_entry_utc"])
        lo, hi = month_bounds(month)
        em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        res = {k: [] for k in pooled}
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
            sd0 = P["sd"][ib]
            for k, S in (("S=30", 30.0), ("S=90", 90.0), ("adaptive", S_of.get(sd0, 30.0))):
                q = dict(early=4.0, stop=4.0, time_bars=27, S=S * (3 if eth else 1))
                px, xs, xb, _ = leg(cx, ib, fill, s0, d > 0, q)
                res[k].append((px - fill) * d)
        print(f"\n===== {month} ({len(res['HIS'])} episodes) | adaptive S: "
              f"q25/50/75 = {np.percentile(Ss,25):.0f}/{np.percentile(Ss,50):.0f}/{np.percentile(Ss,75):.0f} s =====")
        print("| plan | Win rate | Avg win / loss | Total |")
        tot = {}
        for k in ("HIS", "S=30", "S=90", "adaptive"):
            a = np.asarray(res[k]); wn = a > 0
            tot[k] = a.sum()
            print(f"| {k} | {wn.mean():.0%} | +{a[wn].mean():.2f} / {a[~wn].mean():.2f} | {a.sum():+.1f} |")
            pooled[k] += list(a)
        mech = {k: tot[k] for k in ("S=30", "S=90", "adaptive")}
        worst_flags.append(min(mech, key=mech.get) == "adaptive")
    print("\n===== POOLED (3 months) =====")
    for k in ("HIS", "S=30", "S=90", "adaptive"):
        a = np.asarray(pooled[k])
        print(f"| {k} | {(a>0).mean():.0%} | {a.sum():+.1f} |")
    win = (np.sum(pooled["adaptive"]) > max(np.sum(pooled["S=30"]), np.sum(pooled["S=90"])))
    print(f"\nFREEZE CRITERION: pooled win = {win}; worst-in-a-month = {any(worst_flags)}"
          f" -> {'PASS - freeze as M2' if win and not any(worst_flags) else 'FAIL - M1 stands'}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
