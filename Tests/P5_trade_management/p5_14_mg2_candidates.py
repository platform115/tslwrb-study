#!/usr/bin/env python3
"""
p5_14_mg2_candidates.py — MG-2: MANAGEMENT CANDIDATES ON HIS ENTRIES. (T-MG02.)
===============================================================================
Pre-registered (MG1 report): baselines M0 (no stall; fast-fail 1.5, as a
single leg - reversal omitted, noted) and M1 (S=30), both FROZEN, run not
modified. Candidates:
  P-grid : M1-family with S in {60, 90, 120, 180} (ETH 3x)
  L-1    : structure-conditioned patience - stall clock (S=30) runs ONLY
           while price is NOT beyond the trigger edge; beyond it, no stall.
           Stop/time/session as M1.
  L-2a/b : target = nearest profit-direction structure edge >= 2 pts away
           at entry; stop = trigger edge -/+ {1, 2} pts; time/session kept.
  L-3    : trail = most recent same-direction 5m swing level (updates as
           swings confirm); initial stop = trigger edge -/+ 1; time/session.
Trigger edge: the interacted REA edge nearest his fill at entry; fallback
fill -/+ 2 pts when none (count reported). All exits per-second mids, <=t.
Metric: standard table + capture of own-window MFE. HIS actuals + M0/M1
shown for reference.

RUN: python3 Tests/P5_trade_management/p5_14_mg2_candidates.py         (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P6_imitation_study"))
from p5_10_stall_stack_dials import leg
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p6_22_s6_1_presence import Resolver
from p6_23_s6_2_interaction import edges_at
from p6_24_s6_3_selectors import interact_edges
from p6_15_g3_reaction import swings
from p6_12_g1_hidden_gap import resample_tf

COLS = ["ts_event", "open", "high", "low", "close", "is_roll_day", "session_date"]


def leg_custom(cx, fb, fill, fill_s, long, mode, edge, target=None, stop_px=None,
               trail_fn=None, S=30):
    best = fill; lbest = fill_s
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1
    while i < len(cx.secs):
        s = int(cx.secs[i])
        while jc < len(cx.bsec) and cx.bsec[jc] + 60 <= s:
            if jc + 1 >= len(cx.bsec) or cx.sd[jc + 1] != cx.sd[fb] or not cx.rth[jc + 1]:
                return cx.c[jc], cx.bsec[jc] + 60, "session"
            if jc >= fb + 27:
                return cx.c[jc], cx.bsec[jc] + 60, "time"
            jc += 1
        m = cx.mids[i]
        if (m > best) if long else (m < best):
            best, lbest = m, s
        if mode == "L1":
            beyond = (m > edge) if long else (m < edge)
            if not beyond and s - lbest > S:
                return m, s, "stall"
            stop = fill - 4.0 if long else fill + 4.0
            if (m <= stop if long else m >= stop):
                return (min(stop, m) if long else max(stop, m)), s, "stop"
        elif mode == "L2":
            if (m >= target if long else m <= target):
                return target, s, "target"
            if (m <= stop_px if long else m >= stop_px):
                return (min(stop_px, m) if long else max(stop_px, m)), s, "stop"
        elif mode == "L3":
            tr = trail_fn(s)
            if tr is not None and ((m <= tr) if long else (m >= tr)):
                return m, s, "trail"
            if (m <= stop_px if long else m >= stop_px):
                return (min(stop_px, m) if long else max(stop_px, m)), s, "stop"
        i += 1
    j = len(cx.secs) - 1
    return cx.mids[j], int(cx.secs[j]), "eof"


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

    swing_cache = {}
    def swings_of(sd0):
        if sd0 not in swing_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            rb = resample_tf(g[COLS], 5); rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            swing_cache[sd0] = swings(rb, 5, 2)
        return swing_cache[sd0]

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds("2025-10")
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    variants = (["M0 (no stall, ff1.5)", "M1 (S=30)"] +
                [f"P S={S}" for S in (60, 90, 120, 180)] +
                ["L-1 cond-patience", "L-2a edge tgt/stop1", "L-2b edge tgt/stop2",
                 "L-3 swing trail"])
    res = {v: [] for v in variants}
    nofb = 0
    for _, r in em.iterrows():
        s0 = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        d = 1 if r.side == "long" else -1
        long = d > 0
        ib = int(np.searchsorted(cx.bts, s0 * 10**9, "right")) - 1
        if ib < 60:
            continue
        ents = np.atleast_1d(r.entry_prices).astype(float)
        fill = float(ents[np.isfinite(ents)][0])
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        sd0 = sec_sd(t)
        E = interact_edges(R, sd0, t, "REA", 15, secs, mids, d) if sd0 else []
        edge = min(E, key=lambda q: abs(fill - q)) if E else (fill - d * 2.0)
        if not E:
            nofb += 1
        eth = not cx.rth[ib]
        for v in variants:
            if v.startswith("M0"):
                q = dict(early=1.5, stop=4.0, time_bars=27, S=10**9)
                px, xs, xb, _ = leg(cx, ib, fill, s0, long, q)
            elif v.startswith("M1") or v.startswith("P "):
                S = 30 if v.startswith("M1") else int(v.split("=")[1])
                q = dict(early=4.0, stop=4.0, time_bars=27, S=S * (3 if eth else 1))
                px, xs, xb, _ = leg(cx, ib, fill, s0, long, q)
            elif v.startswith("L-1"):
                px, xs, _ = leg_custom(cx, ib, fill, s0, long, "L1", edge,
                                       S=(90 if eth else 30))
            elif v.startswith("L-2"):
                kstop = 1.0 if v.endswith("stop1") else 2.0
                alledges = []
                for fam in ("REA", "GAP"):
                    alledges += edges_at(R, sd0, t, fam) if sd0 else []
                fwd = [e for e in alledges if (e - fill) * d >= 2.0]
                target = (min(fwd) if long else max(fwd)) if fwd else fill + d * 4.0
                stop_px = edge - d * kstop
                px, xs, _ = leg_custom(cx, ib, fill, s0, long, "L2", edge,
                                       target=target, stop_px=stop_px)
            else:  # L-3
                sw = swings_of(sd0) if sd0 else []
                side_want = "low" if long else "high"
                def trail_fn(s, sw=sw, side_want=side_want):
                    best = None
                    for z in sw:
                        cts = int(pd.Timestamp(z["comp"]).value // 10**9)
                        if cts <= s and z["side"] == side_want:
                            if best is None or cts > best[0]:
                                best = (cts, z["px"])
                    return best[1] if best else None
                stop_px = edge - d * 1.0
                px, xs, _ = leg_custom(cx, ib, fill, s0, long, "L3", edge,
                                       stop_px=stop_px, trail_fn=trail_fn)
            res[v].append((px - fill) * d)
    print(f"(episodes with no interacted edge, fallback used: {nofb})")
    his = []
    for _, r in em.iterrows():
        ents = np.atleast_1d(r.entry_prices).astype(float)
        exts = np.atleast_1d(r.exit_prices).astype(float)
        ents, exts = ents[np.isfinite(ents)], exts[np.isfinite(exts)]
        if len(ents) and len(exts):
            his.append((exts.mean() - ents.mean()) * (1 if r.side == "long" else -1))
    print(f"\n===== MG-2 on HIS 92 entries (2025-10, per-unit) =====")
    print("| plan | Trades | Win rate | Avg win / loss | Total | Max below start |")
    def prt(name, pnl):
        a = np.asarray(pnl); wn = a > 0
        dd = -min(0.0, float(np.min(np.cumsum(a))))
        aw = a[wn].mean() if wn.any() else np.nan
        al = a[~wn].mean() if (~wn).any() else np.nan
        print(f"| {name} | {len(a)} | {wn.mean():.0%} | +{aw:.2f} / {al:.2f} | {a.sum():+.1f} | {dd:.1f} |")
    prt("HIS ACTUAL", his)
    for v in variants:
        prt(v, res[v])


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
