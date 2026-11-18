#!/usr/bin/env python3
"""
p5_4_wrb_pt_anatomy.py — P5.4 / Management phase: the WRB pt mechanism AS HE
USES IT (user-corrected 2026-11-18). TRAINING MONTHS ONLY. RTH leaders.
===============================================================================
Mechanism: hold while SAME-DIRECTION WRBs keep OCCURRING after entry - the
1st new WRB = pt1, 2nd = pt2, 3rd = pt3. An event count / progress clock,
not price levels. This measures, per RTH episode leader (p5_2 rule), on the
1m / 3m / 5m charts separately:
  - how many same-direction WRBs complete within the 30-min window
  - the captured points if exiting AT pt1 / pt2 / pt3 completion (mid at
    that second), vs the window peak
  - minutes to each pt
  - captured points if exiting at the FIRST OPPOSITE-direction WRB
  - where the peak sits relative to the pt clock (before pt1 / pt1-pt2 /
    pt2-pt3 / after pt3) - is the WRB count a good "move is done" clock?
WRB definition: body strictly > each of the prior 3 bodies, same session,
no doji (the project's standing wrb_bodies definition). Completion time =
bar close time. Fires-not-trades, mid-based, as all anatomy so far.

RUN: python3 Tests/P5_trade_management/p5_4_wrb_pt_anatomy.py             (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies             # noqa: E402
from p4_2b_zone_mtf import resample                    # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_2_deoverlap_anatomy import leaders             # noqa: E402

TICK = 0.25
H = 1800
TFS = (1, 3, 5)


def wrb_events(bars):
    """Per tf: (comp_ns sorted, dir +1/-1) for all WRBs."""
    out = {}
    for tf in TFS:
        rb = bars if tf == 1 else resample(bars, tf)
        w = wrb_bodies(rb)
        comp = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + tf * int(60e9)
        d = np.where(w.direction.to_numpy() == "bullish", 1, -1)
        o = np.argsort(comp)
        out[tf] = (comp[o], d[o])
    return out


def run(repo):
    c_day = X.c_day_fun(repo)
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
        EV = wrb_events(bars)

        print(f"===== {m}: {len(led)} RTH episode leaders =====")
        for tf in TFS:
            comp, wd = EV[tf]
            rows = []
            for i, d0 in led:
                s0 = int(secs[i]); f0 = float(mids[i])
                j1 = np.searchsorted(secs, s0, "right")
                j2 = np.searchsorted(secs, s0 + H, "right")
                if j2 - j1 < 10:
                    continue
                path = (mids[j1:j2] - f0) * d0
                pk = float(path.max()); tpk = int(secs[j1 + int(np.argmax(path))]) - s0
                a = np.searchsorted(comp, s0 * 10**9, "right")
                b = np.searchsorted(comp, (s0 + H) * 10**9, "right")
                same = [k for k in range(a, b) if wd[k] == d0]
                opp = [k for k in range(a, b) if wd[k] == -d0]

                def val_at(ns):
                    j = np.searchsorted(secs, ns // 10**9, "right") - 1
                    return (float(mids[j]) - f0) * d0 if j >= j1 else np.nan

                pts = [val_at(comp[k]) for k in same[:3]]
                tms = [int(comp[k] // 10**9 - s0) for k in same[:3]]
                ov = val_at(comp[opp[0]]) if opp else np.nan
                otm = int(comp[opp[0]] // 10**9 - s0) if opp else None
                # peak position on the pt clock
                if not same or tpk < tms[0]:
                    seg = 0
                elif len(same) < 2 or tpk < tms[1]:
                    seg = 1
                elif len(same) < 3 or tpk < tms[2]:
                    seg = 2
                else:
                    seg = 3
                rows.append((len(same), pts + [np.nan] * (3 - len(pts)),
                             tms + [np.nan] * (3 - len(tms)), ov, otm, pk, seg))
            n = len(rows)
            cnt = np.array([r[0] for r in rows])
            pts = np.array([r[1] for r in rows], float)
            tms = np.array([r[2] for r in rows], float)
            ovs = np.array([r[3] for r in rows], float)
            pks = np.array([r[5] for r in rows], float)
            segs = np.array([r[6] for r in rows])
            md = lambda v: float(np.nanmedian(v)) if np.isfinite(v).any() else float("nan")
            print(f"### {tf}m chart WRBs")
            print(f"| Same-direction WRBs within 30 min | >=1: "
                  f"{(cnt>=1).mean():.0%} | >=2: {(cnt>=2).mean():.0%} | "
                  f">=3: {(cnt>=3).mean():.0%} |")
            print("| Exit at | median captured (pts) | median minutes | episodes with it |")
            print("|---|---|---|---|")
            for k, name in enumerate(("pt1 (1st WRB)", "pt2 (2nd)", "pt3 (3rd)")):
                have = np.isfinite(pts[:, k])
                print(f"| {name} | {md(pts[:,k]):+.2f} | {md(tms[:,k])/60:.1f} | "
                      f"{have.mean():.0%} |")
            print(f"| first OPPOSITE WRB | {md(ovs):+.2f} | "
                  f"{md(np.array([r[4] if r[4] is not None else np.nan for r in rows], float))/60:.1f} "
                  f"| {np.isfinite(ovs).mean():.0%} |")
            print(f"| (window peak, reference) | {md(pks):+.2f} | — | 100% |")
            print(f"| Peak falls: before pt1 {np.mean(segs==0):.0%} | pt1-pt2 "
                  f"{np.mean(segs==1):.0%} | pt2-pt3 {np.mean(segs==2):.0%} | "
                  f"after pt3 {np.mean(segs==3):.0%} |")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
