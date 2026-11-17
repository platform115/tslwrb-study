#!/usr/bin/env python3
"""
p4_70_derive_window.py — P4.70 / Strategy 2: (A) which estimator reproduces the
fixed numbers, (B) deriving the 7-second window itself, (C) intraday N-bar
rolling thresholds. TRAINING MONTHS ONLY.
=================================================================================
A) For each day-range estimator (T-EN72 battery), the daily thresholds it
   generated across the training sessions, against the fixed 13 tk / 50 tk:
   median, middle half, and RMS miss. "The one we're looking for" = the one
   whose daily numbers land closest to the fixed ones.
B) Three measurements that could yield the window from data:
   B1 duration of extreme one-sided flow: 99th/99.5th percentile of the
      consecutive-seconds run length of same-side signed volume
   B2 momentum memory: first lag (seconds) where the autocorrelation of
      1-second mid changes drops below 0.05
   B3 burst concentration: for top-0.5% 20-second moves, the median share of
      the move that happened in its FINAL 7 seconds (high share = the burst
      is intrinsically a <=7 s event)
C) User's reversed rolling estimator: thresholds from the last N COMPLETED
   1-min bars (N = 5/10/15/20/30/50), recomputed every bar:
   R_est(i) = c_N x meanTR_N(i), c_N = training median of day_range/meanTR_N
   (frozen-style calibration); burst = 0.042 x R_est, thrust = 0.17 x R_est.

RUN: python3 Tests/P4_entry_determination/p4_70_derive_window.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
from p4_69_adaptation_plan import session_history, EWMA_L  # noqa: E402

TICK = 0.25
CLUST = 120
BURST_SHARE, THRUST_SHARE = 0.042, 0.17
NS = (5, 10, 15, 20, 30, 50)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}
    train_sd = [d for d in dates if d.startswith("2025-10") or d.startswith("2022-02")]
    a_on = float(np.median([SH.rth[d] / SH.on[d] for d in train_sd
                            if np.isfinite(SH.on.get(d, np.nan)) and SH.on[d] > 0]))
    b_o30 = float(np.median([SH.rth[d] / SH.open30[d] for d in train_sd
                             if np.isfinite(SH.open30.get(d, np.nan)) and SH.open30[d] > 0]))

    def r_est(method, d):
        i = pos.get(d)
        if i is None or i == 0:
            return None
        if method == "PRIORDAY":
            return float(SH.rth.iloc[i - 1])
        if method == "EWMA":
            vals = SH.rth.iloc[max(0, i - 15):i]
            e = float(vals.iloc[0])
            for v in vals.iloc[1:]:
                e = EWMA_L * e + (1 - EWMA_L) * float(v)
            return e
        if method == "ATR14D":
            return float(SH.rth.iloc[max(0, i - 14):i].mean())
        if method == "TRAIL21":
            return float(SH.rth.iloc[max(0, i - 21):i].mean())
        if method == "OVERNIGHT":
            v = SH.on.get(d, np.nan)
            return a_on * float(v) if np.isfinite(v) and v > 0 else None
        if method == "OPEN30":
            v = SH.open30.get(d, np.nan)
            return b_o30 * float(v) if np.isfinite(v) and v > 0 else None

    print("A) Did any estimator GENERATE the fixed numbers (13 tk burst / 50 tk")
    print("   thrust)? Daily thresholds across the 42 training sessions:\n")
    print("| Estimator | Burst: median (middle half) | RMS miss vs 13 | "
          "Thrust: median (middle half) | RMS miss vs 50 |")
    print("|---|---|---|---|---|")
    for method in ("PRIORDAY", "EWMA", "ATR14D", "TRAIL21", "OVERNIGHT", "OPEN30"):
        bs, ts = [], []
        for d in train_sd:
            R = r_est(method, d)
            if R:
                bs.append(BURST_SHARE * R); ts.append(THRUST_SHARE * R)
        bs, ts = np.asarray(bs), np.asarray(ts)
        print(f"| {method} | {np.median(bs):.1f} ({np.percentile(bs,25):.1f}-"
              f"{np.percentile(bs,75):.1f}) | {np.sqrt(np.mean((bs-13)**2)):.1f} "
              f"| {np.median(ts):.0f} ({np.percentile(ts,25):.0f}-"
              f"{np.percentile(ts,75):.0f}) | {np.sqrt(np.mean((ts-50)**2)):.0f} |")

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    print("\nB) Deriving the WINDOW from the data:\n")
    for m, P in Ps.items():
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{m}_full.parquet"))
        sv = (f.buyv - f.sellv).to_numpy(float)
        runl = np.zeros(len(secs)); cur = 0; last_sign = 0
        for i in range(len(secs)):
            s = np.sign(sv[i])
            if s != 0 and s == last_sign:
                cur += 1
            elif s != 0:
                cur = 1; last_sign = s
            runl[i] = cur
        r = runl[keep]
        # B2 autocorrelation of 1s mid changes
        dmid = np.diff(mids)
        km = keep[1:] & keep[:-1]
        x = dmid[km]; x = x - x.mean()
        lags = []
        for L in range(1, 31):
            ac = np.corrcoef(x[:-L], x[L:])[0, 1]
            lags.append(ac)
        first_low = next((L for L, ac in enumerate(lags, 1) if ac < 0.05), None)
        # B3 share of top-0.5% 20s moves completed in the final 7s
        i20 = np.searchsorted(secs, secs - 20)
        i7 = np.searchsorted(secs, secs - 7)
        mv20 = (mids - mids[np.maximum(i20, 0)]) / TICK
        mv7 = (mids - mids[np.maximum(i7, 0)]) / TICK
        thr20 = np.percentile(np.abs(mv20)[keep], 99.5)
        sel = keep & (np.abs(mv20) >= thr20)
        share = (mv7[sel] / mv20[sel])
        share = share[np.isfinite(share)]
        print(f"  [{m}] B1 one-sided flow run length: 99th pct = "
              f"{np.percentile(r,99):.0f}s, 99.5th = {np.percentile(r,99.5):.0f}s | "
              f"B2 momentum memory gone after {first_low}s "
              f"(lag-1 ac {lags[0]:.2f}, lag-5 {lags[4]:.2f}, lag-10 {lags[9]:.2f}) | "
              f"B3 median {np.median(share):.0%} of an extreme 20s move happens "
              f"in its final 7s")

    print("\nC) Intraday rolling thresholds from the last N completed 1-min bars:\n")
    # calibrate c_N on training bars (frozen-style)
    print("| N bars | c_N | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|---|")
    for N in NS:
        cns = []
        for m, P in Ps.items():
            cx = P["cx"]
            h, l, cl = cx.h, cx.l, cx.c
            pc = np.roll(cl, 1); pc[0] = cl[0]
            tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc))) / TICK
            atrN = pd.Series(tr).shift(1).rolling(N).mean().to_numpy()  # completed bars only
            P[f"_atr{N}"] = atrN
            bars = cx.bars[cx.bars.rth]
            dr = bars.groupby(bars.session_date.astype(str)).apply(
                lambda g: (g.high.max() - g.low.min()) / TICK)
            drmap = dr.to_dict()
            day_rng = np.array([drmap.get(s, np.nan) for s in P["sd"]])
            ok = cx.rth & np.isfinite(atrN) & np.isfinite(day_rng)
            cns += list(day_rng[ok] / atrN[ok])
        c_N = float(np.median(cns))
        per_m = {}
        for m, P in Ps.items():
            secs, mids, keep = P["secs"], P["mids"], P["keep"]
            iw = np.searchsorted(secs, secs - 7)
            mv7 = (mids - mids[np.maximum(iw, 0)]) / TICK
            atrN = P[f"_atr{N}"]
            bar_i = np.searchsorted(P["cx"].bts, secs * 10**9, "right") - 1
            Rsec = c_N * atrN[np.clip(bar_i, 0, len(atrN) - 1)]
            fl3 = []
            last = -10**18
            for i in np.flatnonzero(keep & np.isfinite(Rsec)):
                if abs(mv7[i]) < BURST_SHARE * Rsec[i]:
                    continue
                if secs[i] - last > CLUST:
                    fl3.append((i, int(np.sign(mv7[i])), THRUST_SHARE * Rsec[i]))
                    last = secs[i]
            kept = []
            for i, s, tthr in fl3:
                s0 = int(secs[i])
                ib = int(np.searchsorted(P["cx"].bts, s0 * 10**9)) - 1
                if ib < 60 or not P["cx"].rth[ib]:
                    continue
                ft = P["feats"](ib, s, s0)
                if ft["ret5m"] >= tthr:
                    kept.append((i, s))
            per_m[m] = sim(P, kept, lambda *a: True)
        print(row(f"last {N} bars (c_{N}={c_N:.1f})", per_m).replace("| last", f"| {N} | {c_N:.1f} | last", 1)
              .replace(f"last {N} bars (c_{N}={c_N:.1f}) | ", ""))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
