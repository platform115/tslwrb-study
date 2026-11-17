#!/usr/bin/env python3
"""
p4_69_adaptation_plan.py — P4.69 / Strategy 2: the PRE-REGISTERED adaptation
battery. TRAINING MONTHS ONLY (this run); the frozen plan for validation lives
in ADAPTATION_PLAN.md.
=============================================================================
Design assumption (user): the burst WINDOW is near-universal (fixed 7 s);
only the TICK thresholds adapt. Each estimator produces an expected day range
R_est, and thresholds follow the frozen T-EN71 ratios:
    burst threshold  = 0.042 x R_est      thrust threshold = 0.17 x R_est
Estimators (precedent in parentheses; calibration constants from training,
frozen in ADAPTATION_PLAN.md):
  FIXED       13 tk burst / 50 tk thrust (baseline, no adaptation)
  PRIORDAY    R_est = previous session's RTH range
  EWMA        R_est_d = 0.7 R_est_(d-1) + 0.3 R_(d-1)  (RiskMetrics-style)
  ATR14D      R_est = mean RTH range, trailing 14 sessions (Wilder 1978)
  TRAIL21     R_est = mean RTH range, trailing 21 sessions (slow recalibration)
  OVERNIGHT   R_est = a x overnight (ETH) range, a = training median of
              RTH/overnight (Crabel 1990 lineage)
  OPEN30      R_est = b x first-30-min RTH range, b = training median of
              RTH/open30; trades only after the first 30 min for this variant
Session-range history comes from the full front-month series, so trailing
estimators reach back across month boundaries. All variants skip each month's
first session (prior-day needs one) - fixed baseline too, for fairness.
Config otherwise: 7 s burst window, direction = burst sign, no signal, no
session cut, 120 s clustering, v11 sketch management, mid fills.

RUN: python3 Tests/P4_entry_determination/p4_69_adaptation_plan.py        (repo root)
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
BURST_SHARE, THRUST_SHARE = 0.042, 0.17
EWMA_L = 0.7


def session_history(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    g = es.groupby([es.session_date.astype(str), es.session == "RTH"])
    hi = g.high.max(); lo = g.low.min()
    rng = ((hi - lo) / TICK).unstack()
    out = pd.DataFrame({"rth": rng.get(True), "on": rng.get(False)}).dropna(subset=["rth"])
    out = out.sort_index()
    # first-30-min RTH range per session
    rth = es[es.session == "RTH"].copy()
    rth["sd"] = rth.session_date.astype(str)
    rth = rth.sort_values("ts_event")
    o30 = rth.groupby("sd").head(30).groupby("sd").apply(
        lambda x: (x.high.max() - x.low.min()) / TICK)
    out["open30"] = o30
    return out


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}
    # frozen calibration constants (training sessions only)
    train_sd = [d for d in dates if d.startswith("2025-10") or d.startswith("2022-02")]
    a_on = float(np.median([SH.rth[d] / SH.on[d] for d in train_sd
                            if np.isfinite(SH.on.get(d, np.nan)) and SH.on[d] > 0]))
    b_o30 = float(np.median([SH.rth[d] / SH.open30[d] for d in train_sd
                             if np.isfinite(SH.open30.get(d, np.nan)) and SH.open30[d] > 0]))
    print(f"frozen constants: a_overnight = {a_on:.2f}, b_open30 = {b_o30:.2f}, "
          f"shares = {BURST_SHARE}/{THRUST_SHARE}, EWMA lambda = {EWMA_L}\n")

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
        return None

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    for m, P in Ps.items():
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 7)
        P["_mv7"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        # per-second session-date string via bar mapping
        bar_i = np.searchsorted(P["cx"].bts, secs * 10**9, "right") - 1
        P["_sdsec"] = P["sd"][np.clip(bar_i, 0, len(P["sd"]) - 1)]
        P["_first"] = sorted(set(P["sd"][P["cx"].rth]))[0]
        # minute-of-rth per second for OPEN30's delay
        P["_minrth"] = P["mins_rth"][np.clip(bar_i, 0, len(P["sd"]) - 1)]

    def build(P, method):
        mv7, keep = P["_mv7"], P["keep"]
        out = []
        last = -10**18
        th_cache = {}
        for i in np.flatnonzero(keep):
            d = P["_sdsec"][i]
            if d == P["_first"]:
                continue
            if method == "OPEN30" and P["_minrth"][i] < 30:
                continue
            if d not in th_cache:
                if method == "FIXED":
                    th_cache[d] = (np.percentile(np.abs(mv7)[keep], 99.5), 50.0)
                else:
                    R = r_est(method, d)
                    th_cache[d] = (BURST_SHARE * R, THRUST_SHARE * R) if R else None
            tc = th_cache[d]
            if tc is None or abs(mv7[i]) < tc[0]:
                continue
            if P["secs"][i] - last > CLUST:
                out.append((i, int(np.sign(mv7[i])), tc[1]))
                last = P["secs"][i]
        return out

    print("| Estimator | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for method in ("FIXED", "PRIORDAY", "EWMA", "ATR14D", "TRAIL21", "OVERNIGHT", "OPEN30"):
        per_m = {}
        for m, P in Ps.items():
            fl3 = build(P, method)
            thr_map = {i: t for i, _, t in fl3}

            def ctx(ft, ib, d0, P_, a2, b2, _tm=thr_map):
                return True   # thrust checked below via closure trick
            # sim() checks context via ctx_fun(ft, ib, d0, P, a2, b2); we need
            # per-fire thrust -> wrap: filter fires by thrust inside ctx using feats
            fl = [(i, s) for i, s, _ in fl3]
            tmap = {i: t for i, s, t in fl3}

            def ctx2(ft, ib, d0, P_, a2, b2, _fl=None):
                return True
            # do thrust filtering manually: pre-filter fires whose ret5m >= thrust
            kept = []
            for i, s in fl:
                s0 = int(P["secs"][i])
                ib = int(np.searchsorted(P["cx"].bts, s0 * 10**9)) - 1
                if ib < 60 or not P["cx"].rth[ib]:
                    continue
                ft = P["feats"](ib, s, s0)
                if ft["ret5m"] >= tmap[i]:
                    kept.append((i, s))
            per_m[m] = sim(P, kept, lambda *a: True)
        print(row(method, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
