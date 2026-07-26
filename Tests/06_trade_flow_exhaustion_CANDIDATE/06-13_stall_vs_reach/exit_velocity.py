#!/usr/bin/env python3
"""
exit_velocity.py — EXIT-window exploration, probe B: price-path velocity death into the exit
=============================================================================================
GOAL (reframe): the exit is the trader's OWN decision and he never documented a rule for bailing a
stalling winner. So this is not prediction — it is reverse-engineering the TRIGGER: is there a
consistent, mechanical price-movement event in the seconds before a stall-bail that is absent before a
target-exit? velocity_ratio showed deceleration-vs-pre-entry-pace marks stallers at ENTRY; this asks the
same primitive at the EXIT, which we only ever tested with order-flow (null), never with price velocity.

HYPOTHESIS (pre-registered): price-path velocity DECELERATES into the exit more before a stall-bail than
before a target-exit (he cuts when the move dies; a target exit happens while price still moves / right
off the pt1 WRB). UNSIGNED path-length (a bail can be price moving against, also movement; "died" = low
path length either way). Direction tests handled separately in probe C.

FEATURES (per-second mid; pathlen = sum|delta mid| in ticks = distance travelled):
  exit_decel    = pathlen[exit-W, exit] / pathlen[exit-2W, exit-W]   (<1 = decelerating into exit;
                  self-normalising: both windows are late in the SAME trade => regime-controlled)
  exit_vel_norm = (pathlen[exit-W, exit]/W) / (pathlen[entry-60s, entry]/60)   (exit speed vs the trade's
                  own starting pace; cross-check against trade-level volatility, mirrors velocity_ratio)
PRE-REGISTERED DIRECTION: stall < reach (stalls decelerate / move less into the exit) => AUC(reach pos)>0.5.

OUTCOME: BINARY reach (47) vs stall (29), exit-anchored. exit_decel needs hold>=2W; exit_vel_norm needs
hold>=W. W=30 PRIMARY, 60 robustness. Two-sample bootstrap CI (seed 0, 10000); clears iff CI excludes 0.5.

TRIGGER READ (the point, beyond AUC): the stall-arm distribution of exit_decel — a tight band well below
1.0 = a consistent velocity-death trigger (candidate mechanical exit rule); a wide spread = no stable
trigger even if the AUC separates.

DATA: windowed parquet keeps pre_entry_min=60 and post_exit_min=5 -> full exit window present for BOTH
arms (verified via config). Coverage (valid-n per arm) is reported first.

REUSES: build_arms (forward_battery); read_per_second, S, TICK (trade_flow_exhaustion);
pathlen_tk (velocity_acceleration); rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 exit_velocity.py --config config.toml --wrb wrb_1m.parquet
      python3 exit_velocity.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, read_per_second
from forward_battery import build_arms
from velocity_acceleration import pathlen_tk
from range_expansion import rank_auc, two_sample_boot_ci

TAUS = [30, 60]
PRE_S = 60
N_MIN = 8


def feats(sec, mid, entry, exit_, W):
    final = pathlen_tk(sec, mid, exit_ - S(W), exit_)
    prev = pathlen_tk(sec, mid, exit_ - S(2 * W), exit_ - S(W))
    pre = pathlen_tk(sec, mid, entry - S(PRE_S), entry)
    decel = (final / prev) if (prev and prev > 0) else np.nan
    vel_norm = ((final / W) / (pre / PRE_S)) if (np.isfinite(final) and pre and pre > 0) else np.nan
    return dict(exit_decel=decel, exit_vel_norm=vel_norm)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(PRE_S) - S(2); t_max = g.exit.max() + S(2)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for W in TAUS:
        sub = g[g.hold >= 2 * W].copy()
        F = pd.DataFrame([feats(sec, mid, r.entry, r.exit, W) for _, r in sub.iterrows()], index=sub.index)
        for c in ("exit_decel", "exit_vel_norm"):
            sub[c] = F[c].values
        rA = sub[sub.grp == "reach"]; sA = sub[sub.grp == "stall"]
        tag = "  <<< PRIMARY" if W == 30 else ""
        print(f"\n========== W={W}s  (hold>=2W)  reach={len(rA)} stall={len(sA)} =========={tag}")
        if len(rA) < N_MIN or len(sA) < N_MIN:
            print("  UNINFORMATIVE (n<8)"); continue
        for c in ("exit_decel", "exit_vel_norm"):
            r = rA[c].dropna().values; s = sA[c].dropna().values
            ci = two_sample_boot_ci(r, s, seed=seed)
            flag = "** reach>stall (clears)" if (ci["clears"] and ci["auc"] > 0.5) else \
                   ("clears WRONG way" if ci["clears"] else "  -")
            print(f"  {c:14s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
                  f"Rmed={np.nanmedian(r):.3f} Smed={np.nanmedian(s):.3f} (nR={len(r)} nS={len(s)}) {flag}")
        # TRIGGER read: stall-arm exit_decel tightness
        s = sA["exit_decel"].dropna().values
        print(f"  TRIGGER(stall exit_decel): q25={np.quantile(s,.25):.2f} med={np.quantile(s,.5):.2f} "
              f"q75={np.quantile(s,.75):.2f}  frac<1.0={np.mean(s<1):.2f}  "
              f"{'tight band' if (np.quantile(s,.75)-np.quantile(s,.25))<0.6 else 'wide (no stable trigger)'}")
    print("\nREAD: clears reach>stall AND a TIGHT stall exit_decel band <1 = a consistent velocity-death "
          "trigger before stall-bails (candidate mechanical exit rule). Clears but WIDE stall band = the "
          "groups differ but there is no stable trigger. Null/wrong-way = the bail is not a velocity-death "
          "event -> queue A (give-back from peak) as the trigger instead.")


def selftest(config, wrb):
    print("=== SELF-TEST: exit-window decel + vel_norm ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 200)).astype(np.int64)
    # trade: entry at idx60, exit at idx180. preceding exit-window [120,150] fast; final [150,180] slow => decel<1
    mid = 5000 + np.zeros(200)
    mid[120:150] = 5000 + (np.arange(30) % 2) * 2.0     # fast zigzag (preceding window)
    mid[150:180] = 5000 + np.linspace(0, 0.5, 30)        # slow drift (final window) -> decel<1
    entry = base + S(60); exit_ = base + S(180)
    f = feats(sec, mid, entry, exit_, 30)
    print(f"  exit_decel={f['exit_decel']:.3f} (fast->slow into exit, expect <1)")
    assert f["exit_decel"] < 1
    # reverse: slow preceding, fast final -> decel>1
    mid2 = 5000 + np.zeros(200)
    mid2[120:150] = 5000 + np.linspace(0, 0.5, 30)
    mid2[150:180] = 5000 + (np.arange(30) % 2) * 2.0
    f2 = feats(sec, mid2, entry, exit_, 30)
    print(f"  exit_decel(reversed)={f2['exit_decel']:.3f} (slow->fast, expect >1)")
    assert f2["exit_decel"] > 1
    assert rank_auc([3, 4, 5], [0, 1, 2]) == 1.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
