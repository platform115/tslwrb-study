#!/usr/bin/env python3
"""
p4_54_unexplained_autopsy.py — P4.54: the unexplained ~62% of his GROUP A
entries, one by one, against his own chat.
==========================================================================
Takes every Group A entry NOT within 2 ticks of the discriminating anchor set
(his prior trade prices, first-reaction WRBs 1m/5m/10m, all 10m reaction WRBs)
and dumps, per entry: time, side, price, context (minutes since the KME,
position in the day's range so far, tick distance to the nearest anchor of
each family), and his chat messages from 10 min before to 5 min after.
Output is for human reading - the classification happens by eye, recorded
in the registry when done.

RUN: python3 Tests/P4_entry_determination/p4_54_unexplained_autopsy.py   (repo root)
OUT: p4_54_unexplained.txt (also p4_54_explained.txt for contrast reading)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
import p4_51_kme_levels as p51                         # noqa: E402
from p4_49_sec_engine import Ctx, ALL_MONTHS           # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_53_anchor_sweep import month_anchors, TOL_TK, LIFE_NS, ZONE_LIFE_NS  # noqa: E402

TICK = 0.25
DISC = ["his-exit", "his-entry", "firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]


def min_dist(points, ts, px, life):
    best = np.inf
    for t0, p0 in points:
        if t0 <= ts <= t0 + life:
            best = min(best, abs(px - p0) / TICK)
    return best


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    mts = pd.DatetimeIndex(msg.datetime_utc).as_unit("ns").asi8
    order = np.argsort(mts); mts = mts[order]
    mtx = msg.message.to_numpy()[order]; mact = msg.trade_action.to_numpy()[order]
    ev_all = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    fu = open(os.path.join(HERE, "p4_54_unexplained.txt"), "w")
    fe = open(os.path.join(HERE, "p4_54_explained.txt"), "w")
    n_un = n_ex = 0
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        for _, t in e_m[g == "A"].iterrows():
            ts = pd.Timestamp(t.first_entry_utc).value
            px = float(np.asarray(t.entry_prices).ravel()[0])
            ib = int(np.searchsorted(cx.bts, ts)) - 1
            dists = {k: min_dist(W[k], ts, px, LIFE_NS) for k in DISC}
            explained = min(dists.values()) <= TOL_TK
            iev = int(np.searchsorted(ev_all, ts, side="right")) - 1
            mins = (ts - ev_all[iev]) / 60e9 if iev >= 0 else np.inf
            dh, dl = R["today-high"][ib], R["today-low"][ib]
            pos = (px - dl) / (dh - dl) if np.isfinite(dh) and dh > dl else np.nan
            f = fe if explained else fu
            if explained:
                n_ex += 1
            else:
                n_un += 1
            f.write(f"\n=== {month} {pd.Timestamp(ts)} HIS {t.side} @ {px} "
                    f"pnl {t.realized_pnl:+.1f} ===\n")
            f.write(f"  {mins:.0f} min after KME | at {pos:.0%} of day range | "
                    + " ".join(f"{k}:{v:.0f}tk" for k, v in dists.items() if np.isfinite(v)) + "\n")
            a, b = np.searchsorted(mts, ts - 10 * 60_000_000_000), \
                   np.searchsorted(mts, ts + 5 * 60_000_000_000)
            for k in range(a, b):
                dt = pd.Timestamp(mts[k]).strftime("%H:%M")
                act = f" [{mact[k]}]" if isinstance(mact[k], str) and mact[k] else ""
                f.write(f"  {dt}{act} {str(mtx[k]).strip()[:260]}\n")
    fu.close(); fe.close()
    print(f"unexplained: {n_un} -> p4_54_unexplained.txt | explained: {n_ex} -> p4_54_explained.txt")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
