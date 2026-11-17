#!/usr/bin/env python3
"""
p4_84_shares.py — P4.84 / Strategy 2: the SHARES varied (3 steps either side).
TRAINING MONTHS ONLY.
===============================================================================
Burst share (how violent the 8-s move must be, as a fraction of the estimated
day range): 0.030 / 0.034 / 0.038 / [0.042] / 0.046 / 0.050 / 0.054
Thrust share (how big the 2-min move behind it must be): 0.11 / 0.13 / 0.15 /
[0.17] / 0.19 / 0.21 / 0.23   (applied with the frozen sqrt(2/5) scaling)
One share varied at a time, the other held at its frozen value. Both lead
configs (ATR14D, INTRADAY10); 45 s gap, 1-bar wait; all else frozen.

RUN: python3 Tests/P4_entry_determination/p4_84_shares.py                 (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
C_N = 22.7
W, GAP, WAIT = 2, 45, 1
B0, T0 = 0.042, 0.17
BS = (0.030, 0.034, 0.038, 0.042, 0.046, 0.050, 0.054)
TS = (0.11, 0.13, 0.15, 0.17, 0.19, 0.21, 0.23)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {}
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        P["_bar_i"] = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        P["_Rday"] = {d: atr14d(d) for d in set(P["sd"])}
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        Ps[m] = P

    def run_cfg(P, scheme, bshare, tshare):
        cx = P["cx"]
        secs, keep = P["secs"], P["keep"]
        if scheme == "ATR14D":
            Rs = np.array([P["_Rday"].get(d) or np.nan for d in P["sd"]])[P["_bar_i"]]
        else:
            Rs = C_N * P["_atr10"][P["_bar_i"]]
        bt = bshare * Rs
        kept = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(bt)):
            if abs(P["_mv8"][i]) < bt[i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = P["_bar_i"][i]
            if ib < 60 or not cx.rth[ib]:
                continue
            d0 = int(np.sign(P["_mv8"][i]))
            tthr = tshare * np.sqrt(W / 5) * Rs[i]
            if np.isfinite(tthr) and d0 * P["_ret2"][ib] >= tthr:
                kept.append((i, d0))
        return sim(P, kept, lambda *a: True, cooldown=WAIT)

    for scheme in ("ATR14D", "INTRADAY10"):
        print(f"===== {scheme}: BURST share varied (thrust held {T0}) =====")
        print("| Burst share | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for b in BS:
            per_m = {m: run_cfg(Ps[m], scheme, b, T0) for m, _ in MONTHS}
            tag = " <= frozen" if b == B0 else ""
            print(row(f"{b:.3f}{tag}", per_m))
        print(f"===== {scheme}: THRUST share varied (burst held {B0}) =====")
        print("| Thrust share | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for t in TS:
            per_m = {m: run_cfg(Ps[m], scheme, B0, t) for m, _ in MONTHS}
            tag = " <= frozen" if t == T0 else ""
            print(row(f"{t:.2f}{tag}", per_m))


def cross(repo):
    """Full burst x thrust matrix (totals, both months pooled; win rate in a
    second matrix). Fires per burst share precomputed once."""
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {}
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        P["_bar_i"] = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        P["_Rday"] = {d: atr14d(d) for d in set(P["sd"])}
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        Ps[m] = P
    for scheme in ("ATR14D", "INTRADAY10"):
        # precompute per burst share: candidate fires with their thrust refs
        cand = {}
        for m, P in Ps.items():
            cx = P["cx"]
            secs, keep = P["secs"], P["keep"]
            if scheme == "ATR14D":
                Rs = np.array([P["_Rday"].get(d) or np.nan for d in P["sd"]])[P["_bar_i"]]
            else:
                Rs = C_N * P["_atr10"][P["_bar_i"]]
            for b in BS:
                bt = b * Rs
                kept = []
                last = -10**18
                for i in np.flatnonzero(keep & np.isfinite(bt)):
                    if abs(P["_mv8"][i]) < bt[i]:
                        continue
                    if secs[i] - last <= GAP:
                        continue
                    last = int(secs[i])
                    ib = P["_bar_i"][i]
                    if ib < 60 or not cx.rth[ib]:
                        continue
                    d0 = int(np.sign(P["_mv8"][i]))
                    kept.append((i, d0, float(Rs[i]), float(d0 * P["_ret2"][ib])))
                cand[(m, b)] = kept
        tot = {}; wr = {}; ntr = {}
        for b in BS:
            for t in TS:
                allp = []
                for m, P in Ps.items():
                    sel = [(i, d0) for i, d0, R, r2 in cand[(m, b)]
                           if np.isfinite(R) and r2 >= t * np.sqrt(W / 5) * R]
                    allp += sim(P, sel, lambda *a: True, cooldown=WAIT)
                a = np.asarray(allp)
                tot[(b, t)] = a.sum()
                wr[(b, t)] = (a > 0).mean() if len(a) else np.nan
                ntr[(b, t)] = len(a)
        print(f"===== {scheme}: TOTAL points (rows = burst share, cols = thrust share) =====")
        print("| burst\\thrust | " + " | ".join(f"{t:.2f}" for t in TS) + " |")
        print("|---|" + "---|" * len(TS))
        for b in BS:
            mark = "*" if b == B0 else ""
            print(f"| {b:.3f}{mark} | " + " | ".join(
                f"{tot[(b, t)]:+.0f}{'*' if (b, t) == (B0, T0) else ''}" for t in TS) + " |")
        print(f"===== {scheme}: win rate / trades =====")
        print("| burst\\thrust | " + " | ".join(f"{t:.2f}" for t in TS) + " |")
        print("|---|" + "---|" * len(TS))
        for b in BS:
            print(f"| {b:.3f} | " + " | ".join(
                f"{wr[(b, t)]:.0%}/{ntr[(b, t)]}" for t in TS) + " |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--cross", action="store_true", help="full 7x7 burst x thrust matrix")
    ap.add_argument("--low", action="store_true",
                    help="extend the burst axis BELOW the original grid "
                         "(0.014-0.030; 0.030 = overlap anchor with --cross)")
    a = ap.parse_args()
    if a.low:
        globals()["BS"] = (0.014, 0.018, 0.022, 0.026, 0.030)
        print("BURST AXIS EXTENSION below the original grid (0.030 repeated as anchor).")
        print("Looking for where the surface turns; TRAINING MONTHS ONLY.\n")
        cross(a.repo)
    elif a.cross:
        cross(a.repo)
    else:
        run(a.repo)
