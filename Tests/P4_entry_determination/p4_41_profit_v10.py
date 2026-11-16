#!/usr/bin/env python3
"""
p4_41_profit_v10.py — the STRATEGY_SPEC_v10 simulator (reproducible reference).
================================================================================
v10 = ungated score>=6 on the relaxed universe (p4_36_all_signals.csv) · direction
= 5-min move · CONFIRMATION ENTRY: stop order at the signal bar's momentum-side
extreme, valid 5 bars, no-trade if untouched · v9-B exit stack (fast-fail 2.0 x
2 bars with ONE reversal, stop 4.0, pt ladder, time 9 bars) · 5-min cooldown.
Variants reported: full 10-condition score, price-only 8-condition (>=5, >=6),
and the gated <=15min arm. Registered: T-EN45.

RUN: python3 Tests/P4_entry_determination/p4_41_profit_v10.py            (repo root)
OUT: p4_41_trades.csv (full-v10 per-trade rows)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                 # noqa: E402
from p4_31_profit_v9 import run_leg, ARMS             # noqa: E402
from p4_33_losscuts import month_ctx, row             # noqa: E402

WAIT = 5


def simulate(es, sig, gate, collect=None):
    p = dict(ARMS["B (momentum ladder)"])
    pnl, per_m = [], {}
    for month, sym in MONTHS:
        bars, pre, prev, lo, hi = month_ctx(es, month, sym)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy(); o = bars.open.to_numpy()
        h, l = bars.high.to_numpy(), bars.low.to_numpy()
        g = sig[sig.month == month]; g = g[gate(g)]
        busy = -1; mp = []
        for _, r in g.sort_values("comp_ns").iterrows():
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
            px, xi, reason, _ = run_leg(bars, pre, fb, fill, long, 1.0, p, fb + 1, uref)
            tot = (px - fill) if long else (fill - px)
            if reason == "faststop":
                px2, xi2, r2, _ = run_leg(bars, pre, xi, px, not long, 1.0, p, xi + 1, uref)
                tot += (px2 - px) if (not long) else (px - px2)
                reason = f"faststop->{r2}"
                xi = xi2
            mp.append(tot)
            if collect is not None:
                collect.append(dict(month=month, ts=bars.ts_event.iloc[fb], side="long" if long else "short",
                                    fill=fill, pnl_pts=tot, reason=reason, hold=xi - fb))
            busy = xi + 5
        pnl += mp
        per_m[month] = sum(mp)
    return np.asarray(pnl), per_m


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    sig["score8"] = sig.score - sig.k5.astype(int) - sig.k9.astype(int)
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    keep = []
    for name, gate, coll in [
        ("v10 FULL (ungated 10-cond >=6)", lambda d: d.score >= 6, keep),
        ("v10 gated arm (news<=15m)", lambda d: (d.score >= 6) & (d.mins_since <= 15), None),
        ("price-only (8-cond >=5)", lambda d: d.score8 >= 5, None),
        ("price-only strict (8-cond >=6)", lambda d: d.score8 >= 6, None),
    ]:
        a, per_m = simulate(es, sig, gate, coll)
        w = a > 0
        pm = " | ".join(f"{m}: {v:+.0f}" for m, v in per_m.items())
        print(f"| {name} | {len(a)} | {w.mean():.0%} | +{a[w].mean():.2f} / {a[~w].mean():.2f} | {a.sum():+.1f} ({pm}) |")
    pd.DataFrame(keep).to_csv(os.path.join(HERE, "p4_41_trades.csv"), index=False)
    print("\nREAD: the committed reference for spec v10 (T-EN45); in-sample, costs excluded,")
    print("out-of-sample validation owed before any profitability claim.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
