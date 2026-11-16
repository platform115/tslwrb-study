#!/usr/bin/env python3
"""
p4_57_trigger_catch.py — P4.57: the mechanical trigger, measured by CATCH RATE.
================================================================================
From P4.56: he does not rest limits. Price touches the level; ~11 s later (middle
half 5-28 s) he fires at market, and his entry second sits high in the window's
10-second thrust (74th pct mid-move and signed volume). The trigger candidate:
  FIRE at second s when:
    1. a live level was touched (within 1 tick) in the last 45 s
    2. the last 10 s moved >= M ticks in direction d
    3. the last 10 s signed volume agrees with d (>= V contracts)
Measured here by CATCHING, not P&L: a his-entry is CAUGHT when a fire lands
within 120 s of it with the same direction. Also reported: fires per RTH day
(the cost side) and the share of fires near any of his A entries.
Two level sets: strategy-knowable (reaction WRBs only) and descriptive upper
bound (adds his own prior trade prices). Universe: his GROUP A entries, all
four run months.

RUN: python3 Tests/P4_entry_determination/p4_57_trigger_catch.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_49_sec_engine import Ctx, ALL_MONTHS           # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_53_anchor_sweep import month_anchors           # noqa: E402

TICK = 0.25
LIFE_NS = 60 * int(60e9)
TOUCH_TK, TOUCH_WIN = 1, 45
MATCH_S = 120
KNOWABLE = ["firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]
UPPER = KNOWABLE + ["his-exit", "his-entry"]


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    grids = [(2, 0), (2, 50), (3, 50), (4, 100)]
    res = {(ks, M, V): [0, 0, 0, 0] for ks in ("knowable", "upper") for M, V in grids}
    # caught, his_n, fires, fires_near_his
    n_days = 0
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64)
        mids = f.mid.to_numpy(float)
        sv = (f.buyv - f.sellv).to_numpy(float)
        csv_ = np.concatenate([[0.0], np.cumsum(sv)])
        # restrict to RTH seconds inside the month
        rth_bars = cx.bars[cx.bars.rth]
        rb = pd.DatetimeIndex(rth_bars.ts_event).as_unit("ns").asi8 // 1_000_000_000
        rset = np.zeros(0, dtype=np.int64)
        keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        n_days += len(np.unique(secs[keep] // 86400))
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        eA = e_m[g == "A"]
        his_s = np.array([pd.Timestamp(x).value // 10**9 for x in eA.first_entry_utc], dtype=np.int64)
        his_d = np.array([1 if s == "long" else -1 for s in eA.side])
        # score>=6 signal windows (the Group A context), by direction
        sg = cx.sig[cx.sig.score >= 6]
        sig_s = sg.comp_ns.to_numpy(np.int64) // 10**9
        sig_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
        order = np.argsort(sig_s); sig_s, sig_d = sig_s[order], sig_d[order]

        def gated(s_arr, d_arr):
            out = np.zeros(len(s_arr), bool)
            for j in range(len(s_arr)):
                a = np.searchsorted(sig_s, s_arr[j] - 300)
                b = np.searchsorted(sig_s, s_arr[j], side="right")
                out[j] = bool((sig_d[a:b] == d_arr[j]).any())
            return out

        for ks, keys in [("knowable", KNOWABLE), ("upper", UPPER)]:
            pts = sorted(sum((W[k] for k in keys), []))
            lt = np.array([t for t, _ in pts], dtype=np.int64)
            lp = np.array([p for _, p in pts])
            # per second: near a live level? (level touched at that second)
            near = np.zeros(len(secs), bool)
            for i in np.flatnonzero(keep):
                s_ns = secs[i] * 10**9
                a, b = np.searchsorted(lt, s_ns - LIFE_NS), np.searchsorted(lt, s_ns, side="right")
                if b > a and np.abs(mids[i] - lp[a:b]).min() / TICK <= TOUCH_TK:
                    near[i] = True
            # touched within last TOUCH_WIN seconds (rolling via last-touch index)
            last_touch = np.full(len(secs), -10**18, dtype=np.int64)
            lt_s = -10**18
            for i in range(len(secs)):
                if near[i]:
                    lt_s = secs[i]
                last_touch[i] = lt_s
            i10 = np.searchsorted(secs, secs - 10)
            mv10 = mids - mids[np.maximum(i10 - 0, 0)]
            vol10 = csv_[np.arange(1, len(secs) + 1)] - csv_[i10]
            for M, V in grids:
                d = np.sign(mv10)
                fire = keep & (secs - last_touch <= TOUCH_WIN) & (np.abs(mv10) / TICK >= M) \
                       & (np.abs(vol10) >= V) & (np.sign(vol10) == d) & (d != 0)
                fi = np.flatnonzero(fire)
                # thin consecutive fires: keep first of each 120s cluster
                sel = []
                last = -10**18
                for i in fi:
                    if secs[i] - last > MATCH_S:
                        sel.append(i); last = secs[i]
                fs = secs[np.array(sel, dtype=int)] if sel else np.zeros(0, dtype=np.int64)
                fd = d[np.array(sel, dtype=int)] if sel else np.zeros(0)
                gm = gated(fs, fd)
                fs, fd = fs[gm], fd[gm]
                caught = 0
                for hs, hd in zip(his_s, his_d):
                    m = (np.abs(fs - hs) <= MATCH_S) & (fd == hd)
                    caught += int(m.any())
                near_his = 0
                for j in range(len(fs)):
                    if ((np.abs(his_s - fs[j]) <= MATCH_S) & (his_d == fd[j])).any():
                        near_his += 1
                r = res[(ks, M, V)]
                r[0] += caught; r[1] += len(his_s); r[2] += len(fs); r[3] += near_his
    print(f"Trigger: score>=6 signal (same direction) within the last 5 min AND level")
    print(f"touched <= {TOUCH_WIN}s ago AND 10s move >= M ticks AND 10s signed volume >= V,")
    print(f"agreeing in direction. Caught = fire within {MATCH_S}s of his entry, same")
    print(f"direction. RTH days in sample: {n_days}.\n")
    print("| Level set | M (ticks) | V (contracts) | His A caught | Catch rate | Fires total | Fires/day | Fires near his A |")
    print("|---|---|---|---|---|---|---|---|")
    for (ks, M, V), (c, hn, fn, nh) in res.items():
        print(f"| {ks} | {M} | {V} | {c}/{hn} | {c/hn:.0%} | {fn} | {fn/max(n_days,1):.1f} "
              f"| {nh}/{fn} = {nh/max(fn,1):.0%} |")
    print("\nREAD: catch rate vs fire volume is the trade-off; P&L comes later. First-pass")
    print("thresholds from the P4.56 distributions; recorded.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
