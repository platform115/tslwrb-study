#!/usr/bin/env python3
"""
p6_31_m2_momentum_grid.py — CYCLE-2 M-2: MOMENTUM-STATE GRID. (T-IM38.)
===============================================================================
PRE-REGISTERED RANGES (user: test the variables with ranges):
  bursts5   >= {6, 8, 10, 12}        (bursts in last 5 min)
  silence   <= {30, 60, 90} s        (since last burst)
  mv60      >= {1, 2, 3, 4} ticks    (aligned 60-s move)
  add-on A: flow1 aligned > {0, 1} c/s
  add-on B: vrate60 >= {30, 40, 50} c/s
Base grid 4x3x4 = 48 cells; each add-on evaluated on EVERY base cell
(48 + 48*2 + 48*3 = 288 cells, all computed, all saved; printout shows the
base grid and the efficiency frontier). DECISION METRIC (pre-named):
catch of the 57 V1-uncaught entries vs fires/day - the frontier, not a
single winner. All components honest/<=t (battery machinery, T-EN101-class).

RUN: python3 Tests/P6_imitation_study/p6_31_m2_momentum_grid.py        (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P5_trade_management"))
from p6_0_feature_battery import build_ctx
from p4_2_entry_context import month_bounds

DEDUP = 300


def run(repo="."):
    C = build_ctx(repo, "2025-10")
    secs, mids = C["secs"], C["mids"]
    TICK = 0.25
    # per-second arrays, all <=t
    cb = np.concatenate([[0], np.cumsum(C["burst"].astype(np.int64))])
    i300 = np.searchsorted(secs, secs - 300)
    bursts5 = cb[np.arange(len(secs)) + 1] - cb[i300]
    lastb = np.full(len(secs), -1e12)
    lb = -1e12
    barr = C["burst"]
    for i in range(len(secs)):
        if barr[i]:
            lb = secs[i]
        lastb[i] = lb
    silence = secs - lastb
    i60 = np.searchsorted(secs, secs - 60)
    mv60 = (mids - mids[np.maximum(i60, 0)]) / TICK
    csv_, ctv = C["csv"], C["ctv"]
    flow1 = (csv_[np.arange(len(secs)) + 1] - csv_[i60]) / 60.0
    vrate60 = (ctv[np.arange(len(secs)) + 1] - ctv[i60]) / 60.0

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds("2025-10")
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    D = pd.read_parquet(os.path.join(repo, "Data/inputs/s6_selectors_final.parquet"))
    v1 = D["V1 rea&sig"].to_numpy()
    ej, eside, eunc = [], [], []
    for i, (_, r) in enumerate(em.iterrows()):
        t = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        j = int(np.searchsorted(secs, t, "right")) - 1
        if j < 4000:
            continue
        ej.append(j); eside.append(1 if r.side == "long" else -1)
        eunc.append(not v1[i])
    ej = np.array(ej); eside = np.array(eside); eunc = np.array(eunc)
    n_unc = int(eunc.sum()); n_all = len(ej)
    ndays = len(set(C["sd_sec"]))
    grid30 = np.arange(0, len(secs), 30)

    def score(cond_fn, label, rows):
        """cond_fn(j_array, d) -> bool array."""
        cu = cond_fn(ej, eside)
        catch_unc = int((cu & eunc).sum()); catch_all = int(cu.sum())
        fires = 0
        for d in (1, -1):
            c = cond_fn(grid30, np.full(len(grid30), d))
            idx = grid30[c]
            last = -1e12
            for j in idx:
                if secs[j] - last > DEDUP:
                    fires += 1; last = secs[j]
        rows.append(dict(cell=label, catch_unc=catch_unc, unc_pct=catch_unc / n_unc,
                         catch_all=catch_all, fires_day=fires / ndays))

    rows = []
    for B in (6, 8, 10, 12):
        for S in (30, 60, 90):
            for M in (1, 2, 3, 4):
                def base(j, d, B=B, S=S, M=M):
                    return (bursts5[j] >= B) & (silence[j] <= S) & (d * mv60[j] >= M)
                score(base, f"B{B}/S{S}/M{M}", rows)
                for F in (0, 1):
                    score(lambda j, d, B=B, S=S, M=M, F=F:
                          base(j, d) & (np.asarray(d) * flow1[j] > F),
                          f"B{B}/S{S}/M{M}+F{F}", rows)
                for V in (30, 40, 50):
                    score(lambda j, d, B=B, S=S, M=M, V=V:
                          base(j, d) & (vrate60[j] >= V),
                          f"B{B}/S{S}/M{M}+V{V}", rows)
        print(".", end="", flush=True)
    R = pd.DataFrame(rows)
    R.to_csv(os.path.join(repo, "Tests/P6_imitation_study/m2_momentum_grid_cells.csv"), index=False)
    print(f"\n\n===== M-2 GRID ({len(R)} cells; {n_unc} uncaught targets, {n_all} entries, {ndays} sessions) =====")
    base_rows = R[~R.cell.str.contains(r"\+")]
    print("## base grid (all 48 cells)")
    print("| cell | uncaught catch | all catch | fires/day |")
    for _, r in base_rows.iterrows():
        print(f"| {r.cell} | {r.catch_unc}/{n_unc} ({r.unc_pct:.0%}) | {r.catch_all}/{n_all} | {r.fires_day:.0f} |")
    print("\n## efficiency frontier (all 288 cells; best uncaught-catch at each fires/day band)")
    R["band"] = pd.cut(R.fires_day, [0, 10, 20, 40, 80, 160, 1e9],
                       labels=["<=10", "10-20", "20-40", "40-80", "80-160", ">160"])
    for b, g in R.groupby("band", observed=True):
        if not len(g):
            continue
        top = g.sort_values("catch_unc", ascending=False).head(3)
        for _, r in top.iterrows():
            print(f"  {b}: {r.cell} -> uncaught {r.catch_unc}/{n_unc} ({r.unc_pct:.0%}), "
                  f"all {r.catch_all}/{n_all}, fires/day {r.fires_day:.0f}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
