#!/usr/bin/env python3
"""
p5_3_level_hypothesis.py — P5.3 / Management phase: THE LEVEL HYPOTHESIS.
TRAINING MONTHS ONLY. RTH episode leaders.
===============================================================================
Standing user-flagged hypothesis: levels select nothing at ENTRY (five nulls),
but once a trade is on they may govern it - favorable excursions should STALL
at WRB boundaries / KME-zone levels if so.

Operationalized: for each RTH episode-leader fire (p5_2 rule) whose favorable
excursion reaches >= 2 pts (so a "peak" is meaningful), take the favorable
PEAK within the 30-min window and measure the tick distance from the peak
price to the nearest ACTIVE level at that moment. Two catalogs, separately:
  A. ALL WRB body bounds, 1m/3m/5m charts, each level active for 60 min
     after its WRB completes (the general boundary hypothesis)
  B. Post-KME reaction WRB bounds, 1/3/5/10/15m (the p4_51 definition)
NULLS (both needed - WRB levels sit near recent price action, and so do path
extremes, so ambient chance alone is not a fair bar):
  N1 ambient: distance from every 5th RTH 1-min close to active levels
     (chance proximity given level density)
  N2 anti-peak: the SAME fire's adverse extreme (price and time), same
     distance measure - an extreme of the same path that the hypothesis does
     NOT privilege.
Verdict standard: peaks must be closer than BOTH nulls to count as support.
Report: median distance and share within 2 / 4 / 8 ticks.

RUN: python3 Tests/P5_trade_management/p5_3_level_hypothesis.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies             # noqa: E402
from p4_2b_zone_mtf import resample                    # noqa: E402
from p4_51_kme_levels import levels_for_month, dist_ticks, LIFE_MIN  # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_2_deoverlap_anatomy import leaders             # noqa: E402

TICK = 0.25
H = 1800
MIN_MFE = 2.0
ALL_TFS = (1, 3, 5)


def all_wrb_levels(bars):
    """Catalog A: every WRB body bound on 1/3/5m, active LIFE_MIN after completion."""
    out = {}
    for tf in ALL_TFS:
        rb = bars if tf == 1 else resample(bars, tf)
        w = wrb_bodies(rb)
        comp = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + tf * int(60e9)
        order = np.argsort(comp)
        out[tf] = (comp[order], w.body_bottom.to_numpy()[order],
                   w.body_top.to_numpy()[order])
    return out


def stats(ds):
    ds = np.asarray([d for d in ds if np.isfinite(d)])
    if not len(ds):
        return "n=0"
    return (f"n={len(ds)}, median {np.median(ds):.1f} ticks, "
            f"within 2/4/8: {np.mean(ds<=2):.0%}/{np.mean(ds<=4):.0%}/{np.mean(ds<=8):.0%}")


def run(repo):
    c_day = X.c_day_fun(repo)
    ev_all = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]; bars = cx.bars
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()[bar_i]
        cds = {d: c_day(d) for d in set(P["sd"])}
        P["_Cday"] = np.array([cds.get(d) or np.nan for d in P["sd"]])[bar_i]
        P["_ret2"] = np.concatenate([[0.0] * X.W, (cx.c[X.W:] - cx.c[:-X.W]) / TICK])
        P["_base_keep"] = P["keep"]
        led = leaders(X.fires_2a(P, np.asarray(cx.rth)), secs)

        lo, hi = month_bounds(m)
        catA = all_wrb_levels(bars)
        catB = levels_for_month(bars, ev_all, lo, hi)
        cats = [("A: all WRB bounds 1/3/5m", catA, ALL_TFS),
                ("B: post-KME reaction WRB bounds", catB, tuple(catB.keys()))]

        # collect peak / anti-peak per qualifying leader
        peaks, antis = [], []
        for i, d0 in led:
            s0 = int(secs[i]); f0 = float(mids[i])
            j1 = np.searchsorted(secs, s0, "right")
            j2 = np.searchsorted(secs, s0 + H, "right")
            if j2 - j1 < 10:
                continue
            path = (mids[j1:j2] - f0) * d0
            if path.max() < MIN_MFE:
                continue
            kp = int(np.argmax(path)); ka = int(np.argmin(path))
            peaks.append((int(secs[j1 + kp]) * 10**9, float(mids[j1 + kp])))
            antis.append((int(secs[j1 + ka]) * 10**9, float(mids[j1 + ka])))

        # ambient null: every 5th RTH 1m close
        rth_idx = np.flatnonzero(np.asarray(cx.rth))[::5]
        amb = [(int(cx.bts[k]) + int(60e9), float(cx.c[k])) for k in rth_idx]

        print(f"===== {m}: {len(peaks)} qualifying leaders (MFE >= {MIN_MFE} pts) =====")
        for cname, lv, tfs in cats:
            print(f"-- Catalog {cname}")
            for label, pts in [("favorable PEAKS", peaks),
                               ("anti-peaks (same fires, adverse extreme)", antis),
                               ("ambient (every 5th RTH 1m close)", amb)]:
                ds = [dist_ticks(lv, tfs, t, p) for t, p in pts]
                print(f"   {label}: {stats(ds)}")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
