#!/usr/bin/env python3
"""
range_expansion.py — PRICE-MOVEMENT vein, probe #1: range-expansion rate
=========================================================================
WHY (pivot): the trader's own account is that the MOVEMENT/SPEED of price action drives cut/hold.
The entire order-flow family (sign/OFI/persistence/book/magnitude) is null; the one apparent positive
(flow_level/ER vs time-to-pt1) turned out to be a window-contamination ARTIFACT (pt1 sits at/before
entry for ~half of reaches, so the "early" window peeked at/after the target). So we change PRIMITIVE:
price RANGE EXPANSION, which is also the WRB construct itself (a WRB = a range-expansion event).

HYPOTHESIS (pre-registered): trades that REACH target show higher early-window range EXPANSION than
trades that STALL. He holds when movement expands, cuts when it compresses (Crabel 1990 contraction/
expansion; Wilder ATR 1978; Lo & MacKinlay 1988 variance ratio = ballistic vs diffusive).

FEATURES (both scale-free; regime-normalised so they are not just "it was a volatile day"):
  expansion_ratio = realized_range[entry, entry+tau] / realized_range[entry-tau, entry]
                    >1 => range expanded as the trade began, vs the immediately preceding regime.
  within_accel    = realized_range[2nd half of early window] / realized_range[1st half]
                    >1 => movement accelerating within the early window.
  (realized_range = max(mid)-min(mid) over the span, in ticks.)

OUTCOME: BINARY reach (47) vs stall (29) — the ROBUST label. Deliberately NOT time-to-pt1 (contaminated)
and NOT raw MFE (volatility/duration confounded). Entry-forward, SURVIVORS-only (hold>=tau): the clean
frame that fixed the earlier leakage.

WINDOWS: tau=60s PRIMARY (survivors ~45 reach / ~24 stall), tau=30s robustness. Capped at 60 because
the expansion_ratio pre-window needs tau seconds BEFORE entry (windowed parquet carries ~60s pre-entry).

DIRECTION (pre-registered): reach > stall => AUC > 0.5. Clears iff cluster/two-sample bootstrap CI
(seed 0, 10000) excludes 0.5. Reported two-sided.

REUSES: build_arms, read_trade_full (forward_battery); S, TICK (trade_flow_exhaustion). AUC + two-sample
bootstrap implemented locally (rank AUC; resample within each arm).

RUN:  python3 range_expansion.py --config config.toml --wrb wrb_1m.parquet
      python3 range_expansion.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK
from forward_battery import build_arms, read_trade_full

TAUS = [60, 30]
N_MIN = 8


def rank_auc(pos, neg):
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos = pos[~np.isnan(pos)]; neg = neg[~np.isnan(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    allv = np.concatenate([pos, neg]); order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(len(allv)); ranks[order] = np.arange(1, len(allv) + 1)
    # average ties
    u, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    s = np.zeros(len(u)); np.add.at(s, inv, ranks); ranks = (s / cnt)[inv]
    rp = ranks[:len(pos)].sum()
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def two_sample_boot_ci(pos, neg, seed=0, B=10000):
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos = pos[~np.isnan(pos)]; neg = neg[~np.isnan(neg)]
    a = rank_auc(pos, neg)
    if not np.isfinite(a):
        return dict(auc=np.nan, lo=np.nan, hi=np.nan, clears=False, npos=len(pos), nneg=len(neg))
    rng = np.random.default_rng(seed); boot = np.empty(B)
    for i in range(B):
        boot[i] = rank_auc(pos[rng.integers(0, len(pos), len(pos))],
                           neg[rng.integers(0, len(neg), len(neg))])
    lo, hi = float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5))
    return dict(auc=a, lo=lo, hi=hi, clears=(lo > 0.5 or hi < 0.5), npos=len(pos), nneg=len(neg))


def realized_range_tk(ts_ns, mid, t0, t1):
    lo = np.searchsorted(ts_ns, np.int64(t0.value)); hi = np.searchsorted(ts_ns, np.int64(t1.value))
    if hi - lo < 2:
        return np.nan
    seg = mid[lo:hi]
    return (np.nanmax(seg) - np.nanmin(seg)) / TICK


def features(ts_ns, mid, entry, tau):
    R_early = realized_range_tk(ts_ns, mid, entry, entry + S(tau))
    R_pre = realized_range_tk(ts_ns, mid, entry - S(tau), entry)
    h1 = realized_range_tk(ts_ns, mid, entry, entry + S(tau // 2))
    h2 = realized_range_tk(ts_ns, mid, entry + S(tau // 2), entry + S(tau))
    er = (R_early / R_pre) if (R_pre and R_pre > 0) else np.nan
    wa = (h2 / h1) if (h1 and h1 > 0) else np.nan
    return dict(expansion_ratio=er, within_accel=wa, R_early=R_early)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(max(TAUS)) - S(2); t_max = (g.entry + S(max(TAUS))).max()
    ts_ns, rs, sz, mid = read_trade_full(windowed, t_min, t_max)

    for tau in TAUS:
        sub = g[g.hold >= tau].copy()
        rows = [features(ts_ns, mid, r.entry, tau) for _, r in sub.iterrows()]
        F = pd.DataFrame(rows, index=sub.index)
        for c in ("expansion_ratio", "within_accel"):
            sub[c] = F[c].values
        rA = sub[sub.grp == "reach"]; sA = sub[sub.grp == "stall"]
        tag = "  <<< PRIMARY" if tau == 60 else ""
        print(f"\n========== tau={tau}s  survivors reach={len(rA)} stall={len(sA)} =========={tag}")
        if len(rA) < N_MIN or len(sA) < N_MIN:
            print("  UNINFORMATIVE (n<8)"); continue
        for c in ("expansion_ratio", "within_accel"):
            ci = two_sample_boot_ci(rA[c].values, sA[c].values, seed=seed)
            flag = "** reach>stall (clears)" if (ci["clears"] and ci["auc"] > 0.5) else \
                   ("clears WRONG way" if ci["clears"] else "  -")
            print(f"  {c:16s} AUC={ci['auc']:.3f}  CI[{ci['lo']:.3f},{ci['hi']:.3f}]  "
                  f"Rmed={np.nanmedian(rA[c]):+.3f} Smed={np.nanmedian(sA[c]):+.3f}  {flag}")
    print("\nREAD: expansion_ratio>1 and reach>stall (AUC>0.5, CI clears) = early range EXPANSION marks "
          "reachers, matching the trader's stated model. Null here weakens the movement hypothesis at the "
          "1m-tape resolution; next probe = velocity/acceleration of the mid path itself.")


def selftest(config, wrb):
    print("=== SELF-TEST: rank_auc + realized_range + features ===")
    print(f"  AUC pos>neg: {rank_auc([3,4,5],[0,1,2]):.3f} (expect 1.0)")
    print(f"  AUC reversed:{rank_auc([0,1,2],[3,4,5]):.3f} (expect 0.0)")
    print(f"  AUC overlap: {rank_auc([1,2,3],[1,2,3]):.3f} (expect 0.5)")
    assert rank_auc([3,4,5],[0,1,2]) == 1.0 and rank_auc([1,2,3],[1,2,3]) == 0.5
    ci = two_sample_boot_ci([3,4,5,6,7,8,9,10], [0,1,2,3,4,5,6,7], seed=0)
    print(f"  two-sample clears: AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] clears={ci['clears']}")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    ts_ns = (base.value + np.arange(0, 120) * 1_000_000_000).astype(np.int64)
    # pre-window [entry-30,entry] range 4 ticks; early [entry,entry+30] range 16 ticks => ratio 4
    mid = np.concatenate([5000 + np.linspace(0, 1.0, 30),        # 30s pre: range 1.0 pt = 4 tk
                          5000 + np.linspace(0, 4.0, 30),        # 1st half early: 4 pt = 16 tk
                          5004 + np.linspace(0, 4.0, 60)])       # filler
    entry = base + S(30)
    rr_pre = realized_range_tk(ts_ns, mid, entry - S(30), entry)
    rr_early = realized_range_tk(ts_ns, mid, entry, entry + S(30))
    print(f"  pre range={rr_pre:.1f}tk  early range={rr_early:.1f}tk  ratio={rr_early/rr_pre:.2f}")
    assert abs(rr_pre - 4.0) < 0.5 and abs(rr_early - 16.0) < 0.5
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
