#!/usr/bin/env python3
"""
p4_43_exit_sharpen.py — P4.43: Strategy 1 exit sharpening (IN-SAMPLE, declared).
=================================================================================
User direction: (a) let winners run better, (b) stop losses sooner. Entry engine
frozen at Strategy 1 / spec v10 (ungated score>=6, confirmation entry, one
reversal on fast-fail). Exits generalized into run_leg2; GATE: the baseline
parameter set must reproduce v10's +288.5 exactly, or everything below is void.
One knob family at a time; the best W knob and best L knob are then combined.
IN-SAMPLE on the discovery months (Oct-2025, Feb-2022) - the sandbox; any
winner here still needs fresh data before it counts.

RUN: python3 Tests/P4_entry_determination/p4_43_exit_sharpen.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_33_losscuts import month_ctx                   # noqa: E402

WAIT = 5
BASE = dict(early=2.0, early_bars=2, stop=4.0, ladder=True, time_bars=9)


def run_leg2(bars, pre, fb, fill, long, p, start_j, e_uref=None):
    """Generalized leg. p keys: early, early_bars, stop, ladder, time_bars,
    time_only_losing, time_cap, be_at, trail=(arm,dist), nopro=(bars,min_pts)."""
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt, wbody = pre
    n_pt = 0
    best = fill                      # favorable extreme through bar j-1
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session"
        npx = p.get("nopro")
        if npx and j - fb == npx[0]:
            fav = (c[j - 1] - fill) if long else (fill - c[j - 1])
            if fav < npx[1]:
                return o[j], j, "nopro"
        early = j < fb + p.get("early_bars", 2)
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        fav_best = (best - fill) if long else (fill - best)
        if p.get("be_at") and fav_best >= p["be_at"]:
            stop = max(stop, fill) if long else min(stop, fill)
        tr = p.get("trail")
        if tr and fav_best >= tr[0]:
            t = best - tr[1] if long else best + tr[1]
            stop = max(stop, t) if long else min(stop, t)
        if (l[j] <= stop if long else h[j] >= stop):
            xp = stop
            if p.get("gapfill"):            # realistic: bar opens beyond stop -> open
                xp = min(stop, o[j]) if long else max(stop, o[j])
            if "_audit" in p:               # tally: was this a gap-through fill?
                p["_audit"].append(abs(xp - stop) > 1e-9 if p.get("gapfill")
                                   else (o[j] < stop if long else o[j] > stop))
            return xp, j, ("faststop" if early else "stop")
        if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            n_pt += 1
            big = p["ladder"] and e_uref and wbody[j] >= 2.0 * e_uref
            if n_pt >= 3 or not big:
                return c[j], j, f"pt{n_pt}"
        if j >= fb + p.get("time_bars", 9):
            fav = (c[j] - fill) if long else (fill - c[j])
            if not (p.get("time_only_losing") and fav > 0):
                return c[j], j, "time"
            if j >= fb + p.get("time_cap", 20):
                return c[j], j, "timecap"
        best = max(best, h[j]) if long else min(best, l[j])
    return c[-1], len(bars) - 1, "eof"


def simulate(es, sig, p):
    pr = {**BASE, **p}
    prev_leg = {**pr, **pr.get("rev", {})}
    pnl, per_m = [], {}
    for month, sym in MONTHS:
        bars, pre_, prev, lo, hi = month_ctx(es, month, sym)
        from p4_31_profit_v9 import wrb_flags
        pre = wrb_flags(bars)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy(); o = bars.open.to_numpy()
        h, l = bars.high.to_numpy(), bars.low.to_numpy()
        g = sig[(sig.month == month) & (sig.score >= 6)]
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
            px, xi, reason = run_leg2(bars, pre, fb, fill, long, pr, fb + 1, uref)
            tot = (px - fill) if long else (fill - px)
            if reason == "faststop":
                px2, xi2, _ = run_leg2(bars, pre, xi, px, not long, prev_leg, xi + 1, uref)
                tot += (px2 - px) if (not long) else (px - px2)
                xi = xi2
            mp.append(tot)
            busy = xi + 5
        pnl += mp
        per_m[month] = sum(mp)
    return np.asarray(pnl), per_m


def line(name, a, per_m):
    w = a > 0
    pm = " | ".join(f"{m}: {v:+.0f}" for m, v in per_m.items())
    return (f"| {name} | {len(a)} | {w.mean():.0%} | +{a[w].mean():.2f} / {a[~w].mean():.2f} "
            f"| {a.sum():+.1f} ({pm}) |")


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    a0, pm0 = simulate(es, sig, {})
    assert abs(a0.sum() - 288.5) < 0.01 and len(a0) == 344, \
        f"GATE FAILED: baseline {a0.sum():+.1f} n={len(a0)} != +288.5 n=344"
    print("GATE OK: generalized engine reproduces v10 baseline (+288.5, 344 trades)\n")
    fam = {
        "W1 time stop 12": {"time_bars": 12},
        "W2 time stop 15": {"time_bars": 15},
        "W3 time stop 20": {"time_bars": 20},
        "W4 time 9 only-if-losing (cap 20)": {"time_only_losing": True, "time_cap": 20},
        "W5 breakeven stop after +2.0": {"be_at": 2.0},
        "W6 trail 3.0 behind best after +2.0": {"trail": (2.0, 3.0)},
        "L1 stop 3.0": {"stop": 3.0},
        "L2 stop 2.5": {"stop": 2.5},
        "L3 fast-fail 1.5 (first 2 bars)": {"early": 1.5},
        "L4 fast-fail window 3 bars": {"early_bars": 3},
        "L5 reversal-leg stop 2.5": {"rev": {"stop": 2.5}},
        "L6 no-progress <+0.5 after 4 bars": {"nopro": (4, 0.5)},
    }
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    print(line("v10 baseline (Strategy 1)", a0, pm0))
    res = {}
    for name, p in fam.items():
        a, pm = simulate(es, sig, p)
        res[name] = (a.sum(), p, all(v > 0 for v in pm.values()))
        print(line(name, a, pm))
    bw = max((k for k in res if k.startswith("W")), key=lambda k: res[k][0])
    bl = max((k for k in res if k.startswith("L")), key=lambda k: res[k][0])
    combo = {**res[bw][1], **res[bl][1]}
    a, pm = simulate(es, sig, combo)
    print(line(f"COMBO best-W + best-L ({bw[:2]}+{bl[:2]})", a, pm))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hw = e_m.realized_pnl > 0
        print(f"| HIS {month} | {len(e_m)} | {hw.mean():.0%} | +{e_m.realized_pnl[hw].mean():.1f} / "
              f"{e_m.realized_pnl[~hw].mean():.1f} (as parsed) | {e_m.realized_pnl.sum():+.0f} (as parsed) |")
    print("\nREAD: IN-SAMPLE grid, declared; one knob per row; any pick needs fresh data")
    print("before it counts. Both-months-positive matters more than the pooled total.")
    return es, sig


def sens(repo):
    """Plateau test around the combo: fragile spike or broad ridge?"""
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    for arm in (1.5, 2.0, 2.5):
        for dist in (2.5, 3.0, 3.5):
            for ff in (1.5, 2.0):
                a, pm = simulate(es, sig, {"trail": (arm, dist), "early": ff})
                print(line(f"trail arm {arm} dist {dist} ff {ff}", a, pm))
    print("\nREAD: in-sample plateau check - a broad ridge means the combo is not a")
    print("knife-edge fit; a single spike would mean it is.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--sens", action="store_true")
    a = ap.parse_args()
    sens(a.repo) if a.sens else run(a.repo)
