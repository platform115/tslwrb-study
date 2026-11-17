#!/usr/bin/env python3
"""
p4_73_thrust_window.py — P4.73 / Strategy 2: the THRUST WINDOW varied
(2/3/5/7/10 min), under FIXED / ATR14D / INTRADAY10. TRAINING MONTHS ONLY.
===========================================================================
User grid. Scaling rule (declared, flagged): thrust thresholds scale by
sqrt(window/5) - square-root-of-time - so selectivity is comparable across
windows. FIXED thrust: 32/39/50/59/71 tk; adapters: share = 0.17 x sqrt(w/5).
Schemes:
  FIXED      burst 13 tk / 7 s (reference - known to work in training)
  ATR14D     burst 0.042 x R_est / 8 s; R_est = trailing-14-session mean range
  INTRADAY10 burst 0.042 x 22.7 x meanTR(last 10 completed bars) / 8 s
All else unchanged: direction = burst sign, no signal, no session cut, 120 s
clustering, 5-bar cooldown, v11 sketch management, mid fills.

RUN: python3 Tests/P4_entry_determination/p4_73_thrust_window.py          (repo root)
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
WINDOWS = (2, 3, 5, 7, 10)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    for m, P in Ps.items():
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        for w_s in (7, 8):
            iw = np.searchsorted(secs, secs - w_s)
            P[f"_mv{w_s}"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        h_, l_, c_ = cx.h, cx.l, cx.c
        pc = np.roll(c_, 1); pc[0] = c_[0]
        tr = np.maximum(h_ - l_, np.maximum(np.abs(h_ - pc), np.abs(l_ - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        P["_retw"] = {w: np.concatenate([[0.0] * w, (c_[w:] - c_[:-w]) / TICK]) for w in WINDOWS}
        P["_Rday"] = {d: atr14d(d) for d in set(P["sd"])}

    def fires(P, scheme):
        secs = P["secs"]; keep = P["keep"]
        if scheme == "FIXED":
            mv = P["_mv7"]; bt = np.full(len(secs), 13.0)
        elif scheme == "ATR14D":
            mv = P["_mv8"]
            Rs = np.array([P["_Rday"].get(d) or np.nan for d in P["sd"]])[P["_bar_i"]]
            bt = BURST_SHARE * Rs
        else:
            mv = P["_mv8"]
            bt = BURST_SHARE * C_N * P["_atr10"][P["_bar_i"]]
        out = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(bt)):
            if abs(mv[i]) < bt[i]:
                continue
            if secs[i] - last > CLUST:
                out.append(i)
                last = secs[i]
        return out, mv

    print("Scaling rule: thrust threshold x sqrt(window/5). FIXED thrust by window:")
    print("  " + ", ".join(f"{w}m: {50*np.sqrt(w/5):.0f}tk" for w in WINDOWS) + "\n")
    for scheme in ("FIXED", "ATR14D", "INTRADAY10"):
        print(f"===== {scheme} =====")
        print("| Thrust window | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for w in WINDOWS:
            scale = np.sqrt(w / 5)
            per_m = {}
            for m, P in Ps.items():
                fl, mv = fires(P, scheme)
                retw = P["_retw"][w]
                kept = []
                for i in fl:
                    d0 = int(np.sign(mv[i]))
                    ib = P["_bar_i"][i]
                    if ib < 60 or not P["cx"].rth[ib]:
                        continue
                    if scheme == "FIXED":
                        tthr = 50.0 * scale
                    elif scheme == "ATR14D":
                        R = P["_Rday"].get(P["sd"][ib])
                        if not R:
                            continue
                        tthr = THRUST_SHARE * scale * R
                    else:
                        tthr = THRUST_SHARE * scale * C_N * P["_atr10"][ib]
                        if not np.isfinite(tthr):
                            continue
                    if d0 * retw[ib] >= tthr:
                        kept.append((i, d0))
                per_m[m] = sim(P, kept, lambda *a: True)
            tag = " <= current" if w == 5 else ""
            print(row(f"{w} min{tag}", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
