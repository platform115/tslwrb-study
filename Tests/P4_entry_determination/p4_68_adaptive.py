#!/usr/bin/env python3
"""
p4_68_adaptive.py — P4.68 / Strategy 2: deriving the trigger numbers from the
data itself (adaptive thresholds). TRAINING MONTHS ONLY.
==============================================================================
A) WHY short windows: continuation profile. For each window w, take all RTH
   seconds whose |move over w| is in that month's top 0.5%, and measure the
   mean further move IN THE SAME DIRECTION over the next 1 / 3 / 5 minutes
   (samples thinned to one per 30 s to limit overlap).
B) WHAT the fixed numbers are made of: per day, the top-0.5%% cutoff of |7s
   moves| and the thrust reference, each as a fraction of that day's range;
   plus the correlation between the daily cutoff and the daily range.
C) ADAPTIVE vs FIXED, honestly cross-calibrated: burst threshold = top-0.5%%
   cutoff of |7s moves| over the TRAILING 5 sessions (self-calibrating, no
   coefficient); thrust = k x trailing-5-session mean daily range, with k
   calibrated on the OTHER month (k = 50tk / that month's mean daily range).
   First 5 sessions of each month skipped for burn-in - the fixed-number
   rows are re-run with the same skip so the comparison is fair.
Config under test: the standing leader (0.5%%/7s trigger, thrust-50 context,
no signal, no session cut), v11 sketch management, mid fills.

RUN: python3 Tests/P4_entry_determination/p4_68_adaptive.py               (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402

TICK = 0.25
CLUST = 120
BURN = 5


def mv_window(P, w):
    secs, mids = P["secs"], P["mids"]
    iw = np.searchsorted(secs, secs - w)
    return (mids - mids[np.maximum(iw, 0)]) / TICK


def day_of(P):
    return P["secs"] // 86400


def run(repo):
    Ps = {m: prep(repo, m) for m, _ in MONTHS}

    # ---- A: continuation profile ----
    print("A) CONTINUATION after a top-0.5% move in window w (mean further move,")
    print("   same direction, ticks; samples one per 30 s):\n")
    print("| Window | Qualifying moves | +1 min | +3 min | +5 min |")
    print("|---|---|---|---|---|")
    for w in (5, 7, 10, 20, 30, 60):
        n_all = 0; fwd = {60: [], 180: [], 300: []}
        for m, P in Ps.items():
            mv = mv_window(P, w)
            thr = np.percentile(np.abs(mv)[P["keep"]], 99.5)
            secs, mids = P["secs"], P["mids"]
            idx = np.flatnonzero(P["keep"] & (np.abs(mv) >= thr))
            last = -10**18; sel = []
            for i in idx:
                if secs[i] - last >= 30:
                    sel.append(i); last = secs[i]
            n_all += len(sel)
            for K in fwd:
                j = np.searchsorted(secs, secs[np.array(sel, dtype=int)] + K, "right") - 1
                fwd[K] += list((mids[j] - mids[np.array(sel, dtype=int)]) / TICK
                               * np.sign(mv[np.array(sel, dtype=int)]))
        print(f"| {w}s | {n_all} | {np.mean(fwd[60]):+.2f} | {np.mean(fwd[180]):+.2f} "
              f"| {np.mean(fwd[300]):+.2f} |")

    # ---- B: what the numbers are made of ----
    print("\nB) PER-DAY structure (both months pooled):")
    ratios_q, ratios_corr = [], []
    for m, P in Ps.items():
        mv7 = np.abs(mv_window(P, 7))
        d = day_of(P)
        days = np.unique(d[P["keep"]])
        cx = P["cx"]
        bars = cx.bars[cx.bars.rth]
        dr = bars.groupby(bars.session_date.astype(str)).apply(
            lambda g: (g.high.max() - g.low.min()) / TICK)
        qs, rngs = [], []
        for dd in days:
            k = P["keep"] & (d == dd)
            if k.sum() < 3600:
                continue
            q = np.percentile(mv7[k], 99.5)
            ts = pd.Timestamp(int(P["secs"][np.flatnonzero(k)[0]]), unit="s", tz="UTC")
            # session date of this day (approximate by calendar date string match)
            sd_match = [s for s in dr.index if ts.strftime("%Y-%m-%d") in s]
            if not sd_match:
                continue
            qs.append(q); rngs.append(float(dr[sd_match[0]]))
        qs, rngs = np.asarray(qs), np.asarray(rngs)
        ratios_q += list(qs / rngs)
        ratios_corr.append(np.corrcoef(qs, rngs)[0, 1])
        print(f"  [{m}] daily 0.5% cutoff of 7s moves: {qs.min():.0f}-{qs.max():.0f} ticks "
              f"(median {np.median(qs):.0f}) | daily range {rngs.min():.0f}-{rngs.max():.0f} "
              f"| corr(cutoff, range) = {np.corrcoef(qs, rngs)[0,1]:.2f}")
    print(f"  POOLED: burst cutoff as a share of the day's range: median "
          f"{np.median(ratios_q):.1%} (IQR {np.percentile(ratios_q,25):.1%}-"
          f"{np.percentile(ratios_q,75):.1%})")
    print(f"  Thrust 50tk as a share of mean daily range: "
          + ", ".join(f"{m}: {50/np.mean([float(v) for v in Ps[m]['cx'].bars[Ps[m]['cx'].bars.rth].groupby(Ps[m]['cx'].bars[Ps[m]['cx'].bars.rth].session_date.astype(str)).apply(lambda g,: (g.high.max()-g.low.min())/TICK)]):.1%}" for m in Ps))

    # ---- C: adaptive vs fixed, cross-calibrated ----
    print("\nC) ADAPTIVE vs FIXED (first 5 sessions of each month skipped in BOTH):\n")
    print("| Variant | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    mean_dr = {}
    for m, P in Ps.items():
        bars = P["cx"].bars[P["cx"].bars.rth]
        mean_dr[m] = float(np.mean(bars.groupby(bars.session_date.astype(str)).apply(
            lambda g: (g.high.max() - g.low.min()) / TICK)))
    months = list(Ps)
    k_from = {months[0]: 50 / mean_dr[months[1]], months[1]: 50 / mean_dr[months[0]]}

    def build_fires(P, thr_by_day, w=7):
        mv = mv_window(P, w)
        secs = P["secs"]; d = day_of(P)
        out = []; last = -10**18
        for i in np.flatnonzero(P["keep"]):
            t = thr_by_day.get(int(d[i]))
            if t is None or abs(mv[i]) < t:
                continue
            if secs[i] - last > CLUST:
                out.append((i, int(np.sign(mv[i])))); last = secs[i]
        return out

    for m, P in Ps.items():
        mv7 = np.abs(mv_window(P, 7))
        d = day_of(P)
        days = sorted(set(int(x) for x in np.unique(d[P["keep"]])))
        fixed_thr = {dd: np.percentile(mv7[P["keep"]], 99.5) for dd in days[BURN:]}
        adapt_thr = {}
        roll_rng = {}
        bars = P["cx"].bars[P["cx"].bars.rth]
        dr = bars.groupby(bars.session_date.astype(str)).apply(
            lambda g: (g.high.max() - g.low.min()) / TICK)
        dr_vals = list(dr.values)
        for j, dd in enumerate(days):
            if j < BURN:
                continue
            kprev = P["keep"] & np.isin(d, days[j - BURN:j])
            adapt_thr[dd] = np.percentile(mv7[kprev], 99.5)
            roll_rng[dd] = float(np.mean(dr_vals[max(0, j - BURN):j]))
        P["_adapt"] = (adapt_thr, roll_rng)
        P["_fixed"] = fixed_thr

    def CTX_fixed(ft, ib, d0, P, a2, b2):
        return ft["ret5m"] >= 50

    def mk_ctx_adapt(m):
        def f(ft, ib, d0, P, a2, b2):
            s0 = None  # thrust uses rolling range via bar's day
            # find day from bar time
            dd = int(P["cx"].bts[ib] // 10**9 // 86400)
            rr = P["_adapt"][1].get(dd)
            return rr is not None and ft["ret5m"] >= k_from[m] * rr
        return f

    for name, use_adapt in [("FIXED numbers (13-14tk burst, thrust 50tk)", False),
                            ("ADAPTIVE (trailing-5d quantile burst, k x rolling range thrust)", True)]:
        per_m = {}
        for m, P in Ps.items():
            thr = P["_adapt"][0] if use_adapt else P["_fixed"]
            fl = build_fires(P, thr)
            ctx = mk_ctx_adapt(m) if use_adapt else CTX_fixed
            per_m[m] = sim(P, fl, ctx)
        print(row(name, per_m))
    print("\nREAD: k calibrated on the OTHER month (k = 50tk / its mean daily range):")
    for m in months:
        print(f"  {m}: k = {k_from[m]:.3f} x trailing-5-session mean daily range")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
