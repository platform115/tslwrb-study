#!/usr/bin/env python3
"""
give_back.py — EXIT-window exploration, probe A: give-back from the MFE peak (excursion management)
====================================================================================================
GOAL (reframe): reverse-engineer the stall-bail TRIGGER (he never documented one). Probe B showed the
bail is NOT a velocity-death event (exit_decel null). The most documented alternative for why a
discretionary trader cuts a WINNER is excursion management: "open profit gave back too much from its
peak" (Sweeney 1996, Maximum Adverse Excursion; Tomasini & Jaekle 2009).

HYPOTHESIS (pre-registered): before a stall-bail the trade has surrendered a larger FRACTION of its peak
favorable excursion, and exits longer after that peak, than before a target-exit. (Target exit = taken
near the favorable peak / into the move; stall = bailed after profit eroded.)

FEATURES (per-second mid; favorable f(t) = (mid(t)-entry_px)*sign / tick):
  give_back_frac  = (MFE - fav_at_exit) / MFE   over [entry, exit].  SCALE-FREE -> reaches' larger
                    absolute MFE cannot inflate it (the MFE-level circularity control). 0 = exit at peak;
                    ->1 = gave it all back.
  time_since_mfe  = seconds from the MFE peak to the exit.  How long he watched it erode.
PRE-REGISTERED DIRECTION: stall > reach for both (so AUC with reach as positive < 0.5 = MATCHES).

OUTCOME: BINARY reach (47) vs stall (29), whole-trade, MFE>0. Rank AUC + two-sample bootstrap CI
(seed 0, 10000); clears iff CI excludes 0.5. TRIGGER read: stall-arm give_back_frac tightness (a
consistent band = candidate "max give-back" exit rule; wide = no stable trigger even if it separates).

CAVEAT (logged): the exit is endogenous (his decision) so separation is partly behavioral-by-definition;
give_back_frac being a FRACTION controls the MFE-level circularity, but the real evidence is a tight,
reproducible stall band, not the AUC alone.

REUSES: build_arms (forward_battery); read_per_second, S, TICK (trade_flow_exhaustion);
rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 give_back.py --config config.toml --wrb wrb_1m.parquet
      python3 give_back.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci

N_MIN = 8
# expected direction: stall > reach -> AUC(reach positive) < 0.5
EXPECT_LOW = {"give_back_frac", "time_since_mfe"}


def feats(sec, mid, entry, exit_, entry_px, side):
    a = np.searchsorted(sec, np.int64(pd.Timestamp(entry).value // 1_000_000_000), "left")
    b = np.searchsorted(sec, np.int64(pd.Timestamp(exit_).value // 1_000_000_000), "right")
    if b - a < 3:
        return dict(give_back_frac=np.nan, time_since_mfe=np.nan)
    s = sec[a:b]; m = mid[a:b]
    fav = ((m - entry_px) if side == "long" else (entry_px - m)) / TICK
    k = int(np.argmax(fav)); mfe = fav[k]
    if mfe <= 0:
        return dict(give_back_frac=np.nan, time_since_mfe=np.nan)
    return dict(give_back_frac=(mfe - fav[-1]) / mfe, time_since_mfe=float(s[-1] - s[k]))


def auc_line(name, r, s, seed):
    ci = two_sample_boot_ci(r, s, seed=seed)
    want_low = name in EXPECT_LOW
    matches = ci["clears"] and ((ci["auc"] < 0.5) == want_low)
    flag = ("** stall>reach (matches)" if (matches and want_low) else
            "** reach>stall (matches)" if matches else
            ("clears OPPOSITE hypothesis" if ci["clears"] else "  -"))
    print(f"  {name:14s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
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
    for c in ("give_back_frac", "time_since_mfe"):
        g[c] = F[c].values
    rA = g[g.grp == "reach"]; sA = g[g.grp == "stall"]
    nR = rA.give_back_frac.notna().sum(); nS = sA.give_back_frac.notna().sum()
    print(f"  valid (MFE>0): reach {nR} / stall {nS}")
    if nR < N_MIN or nS < N_MIN:
        print("  UNINFORMATIVE (n<8)"); return
    print("\n=== give-back & timing (pre-registered: stall > reach) ===")
    for c in ("give_back_frac", "time_since_mfe"):
        auc_line(c, rA[c].dropna().values, sA[c].dropna().values, seed)
    s = sA["give_back_frac"].dropna().values
    iqr = np.quantile(s, .75) - np.quantile(s, .25)
    print(f"\n  TRIGGER(stall give_back_frac): q25={np.quantile(s,.25):.2f} med={np.quantile(s,.5):.2f} "
          f"q75={np.quantile(s,.75):.2f}  frac>0.33={np.mean(s>1/3):.2f}  "
          f"{'tight band' if iqr<0.30 else 'wide (no stable trigger)'}")
    print("\nREAD: stall>reach give_back AND a tight stall band = a consistent 'max give-back' exit trigger "
          "(candidate rule). Clears but wide = groups differ, no stable rule. Null/opposite = the bail is "
          "not a give-back event -> queue C (adverse reversal) / D (stagnation).")


def selftest(config, wrb):
    print("=== SELF-TEST: give_back_frac + time_since_mfe ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 100)).astype(np.int64)
    # long, entry 5000: rises to +10 ticks (mid 5002.5) by t=40, retraces to +6 (mid 5001.5) at exit t=80
    mid = np.full(100, 5000.0)
    mid[0:40] = 5000 + np.linspace(0, 2.5, 40)     # up to +10 ticks
    mid[40:80] = 5000 + np.linspace(2.5, 1.5, 40)  # back to +6 ticks
    f = feats(sec, mid, base, base + S(79), 5000.0, "long")
    print(f"  give_back_frac={f['give_back_frac']:.3f} (peak10 end6 -> 0.40)  time_since_mfe={f['time_since_mfe']:.0f}s")
    assert abs(f["give_back_frac"] - 0.4) < 0.05 and f["time_since_mfe"] > 30
    # exit at peak -> give_back 0
    mid2 = np.full(100, 5000.0); mid2[0:80] = 5000 + np.linspace(0, 2.5, 80)
    f2 = feats(sec, mid2, base, base + S(79), 5000.0, "long")
    print(f"  give_back_frac(exit at peak)={f2['give_back_frac']:.3f} (expect ~0)")
    assert f2["give_back_frac"] < 0.05
    assert rank_auc([3, 4, 5], [0, 1, 2]) == 1.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
