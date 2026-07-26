#!/usr/bin/env python3
"""
velocity_ratio_confirm.py — robustness of the one clear (velocity_ratio, tau=60, AUC 0.660)
============================================================================================
velocity_ratio cleared at tau=60 (AUC 0.660, CI [0.522,0.788], reach>stall). Before building on it,
confirm it is not (a) carried by a few of the 24 stalls, or (b) a label-shuffle fluke. Three checks,
each independent of the bootstrap CI that first flagged it:

  1. DECOMPOSITION. Quartiles of velocity_ratio per arm + fraction below 1.0 (= decelerated vs own
     pre-entry pace). Tests the mechanism read: reachers hold pace (~1.0), stallers decelerate (<1.0).
  2. JACKKNIFE (leave-one-out). Recompute AUC dropping each single trade. If the clear depends on one
     point, min-AUC over drops falls toward/below 0.5. Robust effect => all drops stay well above 0.5.
  3. PERMUTATION. Shuffle reach/stall labels 10000x (seed 0), recompute AUC; one-sided p = fraction
     >= observed (pre-registered reach>stall). Exact-ish significance that does not assume the bootstrap.

No new hypothesis — this only stress-tests an existing clear. tau=60 primary, tau=30 shown for context.

REUSES: build_arms (forward_battery); read_per_second, S, TICK (trade_flow_exhaustion);
features, pathlen_tk (velocity_acceleration); rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 velocity_ratio_confirm.py --config config.toml --wrb wrb_1m.parquet
      python3 velocity_ratio_confirm.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, read_per_second
from forward_battery import build_arms
from velocity_acceleration import features
from range_expansion import rank_auc, two_sample_boot_ci

TAUS = [60, 30]


def jackknife_auc(pos, neg):
    """Leave-one-out AUC range over dropping each single observation (from either arm)."""
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos = pos[~np.isnan(pos)]; neg = neg[~np.isnan(neg)]
    aucs = []
    for i in range(len(pos)):
        aucs.append(rank_auc(np.delete(pos, i), neg))
    for j in range(len(neg)):
        aucs.append(rank_auc(pos, np.delete(neg, j)))
    a = np.array(aucs)
    return dict(min=float(a.min()), max=float(a.max()), mean=float(a.mean()),
                n_below_half=int((a <= 0.5).sum()))


def perm_test(pos, neg, seed=0, B=10000):
    """One-sided label-permutation p for reach>stall (pre-registered)."""
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos = pos[~np.isnan(pos)]; neg = neg[~np.isnan(neg)]
    obs = rank_auc(pos, neg); pool = np.concatenate([pos, neg]); npos = len(pos)
    rng = np.random.default_rng(seed); ge = 0
    for _ in range(B):
        rng.shuffle(pool)
        if rank_auc(pool[:npos], pool[npos:]) >= obs:
            ge += 1
    return obs, (ge + 1) / (B + 1)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(max(TAUS)) - S(2); t_max = (g.entry + S(max(TAUS))).max()
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for tau in TAUS:
        sub = g[g.hold >= tau].copy()
        sub["vr"] = [features(sec, mid, r.entry, tau)["velocity_ratio"] for _, r in sub.iterrows()]
        rA = sub[sub.grp == "reach"].vr.dropna().values
        sA = sub[sub.grp == "stall"].vr.dropna().values
        ci = two_sample_boot_ci(rA, sA, seed=seed)
        tag = "  <<< PRIMARY" if tau == 60 else ""
        print(f"\n========== tau={tau}s  reach={len(rA)} stall={len(sA)}  AUC={ci['auc']:.3f} "
              f"CI[{ci['lo']:.3f},{ci['hi']:.3f}] =========={tag}")
        q = lambda a, p: np.quantile(a, p)
        print("  1. DECOMPOSITION (velocity_ratio; 1.0 = held pre-entry pace)")
        print(f"     reach  q25={q(rA,.25):.3f} med={q(rA,.5):.3f} q75={q(rA,.75):.3f}  "
              f"frac<1.0 = {np.mean(rA<1):.2f}")
        print(f"     stall  q25={q(sA,.25):.3f} med={q(sA,.5):.3f} q75={q(sA,.75):.3f}  "
              f"frac<1.0 = {np.mean(sA<1):.2f}")
        jk = jackknife_auc(rA, sA)
        print(f"  2. JACKKNIFE  min={jk['min']:.3f} max={jk['max']:.3f} mean={jk['mean']:.3f}  "
              f"drops with AUC<=0.5: {jk['n_below_half']}  "
              f"{'(robust)' if jk['min']>0.5 else '(FRAGILE: a single drop crosses 0.5)'}")
        obs, p = perm_test(rA, sA, seed=seed)
        print(f"  3. PERMUTATION  observed AUC={obs:.3f}  one-sided p={p:.4f}  "
              f"{'(beyond shuffle)' if p<0.05 else '(within shuffle noise)'}")
    print("\nREAD: robust if (stall frac<1 >> reach) AND jackknife min stays >0.5 AND perm p<0.05 at tau=60. "
          "Fragile if any single drop crosses 0.5 or p only marginal — then it is a soft clear at n=24 stalls.")


def selftest(config, wrb):
    print("=== SELF-TEST: jackknife + permutation ===")
    sep_pos = np.arange(10, 22.0); sep_neg = np.arange(0, 12.0)  # clearly separated
    jk = jackknife_auc(sep_pos, sep_neg)
    print(f"  separated jackknife min={jk['min']:.3f} (expect >0.5)"); assert jk["min"] > 0.5
    _, p_sep = perm_test(sep_pos, sep_neg, seed=0, B=2000)
    print(f"  separated perm p={p_sep:.4f} (expect small)"); assert p_sep < 0.05
    rng = np.random.default_rng(1)
    a = rng.normal(0, 1, 30); b = rng.normal(0, 1, 30)
    _, p_null = perm_test(a, b, seed=0, B=2000)
    print(f"  overlapping perm p={p_null:.4f} (expect not small)"); assert p_null > 0.05
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
