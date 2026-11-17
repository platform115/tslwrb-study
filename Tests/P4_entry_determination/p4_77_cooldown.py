#!/usr/bin/env python3
"""
p4_77_cooldown.py — P4.77 / Strategy 2: cooldown after exit varied
(1/2/3/4/5/6/7/10 bars). TRAINING MONTHS ONLY.
===================================================================
Under the two lead configs (frozen): ATR14D + static 2-min thrust window,
and INTRADAY10 + static 2-min. Burst 0.042 x R_est / 8 s; thrust
0.17 x sqrt(2/5) x R_est. All else unchanged (direction = burst sign,
no signal, no session cut, 120 s clustering, v11 sketch, mid fills).
Cooldown = bars to wait after the exit bar before the next entry is allowed
(5 = current; 1 bar ~ 1 minute).

RUN: python3 Tests/P4_entry_determination/p4_77_cooldown.py               (repo root)
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
CLUST = 120
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
W = 2
COOLS = (1, 2, 3, 4, 5, 6, 7, 10)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    kept_all = {}
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
        for scheme in ("ATR14D", "INTRADAY10"):
            if scheme == "ATR14D":
                Rs = np.array([Rday.get(d) or np.nan for d in P["sd"]])[bar_i]
            else:
                Rs = C_N * atr10[bar_i]
            bt = BURST_SHARE * Rs
            fl = []; last = -10**18
            for i in np.flatnonzero(keep & np.isfinite(bt)):
                if abs(mv8[i]) < bt[i]:
                    continue
                if secs[i] - last > CLUST:
                    fl.append(i); last = secs[i]
            kept = []
            for i in fl:
                ib = bar_i[i]
                if ib < 60 or not cx.rth[ib]:
                    continue
                d0 = int(np.sign(mv8[i]))
                tthr = THRUST_SHARE * np.sqrt(W / 5) * Rs[i]
                if np.isfinite(tthr) and d0 * ret2[ib] >= tthr:
                    kept.append((i, d0))
            kept_all[(m, scheme)] = kept
    for scheme in ("ATR14D", "INTRADAY10"):
        print(f"===== {scheme} + 2-min window =====")
        print("| Cooldown (bars) | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for cd in COOLS:
            per_m = {m: sim(Ps[m], kept_all[(m, scheme)], lambda *a: True, cooldown=cd)
                     for m, _ in MONTHS}
            tag = " <= current" if cd == 5 else ""
            print(row(f"{cd}{tag}", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
