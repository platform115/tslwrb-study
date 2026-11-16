#!/usr/bin/env python3
"""
p4_50_his_overlap.py — P4.50: his trades vs our ACTUAL entries (per-second engine),
by group, all four months.
====================================================================================
Group (unchanged definitions, relaxed signal universe):
  A = same-direction signal scoring >= 6 in the 5 min before his entry
  B = same-direction signal present but under-scored
  C-fade = only an opposite-direction signal · C-other = no signal
MATCH = our fill (p4_49 per-second engine) within +/-5 min of his entry, same
side, and |our fill - his entry price| <= 1.0 pt (loose match: <= 2.0 pts).

RUN: python3 Tests/P4_entry_determination/p4_50_his_overlap.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_49_sec_engine import Ctx, simulate, V10, V11, ALL_MONTHS   # noqa: E402

TOL_NS = 5 * 60_000_000_000


def groups_for(repo, month, insample, e_m):
    if insample:
        sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
        sig = sig[sig.month == month]
    else:
        from p4_42_v10_oos import score_month
        sig, _, _ = score_month(repo, month)
    comp = sig.comp_ns.to_numpy(np.int64)
    dirs = sig.direction.to_numpy()
    sc = sig.score.to_numpy()
    out = []
    for _, t in e_m.iterrows():
        en = pd.Timestamp(t.first_entry_utc).value
        want = "bullish" if t.side == "long" else "bearish"
        m = (comp >= en - TOL_NS) & (comp < en)
        md = m & (dirs == want)
        if md.any():
            out.append("A" if sc[np.flatnonzero(md)].max() >= 6 else "B")
        elif m.any():
            out.append("C-fade")
        else:
            out.append("C-other")
    return np.array(out)


def match(e_m, trades, tol_px):
    if not trades:
        return np.zeros(len(e_m), bool)
    tt = np.array([t["ts"].value for t in trades])
    sides = np.array([t["side"] for t in trades])
    fills = np.array([t["fill"] for t in trades])
    hit = []
    for _, t in e_m.iterrows():
        en = pd.Timestamp(t.first_entry_utc).value
        p0 = float(np.asarray(t.entry_prices).ravel()[0])
        m = (np.abs(tt - en) <= TOL_NS) & (sides == t.side) & (np.abs(fills - p0) <= tol_px)
        hit.append(bool(m.any()))
    return np.array(hit)


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    print("MATCH = our per-second fill within +/-5 min, same side, within 1.0 pt of his")
    print("entry price (loose: within 2.0 pts).\n")
    print("| Month | Group | His trades | v10 matched (loose) | v11 matched (loose) |")
    print("|---|---|---|---|---|")
    tot = {}
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        t10, t11 = [], []
        simulate(cx, V10, t10)
        simulate(cx, V11, t11)
        lo, hi = month_bounds(month)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        m10, m10l = match(e_m, t10, 1.0), match(e_m, t10, 2.0)
        m11, m11l = match(e_m, t11, 1.0), match(e_m, t11, 2.0)
        for grp in ("A", "B", "C-fade", "C-other"):
            k = g == grp
            print(f"| {month} | {grp} | {int(k.sum())} | {int(m10[k].sum())} ({int(m10l[k].sum())}) "
                  f"| {int(m11[k].sum())} ({int(m11l[k].sum())}) |")
            a = tot.setdefault(grp, np.zeros(5, int))
            a += [k.sum(), m10[k].sum(), m10l[k].sum(), m11[k].sum(), m11l[k].sum()]
    print("|---|---|---|---|---|")
    for grp, a in tot.items():
        print(f"| ALL | {grp} | {a[0]} | {a[1]} ({a[2]}) | {a[3]} ({a[4]}) |")
    s = np.sum(list(tot.values()), axis=0)
    print(f"| ALL | all | {s[0]} | {s[1]} ({s[2]}) | {s[3]} ({s[4]}) |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
