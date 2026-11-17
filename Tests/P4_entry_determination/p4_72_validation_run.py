#!/usr/bin/env python3
"""
p4_72_validation_run.py — P4.72 / Strategy 2: THE AUTHORIZED VALIDATION RUN
(2021-09 and 2024-11). Preliminary side check; variable modding resumes after.
==============================================================================
Scope (user-authorized, ADAPTATION_PLAN + pruning):
  BATTERY (6): FIXED control (literal 13 tk burst / 50 tk thrust / 7 s window
    - NOT month-recomputed) | ATR14D | EWMA | OPEN30 | INTRADAY10 | INTRADAY20
    (adaptive variants: training-derived 8 s window; shares 0.042/0.17;
    constants a_on/b_o30/c_N/lambda frozen from training)
  DETECTOR CONFIGS (12): thrust {30,40,50} tk x trigger {D1 top0.5%/7s,
    D1 top1%/10s, D6 accel top1%/10s, D1(0.5%/7s)+D6 union} - percentile
    triggers are self-calibrating BY DEFINITION in this family (as in T-EN69).
Engineering guarantees: per-second mids for every trigger and fill; leg_sec
(v11 sketch) exits; signals (unused here) still built the gate-proven way;
no quantity is computed from validation data except the self-calibrating
percentile triggers that are defined that way.
Metrics per config per month: trades, his matched, win rate, avg win/loss,
total, max-below-start. Decision rule for the battery: maximin (pre-registered).

RUN: python3 Tests/P4_entry_determination/p4_72_validation_run.py         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_66_context_ablation import prep, sim           # noqa: E402
from p4_69_adaptation_plan import session_history, EWMA_L  # noqa: E402

TICK = 0.25
CLUST, MATCH_S = 120, 120
BURST_SHARE, THRUST_SHARE = 0.042, 0.17
C_N = 22.7
VAL_MONTHS = ["2021-09", "2024-11"]


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}
    train_sd = [d for d in dates if d.startswith("2025-10") or d.startswith("2022-02")]
    a_on = float(np.median([SH.rth[d] / SH.on[d] for d in train_sd
                            if np.isfinite(SH.on.get(d, np.nan)) and SH.on[d] > 0]))
    b_o30 = float(np.median([SH.rth[d] / SH.open30[d] for d in train_sd
                             if np.isfinite(SH.open30.get(d, np.nan)) and SH.open30[d] > 0]))
    assert abs(a_on - 0.98) < 0.05 and abs(b_o30 - 2.62) < 0.1, (a_on, b_o30)

    def r_est(method, d):
        i = pos.get(d)
        if i is None or i == 0:
            return None
        if method == "EWMA":
            vals = SH.rth.iloc[max(0, i - 15):i]
            e = float(vals.iloc[0])
            for v in vals.iloc[1:]:
                e = EWMA_L * e + (1 - EWMA_L) * float(v)
            return e
        if method == "ATR14D":
            return float(SH.rth.iloc[max(0, i - 14):i].mean())
        if method == "OPEN30":
            v = SH.open30.get(d, np.nan)
            return b_o30 * float(v) if np.isfinite(v) and v > 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    results = {}
    for month in VAL_MONTHS:
        P = prep(repo, month, insample=False)
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        lo, hi = month_bounds(month)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])

        def mvw(w):
            iw = np.searchsorted(secs, secs - w)
            return (mids - mids[np.maximum(iw, 0)]) / TICK

        mv7, mv8, mv10 = mvw(7), mvw(8), mvw(10)
        i10 = np.searchsorted(secs, secs - 10)
        i30 = np.searchsorted(secs, secs - 30)
        prev20 = (mids[np.maximum(i10, 0)] - mids[np.maximum(i30, 0)]) / TICK
        accel = np.abs(mv10) - np.abs(prev20)
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        sdsec = P["sd"][bar_i]
        # intraday atrN
        h_, l_, c_ = cx.h, cx.l, cx.c
        pc = np.roll(c_, 1); pc[0] = c_[0]
        tr = np.maximum(h_ - l_, np.maximum(np.abs(h_ - pc), np.abs(l_ - pc))) / TICK
        atr = {N: pd.Series(tr).shift(1).rolling(N).mean().to_numpy() for N in (10, 20)}

        def cluster(idx_sign_thr):
            out = []; last = -10**18
            for i, s, t in idx_sign_thr:
                if secs[i] - last > CLUST:
                    out.append((i, s, t)); last = secs[i]
            return out

        def finish(fl3, name):
            kept = []
            for i, s, tthr in fl3:
                s0 = int(secs[i])
                ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
                if ib < 60 or not cx.rth[ib]:
                    continue
                ft = P["feats"](ib, s, s0)
                if ft["ret5m"] >= tthr:
                    kept.append((i, s))
            pnl = sim(P, kept, lambda *a: True)
            matched = 0
            for i, s in kept:
                s0 = int(secs[i])
                if ((np.abs(hs - s0) <= MATCH_S) & (hd == s)).any():
                    matched += 1
            a = np.asarray(pnl); wn = a > 0
            dd0 = -min(0.0, float(np.min(np.cumsum(a)))) if len(a) else 0.0
            results.setdefault(name, {})[month] = (len(a), matched, wn, a, dd0)

        # BATTERY
        finish(cluster([(i, int(np.sign(mv7[i])), 50.0)
                        for i in np.flatnonzero(keep & (np.abs(mv7) >= 13.0))]), "FIXED 13/50/7s")
        for method in ("ATR14D", "EWMA", "OPEN30"):
            fl = []
            Rcache = {}
            for i in np.flatnonzero(keep):
                d = sdsec[i]
                if d not in Rcache:
                    Rcache[d] = r_est(method, d)
                R = Rcache[d]
                if R is None or abs(mv8[i]) < BURST_SHARE * R:
                    continue
                if method == "OPEN30" and P["mins_rth"][bar_i[i]] < 30:
                    continue
                fl.append((i, int(np.sign(mv8[i])), THRUST_SHARE * R))
            finish(cluster(fl), method)
        for N in (10, 20):
            Rsec = C_N * atr[N][bar_i]
            fl = [(i, int(np.sign(mv8[i])), THRUST_SHARE * Rsec[i])
                  for i in np.flatnonzero(keep & np.isfinite(Rsec))
                  if abs(mv8[i]) >= BURST_SHARE * Rsec[i]]
            finish(cluster(fl), f"INTRADAY{N}")
        # DETECTOR CONFIGS
        thr_d1a = np.percentile(np.abs(mv7)[keep], 99.5)
        thr_d1b = np.percentile(np.abs(mv10)[keep], 99.0)
        thr_d6 = np.percentile(accel[keep & np.isfinite(accel)], 99.0)
        f_d1a = [(i, int(np.sign(mv7[i]))) for i in np.flatnonzero(keep & (np.abs(mv7) >= thr_d1a))]
        f_d1b = [(i, int(np.sign(mv10[i]))) for i in np.flatnonzero(keep & (np.abs(mv10) >= thr_d1b))]
        f_d6 = [(i, int(np.sign(mv10[i]))) for i in np.flatnonzero(keep & (accel >= thr_d6))]
        f_un = sorted(set(f_d1a) | set(f_d6), key=lambda t: secs[t[0]])
        for tname, fl in [("D1 0.5%/7s", f_d1a), ("D1 1%/10s", f_d1b),
                          ("D6 accel", f_d6), ("D1+D6 union", f_un)]:
            for thrust in (30, 40, 50):
                fl3 = cluster([(i, s, float(thrust)) for i, s in fl])
                finish(fl3, f"{tname}, thrust {thrust}")
    # report
    print("| Config | " + " | ".join(
        f"{m}: trades / his / win% / total / DD" for m in VAL_MONTHS) + " | Worst month |")
    print("|---|---|---|---|")
    for name, per in results.items():
        cells = []; worst = None
        for m in VAL_MONTHS:
            n, matched, wn, a, dd0 = per[m]
            tot = a.sum() if n else 0.0
            worst = tot if worst is None else min(worst, tot)
            cells.append(f"{n} / {matched} / {wn.mean():.0%} / {tot:+.1f} / {dd0:.1f}"
                         if n else "0 trades")
        print(f"| {name} | " + " | ".join(cells) + f" | {worst:+.1f} |")
    print("\nHIS months (all entries, as parsed): 2021-09: 173 trades, 79%, +477 |")
    print("2024-11: 69 trades, 75%, +450")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
