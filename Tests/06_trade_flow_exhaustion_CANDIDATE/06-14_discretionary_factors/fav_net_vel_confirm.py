#!/usr/bin/env python3
"""
fav_net_vel_confirm.py — F1/S2 confirmation: is the fav_net_vel clear robust, and is it a new axis?
====================================================================================================
s2_directional_velocity found fav_net_vel @ tau=60 clears on the DECISIVE survivor subset
(AUC 0.669 [0.527,0.800] raw; 0.690 norm) with rho(fav_net_vel, velocity_ratio) ~ +0.01.
Same treatment velocity_ratio got before candidate status (velocity_ratio_confirm), plus a proper
test of the independence claim.

PRE-REGISTERED:
  Target: fav_net_vel (RAW), tau=60, survivor subset hold>=60 (45/24) DECISIVE; all-trades line too.
  1) JACKKNIFE  leave-one-out AUC; robust iff min > 0.5 (no single trade carries the clear).
  2) PERMUTATION 10000 label shuffles (seed 0), one-sided p = frac(perm AUC >= observed); p < 0.05.
  3) DECOMPOSITION fraction of each arm with net favorable progress > 0 at 60s
     (reach median +0.083 tk/s vs stall ~0 -> expect reach frac substantially higher).
  4) INDEPENDENCE rho(fav_net_vel, velocity_ratio) with pair-bootstrap 95% CI (10000, seed 0).
     The +0.01 point estimate at n=69 has a wide CI; claim "new axis" only if CI is comfortably
     inside (-0.4, +0.4) — i.e. excludes strong redundancy, not "proves zero."
  5) STRATIFIED F5 PREVIEW velocity_ratio AUC within low/high halves of fav_net_vel (median split).
     Cells need >=8 per arm to be informative. If VR separates within halves, the two features are
     combinable (gated-rule material); if VR dies within halves, they overlap more than rho suggests.

RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/fav_net_vel_confirm.py \
      --config config.toml --wrb wrb_1m.parquet
  ... --selftest for synthetic checks.
Registry: T-DF02 · family=speed · code_ref=06-14_discretionary_factors/fav_net_vel_confirm.py
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from velocity_acceleration import pathlen_tk
from s2_directional_velocity import s2_feats, spearman, PRE_W

TAU = 60
N_MIN = 8


def jackknife(r, s):
    aucs = []
    for i in range(len(r)):
        aucs.append(rank_auc(np.delete(r, i), s))
    for j in range(len(s)):
        aucs.append(rank_auc(r, np.delete(s, j)))
    a = np.array(aucs, float)
    return float(np.nanmin(a)), float(np.nanmax(a))


def permutation_p(r, s, seed=0, B=10000):
    obs = rank_auc(r, s)
    pool = np.concatenate([r, s]); nr = len(r)
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(B):
        p = rng.permutation(pool)
        if rank_auc(p[:nr], p[nr:]) >= obs:
            hits += 1
    return obs, (hits + 1) / (B + 1)


def spearman_boot_ci(x, y, seed=0, B=10000):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y); x, y = x[m], y[m]
    rho = spearman(x, y)
    rng = np.random.default_rng(seed); boot = np.empty(B)
    idx = np.arange(len(x))
    for i in range(B):
        k = rng.integers(0, len(x), len(x))
        boot[i] = spearman(x[k], y[k])
    return rho, float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5)), len(x)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    F = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, TAU, r.side) for _, r in g.iterrows()],
                     index=g.index)
    g = g.join(F)
    # velocity_ratio on the same trades (survivors)
    vr = []
    for _, r in g.iterrows():
        fwd = pathlen_tk(sec, mid, r.entry, pd.Timestamp(r.entry) + S(TAU))
        pre = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(PRE_W), r.entry)
        vr.append((fwd / TAU) / (pre / PRE_W) if (fwd is not None and np.isfinite(fwd) and pre and pre > 0) else np.nan)
    g["velocity_ratio"] = np.array(vr, float)

    surv = g[g.hold >= TAU]
    rS = surv[surv.grp == "reach"]; sS = surv[surv.grp == "stall"]
    r = rS["fav_net_vel"].dropna().values; s = sS["fav_net_vel"].dropna().values
    print(f"\n=== DECISIVE frame: survivors hold>={TAU}s  reach={len(r)} stall={len(s)} ===")
    ci = two_sample_boot_ci(r, s, seed=seed)
    print(f"  fav_net_vel AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"{'CLEARS' if ci['clears'] and ci['auc']>0.5 else 'no clear'}")

    lo, hi = jackknife(r, s)
    print(f"  [1] jackknife AUC min={lo:.3f} max={hi:.3f}  -> {'ROBUST (min>0.5)' if lo > 0.5 else 'FRAGILE (min<=0.5)'}")

    obs, p = permutation_p(r, s, seed=seed)
    print(f"  [2] permutation p={p:.4f} (one-sided, AUC>=obs {obs:.3f})  -> {'beyond shuffle' if p < 0.05 else 'NOT beyond shuffle'}")

    fr = float((r > 0).mean()); fs = float((s > 0).mean())
    print(f"  [3] decomposition: frac(net favorable progress > 0 at {TAU}s)  reach={fr:.2f}  stall={fs:.2f}")

    rho, rlo, rhi, n = spearman_boot_ci(surv["fav_net_vel"].values, surv["velocity_ratio"].values, seed=seed)
    verdict = "supports NEW AXIS (excludes strong redundancy)" if (rlo > -0.4 and rhi < 0.4) else "CI too wide / redundancy not excluded"
    print(f"  [4] rho(fav_net_vel, velocity_ratio) = {rho:+.3f}  CI[{rlo:+.3f},{rhi:+.3f}]  n={n}  -> {verdict}")

    med = np.nanmedian(surv["fav_net_vel"].values)
    print(f"  [5] stratified F5 preview (split at fav_net_vel median {med:.3f}):")
    for name, half in (("LOW ", surv[surv.fav_net_vel <= med]), ("HIGH", surv[surv.fav_net_vel > med])):
        rr = half[half.grp == "reach"]["velocity_ratio"].dropna().values
        ss = half[half.grp == "stall"]["velocity_ratio"].dropna().values
        if len(rr) < N_MIN or len(ss) < N_MIN:
            print(f"      {name} half: reach={len(rr)} stall={len(ss)}  UNINFORMATIVE (n<{N_MIN})")
            continue
        c = two_sample_boot_ci(rr, ss, seed=seed)
        print(f"      {name} half: VR AUC={c['auc']:.3f} CI[{c['lo']:.3f},{c['hi']:.3f}] (nR={len(rr)} nS={len(ss)})")

    # all-trades line (B-design descriptive view)
    rA = g[g.grp == "reach"]["fav_net_vel"].dropna().values
    sA = g[g.grp == "stall"]["fav_net_vel"].dropna().values
    cA = two_sample_boot_ci(rA, sA, seed=seed)
    print(f"\n  [all-trades B-design] fav_net_vel AUC={cA['auc']:.3f} CI[{cA['lo']:.3f},{cA['hi']:.3f}] (nR={len(rA)} nS={len(sA)})")

    print("\nREAD: candidate iff [1] min>0.5 AND [2] p<0.05 on the decisive frame. [4] adjudicates the "
          "independence claim honestly (CI, not point estimate). [5] previews F5: VR separating within "
          "halves = combinable axes; VR dying within halves = overlap despite low rho. Registry: T-DF02.")


def selftest(config, wrb):
    print("=== SELF-TEST ===")
    rng = np.random.default_rng(1)
    r = rng.normal(1.0, 1.0, 45); s = rng.normal(0.0, 1.0, 24)          # separated groups
    lo, hi = jackknife(r, s)
    a = rank_auc(r, s)
    print(f"  jackknife around AUC={a:.3f}: min={lo:.3f} max={hi:.3f} (should bracket, stay >0.5)")
    assert lo > 0.5 and lo <= a <= hi
    obs, p = permutation_p(r, s, seed=0, B=2000)
    print(f"  permutation separated: p={p:.4f} (expect <0.01)"); assert p < 0.01
    same = rng.normal(0, 1, 45); same2 = rng.normal(0, 1, 24)
    _, p2 = permutation_p(same, same2, seed=0, B=2000)
    print(f"  permutation null: p={p2:.4f} (expect >0.05)"); assert p2 > 0.05
    x = rng.normal(0, 1, 69); y = x * 0.9 + rng.normal(0, 0.3, 69)
    rho, rlo, rhi, n = spearman_boot_ci(x, y, B=2000)
    print(f"  spearman corr pair: rho={rho:+.3f} CI[{rlo:+.3f},{rhi:+.3f}] (expect high, CI>0)")
    assert rho > 0.7 and rlo > 0.4
    z = rng.normal(0, 1, 69)
    rho2, rlo2, rhi2, _ = spearman_boot_ci(x, z, B=2000)
    print(f"  spearman indep pair: rho={rho2:+.3f} CI[{rlo2:+.3f},{rhi2:+.3f}] (expect CI straddles 0)")
    assert rlo2 < 0 < rhi2
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
