#!/usr/bin/env python3
"""
m4b_followup.py — T-MG10: (1) M4C joint test (J: carry ties, don't
discard); (2) the OTHER-gap cause checks on the 16 trades (J: fix this).
RUN: python3 Tests/P5_trade_management/m4b_followup.py > Tests/P5_trade_management/M4B_REPORT.md
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

wb = pd.read_parquet("Data/inputs/wrb_1m.parquet")
wb["comp_s"] = (wb.ts_event.dt.tz_convert(None).astype("int64")
                // 10**9 + 60)
wb["is_wrb"] = wb.body_size > wb.prior_body_max
WRB = {}
for mo, nxt in MONTHS.items():
    w = wb[(wb.ts_event >= f"{mo}-01") & (wb.ts_event < nxt) & wb.is_wrb]
    WRB[mo] = {+1: np.sort(w[w.direction == "bearish"].comp_s.to_numpy()),
               -1: np.sort(w[w.direction == "bullish"].comp_s.to_numpy())}


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
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                      "side"]]

print("# M4B REPORT — TIE CARRIED + OTHER-GAP CAUSES (T-MG10)")
print("STATUS: CLOSED | 2026-11-25 | J directives: carry the M4C tie "
      "to the joint test; resolve the 16-trade OTHER class")
print()
# ---- 1. M4C joint ----
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
print("## 1. M4C JOINT TEST (Strategy 4A d1.25 entries, our fills; "
      "yardstick = G2-1's +135.8, caught 39, extras +47.0)")
print("| candidate | trades | net (22-02/25-10) | caught/62 | "
      "extras net |")
print("|---|---|---|---|---|")
for sf in (120, 180):
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
            pnl, ix = m4c(exc, ts, int(r.tf), int(r.d), mo, sf)
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
    print(f"| M4C safety{sf} | {len(tr)} | {tr.pnl.sum():+.1f} "
          f"({nets['2022-02']:+.1f}/{nets['2025-10']:+.1f}) | {caught} "
          f"| {tr.pnl[~near].sum():+.1f} |")
print()
# ---- 2. OTHER-gap causes ----
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = HIS62.merge(G, left_on=["month", "sec"],
                 right_on=["month", "entry_msg_s"], suffixes=("", "_g"))
GT["sd_n"] = GT.side_g.map({"long": 1, "short": -1}) \
    if "side_g" in GT else GT.side.map({"long": 1, "short": -1})
if GT.sd_n.isna().all():
    GT["sd_n"] = GT.side.map({"long": 1, "short": -1})
rows = []
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
        peak, tp = 0.0, 0
        ix, why = len(exc) - 1, "end"
        for i in range(len(exc)):
            if exc[i] > peak:
                peak, tp = exc[i], ts[i]
            if exc[i] <= -3.75:
                ix, why = i, "stop"
                break
            if ts[i] - tp >= 60:
                ix, why = i, "stall"
                break
            if ts[i] >= 480:
                ix, why = i, "time"
                break
        ours = -3.75 if why == "stop" else exc[ix]
        gap = r.pnl_stated - ours
        if gap > 1 and why == "stall":
            hold = int(r.hold_s) if np.isfinite(r.hold_s) else 1800
            j3 = int(np.searchsorted(secs, int(r.sec) + hold, "right"))
            later = exc[ix:max(ix + 1, j3 - j1)]
            if len(later) and later.max() >= r.pnl_stated - 0.5:
                continue  # STALL-EARLY, already explained
            # OTHER: run the three checks
            over_cap = hold > 1800
            # exit beyond mids: his exit price vs path extreme in hold
            j4 = int(np.searchsorted(secs, int(r.sec) + min(hold, 7200),
                                     "right"))
            path = (mids[j1:j4] - r.entry_price) * r.sd_n
            beyond = (r.pnl_stated - 0.5) > (path.max() if len(path)
                                             else 0)
            rows.append(dict(month=mo, sec=int(r.sec), gap=round(gap, 2),
                             hold_s=hold, over_cap=over_cap,
                             exit_lag=r.exit_lag_s,
                             exit_verified=bool(r.exit_verified),
                             pnl_recon=bool(r.pnl_recon),
                             beyond_path=bool(beyond)))
O = pd.DataFrame(rows)
print(f"## 2. THE OTHER CLASS, CHECKED TRADE BY TRADE ({len(O)} trades)")
print(f"- holds beyond our 1800s window: {int(O.over_cap.sum())}")
print(f"- his exit price beyond ANY point of the path (within hold, "
      f"7200s cap): {int(O.beyond_path.sum())}")
print(f"- exit message lag (s) on these: q50 = "
      f"{O.exit_lag.median():.0f}; exit verified: "
      f"{O.exit_verified.mean():.0%}; P&L reconciled: "
      f"{O.pnl_recon.mean():.0%}")
print()
print("| month | sec | gap | hold_s | over_cap | beyond_path | "
      "recon |")
print("|---|---|---|---|---|---|---|")
for _, r in O.sort_values("gap", ascending=False).iterrows():
    print(f"| {r.month} | {r.sec} | {r.gap} | {r.hold_s} | "
          f"{r.over_cap} | {r.beyond_path} | {r.pnl_recon} |")
print()
print("Registry: T-MG10.")
