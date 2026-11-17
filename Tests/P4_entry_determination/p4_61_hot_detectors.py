#!/usr/bin/env python3
"""
p4_61_hot_detectors.py — P4.61 / Strategy 2: the hot-moment detector battery.
==============================================================================
Eight second-scale definitions of "something is happening", each calibrated to
the SAME firing budget (its own 99th percentile over RTH seconds, then fires
clustered to one per 120 s), measured against ALL his training-month entries:
  D1 move10    |mid move, last 10 s|
  D2 move30    |mid move, last 30 s|
  D3 intensity total volume, last 10 s
  D4 runlen    consecutive seconds of one-sided signed flow (length)
  D5 bigprint  largest single-second |signed volume| in last 10 s
  D6 accel     move last 10 s minus move in the 20 s before it (burst growing)
  D7 rngexp    60 s range vs its trailing 10-min median
  D8 persist   seconds with any volume in last 10 s (continuous printing)
CAUGHT = fire within 120 s of his entry (direction must match for directional
detectors D1/D2/D4/D6; D3/D5/D7/D8 are direction-less, time-only - marked).
Also: UNIQUE = his entries caught that D1 misses (what each adds).
And the direction question: among his entries with a D1 burst nearby, how often
does the burst's direction equal his side (vs the old 5-min rule's 70.2%)?
Training months only.

RUN: python3 Tests/P4_entry_determination/p4_61_hot_detectors.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_49_sec_engine import Ctx                       # noqa: E402

TICK = 0.25
Q = 99.0
CLUST = 120


def detectors(secs, mids, bv, svv):
    sv = bv - svv
    tv = bv + svv
    csv_ = np.concatenate([[0.0], np.cumsum(sv)])
    ctv = np.concatenate([[0.0], np.cumsum(tv)])
    i10 = np.searchsorted(secs, secs - 10)
    i30 = np.searchsorted(secs, secs - 30)
    idx = np.arange(1, len(secs) + 1)
    mv10 = (mids - mids[np.maximum(i10, 0)]) / TICK
    mv30 = (mids - mids[np.maximum(i30, 0)]) / TICK
    inten = ctv[idx] - ctv[i10]
    # run length of one-sided signed flow
    run = np.zeros(len(secs))
    cur = 0; last_sign = 0
    for i in range(len(secs)):
        s = np.sign(sv[i])
        if s != 0 and s == last_sign:
            cur += 1
        elif s != 0:
            cur = 1; last_sign = s
        run[i] = cur * (last_sign if last_sign else 0)
    bigp = pd.Series(np.abs(sv)).rolling(10, min_periods=1).max().to_numpy()
    prev20 = (mids[np.maximum(i10, 0)] - mids[np.maximum(i30, 0)]) / TICK
    accel = np.abs(mv10) - np.abs(prev20)
    r60 = pd.Series(mids).rolling(60, min_periods=10).apply(lambda x: (x.max() - x.min()) / TICK, raw=False)
    # rolling median via coarse stride for speed
    r60 = r60.to_numpy()
    med600 = pd.Series(r60).rolling(600, min_periods=120).median().to_numpy()
    rngexp = r60 / np.where(med600 > 0, med600, np.nan)
    persist = pd.Series((tv > 0).astype(float)).rolling(10, min_periods=1).sum().to_numpy()
    return {
        "D1 move10": (np.abs(mv10), np.sign(mv10)),
        "D2 move30": (np.abs(mv30), np.sign(mv30)),
        "D3 intensity": (inten, None),
        "D4 runlen": (np.abs(run), np.sign(run)),
        "D5 bigprint": (bigp, None),
        "D6 accel": (accel, np.sign(mv10)),
        "D7 rngexp": (rngexp, None),
        "D8 persist": (persist, None),
    }


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    names = None
    caught = {}; fires = {}; days = 0; his_n = 0
    d1_caught_sets = []
    caught_sets = {}
    dir_match = [0, 0]
    for month, sym in MONTHS:
        cx = Ctx(repo, month, True)
        lo, hi = month_bounds(month)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64); mids = f.mid.to_numpy(float)
        bv = f.buyv.to_numpy(float); svv = f.sellv.to_numpy(float)
        rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
        keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        days += len(np.unique(secs[keep] // 86400))
        D = detectors(secs, mids, bv, svv)
        names = list(D)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])
        his_n += len(hs)
        for nm, (stat, sgn) in D.items():
            st = np.where(np.isfinite(stat), stat, -np.inf)
            thr = np.percentile(st[keep & np.isfinite(stat)], Q)
            fire = keep & (st >= thr)
            fs, fd = [], []
            last = -10**18
            for i in np.flatnonzero(fire):
                if secs[i] - last > CLUST:
                    fs.append(secs[i]); fd.append(sgn[i] if sgn is not None else 0)
                    last = secs[i]
            fs = np.array(fs, dtype=np.int64); fd = np.array(fd)
            fires[nm] = fires.get(nm, 0) + len(fs)
            cs = set()
            for j, (s0, d0) in enumerate(zip(hs, hd)):
                m = np.abs(fs - s0) <= CLUST
                if sgn is not None:
                    m &= (fd == d0)
                if m.any():
                    cs.add((month, int(s0)))
            caught[nm] = caught.get(nm, 0) + len(cs)
            caught_sets.setdefault(nm, set()).update(cs)
            if nm == "D1 move10":
                # direction head-to-head: nearest D1 fire within 120s, any direction
                for s0, d0 in zip(hs, hd):
                    m = np.abs(fs - s0) <= CLUST
                    if m.any():
                        j = int(np.flatnonzero(m)[np.argmin(np.abs(fs[m] - s0))])
                        dir_match[1] += 1
                        dir_match[0] += int(fd[j] == d0)
    d1 = caught_sets["D1 move10"]
    print(f"ALL his entries, training months: n={his_n} | {days} RTH days | each detector")
    print(f"at its own {Q:.0f}th-percentile threshold, fires clustered to one per {CLUST}s.\n")
    print("| Detector | Directional? | Fires/day | His caught | Catch rate | Adds over D1 |")
    print("|---|---|---|---|---|---|")
    dirn = {"D1 move10": "yes", "D2 move30": "yes", "D3 intensity": "no (time-only match)",
            "D4 runlen": "yes", "D5 bigprint": "no (time-only match)",
            "D6 accel": "yes", "D7 rngexp": "no (time-only match)", "D8 persist": "no (time-only match)"}
    for nm in names:
        uniq = len(caught_sets[nm] - d1)
        print(f"| {nm} | {dirn[nm]} | {fires[nm]/days:.0f} | {caught[nm]}/{his_n} "
              f"| {caught[nm]/his_n:.0%} | +{uniq} |")
    allsets = set().union(*caught_sets.values())
    udir = set().union(*(caught_sets[k] for k in ("D1 move10", "D2 move30", "D4 runlen", "D6 accel")))
    uno8 = set().union(*(v for k, v in caught_sets.items() if k != "D8 persist"))
    print(f"| UNION directional (D1,D2,D4,D6) | yes | - | {len(udir)}/{his_n} | {len(udir)/his_n:.0%} | - |")
    print(f"| UNION all but D8 | - | - | {len(uno8)}/{his_n} | {len(uno8)/his_n:.0%} | - |")
    print(f"| UNION all 8 | - | - | {len(allsets)}/{his_n} | {len(allsets)/his_n:.0%} | - |")
    print(f"\nDIRECTION: nearest D1 burst's direction == his side: "
          f"{dir_match[0]}/{dir_match[1]} = {dir_match[0]/max(dir_match[1],1):.1%}"
          f"  (old 5-min momentum rule: 70.2%)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
