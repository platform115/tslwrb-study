#!/usr/bin/env python3
"""
p4_88_atr_memory.py — P4.88 / Strategy 2: the ATR14D MEMORY varied.
TRAINING MONTHS ONLY.
===============================================================================
In the adopted volume lane (post-batch-4), the burst leg runs on the trailing
85th-pct rule and does NOT use ATR14D - the N-session day-range memory now
feeds ONLY the thrust requirement. This round varies that memory:
  N sessions in {1, 2, 3, 5, 7, 12, 14 (baseline), 15}
  plus intraday replacements for the thrust scale (recent bars, as in the
  earlier INTRADAY rounds): C_N x mean TR of the last {10, 30, 60} bars.
Everything else frozen at the adopted lane config: burst = trailing 85th pct
of raw |8-s move| (expanding in-month, min 1 prior session - the tested
form), thrust share 0.13, 45 s gap, 1-bar wait. Quality lane untouched (it
has no ATR14D memory). The trailing-pct rule's own session window (also 14
by convention) is NOT varied here - flagged as a separate dial.

RUN: python3 Tests/P4_entry_determination/p4_88_atr_memory.py              (repo root)
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
TSH = 0.13
NS = (1, 2, 3, 5, 7, 12, 14, 15)
NBARS = (10, 30, 60)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atrN(d, N):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - N):i].mean()) if i and i > 0 else None

    Ps = {}
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_trS"] = pd.Series(tr)
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        P["_sd_sec"] = np.asarray(P["sd"])[bar_i]
        # burst threshold: trailing 85th pct of raw |mv8| (tested form)
        sd = P["_sd_sec"]; keep = P["keep"]
        days = pd.unique(sd[keep])
        thr = np.full(len(secs), np.nan)
        for k, d in enumerate(days):
            prior = keep & np.isin(sd, days[:k])
            if prior.any():
                thr[sd == d] = float(np.percentile(np.abs(P["_mv8"])[prior], 85))
        P["_bthr"] = thr
        Ps[m] = P

    def fires(P, Rthr):
        cx = P["cx"]
        secs, keep = P["secs"], P["keep"]
        kept = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(P["_bthr"]) & np.isfinite(Rthr)):
            if abs(P["_mv8"][i]) < P["_bthr"][i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = P["_bar_i"][i]
            if ib < 60 or not cx.rth[ib]:
                continue
            d0 = int(np.sign(P["_mv8"][i]))
            if d0 * P["_ret2"][ib] >= TSH * np.sqrt(W / 5) * Rthr[i]:
                kept.append((i, d0))
        return kept

    print("ATR14D memory varied - feeds ONLY the thrust scale in the adopted "
          "volume lane (burst = trail-pct85, thrust 0.13, gap 45, wait 1). "
          "Training months only.\n")
    print("| Thrust scale memory | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for N in NS:
        per_m = {}
        for m, P in Ps.items():
            Rd = {d: atrN(d, N) for d in set(P["sd"])}
            Rthr = np.array([Rd.get(d) or np.nan for d in P["sd"]])[P["_bar_i"]]
            per_m[m] = sim(P, fires(P, Rthr), lambda *a: True, cooldown=WAIT)
        tag = " <= baseline (adopted)" if N == 14 else ""
        print(row(f"{N} sessions{tag}", per_m))
    for nb in NBARS:
        per_m = {}
        for m, P in Ps.items():
            atrb = P["_trS"].shift(1).rolling(nb).mean().to_numpy()
            Rthr = (C_N * atrb)[P["_bar_i"]]
            per_m[m] = sim(P, fires(P, Rthr), lambda *a: True, cooldown=WAIT)
        print(row(f"intraday: last {nb} bars x C_N", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
