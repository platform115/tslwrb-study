#!/usr/bin/env python3
"""
p5_15_mg2b.py — MG-2b: THE THREE REFINEMENT CELLS. (T-MG03.)
===============================================================================
Pre-registered in the MG-2 report; nothing else is run.
  L-1b: stall clock (S=30 RTH / 90 ETH) runs only while price is NOT
        beyond the trigger edge. Once price has been >= 1 pt beyond the
        edge, the stop moves TO the edge (structure breakeven).
  L-1c: L-1b, and the stall clock turns back on (S=90 RTH / 270 ETH)
        once price is beyond the edge.
  P+L : stall always on at S=90 (270 ETH); stop = fill-4 until price has
        been >= 1 pt beyond the edge, then stop = edge.
Common: hard stop 4.0 before breakeven, time 27 bars, session close,
per-second mids, trigger edge as in MG-2 (13 fallback cases).

RUN: python3 Tests/P5_trade_management/p5_15_mg2b.py                   (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P6_imitation_study"))
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p6_22_s6_1_presence import Resolver
from p6_24_s6_3_selectors import interact_edges


def leg2(cx, fb, fill, fill_s, long, edge, mode, eth):
    d = 1 if long else -1
    S_base = 90 if eth else 30
    S_beyond = {"L1b": None, "L1c": 270 if eth else 90, "PL": 270 if eth else 90}[mode]
    S_notbeyond = {"L1b": S_base, "L1c": S_base, "PL": 270 if eth else 90}[mode]
    best = fill; lbest = fill_s
    armed = False                      # has price been >= 1 pt beyond the edge
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1
    while i < len(cx.secs):
        s = int(cx.secs[i])
        while jc < len(cx.bsec) and cx.bsec[jc] + 60 <= s:
            if jc + 1 >= len(cx.bsec) or cx.sd[jc + 1] != cx.sd[fb] or not cx.rth[jc + 1]:
                return cx.c[jc], "session"
            if jc >= fb + 27:
                return cx.c[jc], "time"
            jc += 1
        m = cx.mids[i]
        if (m > best) if long else (m < best):
            best, lbest = m, s
        beyond = (m - edge) * d > 0
        if not armed and (m - edge) * d >= 1.0:
            armed = True
        S_now = S_beyond if (beyond and mode != "PL") else S_notbeyond
        if mode == "PL":
            S_now = S_notbeyond
        if S_now is not None and s - lbest > S_now:
            return m, "stall"
        stop = edge if armed else (fill - d * 4.0)
        if (m - stop) * d <= 0:
            return (stop if abs(m - stop) < 4 else m), ("be-stop" if armed else "stop")
        i += 1
    j = len(cx.secs) - 1
    return cx.mids[j], "eof"


def run(repo="."):
    P = prep(repo, "2025-10")
    cx = P["cx"]; secs, mids = P["secs"], P["mids"]
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= "2025-10-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds("2025-10")
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    res = {m: [] for m in ("L1b", "L1c", "PL")}
    reasons = {m: {} for m in res}
    for _, r in em.iterrows():
        s0 = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        d = 1 if r.side == "long" else -1
        ib = int(np.searchsorted(cx.bts, s0 * 10**9, "right")) - 1
        if ib < 60:
            continue
        ents = np.atleast_1d(r.entry_prices).astype(float)
        fill = float(ents[np.isfinite(ents)][0])
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        sd0 = sec_sd(t)
        E = interact_edges(R, sd0, t, "REA", 15, secs, mids, d) if sd0 else []
        edge = min(E, key=lambda q: abs(fill - q)) if E else (fill - d * 2.0)
        eth = not cx.rth[ib]
        for m in res:
            px, why = leg2(cx, ib, fill, s0, d > 0, edge, m, eth)
            res[m].append((px - fill) * d)
            reasons[m][why] = reasons[m].get(why, 0) + 1
    print("===== MG-2b on HIS 92 entries (2025-10, per-unit) =====")
    print("| plan | Trades | Win rate | Avg win / loss | Total | Max below start |")
    print("| HIS ACTUAL | 92 | 82% | +8.56 / -1.31 | +620.0 | 0 |  (reference)")
    print("| M1 / best P-grid | 92 | 75% / 66% | +3.18 / +4.71 | +200.0 / +242.5 | 0 |  (reference)")
    for m, label in (("L1b", "L-1b structure breakeven"),
                     ("L1c", "L-1c + reactivated stall"),
                     ("PL", "P+L S=90 + breakeven")):
        a = np.asarray(res[m]); wn = a > 0
        dd = -min(0.0, float(np.min(np.cumsum(a))))
        print(f"| {label} | {len(a)} | {wn.mean():.0%} | +{a[wn].mean():.2f} / {a[~wn].mean():.2f} "
              f"| {a.sum():+.1f} | {dd:.1f} |")
        print(f"    exits: {reasons[m]}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
