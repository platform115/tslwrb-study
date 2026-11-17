#!/usr/bin/env python3
"""
p4_67_trigger_grid.py — P4.67 / Strategy 2: burst-trigger window x threshold
grid (user-specified). TRAINING MONTHS ONLY.
=============================================================================
Varied (user's grid):
  window: 5, 7, 10, 12, 15, 20, 30 seconds (10 s = the old fixed choice)
  threshold: top 1% (windows 5-20), top 0.5% and top 2% (all windows)
Held unchanged: thrust context (run under BOTH leading combos: thrust 30 and
thrust 50 toward trade direction, no old-signal requirement, no session cut),
direction = burst sign, 120 s clustering, mid fills, v11 sketch management,
5-bar cooldown. Both ledgers: total P&L and his-entries matched (120 s, same
direction). Ranked by total within each context block.

RUN: python3 Tests/P4_entry_determination/p4_67_trigger_grid.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_66_context_ablation import prep, sim           # noqa: E402

TICK = 0.25
CLUST, MATCH_S = 120, 120
GRID = [(1.0, w) for w in (5, 7, 10, 12, 15, 20)] + \
       [(0.5, w) for w in (5, 7, 10, 12, 15, 20, 30)] + \
       [(2.0, w) for w in (5, 7, 10, 12, 15, 20, 30)]


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    his = {}
    for m, _ in MONTHS:
        lo, hi = month_bounds(m)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        his[m] = (np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc],
                           dtype=np.int64),
                  np.array([1 if s == "long" else -1 for s in e_m.side]))
    # precompute per-window move arrays and fire lists per (pct, window)
    fires = {}
    thr_note = {}
    for m, P in Ps.items():
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        for pct, w in GRID:
            iw = np.searchsorted(secs, secs - w)
            mv = (mids - mids[np.maximum(iw, 0)]) / TICK
            st = np.abs(mv)
            thr = np.percentile(st[keep], 100 - pct)
            thr_note.setdefault((pct, w), []).append(thr)
            fl = []
            last = -10**18
            for i in np.flatnonzero(keep & (st >= thr)):
                if secs[i] - last > CLUST:
                    fl.append((i, int(np.sign(mv[i]))))
                    last = secs[i]
            fires[(m, pct, w)] = fl

    def CTX(thrust):
        def f(ft, ib, d0, P, a2, b2):
            return ft["ret5m"] >= thrust
        return f

    for thrust in (30, 50):
        print(f"\n===== context: thrust >= {thrust} ticks / 5 min, no signal, no session "
              f"cut — ranked by total =====")
        print("| Trigger (top %, window) | ~Threshold (ticks) | Trades | His matched | "
              "Win rate | Avg win / loss | Total (Oct / Feb) | Max below start |")
        print("|---|---|---|---|---|---|---|---|")
        out = []
        for pct, w in GRID:
            per_m = {}
            matched = 0
            for m, P in Ps.items():
                fl = fires[(m, pct, w)]
                pnl = sim(P, fl, CTX(thrust))
                per_m[m] = pnl
                hs, hd = his[m]
                # matched: fires passing context that sit near his entries
                # (recompute cheaply: re-run selection logic on fire list)
                for i, d0 in fl:
                    s0 = int(P["secs"][i])
                    ib = int(np.searchsorted(P["cx"].bts, s0 * 10**9)) - 1
                    if ib < 60 or not P["cx"].rth[ib]:
                        continue
                    ft = P["feats"](ib, d0, s0)
                    if ft["ret5m"] >= thrust and \
                            ((np.abs(hs - s0) <= MATCH_S) & (hd == d0)).any():
                        matched += 1
            allp = sum(per_m.values(), [])
            a = np.asarray(allp); wn = a > 0
            dd0 = max((-min(0.0, float(np.min(np.cumsum(p)))) if p else 0.0)
                      for p in per_m.values())
            t_avg = np.mean(thr_note[(pct, w)])
            out.append((a.sum(), pct, w, t_avg, len(a), matched, wn, a, per_m, dd0))
        for tot, pct, w, t_avg, n, matched, wn, a, per_m, dd0 in sorted(out, reverse=True):
            pm = " / ".join(f"{sum(p):+.0f}" for p in per_m.values())
            aw = f"+{a[wn].mean():.2f}" if wn.any() else "-"
            al = f"{a[~wn].mean():.2f}" if (~wn).any() else "-"
            mark = " <= old fixed choice" if (pct, w) == (1.0, 10) else ""
            print(f"| top {pct}%, {w}s{mark} | {t_avg:.0f} | {n} | {matched} | "
                  f"{wn.mean():.0%} | {aw} / {al} | {tot:+.1f} ({pm}) | {dd0:.1f} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
