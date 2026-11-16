#!/usr/bin/env python3
"""
p4_48_realistic_fills.py — P4.48: stop-fill realism check (found via raw-bar
inspection of double-fails in P4.47).
==============================================================================
The exit engine has always filled stop exits AT the stop price, even when the
bar OPENS beyond the stop. Entries already used worst-of(level, open); stops
did not. This script re-runs v10 and v11 on all four months with gap-aware
stop fills: exit = worse of (stop level, bar open). This is the conservative
bound; the optimistic bound is every number previously reported. True fills
sit between (per-second mids exist for all four months and can pin it).

RUN: python3 Tests/P4_entry_determination/p4_48_realistic_fills.py        (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_43_exit_sharpen import simulate, line, run_leg2, BASE   # noqa: E402
from p4_42_v10_oos import score_month, WAIT                     # noqa: E402
from p4_31_profit_v9 import wrb_flags                           # noqa: E402

V11 = {"trail": (2.0, 2.5), "early": 1.5}


def oos(repo, month, p):
    sigm, bars, sym = score_month(repo, month)
    bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
    cl, o = bars.close.to_numpy(), bars.open.to_numpy()
    h, l = bars.high.to_numpy(), bars.low.to_numpy()
    pre = wrb_flags(bars)
    pnl = []; busy = -1
    for _, r in sigm[sigm.score >= 6].sort_values("comp_ns").iterrows():
        ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
        if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
            continue
        fb0 = ib + 1
        if fb0 >= len(bts) or not bars.rth.iloc[fb0] or fb0 <= busy:
            continue
        mv = cl[ib] - cl[ib - 5]
        if mv == 0:
            continue
        long = mv > 0
        uref = r.uref if np.isfinite(r.uref) else None
        lvl = h[ib] if long else l[ib]
        fb = None
        for j in range(fb0, min(fb0 + WAIT, len(bars))):
            if not bars.rth.iloc[j]:
                break
            if (h[j] >= lvl) if long else (l[j] <= lvl):
                fb = j
                fill = max(lvl, o[j]) if long else min(lvl, o[j])
                break
        if fb is None:
            continue
        px, xi, reason = run_leg2(bars, pre, fb, fill, long, p, fb + 1, uref)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xi2, _ = run_leg2(bars, pre, xi, px, not long, p, xi + 1, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            xi = xi2
        pnl.append(tot)
        busy = xi + 5
    return np.asarray(pnl)


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    a0, _ = simulate(es, sig, V11)
    assert abs(a0.sum() - 521.0) < 0.1, "GATE FAILED: default fills changed"
    print("GATE OK: default-fill path unchanged (v11 in-sample +521.0)\n")
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    for name, p in [("v10", {"gapfill": True}), ("v11", {**V11, "gapfill": True})]:
        a, pm = simulate(es, sig, p)
        print(line(f"{name} in-sample, realistic stop fills", a, pm))
        for month in ("2021-09", "2024-11"):
            b = oos(repo, month, {**BASE, **p})
            w = b > 0
            print(f"| {name} {month}, realistic stop fills | {len(b)} | {w.mean():.0%} | "
                  f"+{b[w].mean():.2f} / {b[~w].mean():.2f} | {b.sum():+.1f} pts |")
    print("\nREAD: conservative bound. All previously reported profit totals are the")
    print("optimistic bound. Next: per-second mid data can pin the true fill between.")


def audit(repo):
    """How many stop-type exits were actually gap-through (mis-priced before)?"""
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    tally = []
    p = {**V11, "gapfill": True, "_audit": tally}
    a, _ = simulate(es, sig, p)
    ins = list(tally); tally.clear()
    oosx = {}
    for month in ("2021-09", "2024-11"):
        oos(repo, month, {**BASE, **p})
        oosx[month] = list(tally); tally.clear()
    print("v11, share of STOP-type exits (early cut / full stop / follow-stop) where")
    print("the bar OPENED beyond the stop (i.e., the fill was previously mis-priced):")
    print(f"  in-sample:  {int(np.sum(ins))}/{len(ins)} = {np.mean(ins):.0%}")
    for m, v in oosx.items():
        print(f"  {m}:   {int(np.sum(v))}/{len(v)} = {np.mean(v):.0%}")
    print("Close-based exits (pt ladder, time stop, session end) fill at the bar close")
    print("and were never affected; within-bar stop touches were priced correctly.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--audit", action="store_true")
    a = ap.parse_args()
    audit(a.repo) if a.audit else run(a.repo)
