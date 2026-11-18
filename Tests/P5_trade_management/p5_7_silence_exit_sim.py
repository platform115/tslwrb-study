#!/usr/bin/env python3
"""
p5_7_silence_exit_sim.py — P5.7 / Management phase: BURST-SILENCE EXIT, first
trade sims. TRAINING MONTHS ONLY. 2A RTH entries (current stack).
===============================================================================
The move-death exit, candidate #1, as a real rule: while in a trade, track the
last same-direction mini-burst (|8s move| >= share x R_est, sign matching);
if silence exceeds T seconds -> exit at the mid. Replaces the trail entirely.
Kept from M0: early fast-fail 1.5 (reverses, silence rule active on the
reversal leg too), hard stop 4.0, session close. Time stop 27 bars (the 3x
re-timing; flagged variable). No pt clock in this first pass - one mechanism
at a time.
Probe grid (user: expect to probe a lot): share {0.014, 0.018, 0.022} x
T {30, 60, 90, 120} s. The alive inter-burst p90s measured in P5.6 (11-61 s,
regime-dependent) bracket the sensible T range; the adaptive trailing form of
T comes after the grid says whether the mechanism earns its keep.
References: M0 frozen; C3b (clock only, no trail) from T-EX06.

RUN: python3 Tests/P5_trade_management/p5_7_silence_exit_sim.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_49_sec_engine import V11                       # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
BSH, TSH = 0.022, 0.17
SHARES = (0.014, 0.018, 0.022)
TS = (30, 60, 90, 120)
TIME_BARS = 27


def leg_sil(cx, mv8, Rsec, fb, fill, fill_s, long, share, T):
    p = V11
    best = fill
    early_end = cx.bsec[fb + 2] if fb + 2 < len(cx.bsec) else np.iinfo(np.int64).max
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1
    lb = fill_s                      # the entry fire counts as burst zero
    d0 = 1 if long else -1
    while i < len(cx.secs):
        s = int(cx.secs[i])
        while jc < len(cx.bsec) and cx.bsec[jc] + 60 <= s:
            if jc + 1 >= len(cx.bsec) or cx.sd[jc + 1] != cx.sd[fb] or not cx.rth[jc + 1]:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "session"
            if jc >= fb + TIME_BARS:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "time"
            jc += 1
        m = cx.mids[i]
        if (np.sign(mv8[i]) == d0 and np.isfinite(Rsec[i])
                and abs(mv8[i]) >= share * Rsec[i]):
            lb = s
        elif s - lb > T:
            return m, s, cx.bar_of(s), "silence"
        early = s < early_end
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        if (m <= stop if long else m >= stop):
            xp = min(stop, m) if long else max(stop, m)
            return xp, s, cx.bar_of(s), ("faststop" if early else "stop")
        best = max(best, m) if long else min(best, m)
        i += 1
    j = cx.bar_of(int(cx.secs[-1]))
    return cx.c[j], int(cx.secs[-1]), j, "eof"


def sim_sil(P, fire_list, share, T):
    cx = P["cx"]
    mv8, Rsec = P["_mv8"], P["_Rsec"]
    pnl = []; busy = -1
    for i, d0 in fire_list:
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        fill = float(P["mids"][i]); long = d0 > 0
        px, xs, xb, reason = leg_sil(cx, mv8, Rsec, ib, fill, s0, long, share, T)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_sil(cx, mv8, Rsec, xb, px, xs, not long, share, T)
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
        P["_Rsec"] = P["_Cday"] * P["_atr10"]
        P["_ret2"] = np.concatenate([[0.0] * X.W, (cx.c[X.W:] - cx.c[:-X.W]) / TICK])
        P["_base_keep"] = P["keep"]
        fires[m] = X.fires_2a(P, np.asarray(cx.rth))
        Ps[m] = P

    print("Burst-silence exit vs M0. 2A RTH entries, training months, per-second")
    print("engine, mid fills, faststop reversal kept, cooldown 1, time 27 bars.\n")
    print("| Management | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    per_m = {m: sim(Ps[m], fires[m], lambda *a: True, cooldown=WAIT) for m in Ps}
    print(row("M0 (frozen baseline)", per_m))
    for share in SHARES:
        for T in TS:
            per_m = {m: sim_sil(Ps[m], fires[m], share, T) for m in Ps}
            print(row(f"silence: share {share:.3f}, T {T}s", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
