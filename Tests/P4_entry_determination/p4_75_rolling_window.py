#!/usr/bin/env python3
"""
p4_75_rolling_window.py — P4.75 / Strategy 2: INTRADAY-ROLLING thrust window
(the user's INTRADAY-style adaptation applied to the window itself).
TRAINING MONTHS ONLY.
=============================================================================
At every bar, thrust window w(i) = clamp(75th-percentile length of the
directional 1-min runs COMPLETED in the last N bars, lo..hi) minutes
(fallback 2 when no run completed in the lookback). Thrust threshold scales
with the live window: share x sqrt(w/5) x R_est. Burst side per scheme as
adopted: ATR14D (0.042 x 14-session range, 8 s window) and INTRADAY10
(0.042 x 22.7 x last-10-bar TR, 8 s). Static w=2 rows = reference (P4.73).
Grid: N = 30 / 60 / 120 bars with w free in [1,4]; N = 60 with w in [2,3].
Also reported: how the chosen window distributes over 1/2/3/4 minutes.

RUN: python3 Tests/P4_entry_determination/p4_75_rolling_window.py         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
CLUST = 120
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7


def rolling_window_series(cx, N, lo, hi):
    """Per-bar chosen window (minutes) from runs completed in the last N bars."""
    n = len(cx.c)
    sgn = np.sign(np.diff(cx.c, prepend=cx.c[0]))
    w = np.full(n, 2, dtype=int)
    ends, lens = [], []
    cur = 0; last = 0
    ptr = 0
    for i in range(n):
        if not cx.rth[i]:
            cur = 0; last = 0
        else:
            s = sgn[i]
            if s != 0 and s == last:
                cur += 1
            elif s != 0:
                if cur:
                    ends.append(i); lens.append(cur)
                cur = 1; last = s
        while ptr < len(ends) and ends[ptr] <= i - N:
            ptr += 1
        if ptr < len(ends):
            w[i] = int(np.clip(np.ceil(np.percentile(lens[ptr:], 75)), lo, hi))
    return w


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    for m, P in Ps.items():
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        P["_bar_i"] = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        P["_Rday"] = {d: atr14d(d) for d in set(P["sd"])}
        P["_retw"] = {w: np.concatenate([[0.0] * w, (cx.c[w:] - cx.c[:-w]) / TICK])
                      for w in (1, 2, 3, 4)}

    def fires(P, scheme):
        secs, keep, mv = P["secs"], P["keep"], P["_mv8"]
        if scheme == "ATR14D":
            Rs = np.array([P["_Rday"].get(d) or np.nan for d in P["sd"]])[P["_bar_i"]]
            bt = BURST_SHARE * Rs
        else:
            bt = BURST_SHARE * C_N * P["_atr10"][P["_bar_i"]]
        out = []; last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(bt)):
            if abs(mv[i]) < bt[i]:
                continue
            if secs[i] - last > CLUST:
                out.append(i); last = secs[i]
        return out

    variants = [("static w=2 (reference)", None, None, None)] + \
               [(f"rolling N={N}, w in [{lo},{hi}]", N, lo, hi)
                for N, lo, hi in ((30, 1, 4), (60, 1, 4), (120, 1, 4), (60, 2, 3))]
    for scheme in ("ATR14D", "INTRADAY10"):
        print(f"===== {scheme} =====")
        print("| Window rule | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for name, N, lo, hi in variants:
            per_m = {}
            wd_all = []
            for m, P in Ps.items():
                cx = P["cx"]
                wser = (np.full(len(cx.c), 2, dtype=int) if N is None
                        else rolling_window_series(cx, N, lo, hi))
                wd_all += list(wser[cx.rth])
                fl = fires(P, scheme)
                kept = []
                for i in fl:
                    ib = P["_bar_i"][i]
                    if ib < 60 or not cx.rth[ib]:
                        continue
                    d0 = int(np.sign(P["_mv8"][i]))
                    w = int(wser[ib])
                    if scheme == "ATR14D":
                        R = P["_Rday"].get(P["sd"][ib])
                        if not R:
                            continue
                    else:
                        R = C_N * P["_atr10"][ib]
                        if not np.isfinite(R):
                            continue
                    tthr = THRUST_SHARE * np.sqrt(w / 5) * R
                    if d0 * P["_retw"][w][ib] >= tthr:
                        kept.append((i, d0))
                per_m[m] = sim(P, kept, lambda *a: True)
            extra = ""
            if N is not None:
                c = pd.Series(wd_all).value_counts(normalize=True).sort_index()
                extra = "  (w: " + " ".join(f"{int(k)}m {v:.0%}" for k, v in c.items()) + ")"
            print(row(name, per_m) + extra)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
