#!/usr/bin/env python3
"""
p4_51_kme_levels.py — P4.51: back to basics - are his GROUP A entries placed at
the bounds of post-KME reaction WRBs?
=================================================================================
For his GROUP A trades only (same-direction signal >= 6 in prior 5 min; 141
across the four run months):
  - reaction WRB = a WRB (body > prior 3, same session, no doji) on the 1m, 3m,
    5m, 10m or 15m chart COMPLETING within 45 min after a KME (calendar event)
  - its LEVELS = body top and body bottom
  - a level is ACTIVE from the WRB's completion until 60 min later
  - distance = ticks from his entry price to the nearest active level
Baselines: (a) every RTH 1m close in the same months (chance proximity given
level density), (b) our v11 per-second fills (how we compare).
Choices recorded: 45-min reaction window, 60-min level life, body bounds (not
bar high/low). All are first-pass settings, open to amendment.

RUN: python3 Tests/P4_entry_determination/p4_51_kme_levels.py             (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies             # noqa: E402
from p4_2b_zone_mtf import resample                    # noqa: E402
from p4_49_sec_engine import Ctx, simulate, V11, ALL_MONTHS   # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402

TICK = 0.25
REACT_MIN = 45          # reaction window after the KME (minutes)
LIFE_MIN = 60           # how long a level stays active after the WRB completes
TFS = (1, 3, 5, 10, 15)
FIRST_ONLY = False      # --first: only the FIRST reaction WRB per event per tf


def levels_for_month(bars, ev_all, lo, hi):
    """Per tf: sorted arrays (comp_ns, bottom, top) of post-KME reaction WRBs."""
    out = {}
    evs = np.array([e for e in ev_all if lo.value - 4 * 86400e9 <= e < hi.value], dtype=np.int64)
    for tf in TFS:
        rb = bars if tf == 1 else resample(bars, tf)
        w = wrb_bodies(rb)
        comp = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + tf * int(60e9)
        keep = np.zeros(len(w), bool)
        for e in evs:
            m = (comp > e) & (comp <= e + REACT_MIN * int(60e9))
            if FIRST_ONLY:
                idx = np.flatnonzero(m)
                if len(idx):
                    keep[idx[np.argmin(comp[idx])]] = True
            else:
                keep |= m
        order = np.argsort(comp[keep])
        out[tf] = (comp[keep][order], w.body_bottom.to_numpy()[keep][order],
                   w.body_top.to_numpy()[keep][order])
    return out


def dist_ticks(lv, tfs, en, px):
    """Min tick distance from px to any active level on the given tfs at time en."""
    best = np.inf
    for tf in tfs:
        comp, bot, top = lv[tf]
        a = np.searchsorted(comp, en - LIFE_MIN * int(60e9))
        b = np.searchsorted(comp, en, side="right")
        if b > a:
            d = np.minimum(np.abs(px - bot[a:b]), np.abs(px - top[a:b])).min() / TICK
            best = min(best, d)
    return best


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    ev_all = news_sets(repo)["all"]
    his, base, ours = {t: [] for t in ("1", "3", "5", "135", "10", "15")}, \
                      {t: [] for t in ("1", "3", "5", "135", "10", "15")}, \
                      {t: [] for t in ("1", "3", "5", "135", "10", "15")}
    per_month = []
    GROUPS = {"1": (1,), "3": (3,), "5": (5,), "135": (1, 3, 5), "10": (10,), "15": (15,)}
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        lo, hi = month_bounds(month)
        lv = levels_for_month(cx.bars, ev_all, lo, hi)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        eA = e_m[g == "A"]
        for _, t in eA.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            px = float(np.asarray(t.entry_prices).ravel()[0])
            for k, tfs in GROUPS.items():
                his[k].append(dist_ticks(lv, tfs, en, px))
        # baseline: every RTH 1m close
        rth = cx.bars[cx.bars.rth]
        bns = pd.DatetimeIndex(rth.ts_event).as_unit("ns").asi8 + int(60e9)
        bcl = rth.close.to_numpy()
        m01 = (bns >= lo.value) & (bns < hi.value)
        for en, px in zip(bns[m01], bcl[m01]):
            for k, tfs in GROUPS.items():
                base[k].append(dist_ticks(lv, tfs, int(en), px))
        # our v11 fills
        coll = []
        simulate(cx, V11, coll)
        for t in coll:
            for k, tfs in GROUPS.items():
                ours[k].append(dist_ticks(lv, tfs, t["ts"].value, t["fill"]))
        hm = np.array([his["135"][i] for i in range(len(his["135"]))][-len(eA):])
        per_month.append((month, len(eA), np.mean(hm <= 4) if len(eA) else np.nan))
    print(f"Universe: his GROUP A trades only (n={len(his['135'])}). Levels: body top/")
    print(f"bottom of WRBs completing within {REACT_MIN} min after a KME; active {LIFE_MIN} min.\n")
    print("| Chart | His A: median ticks | His <=1tk (base, ratio) | <=2tk (base, ratio) "
          "| <=4tk (base, ratio) | v11 fills <=2tk |")
    print("|---|---|---|---|---|---|")
    for k, lab in [("1", "1m"), ("3", "3m"), ("5", "5m"), ("135", "1m+3m+5m"),
                   ("10", "10m"), ("15", "15m")]:
        h = np.array(his[k]); b = np.array(base[k]); o = np.array(ours[k])
        hf = h[np.isfinite(h)]; bf = b[np.isfinite(b)]; of = o[np.isfinite(o)]
        cov_h = np.isfinite(h).mean()
        cells = []
        for th in (1, 2, 4):
            hr, br = (hf <= th).mean(), (bf <= th).mean()
            cells.append(f"{hr:.0%} ({br:.0%}, {hr/max(br,1e-9):.2f}x)")
        print(f"| {lab} | {np.median(hf):.1f} (active for {cov_h:.0%}) | " +
              " | ".join(cells) + f" | {(of<=2).mean():.0%} |")
    print("\n| Month | His A trades | within 4tk of a 1m/3m/5m level |")
    print("|---|---|---|")
    for m, n, s in per_month:
        print(f"| {m} | {n} | {s:.0%} |")
    print("\nREAD: 'active for X%' = share of entries/minutes that had any live level;")
    print("proximity shares are computed among those. Ratio >1 = he clusters at these")
    print("levels more than chance. Settings (45/60 min, body bounds) are first-pass.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--first", action="store_true")
    a = ap.parse_args()
    FIRST_ONLY = a.first
    if FIRST_ONLY:
        print("MODE: FIRST reaction WRB per event per chart only\n")
    run(a.repo)
