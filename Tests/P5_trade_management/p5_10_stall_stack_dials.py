#!/usr/bin/env python3
"""
p5_10_stall_stack_dials.py — P5.10 / Management phase: the stall-30 stack's
INHERITED DIALS bracketed one at a time. TRAINING MONTHS ONLY.
===============================================================================
Base stack (T-EX11 best): stall S=30 + early fast-fail 1.5 (reverses) +
hard stop 4.0 + time 27 bars + session close. Each dial bracketed with the
others held at base:
  fast-fail early cut: 1.0 / 1.5 / 2.0 / 2.5   (tuned for M0's 9-min trades;
                                                never re-examined)
  hard stop:           3.0 / 4.0 / 5.0 / 6.0
  time stop (bars):    18 / 27 / 36 / 45       (27 was a 3x convenience pick)
  stall S (seconds):   20 / 30 / 40 / 50       (inside the derived band)
ADAPTER PHASE NOTE (user, standing): any dial that proves sensitive gets an
adaptation candidate next - the stops' natural form is a share of R_est
(points-fixed stops cannot carry across regimes/ETH), the time stop's is the
measured peak-time distribution, S's is the alive-gap band rule (T-EX11).
This round locates the sensitive dials; the adapter round wires them.

RUN: python3 Tests/P5_trade_management/p5_10_stall_stack_dials.py         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, row           # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
BASE = dict(early=1.5, stop=4.0, time_bars=27, S=30)


def leg(cx, fb, fill, fill_s, long, q):
    best = fill
    lbest = fill_s
    early_end = cx.bsec[fb + 2] if fb + 2 < len(cx.bsec) else np.iinfo(np.int64).max
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1
    while i < len(cx.secs):
        s = int(cx.secs[i])
        while jc < len(cx.bsec) and cx.bsec[jc] + 60 <= s:
            if jc + 1 >= len(cx.bsec) or cx.sd[jc + 1] != cx.sd[fb] or not cx.rth[jc + 1]:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "session"
            if jc >= fb + q["time_bars"]:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "time"
            jc += 1
        m = cx.mids[i]
        if (m > best) if long else (m < best):
            best, lbest = m, s
        elif s - lbest > q["S"]:
            return m, s, cx.bar_of(s), "stall"
        early = s < early_end
        sp = q["early"] if early else q["stop"]
        stop = fill - sp if long else fill + sp
        if (m <= stop if long else m >= stop):
            xp = min(stop, m) if long else max(stop, m)
            return xp, s, cx.bar_of(s), ("faststop" if early else "stop")
        i += 1
    j = cx.bar_of(int(cx.secs[-1]))
    return cx.c[j], int(cx.secs[-1]), j, "eof"


def simq(P, fire_list, q):
    cx = P["cx"]
    pnl = []; busy = -1
    for i, d0 in fire_list:
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        fill = float(P["mids"][i]); long = d0 > 0
        px, xs, xb, reason = leg(cx, ib, fill, s0, long, q)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg(cx, xb, px, xs, not long, q)
            tot += (px2 - px) if (not long) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + WAIT
    return pnl


def run(repo):
    c_day = X.c_day_fun(repo)
    Ps, fires = {}, {}
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
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
        fires[m] = X.fires_2a(P, np.asarray(cx.rth))
        Ps[m] = P

    print("Stall-30 stack dials, one at a time (others at base). 2A RTH entries,")
    print("training months, per-second engine, mid fills, cooldown 1.\n")
    print("| Config | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    per_m = {m: simq(Ps[m], fires[m], BASE) for m in Ps}
    print(row("BASE: stall 30 / early 1.5 / stop 4.0 / time 27", per_m))
    for key, vals in [("early", (1.0, 2.0, 2.5)),
                      ("stop", (3.0, 5.0, 6.0)),
                      ("time_bars", (18, 36, 45)),
                      ("S", (20, 40, 50))]:
        for v in vals:
            q = dict(BASE); q[key] = v
            per_m = {m: simq(Ps[m], fires[m], q) for m in Ps}
            print(row(f"{key} = {v}", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
