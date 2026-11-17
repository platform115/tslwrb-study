#!/usr/bin/env python3
"""
p4_90_intraday_memory.py — P4.90 / Strategy 2: the INTRADAY MEMORY (N bars)
swept 5-50 on TRAINING AND VALIDATION months. User-authorized 2026-11-17 in
full knowledge that this spends the reserved months on this check.
===============================================================================
The old 5-50 grid predates the current stack (share 0.022, thrust 0.17,
rolling C(day), gap 45, wait 1), so training is re-run under the current
config alongside validation; the question is whether both samples settle
near the conventional 10.

RUN: python3 Tests/P4_entry_determination/p4_90_intraday_memory.py        (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
from p4_89_cn_adaptive import session_ratio_table, NSESS  # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
BSH, TSH = 0.022, 0.17
NB = (5, 10, 15, 20, 25, 30, 40, 50)


def run(repo):
    RT = session_ratio_table(repo)
    dates = list(RT.index)
    pos = {d: i for i, d in enumerate(dates)}

    def c_day(d):
        i = pos.get(d)
        if not i or i <= 0:
            return None
        w = RT.iloc[max(0, i - NSESS):i]
        return float(w.rng.mean() / w.mtr.mean()) if len(w) and w.mtr.mean() > 0 else None

    groups = [("TRAINING", [(m, True) for m, _ in MONTHS]),
              ("VALIDATION", [("2021-09", False), ("2024-11", False)])]
    for gname, month_list in groups:
        Ps = {}
        for m, insample in month_list:
            P = prep(repo, m, insample=insample)
            cx = P["cx"]
            secs, mids = P["secs"], P["mids"]
            iw = np.searchsorted(secs, secs - 8)
            P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
            bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1,
                            0, len(cx.c) - 1)
            P["_bar_i"] = bar_i
            pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
            tr = np.maximum(cx.h - cx.l,
                            np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
            P["_trS"] = pd.Series(tr)
            P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
            cds = {d: c_day(d) for d in set(P["sd"])}
            P["_Cday"] = np.array([cds.get(d) or np.nan for d in P["sd"]])[bar_i]
            Ps[m] = P

        def fires(P, R):
            cx = P["cx"]
            secs, keep = P["secs"], P["keep"]
            bt = BSH * R
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
                if d0 * P["_ret2"][ib] >= TSH * np.sqrt(W / 5) * R[i]:
                    kept.append((i, d0))
            return kept

        print(f"===== {gname} - quality lane, current stack (0.022 / 0.17 / "
              f"C(day) / gap 45 / wait 1) =====")
        print("| Memory (bars) | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for nb in NB:
            per_m = {}
            for m, P in Ps.items():
                atrb = P["_trS"].shift(1).rolling(nb).mean().to_numpy()[P["_bar_i"]]
                per_m[m] = sim(P, fires(P, P["_Cday"] * atrb), lambda *a: True,
                               cooldown=WAIT)
            tag = " <= baseline (adopted)" if nb == 10 else ""
            print(row(f"{nb}{tag}", per_m))
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
