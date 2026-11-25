#!/usr/bin/env python3
"""
b3_management.py — B3: management candidates on HIS G2 fills (T-MG08).
Spec: B3_SPEC.md (committed first).
RUN: python3 Tests/B_track/b3_management.py > Tests/B_track/B3_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination",
          "P5_trade_management"):
    sys.path.insert(0, os.path.join(T, d))
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}

# ---- his G2 trades ----
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
m = F.kme_mins_since
F["np_"] = np.where(np.isfinite(m) & (m <= 5), "burst",
                    np.where(np.isfinite(m) & (m <= 45), "window", "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
G2 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                   "side"]].copy()
G2 = G2.rename(columns={"side": "side_n"})
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
G2 = G2.merge(G, left_on=["month", "sec"], right_on=["month",
              "entry_msg_s"])
assert len(G2) == 62

# ---- management engines (walk per-second excursions from the fill) ----
def sim_A(exc, ts, S, f, fwin, T1, Tmax):
    for i in range(len(exc)):
        t = ts[i]
        if exc[i] <= -S:
            return -S
        if t <= fwin and exc[i] <= -f:
            return -f
        if exc[i] >= T1:
            return T1
        if t >= Tmax:
            return exc[i]
    return exc[-1] if len(exc) else 0.0


def sim_B(exc, ts, S, arm, trail, Tmax):
    peak, armed = 0.0, False
    for i in range(len(exc)):
        peak = max(peak, exc[i])
        if peak >= arm:
            armed = True
        if armed and exc[i] <= peak - trail:
            return peak - trail
        if not armed and exc[i] <= -S:
            return -S
        if ts[i] >= Tmax:
            return exc[i]
    return exc[-1] if len(exc) else 0.0


def sim_D(exc, ts, stall, S, Tmax):
    peak, t_peak = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, t_peak = exc[i], ts[i]
        if exc[i] <= -S:
            return -S
        if ts[i] - t_peak >= stall:
            return exc[i]
        if ts[i] >= Tmax:
            return exc[i]
    return exc[-1] if len(exc) else 0.0


CELLS = []
for S in (2.5, 3.75):
    for fwin in (30, 60):
        for T1 in (2.25, 4.5):
            for Tmax in (240, 480):
                CELLS.append((f"A S{S} f1.5@{fwin}s T{T1} t{Tmax}",
                              lambda e, t, S=S, fw=fwin, T1=T1, Tm=Tmax:
                              sim_A(e, t, S, 1.5, fw, T1, Tm)))
for trail in (1.5, 2.0):
    CELLS.append((f"B arm2.25 trail{trail}",
                  lambda e, t, tr=trail: sim_B(e, t, 2.5, 2.25, tr, 480)))
for stall in (30, 60, 90):
    for S in (2.5, 3.75):
        CELLS.append((f"D stall{stall} S{S}",
                      lambda e, t, st=stall, S=S: sim_D(e, t, st, S, 480)))
CELLS.append(("M1 baseline (stall30 stop4 t27m)",
              lambda e, t: sim_D(e, t, 30, 4.0, 1620)))

# ---- walk ----
res = {name: [] for name, _ in CELLS}
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in G2[G2.month == mo].iterrows():
        if not np.isfinite(r.entry_price):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        if j2 - j1 < 10:
            continue
        exc = (mids[j1:j2] - r.entry_price) * r.side_n
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        for name, fn in CELLS:
            res[name].append(fn(exc, ts))

HIS_NET = G2.pnl_stated.sum()
print("# B3 REPORT — MANAGEMENT ON HIS G2 FILLS (T-MG08)")
print("STATUS: CLOSED | 2026-11-25 | Spec: B3_SPEC.md (committed first)")
print()
print(f"62 trades, his fills, our exits. HIS actual: {HIS_NET:+.1f} pts, "
      "74% win, +5.71 / -1.97, worst -3.75.")
print()
print("| candidate | net | win | avg win / loss | worst | share of his |")
print("|---|---|---|---|---|---|")
rows = []
for name, _ in CELLS:
    a = np.array(res[name])
    w = a > 0
    rows.append((a.sum(), name, w.mean(),
                 a[w].mean() if w.any() else 0,
                 a[~w].mean() if (~w).any() else 0, a.min()))
for net, name, wr, aw, al, worst in sorted(rows, reverse=True):
    print(f"| {name} | {net:+.1f} | {wr:.0%} | +{aw:.2f} / {al:.2f} | "
          f"{worst:+.2f} | {net / HIS_NET:.0%} |")
print()
print("Selection rule (pre-stated): top 3 by net whose parameter-"
      "neighbors are also positive go to B4.")
print("Registry: T-MG08.")
