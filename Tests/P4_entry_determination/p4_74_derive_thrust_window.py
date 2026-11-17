#!/usr/bin/env python3
"""
p4_74_derive_thrust_window.py — P4.74 / Strategy 2: deriving the 2-minute
thrust window from the data. TRAINING MONTHS ONLY.
===========================================================================
Three measurements that could yield "~2 minutes":
A) POST-BURST DRIFT ZERO-CROSSING: after a top-0.5% 7-s burst, the mean
   further move (same direction) at +30..+300 s; the time where it crosses
   zero = how long a move stays alive before reversion. The thrust window
   should fit inside that life.
B) VARIANCE RATIO (Lo-MacKinlay lineage): VR(w) = Var(w-min return) /
   (w x Var(1-min return)) on RTH closes; the w where VR peaks = the
   timescale where trending is strongest.
C) DIRECTIONAL RUN LENGTH: consecutive same-sign 1-min RTH returns; median /
   75th / 90th percentile run duration in minutes.
Each per month, for stability. Whichever lands at ~2 min becomes the frozen
window rule (plan amendment), with regime-tracking validation deferred to
the purchase months.

RUN: python3 Tests/P4_entry_determination/p4_74_derive_thrust_window.py   (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402

TICK = 0.25
KS = (30, 60, 90, 120, 150, 180, 240, 300)


def run(repo):
    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    print("A) Post-burst drift (mean further move, same direction, ticks):\n")
    print("| Month | " + " | ".join(f"+{k}s" for k in KS) + " | Zero-crossing |")
    print("|---|" + "---|" * (len(KS) + 1))
    for m, P in Ps.items():
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        iw = np.searchsorted(secs, secs - 7)
        mv7 = (mids - mids[np.maximum(iw, 0)]) / TICK
        thr = np.percentile(np.abs(mv7)[keep], 99.5)
        idx = np.flatnonzero(keep & (np.abs(mv7) >= thr))
        sel = []; last = -10**18
        for i in idx:
            if secs[i] - last >= 30:
                sel.append(i); last = secs[i]
        sel = np.array(sel, dtype=int)
        means = []
        for K in KS:
            j = np.searchsorted(secs, secs[sel] + K, "right") - 1
            means.append(float(np.mean((mids[j] - mids[sel]) / TICK * np.sign(mv7[sel]))))
        zc = None
        for a in range(1, len(KS)):
            if means[a] <= 0 < means[a - 1]:
                f = means[a - 1] / (means[a - 1] - means[a])
                zc = KS[a - 1] + f * (KS[a] - KS[a - 1])
                break
        print(f"| {m} | " + " | ".join(f"{v:+.2f}" for v in means) +
              f" | {'%.0f s' % zc if zc else 'none <=300s'} |")

    print("\nB) Variance ratio VR(w) on RTH 1-min returns (peak = trending timescale):\n")
    print("| Month | " + " | ".join(f"w={w}" for w in range(1, 13)) + " | Peak |")
    print("|---|" + "---|" * 13)
    for m, P in Ps.items():
        cx = P["cx"]
        r = pd.Series(cx.c).diff()[cx.rth].dropna().to_numpy()
        v1 = np.var(r)
        vr = []
        for w in range(1, 13):
            rw = np.convolve(r, np.ones(w), "valid")[::1]
            vr.append(np.var(rw) / (w * v1))
        peak = int(np.argmax(vr)) + 1
        print(f"| {m} | " + " | ".join(f"{v:.2f}" for v in vr) + f" | {peak} min |")

    print("\nC) Directional run length of 1-min RTH returns (minutes):\n")
    print("| Month | Median | 75th pct | 90th pct |")
    print("|---|---|---|---|")
    for m, P in Ps.items():
        cx = P["cx"]
        r = np.sign(pd.Series(cx.c).diff()[cx.rth].dropna().to_numpy())
        runs = []; cur = 0; last = 0
        for s in r:
            if s != 0 and s == last:
                cur += 1
            elif s != 0:
                if cur:
                    runs.append(cur)
                cur = 1; last = s
        runs = np.asarray(runs)
        print(f"| {m} | {np.median(runs):.0f} | {np.percentile(runs,75):.0f} "
              f"| {np.percentile(runs,90):.0f} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
