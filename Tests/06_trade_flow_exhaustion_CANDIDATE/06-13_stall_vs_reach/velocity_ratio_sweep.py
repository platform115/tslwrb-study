#!/usr/bin/env python3
"""
velocity_ratio_sweep.py — does the confirmed deceleration signal STRENGTHEN with the forward window?
=====================================================================================================
velocity_ratio cleared + confirmed at tau=60 (AUC 0.660; jackknife min 0.645; perm p=0.014). The
effect grew 0.63->0.66 from tau=30->60, and the mechanism (post-entry DECELERATION takes time to show)
predicts it should keep growing with a longer FORWARD window. This sweeps it.

KEY DESIGN FIX: the PRE-entry normalization window (60s) is capped by the data, but the FORWARD window
is NOT — they are independent. So we keep the fixed-60s pre-entry normalization (the volatility control
that made the feature clean) and sweep ONLY the forward window. No rebuild, no dropped control.

FEATURE (rate-ratio; identical to the confirmed velocity_ratio at tau=60):
  norm_ratio(tau) = (pathlen[entry, entry+tau] / tau) / (pathlen[entry-60, entry] / 60)
                  = forward per-second speed / pre-entry per-second speed.  <1 => decelerated.
CONTEXT (un-normalised, to EXPOSE the volatility confound):
  raw_fwd(tau)    = pathlen[entry, entry+tau] / tau   (ticks/sec).  If raw and norm disagree on
                    separation, the pre-entry normalization is doing real work (volatility control).
  pathlen = sum |delta mid| over per-second mids, in ticks (unsigned -> not pt1-circular).

HYPOTHESIS (pre-registered): reach>stall on norm_ratio at every tau, AUC GROWING 60->90->120 if the
deceleration mechanism is real. Peaks-and-fades => a ~60s entry phenomenon. Clears iff two-sample
bootstrap CI (seed 0, 10000) excludes 0.5.

OUTCOME: BINARY reach (47) vs stall (29), SURVIVORS-only (hold>=tau). n shrinks with tau (stall ~24->~13).

REUSES: build_arms (forward_battery); read_per_second, S (trade_flow_exhaustion);
pathlen_tk (velocity_acceleration); rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 velocity_ratio_sweep.py --config config.toml --wrb wrb_1m.parquet
      python3 velocity_ratio_sweep.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, read_per_second
from forward_battery import build_arms
from velocity_acceleration import pathlen_tk
from range_expansion import rank_auc, two_sample_boot_ci

TAUS = [60, 90, 120]
PRE_S = 60
N_MIN = 8


def feats(sec, mid, entry, tau):
    pre = pathlen_tk(sec, mid, entry - S(PRE_S), entry)
    fwd = pathlen_tk(sec, mid, entry, entry + S(tau))
    pre_rate = pre / PRE_S if (pre and pre > 0) else np.nan
    fwd_rate = fwd / tau if (fwd is not None and np.isfinite(fwd)) else np.nan
    norm = (fwd_rate / pre_rate) if (np.isfinite(fwd_rate) and np.isfinite(pre_rate) and pre_rate > 0) else np.nan
    return dict(norm_ratio=norm, raw_fwd=fwd_rate)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(PRE_S) - S(2); t_max = (g.entry + S(max(TAUS))).max()
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    print("\n  tau | survivors |   norm_ratio (vol-controlled, PRIMARY)    |   raw_fwd (vol-confounded, context)")
    print("  ----+-----------+-------------------------------------------+------------------------------------")
    for tau in TAUS:
        sub = g[g.hold >= tau].copy()
        F = pd.DataFrame([feats(sec, mid, r.entry, tau) for _, r in sub.iterrows()], index=sub.index)
        for c in ("norm_ratio", "raw_fwd"):
            sub[c] = F[c].values
        rA = sub[sub.grp == "reach"]; sA = sub[sub.grp == "stall"]
        nR = rA.norm_ratio.dropna().values; nS = sA.norm_ratio.dropna().values
        if len(nR) < N_MIN or len(nS) < N_MIN:
            print(f"  {tau:>3} | r{len(nR)}/s{len(nS):<3}   UNINFORMATIVE (n<8)"); continue
        cn = two_sample_boot_ci(nR, nS, seed=seed)
        cr = two_sample_boot_ci(rA.raw_fwd.dropna().values, sA.raw_fwd.dropna().values, seed=seed)
        fn = "CLEARS" if (cn["clears"] and cn["auc"] > 0.5) else ("WRONG" if cn["clears"] else "-")
        fr = "clears" if cr["clears"] else "-"
        print(f"  {tau:>3} | r{len(nR)}/s{len(nS):<4} | "
              f"AUC={cn['auc']:.3f} CI[{cn['lo']:.3f},{cn['hi']:.3f}] Rm{np.nanmedian(nR):.2f}/Sm{np.nanmedian(nS):.2f} {fn:6} | "
              f"AUC={cr['auc']:.3f} CI[{cr['lo']:.3f},{cr['hi']:.3f}] {fr}")
    print("\nREAD:")
    print("  norm_ratio AUC GROWS 60->90->120  => deceleration strengthens with window; velocity becomes")
    print("    genuinely usable at the longer window. The study's one finding, upgraded.")
    print("  norm_ratio PEAKS at 60 then fades => a ~60s entry phenomenon; bank it at 60, done.")
    print("  raw_fwd disagrees with norm_ratio  => volatility confound is real; trust the normalized column.")
    print("  raw_fwd ~matches norm_ratio        => volatility is not driving it; both tell the same story.")


def selftest(config, wrb):
    print("=== SELF-TEST: rate-ratio + auc ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 240)).astype(np.int64)
    # pre 60s (idx 0..59): fast zigzag (high pathlen); forward 60..180: slow (low pathlen) => norm<1
    pre = 5000 + (np.arange(60) % 2) * 2.0                # zigzag amp 2 -> big pathlen
    fwd = 5000 + np.linspace(0, 1.0, 180)                 # slow drift -> small pathlen
    mid = np.concatenate([pre, fwd])
    entry = base + S(60)
    f60 = feats(sec, mid, entry, 60); f120 = feats(sec, mid, entry, 120)
    print(f"  norm_ratio tau60={f60['norm_ratio']:.3f}  tau120={f120['norm_ratio']:.3f} (decel => <1)")
    assert f60["norm_ratio"] < 1 and f120["norm_ratio"] < 1
    print(f"  raw_fwd tau60={f60['raw_fwd']:.4f} ticks/s (small, slow forward)")
    assert rank_auc([2, 3, 4], [0, 1, 1.5]) == 1.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
