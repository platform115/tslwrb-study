#!/usr/bin/env python3
"""
p4_79_derive_gap.py — P4.79 / Strategy 2: deriving the firing gap from the
data. TRAINING MONTHS ONLY.
============================================================================
Crossings = RTH seconds where |8-s move| >= the ATR14D burst threshold
(0.042 x trailing-14-session range). Two measurements:
A) INTER-ARRIVAL DISTRIBUTION: time between consecutive crossings, binned.
   Burst clustering shows up as mass at short gaps; the VALLEY between
   "within one episode" and "the next event" is where the firing gap belongs.
B) EPISODE COUNT vs MERGE DISTANCE: merge crossings closer than delta into
   one episode; episodes/day as delta grows. The knee/plateau = the natural
   separation scale (persistence-style argument).
Cross-check: the post-burst drift stays positive for ~74-169 s (T-EN77 A) -
the gap should sit at or below that life so re-fires still catch live moves.

RUN: python3 Tests/P4_entry_determination/p4_79_derive_gap.py             (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
BURST_SHARE = 0.042
BINS = [(0, 5), (5, 10), (10, 20), (20, 30), (30, 60), (60, 120), (120, 300), (300, 10**9)]
DELTAS = (5, 10, 20, 30, 45, 60, 90, 120, 180, 300)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        Rday = {d: atr14d(d) for d in set(P["sd"])}
        Rs = np.array([Rday.get(d) or np.nan for d in P["sd"]])[bar_i]
        cross = secs[np.flatnonzero(keep & np.isfinite(Rs) & (np.abs(mv8) >= BURST_SHARE * Rs))]
        days = len(np.unique(cross // 86400))
        ia = np.diff(cross)
        ia = ia[ia > 0]
        print(f"[{m}] crossings: {len(cross)} over {days} days")
        print("  A) inter-arrival distribution (share of gaps in each bin):")
        line = []
        for lo, hi in BINS:
            share = ((ia >= lo) & (ia < hi)).mean()
            lab = f"{lo}-{hi}s" if hi < 10**9 else f">{lo}s"
            line.append(f"{lab}: {share:.0%}")
        print("     " + " | ".join(line))
        print("  B) episodes/day at merge distance delta:")
        line = []
        for dl in DELTAS:
            n_ep = 1 + int((np.diff(cross) > dl).sum()) if len(cross) else 0
            line.append(f"{dl}s: {n_ep/days:.0f}")
        print("     " + " | ".join(line))
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
