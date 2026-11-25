#!/usr/bin/env python3
"""
m5_round.py — M5: decision-framework exits (T-MG11). Spec: M5_SPEC.md
(committed first).
RUN: python3 Tests/P5_trade_management/m5_round.py > Tests/P5_trade_management/M5_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
STOP, CAP = 3.75, 900


def m3a(exc, ts):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if exc[i] <= -STOP:
            return -STOP, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def m5a(exc, ts, decay):
    peak = 0.0
    trail = 2.0
    armed = False
    last_step = 0.0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak = exc[i]
            if peak >= 1.5:
                armed = True
            while peak - last_step >= 0.5:
                last_step += 0.5
                trail = max(0.75, trail * decay)
        if exc[i] <= -STOP:
            return -STOP, i
        if armed and exc[i] <= peak - trail:
            return peak - trail, i
        if ts[i] >= CAP:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def m5b(exc, ts, tfast, tight):
    peak, tp = 0.0, 0
    mode = None          # None until +2.25 decided or stall path
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if mode is None and peak >= 2.25:
            mode = "fast" if ts[i] <= tfast else "slow"
        if exc[i] <= -STOP:
            return -STOP, i
        if mode == "fast":
            if exc[i] <= peak - tight:
                return peak - tight, i
        else:  # slow or undecided -> patient M3A behavior
            if ts[i] - tp >= 60:
                return exc[i], i
        if ts[i] >= CAP if mode == "fast" else ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def oracle(exc, ts):
    """Hindsight best of (M3A, spike-take at peak-0.75 in first 120s)."""
    a, _ = m3a(exc, ts)
    j = int(np.searchsorted(ts, 120, "right"))
    b = (exc[:j].max() - 0.75) if j > 0 and exc[:j].max() >= 0.75 else a
    return max(a, b), 0


CANDS = {"M5A decay0.8": lambda e, t: m5a(e, t, 0.8),
         "M5A decay0.9": lambda e, t: m5a(e, t, 0.9),
         "M5B f20 tight0.75": lambda e, t: m5b(e, t, 20, 0.75),
         "M5B f20 tight1.0": lambda e, t: m5b(e, t, 20, 1.0),
         "M5B f40 tight0.75": lambda e, t: m5b(e, t, 40, 0.75),
         "M5B f40 tight1.0": lambda e, t: m5b(e, t, 40, 1.0),
         "M3A baseline": m3a,
         "DUAL ORACLE (hindsight diagnostic)": oracle}

# his 62
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
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                      "side"]]
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = HIS62.merge(G, left_on=["month", "sec"],
                 right_on=["month", "entry_msg_s"], suffixes=("_f", ""))
GT["sd_n"] = GT.side.map({"long": 1, "short": -1})

print("# M5 REPORT — DECISION-FRAMEWORK EXITS (T-MG11)")
print("STATUS: CLOSED | 2026-11-25 | Spec: M5_SPEC.md (committed first)")
print()
res = {n: [] for n in CANDS}
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not np.isfinite(r.entry_price):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.sd_n
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        for n, fn in CANDS.items():
            res[n].append(fn(exc, ts)[0])
print("## STAGE 1 — HIS 62 FILLS (qualify: net > M3A's +123.9)")
print("| candidate | net | win | avg win/loss | worst | share of his |")
print("|---|---|---|---|---|---|")
quals = []
for n in CANDS:
    a = np.array(res[n])
    w = a > 0
    net = a.sum()
    print(f"| {n} | {net:+.1f} | {w.mean():.0%} | +{a[w].mean():.2f} / "
          f"{a[~w].mean():.2f} | {a.min():+.2f} | {net/231.2:.0%} |")
    if net > 123.9 and "baseline" not in n and "ORACLE" not in n:
        quals.append(n)
print()
print(f"Stage-1 qualifiers: {quals if quals else 'NONE'}")
print()
# stage 2
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
print("## STAGE 2 — JOINT (adopt: > +135.8, both months > 0, extras "
      ">= 0, catch >= 39)")
print("| candidate | trades | net (22-02/25-10) | caught/62 | extras "
      "net | ADOPT? |")
print("|---|---|---|---|---|---|")
for n in quals + ["M3A baseline"]:
    fn = CANDS[n]
    allt = []
    for mo in MONTHS:
        P = prep(".", mo)
        secs, mids = P["secs"], P["mids"]
        sub = D[(D.month == mo) & (D.disp == 1.25)].sort_values("tf")
        busy = -10**12
        for _, r in sub.iterrows():
            if r.tf < busy:
                continue
            lvl = r.edge + 1.25 * r.d
            j1 = int(np.searchsorted(secs, int(r.tf)))
            j2 = int(np.searchsorted(secs, int(r.tf) + 1800, "right"))
            if j2 - j1 < 5:
                continue
            exc = (mids[j1:j2] - lvl) * r.d
            ts = (secs[j1:j2] - int(r.tf)).astype(int)
            pnl, ix = fn(exc, ts)
            busy = int(secs[j1 + ix])
            allt.append((mo, int(r.tf), int(r.d), pnl))
    tr = pd.DataFrame(allt, columns=["month", "tf", "d", "pnl"])
    nets = tr.groupby("month").pnl.sum()
    caught = 0
    for _, h in HIS62.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in HIS62.iterrows():
        near |= ((tr.month == h.month).to_numpy()
                 & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = tr.pnl[~near].sum()
    pooled = tr.pnl.sum()
    ok = (pooled > 135.8 and all(v > 0 for v in nets.values())
          and exn >= 0 and caught >= 39)
    print(f"| {n} | {len(tr)} | {pooled:+.1f} "
          f"({nets['2022-02']:+.1f}/{nets['2025-10']:+.1f}) | {caught} | "
          f"{exn:+.1f} | {'YES' if ok else 'no'} |")
print()
print("Registry: T-MG11.")
