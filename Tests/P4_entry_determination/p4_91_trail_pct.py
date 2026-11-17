#!/usr/bin/env python3
"""
p4_91_trail_pct.py — P4.91 / Strategy 2: the volume lane's trailing-percentile
coefficient BRACKETED on the low side. TRAINING MONTHS ONLY.
===============================================================================
The adopted burst rule uses the trailing 85th pct of raw |8-s move| - but 85
was picked from {85, 90, 95}: the edge of its own grid. This run completes
the bracket: pct in {70, 75, 80, 85 (baseline), 90, 95}.
Everything else frozen at the adopted volume lane: thrust 0.13 x ATR14D,
45 s gap, 1-bar wait; trailing form = expanding in-month, min 1 prior
session (the tested form).

RUN: python3 Tests/P4_entry_determination/p4_91_trail_pct.py              (repo root)
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
W, GAP, WAIT = 2, 45, 1
TSH = 0.13
PCTS = (70, 75, 80, 85, 90, 95)


def run(repo, val=False):
    month_list = [(m, True) for m, _ in MONTHS] if not val else \
                 [("2021-09", False), ("2024-11", False)]
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {}
    for m, insample in month_list:
        P = prep(repo, m, insample=insample)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        P["_Ratr"] = np.array([{d: atr14d(d) for d in set(P["sd"])}.get(d) or np.nan
                               for d in P["sd"]])[bar_i]
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        P["_sd_sec"] = np.asarray(P["sd"])[bar_i]
        Ps[m] = P

    def fires(P, pct):
        cx = P["cx"]
        secs, keep = P["secs"], P["keep"]
        sd = P["_sd_sec"]
        days = pd.unique(sd[keep])
        thr = np.full(len(secs), np.nan)
        for k, d in enumerate(days):
            prior = keep & np.isin(sd, days[:k])
            if prior.any():
                thr[sd == d] = float(np.percentile(np.abs(P["_mv8"])[prior], pct))
        kept = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(thr) & np.isfinite(P["_Ratr"])):
            if abs(P["_mv8"][i]) < thr[i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = P["_bar_i"][i]
            if ib < 60 or not cx.rth[ib]:
                continue
            d0 = int(np.sign(P["_mv8"][i]))
            if d0 * P["_ret2"][ib] >= TSH * np.sqrt(W / 5) * P["_Ratr"][i]:
                kept.append((i, d0))
        return kept

    print("Volume lane, trailing-percentile coefficient bracketed "
          f"(thrust {TSH} x ATR14D, gap 45, wait 1).\n")
    print("| Trailing pct | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for p in PCTS:
        per_m = {m: sim(Ps[m], fires(Ps[m], p), lambda *a: True, cooldown=WAIT)
                 for m in Ps}
        tag = " <= baseline (adopted)" if p == 85 else ""
        print(row(f"{p}{tag}", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--val", action="store_true",
                    help="run on the reserved months (2021-09, 2024-11)")
    a = ap.parse_args()
    if a.val:
        print("VALIDATION MONTHS - settings frozen\n")
    run(a.repo, val=a.val)
