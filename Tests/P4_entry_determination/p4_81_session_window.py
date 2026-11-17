#!/usr/bin/env python3
"""
p4_81_session_window.py — P4.81 / Strategy 2: session window varied.
TRAINING MONTHS ONLY.
=====================================================================
Under both lead configs (ATR14D + 2-min thrust + 45 s gap + 1-bar wait;
INTRADAY10 same): trade only in the first {1, 2, 3, 4} hours after the RTH
open, or only within 1 hour AFTER a KME (the produced calendar), vs no
restriction (reference). All other settings frozen.

RUN: python3 Tests/P4_entry_determination/p4_81_session_window.py         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
W, GAP, WAIT = 2, 45, 1


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    ev_all = np.asarray(news_sets(repo)["all"], dtype=np.int64)
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
            kept = []
            last = -10**18
            for i in np.flatnonzero(keep & np.isfinite(bt)):
                if abs(mv8[i]) < bt[i]:
                    continue
                if secs[i] - last <= GAP:
                    continue
                last = secs[i]
                ib = bar_i[i]
                if ib < 60 or not cx.rth[ib]:
                    continue
                d0 = int(np.sign(mv8[i]))
                tthr = THRUST_SHARE * np.sqrt(W / 5) * Rs[i]
                if np.isfinite(tthr) and d0 * ret2[ib] >= tthr:
                    kept.append((i, d0, int(P["mins_rth"][ib]), int(secs[i])))
            kept_all[(m, scheme)] = kept

    windows = [("no restriction (reference)", None, None),
               ("first 1 hr after open", 60, None),
               ("first 2 hrs", 120, None),
               ("first 3 hrs", 180, None),
               ("first 4 hrs", 240, None),
               ("within 1 hr after a KME", None, 3600)]
    for scheme in ("ATR14D", "INTRADAY10"):
        print(f"===== {scheme} + 2-min thrust, 45s gap, 1-bar wait =====")
        print("| Session window | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for name, maxmin_, kme_s in windows:
            per_m = {}
            for m, P in Ps.items():
                sel = []
                for i, d0, mr, s0 in kept_all[(m, scheme)]:
                    if maxmin_ is not None and mr >= maxmin_:
                        continue
                    if kme_s is not None:
                        j = np.searchsorted(ev_all, s0 * 10**9, "right") - 1
                        if j < 0 or (s0 * 10**9 - ev_all[j]) > kme_s * 10**9:
                            continue
                    sel.append((i, d0))
                per_m[m] = sim(P, sel, lambda *a: True, cooldown=WAIT)
            print(row(name, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
