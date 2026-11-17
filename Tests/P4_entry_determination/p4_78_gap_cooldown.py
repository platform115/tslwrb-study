#!/usr/bin/env python3
"""
p4_78_gap_cooldown.py — P4.78 / Strategy 2: firing gap x wait-after-exit,
varied TOGETHER (they do overlapping jobs). TRAINING MONTHS ONLY.
==========================================================================
Firing gap = minimum seconds between trigger firings (was fixed 120 s).
Wait = bars after an exit before the next entry (current 5; candidate 1).
Grid: gap {30, 60, 120, 180, 300} s x wait {1, 5} bars, under both lead
configs (ATR14D + 2-min thrust, INTRADAY10 + 2-min thrust). All else frozen.
The his-entry MATCHING window (also 120 s) is a measurement setting, not a
strategy setting - unchanged here.

RUN: python3 Tests/P4_entry_determination/p4_78_gap_cooldown.py           (repo root)
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
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
W = 2
GAPS = (30, 60, 120, 300)
WAITS = (1, 5)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    pre = {}
    for m, P in Ps.items():
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        Rday = {d: atr14d(d) for d in set(P["sd"])}
        ret2 = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        pre[m] = dict(mv8=mv8, bar_i=bar_i, atr10=atr10, Rday=Rday, ret2=ret2)

    for scheme in ("ATR14D", "INTRADAY10"):
        print(f"===== {scheme} + 2-min thrust =====")
        print("| Firing gap | Wait | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|---|")
        for gap in GAPS:
            for wait in WAITS:
                per_m = {}
                for m, P in Ps.items():
                    q = pre[m]
                    secs, keep = P["secs"], P["keep"]
                    if scheme == "ATR14D":
                        Rs = np.array([q["Rday"].get(d) or np.nan for d in P["sd"]])[q["bar_i"]]
                    else:
                        Rs = C_N * q["atr10"][q["bar_i"]]
                    bt = BURST_SHARE * Rs
                    kept = []
                    last = -10**18
                    for i in np.flatnonzero(keep & np.isfinite(bt)):
                        if abs(q["mv8"][i]) < bt[i]:
                            continue
                        if secs[i] - last <= gap:
                            continue
                        last = secs[i]
                        ib = q["bar_i"][i]
                        if ib < 60 or not P["cx"].rth[ib]:
                            continue
                        d0 = int(np.sign(q["mv8"][i]))
                        tthr = THRUST_SHARE * np.sqrt(W / 5) * Rs[i]
                        if np.isfinite(tthr) and d0 * q["ret2"][ib] >= tthr:
                            kept.append((i, d0))
                    per_m[m] = sim(P, kept, lambda *a: True, cooldown=wait)
                tag = " <= current" if (gap, wait) == (120, 5) else ""
                print(row(f"{gap}s | {wait} bars{tag}", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
