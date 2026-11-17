#!/usr/bin/env python3
"""
p4_86_atr_lane_adapt.py — P4.86 / Strategy 2: ATR-lane burst threshold made
ADAPTIVE. TRAINING MONTHS ONLY.
===============================================================================
T-EN91: ATR14D's q = |mv8|/R_est is NOT regime-invariant, so a static burst
share has no derivation in that lane. Candidates tested here, thrust held at
0.15 (the volume-lane column) so only the burst axis moves:

(a1) TRAILING-q PERCENTILE: threshold(day) = Pth pct of q over all PRIOR
     sessions in the loaded data (expanding, min 1 prior session; the month's
     first session cannot fire) x today's ATR14D.  P in {85, 90, 95}.
(a2) TRAILING RAW-TICKS PERCENTILE: threshold(day) = Pth pct of raw |mv8|
     (ticks) over prior sessions. No R_est in the burst leg at all.
(b)  DAYSOFAR scheme: R_est = C_N x mean TR of ALL of today's RTH bars so far
     (expanding from the open, exclusive of the current bar, min 10 bars; the
     first 10 RTH minutes cannot fire). Burst grid 0.014-0.030.
(c)  RTH60 scheme: R_est = C_N x mean TR of the last min(60, bars-so-far)
     RTH bars of TODAY ONLY (never crosses into ETH; min 10 bars). Same grid.
References: ATR14D static shares 0.018 / 0.022 at thrust 0.15.
NOTES: C_N = 22.7 was calibrated on a 10-bar mean TR; reusing it for (b)/(c)
is an approximation - the share grid absorbs the level difference. For (b)/(c)
the thrust uses the scheme's own R_est; for (a) the lane's ATR14D thrust is
unchanged. Trailing percentiles use only data loaded for the month, so the
first session of each month has no fires under (a) - counts dip accordingly.

RUN: python3 Tests/P4_entry_determination/p4_86_atr_lane_adapt.py         (repo root)
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
C_N = 22.7
W, GAP, WAIT = 2, 45, 1
TSH = 0.15
PCTS = (85, 90, 95)
BGRID = (0.014, 0.018, 0.022, 0.026, 0.030)


def day_sofar_R(sd_bar, tr, rth):
    """(b) expanding mean TR of today's RTH bars so far (exclusive, min 10)."""
    out = np.full(len(tr), np.nan)
    df = pd.DataFrame({"d": sd_bar, "t": np.where(rth, tr, 0.0), "n": rth.astype(float)})
    g = df.groupby("d", sort=False)
    cs = g["t"].cumsum() - df["t"]          # exclusive cumsum within day
    cn = g["n"].cumsum() - df["n"]
    m = (cn >= 10).to_numpy()
    out[m] = (cs[m] / cn[m]).to_numpy()
    return C_N * out


def rth60_R(sd_bar, tr, rth):
    """(c) mean TR of the last min(60, so-far) RTH bars of TODAY (min 10)."""
    out = np.full(len(tr), np.nan)
    for d in pd.unique(sd_bar):
        ix = np.flatnonzero((sd_bar == d) & rth)
        if len(ix) < 11:
            continue
        pref = np.concatenate([[0.0], np.cumsum(tr[ix])])
        for k in range(10, len(ix)):        # k = exclusive count so far
            lo = max(0, k - 60)
            out[ix[k]] = (pref[k] - pref[lo]) / (k - lo)
    return C_N * out


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {}
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_tr"] = tr
        P["_Ratr"] = np.array([{d: atr14d(d) for d in set(P["sd"])}.get(d) or np.nan
                               for d in P["sd"]])[bar_i]
        P["_Rday_sofar"] = day_sofar_R(np.asarray(P["sd"]), tr, np.asarray(cx.rth))[bar_i]
        P["_Rrth60"] = rth60_R(np.asarray(P["sd"]), tr, np.asarray(cx.rth))[bar_i]
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        P["_sd_sec"] = np.asarray(P["sd"])[bar_i]       # session date per second
        Ps[m] = P

    def fires(P, bt, Rthr):
        """bt = burst threshold per second (ticks); Rthr = R_est per second
        for the thrust test. Returns the fire list."""
        cx = P["cx"]
        secs, keep = P["secs"], P["keep"]
        kept = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(bt) & np.isfinite(Rthr)):
            if abs(P["_mv8"][i]) < bt[i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = P["_bar_i"][i]
            if ib < 60 or not cx.rth[ib]:
                continue
            d0 = int(np.sign(P["_mv8"][i]))
            if d0 * P["_ret2"][ib] >= TSH * np.sqrt(W / 5) * Rthr[i]:
                kept.append((i, d0))
        return kept

    def trailing_pct(P, pct, raw):
        """Per-second burst threshold from prior sessions' distribution."""
        secs, keep = P["secs"], P["keep"]
        sd = P["_sd_sec"]
        q = np.abs(P["_mv8"]) / P["_Ratr"]
        days = pd.unique(sd[keep])
        thr = np.full(len(secs), np.nan)
        for k, d in enumerate(days):
            prior = keep & np.isin(sd, days[:k]) & np.isfinite(q)
            if not prior.any():
                continue
            v = np.abs(P["_mv8"])[prior] if raw else q[prior]
            t = float(np.percentile(v, pct))
            m = sd == d
            thr[m] = t if raw else t * P["_Ratr"][m]
        return thr

    rows = []
    rows.append(("ATR14D static 0.018 (reference)",
                 {m: (0.018 * Ps[m]["_Ratr"], Ps[m]["_Ratr"]) for m in Ps}))
    rows.append(("ATR14D static 0.022 (reference)",
                 {m: (0.022 * Ps[m]["_Ratr"], Ps[m]["_Ratr"]) for m in Ps}))
    for p in PCTS:
        rows.append((f"(a1) trailing q-pct {p} x ATR14D",
                     {m: (trailing_pct(Ps[m], p, raw=False), Ps[m]["_Ratr"]) for m in Ps}))
    for p in PCTS:
        rows.append((f"(a2) trailing raw-ticks pct {p}",
                     {m: (trailing_pct(Ps[m], p, raw=True), Ps[m]["_Ratr"]) for m in Ps}))
    for b in BGRID:
        rows.append((f"(b) DAYSOFAR, share {b:.3f}",
                     {m: (b * Ps[m]["_Rday_sofar"], Ps[m]["_Rday_sofar"]) for m in Ps}))
    for b in BGRID:
        rows.append((f"(c) RTH60, share {b:.3f}",
                     {m: (b * Ps[m]["_Rrth60"], Ps[m]["_Rrth60"]) for m in Ps}))

    print(f"ATR-lane burst adaptation candidates. Thrust {TSH} throughout; "
          f"45 s gap, 1-bar wait; training months only.\n")
    print("| Config | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for name, per in rows:
        per_m = {m: sim(Ps[m], fires(Ps[m], bt, Rt), lambda *a: True, cooldown=WAIT)
                 for m, (bt, Rt) in per.items()}
        print(row(name, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
