#!/usr/bin/env python3
"""
m6_round.py — M6: level-aware exits (T-MG12). Spec: M6_SPEC.md
(committed first).
RUN: python3 Tests/P5_trade_management/m6_round.py > Tests/P5_trade_management/M6_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination"):
    sys.path.insert(0, os.path.join(T, d))
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
STOP = 3.75
FAMS = ("REA", "SQZ", "GAP", "SHD")


def next_edge(R, sd, t_s, px, d):
    """Nearest certified edge AHEAD of px in direction d at time t."""
    t64 = np.datetime64(int(t_s), "s")
    best = None
    for fam in FAMS:
        for e in edges_at(R, sd, t64, fam):
            ahead = (e - px) * d
            if ahead > 0.25 and (best is None or ahead < best[0]):
                best = (ahead, e)
    return best  # (distance_pts, edge_price) or None


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


def m6a(exc, ts, tgt):
    """Limit at tgt (excursion units); else M3A behavior."""
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


def m6b(exc, ts, arm):
    """Snap mode arms once exc >= arm (level reached): exit peak-0.75."""
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


# his 62
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):   # rarity order (Path C)
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

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

CELLS = {"M6A reach3": ("A", 3.0), "M6A reach5": ("A", 5.0),
         "M6B reach3": ("B", 3.0), "M6B reach5": ("B", 5.0)}

print("# M6 REPORT — LEVEL-AWARE EXITS (T-MG12)")
print("STATUS: CLOSED | 2026-11-25 | Spec: M6_SPEC.md (committed first)")
print()
res = {n: [] for n in CELLS}
res["M3A baseline"] = []
RES = {}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    RES[mo] = Resolver(bm, zr)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not np.isfinite(r.entry_price):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.sd_n
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        ne = next_edge(RES[mo], r.session_date, r.sec, r.entry_price,
                       int(r.sd_n))
        for n, (kind, reach) in CELLS.items():
            tgt = None
            if ne is not None and ne[0] <= reach:
                tgt = ne[0] - 0.25 if kind == "A" else ne[0] - 0.75
                tgt = max(tgt, 0.5)
            res[n].append((m6a(exc, ts, tgt) if kind == "A"
                           else m6b(exc, ts, tgt))[0])
        res["M3A baseline"].append(m3a(exc, ts)[0])
print("## STAGE 1 — HIS 62 FILLS (qualify: net > +123.9)")
print("| candidate | net | win | avg win/loss | worst | share of his |")
print("|---|---|---|---|---|---|")
quals = []
for n in list(CELLS) + ["M3A baseline"]:
    a = np.array(res[n])
    w = a > 0
    net = a.sum()
    print(f"| {n} | {net:+.1f} | {w.mean():.0%} | +{a[w].mean():.2f} / "
          f"{a[~w].mean():.2f} | {a.min():+.2f} | {net/231.2:.0%} |")
    if net > 123.9 and n != "M3A baseline":
        quals.append(n)
print()
print(f"Stage-1 qualifiers: {quals if quals else 'NONE'}")
print()
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
print("## STAGE 2 — JOINT (adopt: > +135.8, both months > 0, extras "
      ">= 0, catch >= 39)")
print("| candidate | trades | net (22-02/25-10) | caught/62 | extras "
      "net | ADOPT? |")
print("|---|---|---|---|---|---|")
for n in quals + ["M3A baseline"]:
    allt = []
    for mo in MONTHS:
        P = prep(".", mo)
        secs, mids = P["secs"], P["mids"]
        bm_sd = None
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
            if n == "M3A baseline":
                pnl, ix = m3a(exc, ts)
            else:
                kind, reach = CELLS[n]
                # session date for the fill: from the bar table
                k = int(np.searchsorted(
                    b.ts_event.dt.tz_convert(None).astype("int64")
                    .to_numpy() // 10**9, int(r.tf), "right")) - 1
                sd0 = b.sd.iloc[k]
                ne = next_edge(RES[mo], sd0, int(r.tf), lvl, int(r.d))
                tgt = None
                if ne is not None and ne[0] <= reach:
                    tgt = ne[0] - (0.25 if kind == "A" else 0.75)
                    tgt = max(tgt, 0.5)
                pnl, ix = (m6a(exc, ts, tgt) if kind == "A"
                           else m6b(exc, ts, tgt))
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
print("Registry: T-MG12.")
