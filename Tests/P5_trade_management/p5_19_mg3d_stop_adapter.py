#!/usr/bin/env python3
"""
p5_19_mg3d_stop_adapter.py — MG-3d: STOP AS A SHARE OF R_est. (T-MG07.)
===============================================================================
The chartered stop adapter (p5_10 notes: points-fixed stops cannot carry
across regimes). Cells, pre-registered:
  stall S=90 (270 ETH) fixed; stop = share x R_est, share grid CORRECTED to {0.08, 0.12, 0.17} after the first run collapsed
  into the 8-pt clip (R_est medians 28-45 pts; disclosed in the report);
  stop clipped to [1.5, 10.0] pts. Baselines: M1 (S=30, stop 4.0), S=90 stop 4.0, HIS.
FREEZE CRITERION: one single share must win pooled over BOTH baselines
and not be the worst mechanical plan in any month -> frozen as M2.

RUN: python3 Tests/P5_trade_management/p5_19_mg3d_stop_adapter.py      (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p5_10_stall_stack_dials import leg
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
import p5_1_excursion_anatomy as X

TICK = 0.25


def run(repo="."):
    c_day = X.c_day_fun(repo)
    months = ["2025-10", "2022-02", "2021-09"]
    plans = ["HIS", "M1 (S30/stop4)", "S90/stop4", "S90/R.08", "S90/R.12", "S90/R.17"]
    pooled = {k: [] for k in plans}
    worst = []
    for month in months:
        P = prep(repo, month, insample=(month == "2025-10"))
        cx = P["cx"]
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        cds = {d: c_day(d) for d in set(P["sd"])}
        ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                             ).dropna(subset=["first_entry_utc"])
        lo, hi = month_bounds(month)
        em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        res = {k: [] for k in plans}
        stops_used = []
        for _, r in em.iterrows():
            s0 = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
            d = 1 if r.side == "long" else -1
            ib = int(np.searchsorted(cx.bts, s0 * 10**9, "right")) - 1
            if ib < 60:
                continue
            ents = np.atleast_1d(r.entry_prices).astype(float)
            exts = np.atleast_1d(r.exit_prices).astype(float)
            ents, exts = ents[np.isfinite(ents)], exts[np.isfinite(exts)]
            if not len(ents) or not len(exts):
                continue
            fill = float(ents[0])
            res["HIS"].append((exts.mean() - ents.mean()) * d)
            eth = not cx.rth[ib]
            Rpts = (cds.get(P["sd"][ib]) or np.nan) * atr10[ib] * TICK
            for k in plans[1:]:
                if k == "M1 (S30/stop4)":
                    S, stp = 30, 4.0
                elif k == "S90/stop4":
                    S, stp = 90, 4.0
                else:
                    share = float(k.split("R.")[1]) / 100 if False else {"S90/R.08": .08, "S90/R.12": .12, "S90/R.17": .17}[k]
                    S = 90
                    stp = float(np.clip(share * Rpts, 1.5, 10.0)) if np.isfinite(Rpts) else 4.0
                q = dict(early=stp, stop=stp, time_bars=27, S=S * (3 if eth else 1))
                px, xs, xb, _ = leg(cx, ib, fill, s0, d > 0, q)
                res[k].append((px - fill) * d)
                if k == "S90/R.12":
                    stops_used.append(stp)
        print(f"\n===== {month} ({len(res['HIS'])} episodes) | R.12 stop q25/50/75 = "
              f"{np.percentile(stops_used,25):.1f}/{np.percentile(stops_used,50):.1f}/{np.percentile(stops_used,75):.1f} pts =====")
        print("| plan | Win rate | Avg win / loss | Total |")
        tot = {}
        for k in plans:
            a = np.asarray(res[k]); wn = a > 0
            tot[k] = a.sum()
            print(f"| {k} | {wn.mean():.0%} | +{a[wn].mean():.2f} / {a[~wn].mean():.2f} | {a.sum():+.1f} |")
            pooled[k] += list(a)
        mech = {k: tot[k] for k in plans[1:]}
        worst.append(min(mech, key=mech.get))
    print("\n===== POOLED =====")
    for k in plans:
        a = np.asarray(pooled[k])
        print(f"| {k} | {(a>0).mean():.0%} | {a.sum():+.1f} |")
    base = max(np.sum(pooled["M1 (S30/stop4)"]), np.sum(pooled["S90/stop4"]))
    print("\nFREEZE CHECK per share:")
    for k in ("S90/R.08", "S90/R.12", "S90/R.17"):
        win = np.sum(pooled[k]) > base
        w = k in worst
        print(f"  {k}: pooled win {win}, worst-in-a-month {w} -> {'PASS' if win and not w else 'fail'}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
