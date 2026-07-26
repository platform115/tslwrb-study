#!/usr/bin/env python3
"""
velocity_acceleration.py — PRICE-MOVEMENT vein, probe #2: per-second velocity & acceleration
==============================================================================================
WHY: the trader cites SPEED/MOVEMENT of price action. range_expansion (probe #1) leaned reach>stall
but did NOT clear (0.59, CI through 0.5). This is the pre-committed FAIR test of the vein at finer
grain: the RATE price moves second-to-second (path length / time), not the size of its range. A choppy
stall and a trending reach can share a range but differ in velocity, so this is genuinely different
from probe #1.

HYPOTHESIS (pre-registered): reachers show higher early per-second VELOCITY and ACCELERATION than
stallers. (Lo & MacKinlay 1988 variance ratio; realized-activity/path-length; Crabel 1990.)

FEATURES (UNSIGNED on purpose — see note; regime-normalised so not just "volatile day"):
  velocity_ratio = pathlen[entry, entry+tau] / pathlen[entry-tau, entry]
  acceleration   = pathlen[2nd half of early window] / pathlen[1st half]
  where pathlen = sum |delta mid| over per-second mids, in ticks (total variation = distance travelled).

WHY UNSIGNED: directional (net favorable) velocity would be CIRCULAR with the binary reach label —
pt1 sits at/inside the early window for ~half of reaches (pt1_open_el median 49s), so "net favorable
ticks/sec" partly measures "already reached pt1." That is exactly the look-ahead that turned the
earlier flow_level/ER speed lead into an artifact. Unsigned path length (a stall can be fast & choppy
too) is the non-circular test of "is price MOVING fast," which is the trader's stated perception.

OUTCOME: BINARY reach (47) vs stall (29), entry-forward SURVIVORS-only (hold>=tau). tau=60 PRIMARY,
30 robustness. DIRECTION: reach>stall => AUC>0.5; clears iff two-sample bootstrap CI (seed 0, 10000)
excludes 0.5. Two-sided.

PRE-COMMITTED STOP: if velocity/acceleration only LEAN sub-threshold like range did, the movement vein
is called — weakly present, not a usable separator at this n — and we stop (no finer-grain chasing).

REUSES: build_arms (forward_battery); read_per_second, S, TICK (trade_flow_exhaustion);
rank_auc, two_sample_boot_ci (range_expansion).

RUN:  python3 velocity_acceleration.py --config config.toml --wrb wrb_1m.parquet
      python3 velocity_acceleration.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci

TAUS = [60, 30]
N_MIN = 8


def pathlen_tk(sec, mid, t0, t1):
    a = np.searchsorted(sec, np.int64(pd.Timestamp(t0).value // 1_000_000_000), "left")
    b = np.searchsorted(sec, np.int64(pd.Timestamp(t1).value // 1_000_000_000), "left")
    if b - a < 2:
        return np.nan
    return np.abs(np.diff(mid[a:b])).sum() / TICK


def features(sec, mid, entry, tau):
    pe = pathlen_tk(sec, mid, entry, entry + S(tau))
    pr = pathlen_tk(sec, mid, entry - S(tau), entry)
    h1 = pathlen_tk(sec, mid, entry, entry + S(tau // 2))
    h2 = pathlen_tk(sec, mid, entry + S(tau // 2), entry + S(tau))
    return dict(velocity_ratio=(pe / pr) if (pr and pr > 0) else np.nan,
                acceleration=(h2 / h1) if (h1 and h1 > 0) else np.nan)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(max(TAUS)) - S(2); t_max = (g.entry + S(max(TAUS))).max()
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for tau in TAUS:
        sub = g[g.hold >= tau].copy()
        F = pd.DataFrame([features(sec, mid, r.entry, tau) for _, r in sub.iterrows()], index=sub.index)
        for c in ("velocity_ratio", "acceleration"):
            sub[c] = F[c].values
        rA = sub[sub.grp == "reach"]; sA = sub[sub.grp == "stall"]
        tag = "  <<< PRIMARY" if tau == 60 else ""
        print(f"\n========== tau={tau}s  survivors reach={len(rA)} stall={len(sA)} =========={tag}")
        if len(rA) < N_MIN or len(sA) < N_MIN:
            print("  UNINFORMATIVE (n<8)"); continue
        for c in ("velocity_ratio", "acceleration"):
            ci = two_sample_boot_ci(rA[c].values, sA[c].values, seed=seed)
            flag = "** reach>stall (clears)" if (ci["clears"] and ci["auc"] > 0.5) else \
                   ("clears WRONG way" if ci["clears"] else "  -")
            print(f"  {c:15s} AUC={ci['auc']:.3f}  CI[{ci['lo']:.3f},{ci['hi']:.3f}]  "
                  f"Rmed={np.nanmedian(rA[c]):+.3f} Smed={np.nanmedian(sA[c]):+.3f}  {flag}")
    print("\nREAD: clears (reach>stall) = price MOVES faster / accelerates into reachers — the trader's "
          "model, finally mechanised. Sub-threshold lean like range => per the pre-commit, the movement "
          "vein is weakly-present-but-not-usable at this n; stop. Wrong-way/null => movement not in the tape.")


def selftest(config, wrb):
    print("=== SELF-TEST: pathlen + features + auc ===")
    assert rank_auc([3, 4, 5], [0, 1, 2]) == 1.0 and rank_auc([1, 2, 3], [1, 2, 3]) == 0.5
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 120)).astype(np.int64)
    # pre 0-30s: flat (pathlen ~0.. use tiny ramp 1 tick total); early 30-60s: zigzag (high pathlen)
    pre = 5000 + np.zeros(30); pre[::2] += 0.25                      # tiny chop, ~ small pathlen
    early = 5000 + (np.arange(30) % 2) * 2.0                          # 0,2,0,2... zigzag = big pathlen
    mid = np.concatenate([pre, early, 5000 + np.zeros(60)])
    entry = base + S(30)
    pe = pathlen_tk(sec, mid, entry, entry + S(30)); pr = pathlen_tk(sec, mid, entry - S(30), entry)
    print(f"  pre pathlen={pr:.1f}tk  early pathlen={pe:.1f}tk  velocity_ratio={pe/pr:.2f} (early>>pre expected)")
    assert pe > pr
    f = features(sec, mid, entry, 30)
    print(f"  features: velocity_ratio={f['velocity_ratio']:.2f}  acceleration={f['acceleration']:.2f}")
    assert np.isfinite(f["velocity_ratio"]) and np.isfinite(f["acceleration"])
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
