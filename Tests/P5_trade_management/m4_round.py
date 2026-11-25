#!/usr/bin/env python3
"""
m4_round.py — M4: path-dependent management round (T-MG09).
Spec: M4_SPEC.md (committed first).
RUN: python3 Tests/P5_trade_management/m4_round.py > Tests/P5_trade_management/M4_REPORT.md
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

# ---------- his G2 trades ----------
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
HISQ = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec"]]
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = HISQ.merge(G, left_on=["month", "sec"], right_on=["month",
                "entry_msg_s"])
assert len(GT) == 62
GT["sd_n"] = GT.side.map({"long": 1, "short": -1})

# ---------- step 0: the OTHER class vs scale-outs ----------
# recompute M3A on his fills to identify big-gap stall trades
def m3a_pnl(exc, ts):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if exc[i] <= -3.75:
            return -3.75, "stop", i
        if ts[i] - tp >= 60:
            return exc[i], "stall", i
        if ts[i] >= 480:
            return exc[i], "time", i
    return (exc[-1], "end", len(exc) - 1) if len(exc) else (0.0, "end", 0)


# ---------- opposite-WRB completion times (for M4C) ----------
wb = pd.read_parquet("Data/inputs/wrb_1m.parquet")
wb = wb[wb.timeframe == "1m"] if "timeframe" in wb else wb
wb["comp_s"] = (wb.ts_event.dt.tz_convert(None).astype("int64")
                // 10**9 + 60)
wb["is_wrb"] = wb.body_size > wb.prior_body_max
WRB = {}
for mo, nxt in MONTHS.items():
    w = wb[(wb.ts_event >= f"{mo}-01") & (wb.ts_event < nxt)
           & wb.is_wrb]
    WRB[mo] = {+1: np.sort(w[w.direction == "bearish"].comp_s.to_numpy()),
               -1: np.sort(w[w.direction == "bullish"].comp_s.to_numpy())}
# (for a LONG trade, +1 key holds the OPPOSITE = bearish WRB times)


def m4a(exc, ts, k, gg):
    peak, tp, budget = 0.0, 0, 60.0
    last_level = 0.0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
            if peak - last_level >= k:
                budget = min(240.0, budget + gg)
                last_level = peak
        if exc[i] <= -3.75:
            return -3.75, i
        if ts[i] - tp >= budget or ts[i] >= 900:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def m4b(exc, ts, hi):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        budget = 60 if peak < 2.25 else (120 if peak < 4.5 else hi)
        if exc[i] <= -3.75:
            return -3.75, i
        if ts[i] - tp >= budget or ts[i] >= 900:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def m4c(exc, ts, t0, d, mo, safety):
    opp = WRB[mo][d]
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if exc[i] <= -3.75:
            return -3.75, i
        j = int(np.searchsorted(opp, t0 + ts[i], "right")) - 1
        if j >= 0 and t0 < opp[j] <= t0 + ts[i]:
            return exc[i], i
        if ts[i] - tp >= safety or ts[i] >= 900:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


CANDS = {}
for k in (1.5, 2.25):
    for gg in (30, 60):
        CANDS[f"M4A k{k} g{gg}"] = (lambda e, t, t0, d, mo, k=k, g=gg:
                                    m4a(e, t, k, g))
for hi in (180, 150):
    CANDS[f"M4B hi{hi}"] = lambda e, t, t0, d, mo, hi=hi: m4b(e, t, hi)
for sf in (120, 180):
    CANDS[f"M4C safety{sf}"] = (lambda e, t, t0, d, mo, sf=sf:
                                m4c(e, t, t0, d, mo, sf))
CANDS["M3A baseline"] = lambda e, t, t0, d, mo: m3a_pnl(e, t)[:3:2]
def m3b(e, t, t0, d, mo):
    peak, tp = 0.0, 0
    for i in range(len(e)):
        if e[i] > peak:
            peak, tp = e[i], t[i]
        if e[i] <= -3.75:
            return -3.75, i
        if t[i] - tp >= 90 or t[i] >= 900:
            return e[i], i
    return (e[-1], len(e) - 1) if len(e) else (0.0, 0)
CANDS["M3B baseline"] = m3b

print("# M4 REPORT — PATH-DEPENDENT MANAGEMENT ROUND (T-MG09)")
print("STATUS: CLOSED | 2026-11-25 | Spec: M4_SPEC.md (committed first)")
print()
# ---------- step 0 ----------
other_scaled = []
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not (np.isfinite(r.entry_price) and np.isfinite(r.pnl_stated)):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.sd_n
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        pnl, why, ix = m3a_pnl(exc, ts)
        gap = r.pnl_stated - pnl
        if gap > 1 and why == "stall":
            hold = int(r.hold_s) if np.isfinite(r.hold_s) else 1800
            j3 = int(np.searchsorted(secs, int(r.sec) + hold, "right"))
            later = exc[ix:max(ix + 1, j3 - j1)]
            if not (len(later) and later.max() >= r.pnl_stated - 0.5):
                other_scaled.append((r.n_entries, r.n_exits, bool(r.scaled)))
oth = pd.DataFrame(other_scaled, columns=["n_in", "n_out", "scaled"])
print("## STEP 0 — THE 'OTHER' GAP CLASS vs SCALE-OUTS")
print(f"OTHER-class trades found: {len(oth)}; multi-exit or scaled: "
      f"{int(((oth.n_out > 1) | oth.scaled).sum())}; multi-entry: "
      f"{int((oth.n_in > 1).sum())}.")
print("Verdict: the share that is multi-unit belongs to the parked "
      "scale-out line, not to single-unit exits.")
print()
# ---------- stage 1 ----------
res = {name: [] for name in CANDS}
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
        for name, fn in CANDS.items():
            out = fn(exc, ts, int(r.sec), int(r.sd_n), mo)
            res[name].append(out[0])
print("## STAGE 1 — ON HIS 62 FILLS (qualify: net > M3A's +135.0)")
print("| candidate | net | win | avg win/loss | worst | share of his "
      "+231.2 |")
print("|---|---|---|---|---|---|")
quals = []
for name in CANDS:
    a = np.array(res[name])
    w = a > 0
    net = a.sum()
    print(f"| {name} | {net:+.1f} | {w.mean():.0%} | "
          f"+{a[w].mean():.2f} / {a[~w].mean():.2f} | {a.min():+.2f} | "
          f"{net/231.2:.0%} |")
    if net > 135.0 and "baseline" not in name:
        quals.append(name)
print()
print(f"Stage-1 qualifiers: {quals if quals else 'NONE'}")
print()
# ---------- stage 2: joint on OUR fills ----------
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                      "side"]]
print("## STAGE 2 — JOINT (Strategy 4A d1.25 entries; adopt: pooled > "
      "+135.8, both months > 0, extras >= 0, catch >= 39)")
print("| candidate | trades | net (22-02/25-10) | caught/62 | extras "
      "net | ADOPT? |")
print("|---|---|---|---|---|---|")
for name in quals + ["M3A baseline"]:
    fn = CANDS[name]
    nets = {}
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
            pnl, ix = fn(exc, ts, int(r.tf), int(r.d), mo)
            busy = int(secs[j1 + ix])
            allt.append((mo, int(r.tf), int(r.d), pnl))
        nets[mo] = sum(p for m2, _, _, p in allt if m2 == mo)
    tr = pd.DataFrame(allt, columns=["month", "tf", "d", "pnl"])
    caught = 0
    for _, h in HIS62.iterrows():
        g = tr[(tr.month == h.month) & (tr.d == h.side)
               & (abs(tr.tf - h.sec) <= 300)]
        if len(g):
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in HIS62.iterrows():
        near |= ((tr.month == h.month).to_numpy()
                 & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = tr.pnl[~near].sum()
    pooled = tr.pnl.sum()
    ok = (pooled > 135.8 and all(v > 0 for v in nets.values())
          and exn >= 0 and caught >= 39)
    print(f"| {name} | {len(tr)} | {pooled:+.1f} "
          f"({nets['2022-02']:+.1f}/{nets['2025-10']:+.1f}) | {caught} "
          f"| {exn:+.1f} | {'YES' if ok else 'no'} |")
print()
print("Registry: T-MG09.")
