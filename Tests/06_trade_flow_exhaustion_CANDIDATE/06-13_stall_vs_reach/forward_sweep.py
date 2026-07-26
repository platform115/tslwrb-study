#!/usr/bin/env python3
"""
forward_sweep.py  — Design (c) over LONGER windows: W = 1/2/3/5 min, entry-anchored
====================================================================================
WHY: forward_battery ran tau=30s (zero truncation, but maybe too short to see a stall develop;
median stall hold is 115s). This sweeps W = 60/120/180/300s. Window = [entry, min(entry+W, exit)].

THE ARTIFACT THIS GUARDS AGAINST: capping at exit means a short stall's window = its WHOLE life
(it ends BECAUSE it stalled), while a reach's window is only its early portion. So window length
differs by arm and, worse, a capped stall window encodes the outcome. A separator at long W could
be "watching the stall die," not "predicting early." TWO GUARDS:
  1. LENGTH-INVARIANT features only (rates/means/slopes/ER/Hurst — totals like abs_move are flagged).
  2. SURVIVORS-ONLY control: at each W, also score ONLY trades with hold>=W, both arms reading the
     full [entry, entry+W] (NO capping, NO leakage). Real signal shows in survivors too; an artifact
     shows ONLY in capped. Survivor power (from data): stall n = 24/13/5/2 at W=60/120/180/300, so
     the control is INFORMATIVE at 60s & 120s, UNINFORMATIVE (stall<8) at 180s & 300s -> at 3-5min
     only capped exists and is artifact-prone; read accordingly.

POOLED 47 vs 29, two-sample bootstrap (seed 0). Two-sided. Discovery = report; Feb = validate.
This is USER-DIRECTED window exploration (not the assistant tau-fishing): the full sweep is
reported, capped and survivors side by side, winners and nulls alike.

REUSES (unchanged, already unit-tested): read_trade_full, window_features, two_sample_boot_ci,
  build_arms (forward_battery); S (trade_flow_exhaustion).

RUN:  python3 forward_sweep.py --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S
from forward_battery import read_trade_full, window_features, two_sample_boot_ci, build_arms

WINDOWS = [60, 120, 180, 300]
FEATS = ["flow_level", "intensity_level", "intensity_slope", "ER_abs", "hurst", "rho1", "abs_move_tk"]
LEN_SENSITIVE = {"abs_move_tk"}          # grows with window; read with care across W
SURV_FLOOR = 8                            # min stall survivors for the clean control to count


def collect(df, ts_ns, rs, sz, mid, W, survivors_only):
    rows = []
    for _, r in df.iterrows():
        if survivors_only:
            if r.hold < W:
                continue
            we = r.entry + S(W)
        else:
            we = min(r.entry + S(W), r.exit)
        f = window_features(ts_ns, rs, sz, mid, r.side, r.entry, we)
        if f is None or f["flagged"]:
            continue
        f["span"] = (pd.Timestamp(we).value - pd.Timestamp(r.entry).value) / 1e9
        rows.append(f)
    return pd.DataFrame(rows)


def line(f, R, Sd, seed):
    ci = two_sample_boot_ci(R[f], Sd[f], seed=seed)
    if not np.isfinite(ci["auc"]):
        return f"     {f:16s} (insufficient)"
    mark = "**" if ci["excludes_half"] else "  "
    tag = " [len-sensitive]" if f in LEN_SENSITIVE else ""
    return (f"  {mark} {f:16s} AUC={ci['auc']:.3f}  CI[{ci['lo']:.3f},{ci['hi']:.3f}]"
            f"  Rmed={R[f].median():+.3f} Smed={Sd[f].median():+.3f}{tag}")


def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    # session_phase (W-invariant entry attribute) — report once
    def sp(df):
        return df.entry.map(lambda t: pd.Timestamp(t).tz_convert("America/New_York")
                            ).map(lambda t: t.hour * 60 + t.minute - 570).to_numpy(float)
    ci = two_sample_boot_ci(sp(reach), sp(stall), seed=seed)
    print(f"[arms] stall={len(stall)} reach={len(reach)}")
    print(f"[context] session_phase (entry, W-invariant): AUC={ci['auc']:.3f} "
          f"CI[{ci['lo']:.3f},{ci['hi']:.3f}]  ({'SEPARATES' if ci['excludes_half'] else 'incl 0.5'})")

    t_min = min(stall.entry.min(), reach.entry.min()) - S(2)
    t_max = max((stall.entry + S(max(WINDOWS))).max(), (reach.entry + S(max(WINDOWS))).max())
    print(f"[read] {windowed}")
    ts_ns, rs, sz, mid = read_trade_full(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")

    for W in WINDOWS:
        print(f"\n================  W = {W}s ({W/60:.0f} min)  ================")
        Rc = collect(reach, ts_ns, rs, sz, mid, W, False)
        Sc = collect(stall, ts_ns, rs, sz, mid, W, False)
        print(f"  -- CAPPED pooled (all trades; stall span med {Sc.span.median():.0f}s vs "
              f"reach {Rc.span.median():.0f}s) reach n={len(Rc)} stall n={len(Sc)} --")
        for f in FEATS:
            print(line(f, Rc, Sc, seed))

        Rs = collect(reach, ts_ns, rs, sz, mid, W, True)
        Ss = collect(stall, ts_ns, rs, sz, mid, W, True)
        if len(Ss) >= SURV_FLOOR:
            print(f"  -- SURVIVORS-only control (full {W}s both arms, NO cap) reach n={len(Rs)} "
                  f"stall n={len(Ss)} --")
            for f in FEATS:
                if f in LEN_SENSITIVE:
                    continue
                print(line(f, Rs, Ss, seed))
        else:
            print(f"  -- SURVIVORS-only: stall n={len(Ss)} < {SURV_FLOOR} -> UNINFORMATIVE; "
                  f"capped read above is artifact-prone (stalls heavily whole-life-capped) --")
    print("\nREAD: a feature is a real early signal only if it separates in BOTH capped AND "
          "survivors-only (W=60/120 have the control). Capped-only separation at W>=180 is "
          "likely the whole-life-capping artifact, not prediction.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    run(a.config, a.wrb, seed=a.seed)
