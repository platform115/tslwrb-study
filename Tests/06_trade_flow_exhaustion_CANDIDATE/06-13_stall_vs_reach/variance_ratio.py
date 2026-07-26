#!/usr/bin/env python3
"""
variance_ratio.py — PRICE-MOVEMENT vein, probe #3: Lo-MacKinlay variance ratio (independent check)
===================================================================================================
WHY: velocity_ratio (path-length SPEED) cleared at tau=60 (AUC 0.660). The strongest test of whether
"movement" is real — vs velocity_ratio being one lucky marginal clear — is an INDEPENDENT movement
primitive agreeing. Variance ratio measures a DIFFERENT thing: the autocorrelation SHAPE of returns
(does price move ballistically/trend, or diffuse/mean-revert), not how fast it moves. Two different
movement measurements separating reach>stall = far stronger than re-confirming one.

VR(q) = Var(q-period return) / (q * Var(1-period return))   (Lo & MacKinlay 1988)
  VR>1 trending (positive return autocorr) · VR=1 random walk · VR<1 mean-reverting (chop).

HYPOTHESIS (pre-registered): reachers TREND (VR higher); stallers CHOP / mean-revert (VR lower) ->
reach VR > stall VR -> AUC>0.5. Independent of velocity_ratio: a stall can be FAST but choppy (high
path length, low VR), a reach can trend (both high). They need not agree — which is the point.
CAVEAT (logged, not fatal): for reaches whose pt1 falls inside the window, the favorable trend that
made VR high is partly the move that reached pt1 — mild coupling, same family as the pt1-timing issue;
VR is direction-agnostic (up/down trend both raise it) so it is less circular than signed velocity.

FEATURE: VR on per-second mid in [entry, entry+tau], SURVIVORS-only. q scales with window
(tau=60 -> q=10; tau=30 -> q=5). OUTCOME: BINARY reach (47) vs stall (29). tau=60 PRIMARY, 30 robustness.
Clears iff two-sample bootstrap CI (seed 0, 10000) excludes 0.5; reach>stall direction.

REUSES: build_arms (forward_battery); read_per_second, S (trade_flow_exhaustion);
rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 variance_ratio.py --config config.toml --wrb wrb_1m.parquet
      python3 variance_ratio.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci

TAUS = [60, 30]
N_MIN = 8


def variance_ratio(sec, mid, t0, t1, q):
    a = np.searchsorted(sec, np.int64(pd.Timestamp(t0).value // 1_000_000_000), "left")
    b = np.searchsorted(sec, np.int64(pd.Timestamp(t1).value // 1_000_000_000), "left")
    m = mid[a:b]
    if len(m) < 2 * q + 2:
        return np.nan
    r1 = np.diff(m)
    v1 = np.var(r1, ddof=1)
    if v1 <= 0:
        return np.nan
    rq = m[q:] - m[:-q]
    vq = np.var(rq, ddof=1)
    return (vq / q) / v1


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(2); t_max = (g.entry + S(max(TAUS))).max()
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for tau in TAUS:
        q = 10 if tau >= 60 else 5
        sub = g[g.hold >= tau].copy()
        sub["vr"] = [variance_ratio(sec, mid, r.entry, r.entry + S(tau), q) for _, r in sub.iterrows()]
        rA = sub[sub.grp == "reach"].vr.dropna().values
        sA = sub[sub.grp == "stall"].vr.dropna().values
        tag = "  <<< PRIMARY" if tau == 60 else ""
        print(f"\n========== tau={tau}s (q={q})  survivors reach={len(rA)} stall={len(sA)} =========={tag}")
        if len(rA) < N_MIN or len(sA) < N_MIN:
            print("  UNINFORMATIVE (n<8)"); continue
        ci = two_sample_boot_ci(rA, sA, seed=seed)
        flag = "** reach>stall (clears)" if (ci["clears"] and ci["auc"] > 0.5) else \
               ("clears WRONG way" if ci["clears"] else "  -")
        print(f"  variance_ratio  AUC={ci['auc']:.3f}  CI[{ci['lo']:.3f},{ci['hi']:.3f}]  "
              f"Rmed={np.nanmedian(rA):.3f} Smed={np.nanmedian(sA):.3f}  {flag}")
        print(f"     reach frac VR>1 (trending) = {np.mean(rA>1):.2f}   stall = {np.mean(sA>1):.2f}")
    print("\nREAD: clears reach>stall = reaches TREND, stalls CHOP — a SECOND, independent movement "
          "feature agreeing with velocity_ratio => the movement vein is real, not a lone marginal clear. "
          "Null => the signal is SPEED (velocity) not SHAPE (trend), and velocity_ratio stands alone (weaker).")


def selftest(config, wrb):
    print("=== SELF-TEST: variance_ratio on known processes ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 200)).astype(np.int64)
    rng = np.random.default_rng(0)
    rw = 5000 + np.cumsum(rng.normal(0, 0.25, 200))                       # iid returns -> VR~1
    # momentum: positively autocorrelated returns (AR(1) +0.6) -> VR>1
    eps = rng.normal(0, 0.25, 200); r = np.zeros(200)
    for t in range(1, 200):
        r[t] = 0.6 * r[t - 1] + eps[t]
    mom = 5000 + np.cumsum(r)
    mr = 5000 + (np.arange(200) % 2) * 0.5 + rng.normal(0, 0.02, 200)     # alternating -> VR<1
    t0 = base; t1 = base + S(180)
    vr_rw = variance_ratio(sec, rw, t0, t1, 10)
    vr_tr = variance_ratio(sec, mom, t0, t1, 10)
    vr_mr = variance_ratio(sec, mr, t0, t1, 10)
    print(f"  random walk VR={vr_rw:.2f} (~1)   momentum VR={vr_tr:.2f} (>1)   mean-revert VR={vr_mr:.2f} (<1)")
    assert vr_tr > 1.3 and vr_mr < 0.8 and 0.5 < vr_rw < 1.8
    assert rank_auc([2, 3, 4], [0, 1, 1.5]) == 1.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
