#!/usr/bin/env python3
"""
exit_reversal.py — EXIT-window exploration, probe C: adverse reversal into the exit (closes the menu)
======================================================================================================
B (velocity death) null, A (give-back) separated-by-construction/no-trigger, D (stagnation) null. C is
the last of the four trader's-eye exit hypotheses and the MOST construction-coupled: exit-DIRECTION is
near-definitional to bail-vs-take, so strong separation is EXPECTED and uninformative. Run for menu
completeness; the only part that could be a real finding is a TIGHT stall retrace band (a soft-stop rule).

HYPOTHESIS (pre-registered): stalls exit as price moves AGAINST the position (reacting to the turn);
reaches exit into favorable continuation / a profit-take.

FEATURES (per-second mid; oriented o = mid if long else -mid; need hold>=W):
  exit_adverse_move = (o[exit] - o[exit-W]) / tick     signed; negative = adverse.   stall < reach
  exit_retrace_ticks= (max o[exit-W,exit] - o[exit]) / tick   ticks given back from the window's local
                      favorable peak to the exit (>=0). The "soft-stop" magnitude.   stall > reach
PRE-REGISTERED: both reach-positive AUC < 0.5 = MATCHES.

OUTCOME: BINARY reach (47) vs stall (29), exit-anchored, hold>=W. W=30 PRIMARY, 60 robustness. Rank AUC
+ two-sample bootstrap CI (seed 0, 10000). TRIGGER read: stall exit_retrace_ticks tightness — a
consistent give-back-in-ticks at the bail = candidate soft-stop; wide = construction, no rule.

REUSES: build_arms (forward_battery); read_per_second, S, TICK (trade_flow_exhaustion);
rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 exit_reversal.py --config config.toml --wrb wrb_1m.parquet
      python3 exit_reversal.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci

TAUS = [30, 60]
N_MIN = 8
EXPECT_LOW = {"exit_adverse_move", "exit_retrace_ticks"}   # stall more adverse/retrace -> AUC(reach pos)<0.5


def feats(sec, mid, exit_, W, side):
    b = np.searchsorted(sec, np.int64(pd.Timestamp(exit_).value // 1_000_000_000), "right")
    a = np.searchsorted(sec, np.int64((pd.Timestamp(exit_) - S(W)).value // 1_000_000_000), "left")
    if b - a < 3:
        return dict(exit_adverse_move=np.nan, exit_retrace_ticks=np.nan)
    o = (mid[a:b] if side == "long" else -mid[a:b]) / TICK
    return dict(exit_adverse_move=float(o[-1] - o[0]),
                exit_retrace_ticks=float(np.max(o) - o[-1]))


def auc_line(name, r, s, seed):
    ci = two_sample_boot_ci(r, s, seed=seed)
    matches = ci["clears"] and (ci["auc"] < 0.5)   # all C features expect stall>reach -> AUC<0.5
    flag = ("** stall>reach (matches; expected by construction)" if matches else
            ("clears OPPOSITE hypothesis" if ci["clears"] else "  -"))
    print(f"  {name:18s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"Rmed={np.nanmedian(r):.2f} Smed={np.nanmedian(s):.2f} (nR={len(r)} nS={len(s)}) {flag}")


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(2); t_max = g.exit.max() + S(2)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for W in TAUS:
        sub = g[g.hold >= W].copy()
        F = pd.DataFrame([feats(sec, mid, r.exit, W, r.side) for _, r in sub.iterrows()], index=sub.index)
        for c in ("exit_adverse_move", "exit_retrace_ticks"):
            sub[c] = F[c].values
        rA = sub[sub.grp == "reach"]; sA = sub[sub.grp == "stall"]
        tag = "  <<< PRIMARY" if W == 30 else ""
        print(f"\n========== W={W}s  reach={len(rA)} stall={len(sA)} =========={tag}")
        if len(rA) < N_MIN or len(sA) < N_MIN:
            print("  UNINFORMATIVE (n<8)"); continue
        for c in ("exit_adverse_move", "exit_retrace_ticks"):
            auc_line(c, rA[c].dropna().values, sA[c].dropna().values, seed)
        s = sA["exit_retrace_ticks"].dropna().values
        iqr = np.quantile(s, .75) - np.quantile(s, .25)
        print(f"  TRIGGER(stall exit_retrace_ticks): q25={np.quantile(s,.25):.1f} med={np.quantile(s,.5):.1f} "
              f"q75={np.quantile(s,.75):.1f} tk  {'TIGHT band (possible soft-stop)' if iqr<3 else 'wide (construction, no rule)'}")
    print("\nREAD: a strong AUC is EXPECTED (exit-direction ~ definitional). The only real finding would be a "
          "TIGHT stall retrace band (consistent ticks given back at the bail = soft-stop). Wide band = the "
          "separation is construction, confirming the 4-hypothesis sweep: no mechanical exit trigger -> discretionary.")


def selftest(config, wrb):
    print("=== SELF-TEST: adverse_move + retrace ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 60)).astype(np.int64)
    # long: window [exit-30,exit]; rises +8 ticks then falls back +2 at exit -> adverse from peak, net +2
    mid = np.full(60, 5000.0)
    mid[30:45] = 5000 + np.linspace(0, 2.0, 15)    # up 8 ticks
    mid[45:60] = 5000 + np.linspace(2.0, 0.5, 15)  # back to +2 ticks
    exit_ = base + S(59)
    f = feats(sec, mid, exit_, 30, "long")
    print(f"  adverse_move={f['exit_adverse_move']:.1f} tk (net over window)  retrace={f['exit_retrace_ticks']:.1f} tk (peak8 -> end2 => 6)")
    assert abs(f["exit_retrace_ticks"] - 6.0) < 0.6
    # monotonic up to exit -> retrace ~0, adverse positive
    mid2 = np.full(60, 5000.0); mid2[30:60] = 5000 + np.linspace(0, 2.0, 30)
    f2 = feats(sec, mid2, exit_, 30, "long")
    print(f"  monotonic: adverse_move={f2['exit_adverse_move']:.1f} (>0)  retrace={f2['exit_retrace_ticks']:.1f} (~0)")
    assert f2["exit_adverse_move"] > 0 and f2["exit_retrace_ticks"] < 0.6
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
