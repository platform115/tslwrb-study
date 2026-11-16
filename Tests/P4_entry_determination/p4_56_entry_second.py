#!/usr/bin/env python3
"""
p4_56_entry_second.py — P4.56: his GROUP A entry SECONDS under the microscope.
===============================================================================
A) THE SCATTER, SOLVED MECHANICALLY: for each Group A entry within 8 ticks of a
   discriminating-set level, did the per-second price touch that level (within
   1 tick) in the 10 min BEFORE his entry, within 5 min AFTER, or never?
   before -> he reacts late; a resting limit at the level fills at-or-better.
   after  -> the limit fills better, moments later.
   never  -> the level is a reference, not an order price - limits would miss him.
B) THE TRIGGER SECOND: within each entry's final 5 minutes, how extreme is the
   tape at his entry second vs the earlier seconds of the same window?
   Features (trailing, per second, signed toward his trade direction):
   mid move last 10s / 30s (ticks), signed volume last 10s / 30s, 60s range.
   Reported as the percentile of his entry second inside its own window -
   median ~50% = he fires at random moments; high = he fires on the burst.
Universe: his GROUP A entries (141), all four run months, per-second data.

RUN: python3 Tests/P4_entry_determination/p4_56_entry_second.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_49_sec_engine import Ctx, ALL_MONTHS           # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_53_anchor_sweep import month_anchors           # noqa: E402

TICK = 0.25
DISC = ["his-exit", "his-entry", "firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]
LIFE_NS = 60 * int(60e9)
NEAR_TK, TOUCH_TK = 8, 1


def nearest_level(W, ts, px):
    best = (np.inf, None)
    for k in DISC:
        for t0, p0 in W[k]:
            if t0 <= ts <= t0 + LIFE_NS:
                d = abs(px - p0) / TICK
                if d < best[0]:
                    best = (d, p0)
    return best


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    touch = dict(before=0, after=0, never=0)
    lead = []
    pct = {f: [] for f in ("mid move 10s", "mid move 30s", "signed vol 10s",
                           "signed vol 30s", "range 60s")}
    n_lvl = n_all = 0
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64)
        mids = f.mid.to_numpy(float)
        sv = (f.buyv - f.sellv).to_numpy(float)
        csv_ = np.concatenate([[0.0], np.cumsum(sv)])

        def mid_at(s):
            i = np.searchsorted(secs, s, "right") - 1
            return mids[i] if i >= 0 else np.nan

        def vol_between(s0, s1):
            a, b = np.searchsorted(secs, s0), np.searchsorted(secs, s1, "right")
            return csv_[b] - csv_[a]

        def feats(s, sgn):
            m0 = mid_at(s)
            out = {"mid move 10s": sgn * (m0 - mid_at(s - 10)) / TICK,
                   "mid move 30s": sgn * (m0 - mid_at(s - 30)) / TICK,
                   "signed vol 10s": sgn * vol_between(s - 10, s),
                   "signed vol 30s": sgn * vol_between(s - 30, s)}
            a, b = np.searchsorted(secs, s - 60), np.searchsorted(secs, s, "right")
            out["range 60s"] = (mids[a:b].max() - mids[a:b].min()) / TICK if b > a else np.nan
            return out

        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        for _, t in e_m[g == "A"].iterrows():
            ts = pd.Timestamp(t.first_entry_utc).value
            s0 = ts // 1_000_000_000
            px = float(np.asarray(t.entry_prices).ravel()[0])
            sgn = 1 if t.side == "long" else -1
            n_all += 1
            # A) limit feasibility at the intended level
            d, L = nearest_level(W, ts, px)
            if L is not None and d <= NEAR_TK:
                n_lvl += 1
                a, b = np.searchsorted(secs, s0 - 600), np.searchsorted(secs, s0)
                m = np.abs(mids[a:b] - L) / TICK <= TOUCH_TK
                if m.any():
                    touch["before"] += 1
                    lead.append(s0 - secs[a:b][np.flatnonzero(m)[-1]])
                else:
                    a2, b2 = np.searchsorted(secs, s0), np.searchsorted(secs, s0 + 300)
                    if (np.abs(mids[a2:b2] - L) / TICK <= TOUCH_TK).any():
                        touch["after"] += 1
                    else:
                        touch["never"] += 1
            # B) percentile of the entry second inside its own window
            f0 = feats(s0, sgn)
            comp_secs = secs[(secs >= s0 - 300) & (secs <= s0 - 30)]
            if len(comp_secs) >= 60:
                comp = {k: [] for k in f0}
                for s in comp_secs[::3]:            # every 3rd second is enough
                    fc = feats(int(s), sgn)
                    for k in f0:
                        comp[k].append(fc[k])
                for k in f0:
                    arr = np.asarray(comp[k], float)
                    arr = arr[np.isfinite(arr)]
                    if len(arr) and np.isfinite(f0[k]):
                        pct[k].append((arr < f0[k]).mean())

    print(f"A) THE SCATTER - his {n_lvl} near-level Group A entries (of {n_all}):")
    print("   did the price touch the intended level (within 1 tick)...\n")
    print("| When | Entries | Share | Meaning |")
    print("|---|---|---|---|")
    tot = max(sum(touch.values()), 1)
    print(f"| in the 10 min BEFORE his entry | {touch['before']} | {touch['before']/tot:.0%} "
          f"| he is late - a resting limit fills at-or-better |")
    print(f"| only in the 5 min AFTER | {touch['after']} | {touch['after']/tot:.0%} "
          f"| the limit fills better, moments later |")
    print(f"| never (+/-10 min) | {touch['never']} | {touch['never']/tot:.0%} "
          f"| level is a reference, not an order price |")
    if lead:
        print(f"\n   When he is late, median lateness: {np.median(lead):.0f} seconds "
              f"(middle half: {np.percentile(lead,25):.0f}-{np.percentile(lead,75):.0f}s)")

    print(f"\nB) THE TRIGGER SECOND - how extreme is the tape at his entry second,")
    print("   as a percentile inside his own final-5-minutes window (50% = typical")
    print("   second; high = he fires on the burst):\n")
    print("| Feature (toward his trade direction) | Median percentile | Share above 80th |")
    print("|---|---|---|")
    for k, v in pct.items():
        v = np.asarray(v)
        print(f"| {k} | {np.median(v):.0%} | {(v > 0.8).mean():.0%} |")
    print(f"\n   (features computed for {len(next(iter(pct.values())))} entries with data)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
