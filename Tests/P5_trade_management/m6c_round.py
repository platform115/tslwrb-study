#!/usr/bin/env python3
"""
m6c_round.py — M6C stage 0: key-level targets as STUDY instrument
(T-MG13). Spec: M6C_SPEC.md (committed first). Uses his key-tier
mentions -> linked object edges; NOTHING here can ship live.
RUN: python3 Tests/P5_trade_management/m6c_round.py > Tests/P5_trade_management/M6C_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P4_entry_determination", "A2_measurement"):
    sys.path.insert(0, os.path.join(T, d))
from p4_66_context_ablation import prep                      # noqa: E402
from a2_3_labels_story import load_mentions                  # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
STOP = 3.75
PATHC_ORDER = ("SQZ", "REA", "GAP", "SHD")   # rarity order, Path C


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


def limit_or_m3a(exc, ts, tgt):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if tgt is not None and exc[i] >= tgt:
            return tgt, i
        if exc[i] <= -STOP:
            return -STOP, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def snap_or_m3a(exc, ts, arm):
    peak, tp = 0.0, 0
    armed = False
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in PATHC_ORDER:
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
assert len(GT) == 62

print("# M6C REPORT — KEY-LEVEL TARGETS, STAGE 0 (STUDY ONLY) (T-MG13)")
print("STATUS: CLOSED | 2026-11-25 | Spec: M6C_SPEC.md | uses HIS chat "
      "labels - nothing here can ship live (spec constraint)")
print()
REACH = (3.0, 5.0, 8.0)
res = {f"{k} reach{a}": [] for k in ("limit", "snap") for a in REACH}
res["M3A baseline"] = []
n_with_key = 0
for mo, nxt in MONTHS.items():
    M = load_mentions(".", mo)
    mt, mk, lo, hi, key = M
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not np.isfinite(r.entry_price):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.sd_n
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        # key-tier mentioned edges BEFORE the fill, ahead of price
        jm = int(np.searchsorted(mt, int(r.sec)))
        best = None
        for i in range(jm):
            if not key[i] or mk[i] > r.sec:
                continue
            for e in (lo[i], hi[i]):
                ahead = (e - r.entry_price) * r.sd_n
                if ahead > 0.25 and (best is None or ahead < best):
                    best = ahead
        if best is not None:
            n_with_key += 1
        for a in REACH:
            tgt = (best - 0.25) if (best is not None and best <= a) \
                else None
            tgt = max(tgt, 0.5) if tgt is not None else None
            res[f"limit reach{a}"].append(limit_or_m3a(exc, ts, tgt)[0])
            arm = (best - 0.75) if (best is not None and best <= a) \
                else None
            arm = max(arm, 0.5) if arm is not None else None
            res[f"snap reach{a}"].append(snap_or_m3a(exc, ts, arm)[0])
        res["M3A baseline"].append(m3a(exc, ts)[0])
print(f"Trades with a key-mentioned edge ahead (any distance): "
      f"{n_with_key}/62.")
print()
print("| candidate | net | win | avg win/loss | worst | share of his |")
print("|---|---|---|---|---|---|")
for n in res:
    a = np.array(res[n])
    w = a > 0
    al = a[~w].mean() if (~w).any() else 0.0
    print(f"| {n} | {a.sum():+.1f} | {w.mean():.0%} | "
          f"+{a[w].mean():.2f} / {al:.2f} | {a.min():+.2f} | "
          f"{a.sum()/231.2:.0%} |")
print()
print("Bar: net > +123.9 clears stage 0 -> stage 1 (computable proxy).")
print("Registry: T-MG13.")
