#!/usr/bin/env python3
"""
p6_30_m1_momentum_char.py — CYCLE-2 M-1: CHARACTERIZE THE UNCAUGHT. (T-IM37.)
Battery features at V1-UNCAUGHT entry seconds vs V1-CAUGHT vs ambient null
(time-of-day matched). Descriptive only. 2025-10.
RUN: python3 Tests/P6_imitation_study/p6_30_m1_momentum_char.py        (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_0_feature_battery import build_ctx, battery
from p4_2_entry_context import month_bounds

RNG = np.random.default_rng(127)
FEATS = ["mv8", "mv20", "mv60", "mv120", "mv300", "rng300", "comp300",
         "volr2", "vrate60", "vratio60_30m", "flow1", "flow5", "bursts5",
         "burst_silence", "stall_5m_extreme", "day_pos", "mins_open",
         "kme_mins_since", "sig_samedir_5m", "sig_best_score"]


def run(repo="."):
    C = build_ctx(repo, "2025-10")
    D = pd.read_parquet(os.path.join(repo, "Data/inputs/s6_selectors_final.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds("2025-10")
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    v1 = D["V1 rea&sig"].to_numpy()
    rows = []
    for i, (_, r) in enumerate(em.iterrows()):
        t = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        d = 1 if r.side == "long" else -1
        f = battery(C, t, d=d)
        if f is None:
            continue
        f["grp"] = "caught" if v1[i] else "UNCAUGHT"
        f["pnl"] = r.realized_pnl
        rows.append(f)
        for _ in range(10):
            t2 = t + int(RNG.integers(-1800, 1800)) + 86400 * int(RNG.integers(-8, 9))
            f2 = battery(C, t2, d=d if RNG.random() < 0.5 else -d)
            if f2 is not None:
                f2["grp"] = "null"; f2["pnl"] = np.nan
                rows.append(f2)
    X = pd.DataFrame(rows)
    print(f"groups: {dict(X.grp.value_counts())}\n")
    print("| feature | UNCAUGHT med | caught med | null med |")
    print("|---|---|---|---|")
    for c in FEATS:
        if c not in X:
            continue
        g = X.groupby("grp")[c].median()
        print(f"| {c} | {g.get('UNCAUGHT', np.nan):.2f} | {g.get('caught', np.nan):.2f} | {g.get('null', np.nan):.2f} |")
    u = X[X.grp == "UNCAUGHT"]
    print(f"\nUNCAUGHT pnl: total {u.pnl.sum():+.1f}, mean {u.pnl.mean():+.2f}, "
          f"n>0 {int((u.pnl>0).sum())}/{len(u)}")
    c_ = X[X.grp == "caught"]
    print(f"caught   pnl: total {c_.pnl.sum():+.1f}, mean {c_.pnl.mean():+.2f}, "
          f"n>0 {int((c_.pnl>0).sum())}/{len(c_)}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
