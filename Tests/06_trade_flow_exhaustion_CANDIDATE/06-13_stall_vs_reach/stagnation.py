#!/usr/bin/env python3
"""
stagnation.py — EXIT-window exploration, probe D: stagnation / time-stop
=========================================================================
GOAL (reframe): reverse-engineer the stall-bail TRIGGER. B (velocity-death into exit) and A (give-back
from peak) both came back "separates partly by construction, NO stable trigger." D tests the time-stop
logic — "he gives up when the trade does nothing for long enough" (Raschke & Connors, Street Smarts 1995).

WHY D MATTERS MOST of the four: give-back (A) and adverse-reversal (C) are definitionally coupled to the
reach/stall label (a target-take is near a peak / favorable by definition). DEADWEIGHT TIME is not — a
trade can make-no-progress for a while whether or not it ultimately reaches. So D has the best chance of
a real trigger vs a construction artifact. NB: the TERMINAL flavor (time since the peak) was already NULL
as time_since_mfe in probe A; D tests the CUMULATIVE flavor instead.

FEATURES (per-second mid; favorable f(t) = (mid-entry_px)*sign/tick; threshold-free, scale-free):
  no_progress_frac      = fraction of trade-seconds that did NOT set a new favorable high
                          (new high at t := f(t) > max f(0..t-1)).  High = lots of deadweight time.
  late_no_progress_frac = same, over the BACK HALF [entry+hold/2, exit].  Did it die late, before the bail.
PRE-REGISTERED DIRECTION: stall > reach (more deadweight) => AUC(reach positive) < 0.5 = MATCHES.

OUTCOME: BINARY reach (47) vs stall (29), whole-trade. Rank AUC + two-sample bootstrap CI (seed 0, 10000);
clears iff CI excludes 0.5. TRIGGER read: stall-arm no_progress_frac tightness (consistent high band =
candidate "dead long enough -> exit" rule; wide = no stable trigger).

REUSES: build_arms (forward_battery); read_per_second, S, TICK (trade_flow_exhaustion);
rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 stagnation.py --config config.toml --wrb wrb_1m.parquet
      python3 stagnation.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci

N_MIN = 8
EXPECT_LOW = {"no_progress_frac", "late_no_progress_frac"}   # stall>reach -> AUC(reach pos)<0.5


def _no_progress_frac(fav):
    if len(fav) < 3:
        return np.nan
    prev_max = np.maximum.accumulate(np.concatenate([[fav[0] - 1], fav[:-1]]))  # running max excl current
    new_high = fav > prev_max
    return 1.0 - float(np.mean(new_high))


def feats(sec, mid, entry, exit_, entry_px, side):
    a = np.searchsorted(sec, np.int64(pd.Timestamp(entry).value // 1_000_000_000), "left")
    b = np.searchsorted(sec, np.int64(pd.Timestamp(exit_).value // 1_000_000_000), "right")
    if b - a < 4:
        return dict(no_progress_frac=np.nan, late_no_progress_frac=np.nan)
    f = (((mid[a:b] - entry_px) if side == "long" else (entry_px - mid[a:b])) / TICK)
    half = len(f) // 2
    return dict(no_progress_frac=_no_progress_frac(f),
                late_no_progress_frac=_no_progress_frac(f[half:]))


def auc_line(name, r, s, seed):
    ci = two_sample_boot_ci(r, s, seed=seed)
    want_low = name in EXPECT_LOW
    matches = ci["clears"] and ((ci["auc"] < 0.5) == want_low)
    flag = ("** stall>reach (matches)" if matches else
            ("clears OPPOSITE hypothesis" if ci["clears"] else "  -"))
    print(f"  {name:21s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"Rmed={np.nanmedian(r):.3f} Smed={np.nanmedian(s):.3f} (nR={len(r)} nS={len(s)}) {flag}")


def run(config, wrb_path, seed=0):
    import tomllib
    cfg = tomllib.load(open(config, "rb"))
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep.source_file + "::" + ep.episode_id.astype(str)
    px = dict(zip(ep.uid, ep.entry_prices.map(lambda a: float(np.asarray(a).ravel()[0]))))
    g["entry_px"] = g.uid.map(px)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(2); t_max = g.exit.max() + S(2)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    F = pd.DataFrame([feats(sec, mid, r.entry, r.exit, r.entry_px, r.side) for _, r in g.iterrows()],
                     index=g.index)
    for c in ("no_progress_frac", "late_no_progress_frac"):
        g[c] = F[c].values
    rA = g[g.grp == "reach"]; sA = g[g.grp == "stall"]
    nR = rA.no_progress_frac.notna().sum(); nS = sA.no_progress_frac.notna().sum()
    print(f"  valid: reach {nR} / stall {nS}")
    if nR < N_MIN or nS < N_MIN:
        print("  UNINFORMATIVE (n<8)"); return
    print("\n=== stagnation (pre-registered: stall > reach) ===")
    for c in ("no_progress_frac", "late_no_progress_frac"):
        auc_line(c, rA[c].dropna().values, sA[c].dropna().values, seed)
    s = sA["no_progress_frac"].dropna().values
    iqr = np.quantile(s, .75) - np.quantile(s, .25)
    print(f"\n  TRIGGER(stall no_progress_frac): q25={np.quantile(s,.25):.2f} med={np.quantile(s,.5):.2f} "
          f"q75={np.quantile(s,.75):.2f}  {'tight band' if iqr<0.20 else 'wide (no stable trigger)'}")
    print("\nREAD: stall>reach AND a tight high stall band = a consistent 'dead long enough -> exit' trigger "
          "(candidate time-stop rule). Clears but wide = differ, no rule. Null/opposite = not a stagnation "
          "event -> only C (adverse reversal) left, and 3 nulls would point hard at 'discretionary'.")


def selftest(config, wrb):
    print("=== SELF-TEST: no_progress_frac ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 100)).astype(np.int64)
    rising = 5000 + np.linspace(0, 5, 100)                       # always new highs -> ~0
    f = feats(sec, rising, base, base + S(99), 5000.0, "long")
    print(f"  monotonic rise: no_progress_frac={f['no_progress_frac']:.3f} (expect ~0)")
    assert f["no_progress_frac"] < 0.05
    pop_then_flat = np.concatenate([5000 + np.linspace(0, 2.5, 20), np.full(80, 5002.5)])  # 20 up, 80 flat
    f2 = feats(sec, pop_then_flat, base, base + S(99), 5000.0, "long")
    print(f"  pop then flat 80/100: no_progress_frac={f2['no_progress_frac']:.3f} (expect ~0.80)")
    assert 0.7 < f2["no_progress_frac"] < 0.9
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0  # reach-low matches stall>reach
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
