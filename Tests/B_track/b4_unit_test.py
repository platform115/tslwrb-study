#!/usr/bin/env python3
"""
b4_unit_test.py — B4: Strategy 4 x M3 joint unit test (T-BS05).
Spec: B4_SPEC.md (committed first).
RUN: python3 Tests/B_track/b4_unit_test.py > Tests/B_track/B4_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = ["2025-10", "2022-02"]

# ---- management (returns pnl, exit_index, mae) ----
def m3_stall(exc, ts, stall, S=3.75, Tmax=480):
    peak, t_peak = 0.0, 0
    mae = 0.0
    for i in range(len(exc)):
        mae = min(mae, exc[i])
        if exc[i] > peak:
            peak, t_peak = exc[i], ts[i]
        if exc[i] <= -S:
            return -S, i, -mae
        if ts[i] - t_peak >= stall or ts[i] >= Tmax:
            return exc[i], i, -mae
    return (exc[-1], len(exc) - 1, -mae) if len(exc) else (0.0, 0, 0.0)


def m3c(exc, ts, S=3.75, f=1.5, fwin=30, T1=4.5, Tmax=480):
    mae = 0.0
    for i in range(len(exc)):
        mae = min(mae, exc[i])
        if exc[i] <= -S:
            return -S, i, -mae
        if ts[i] <= fwin and exc[i] <= -f:
            return -f, i, -mae
        if exc[i] >= T1:
            return T1, i, -mae
        if ts[i] >= Tmax:
            return exc[i], i, -mae
    return (exc[-1], len(exc) - 1, -mae) if len(exc) else (0.0, 0, 0.0)


MGMT = {"M3A": lambda e, t: m3_stall(e, t, 60),
        "M3B": lambda e, t: m3_stall(e, t, 90),
        "M3C": m3c}
ENTRIES = {"4A": lambda d: np.ones(len(d), bool),
           "4B": lambda d: ((d.mv15 > 0) & (d.flow1 > 0)).to_numpy()}

D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
# his G2 targets
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                    "side"]]
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
HISP = {mo: G.merge(HIS[HIS.month == mo], left_on=["month",
        "entry_msg_s"], right_on=["month", "sec"]).pnl_stated
        for mo in MONTHS}

CTX = {mo: prep(".", mo) for mo in MONTHS}

print("# B4 REPORT — STRATEGY 4 x M3 JOINT UNIT TEST (T-BS05)")
print("STATUS: CLOSED | 2026-11-25 | Spec: B4_SPEC.md (committed first) "
      "| harness: fills from the certified B2 scan; exits forward walks")
print()
print("HIS G2, same periods: 62 trades | 74% win | +262.8 / -31.5 | net "
      "+231.2 | +5.71 / -1.97 | worst -3.75 | (per month: 22-02 +85.5 on "
      "40; 25-10 +145.8 on 22)")
print()
rows_out = []
for ename, efun in ENTRIES.items():
    for disp in (1.25, 2.50):
        for mname, mfun in MGMT.items():
            combo = f"{ename} d{disp} x {mname}"
            pooled = dict(trades=0, wins=0, pw=0.0, pl=0.0, worst=0.0,
                          mae=0.0, caught=0, extras=0, extras_net=0.0,
                          dd=0.0, nets={})
            for mo in MONTHS:
                secs, mids = CTX[mo]["secs"], CTX[mo]["mids"]
                sub = D[(D.month == mo) & (D.disp == disp)]
                sub = sub[efun(sub)].sort_values("tf")
                his_m = HIS[HIS.month == mo]
                busy = -10**12
                trades = []
                for _, r in sub.iterrows():
                    if r.tf < busy:
                        continue
                    lvl = r.edge + disp * r.d
                    j1 = int(np.searchsorted(secs, int(r.tf)))
                    j2 = int(np.searchsorted(secs, int(r.tf) + 1800,
                                             "right"))
                    if j2 - j1 < 5:
                        continue
                    exc = (mids[j1:j2] - lvl) * r.d
                    ts = (secs[j1:j2] - int(r.tf)).astype(int)
                    pnl, ix, mae = mfun(exc, ts)
                    busy = int(secs[j1 + ix])
                    trades.append((int(r.tf), int(r.d), pnl, mae))
                tr = pd.DataFrame(trades, columns=["tf", "d", "pnl",
                                                   "mae"])
                net = tr.pnl.sum()
                pooled["nets"][mo] = net
                pooled["trades"] += len(tr)
                pooled["wins"] += (tr.pnl > 0).sum()
                pooled["pw"] += tr.pnl[tr.pnl > 0].sum()
                pooled["pl"] += tr.pnl[tr.pnl <= 0].sum()
                pooled["worst"] = min(pooled["worst"], tr.pnl.min()
                                      if len(tr) else 0)
                pooled["mae"] = max(pooled["mae"], tr.mae.max()
                                    if len(tr) else 0)
                eq = tr.pnl.cumsum()
                dd = float((eq.cummax() - eq).max()) if len(tr) else 0.0
                pooled["dd"] = max(pooled["dd"], dd)
                # catch + extras
                for _, h in his_m.iterrows():
                    if ((tr.d == h.side) & (abs(tr.tf - h.sec)
                                            <= 300)).any():
                        pooled["caught"] += 1
                near = np.zeros(len(tr), bool)
                for _, h in his_m.iterrows():
                    near |= (np.abs(tr.tf - h.sec) <= 300).to_numpy()
                pooled["extras"] += int((~near).sum())
                pooled["extras_net"] += tr.pnl[~near].sum()
            rows_out.append((combo, pooled))

print("## SUMMARY — ALL 12 COMBOS (pooled over both months)")
print("| combo | trades | win | net (22-02 / 25-10) | avg win/loss | "
      "worst | max MAE | max DD | caught /62 | extras | extras net |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for combo, p in sorted(rows_out,
                       key=lambda kv: -(sum(kv[1]["nets"].values()))):
    net = sum(p["nets"].values())
    aw = p["pw"] / p["wins"] if p["wins"] else 0
    nl = p["trades"] - p["wins"]
    al = p["pl"] / nl if nl else 0
    print(f"| {combo} | {p['trades']} | {p['wins']/max(1,p['trades']):.0%}"
          f" | {net:+.1f} ({p['nets']['2022-02']:+.1f} / "
          f"{p['nets']['2025-10']:+.1f}) | +{aw:.2f} / {al:.2f} | "
          f"{p['worst']:+.2f} | {p['mae']:.2f} | {p['dd']:.1f} | "
          f"{p['caught']} | {p['extras']} | {p['extras_net']:+.1f} |")
print()
qual = [(sum(p["nets"].values()), c, p) for c, p in rows_out
        if all(v > 0 for v in p["nets"].values())
        and p["extras_net"] >= 0]
print("## WINNER RULE (pre-stated: positive BOTH months AND extras "
      "net >= 0; highest pooled net)")
if qual:
    net, c, p = max(qual)
    print(f"WINNER: {c} - pooled {net:+.1f}, months "
          f"{p['nets']['2022-02']:+.1f} / {p['nets']['2025-10']:+.1f}, "
          f"caught {p['caught']}/62, extras net {p['extras_net']:+.1f}.")
    print(f"Qualifying combos: {len(qual)} of 12.")
else:
    print("NO COMBO QUALIFIES - honest fail; back to design.")
print()
print("Footer: fills = certified B2 scan (mid-cross stop orders); "
      "single position; fees ~0 per J; regime = training months only; "
      "2024-11 untouched. Registry: T-BS05.")
