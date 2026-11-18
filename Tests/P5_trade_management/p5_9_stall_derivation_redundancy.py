#!/usr/bin/env python3
"""
p5_9_stall_derivation_redundancy.py — P5.9 / Management phase: deriving the
stall clock's S + the silence/stall REDUNDANCY check. TRAINING MONTHS ONLY.
===============================================================================
A) DERIVATION measurement for S (the T-EX10 winner used a hand-picked 30 s):
   on each 2A RTH episode-leader path with MFE >= 2 pts, collect the gaps
   between SUCCESSIVE NEW FAVORABLE EXTREMES during the ALIVE phase (entry to
   peak). The distribution's upper percentiles are what S must exceed to
   avoid cutting live moves. Hindsight labeling (peak known after the fact)
   - same status as the T-EX08 measurement: it justifies a fixed S the way
   the sweep-duration measurement justified the fixed 8 s burst window.
B) REDUNDANCY trade sim: stall-30 alone vs silence-0.022/60 alone vs the OR
   combination (exit when EITHER trips). If OR ~ stall alone, the silence
   exit adds nothing on top and one mechanism suffices (the simpler one).
   Same stack as T-EX09/10: fast-fail 1.5 (reverses), hard stop 4.0,
   time 27 bars, session close; no trail, no pt clock.

RUN: python3 Tests/P5_trade_management/p5_9_stall_derivation_redundancy.py (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_49_sec_engine import V11                       # noqa: E402
from p4_66_context_ablation import prep, row           # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_2_deoverlap_anatomy import leaders             # noqa: E402
from p5_7_silence_exit_sim import sim_sil              # noqa: E402
from p5_8_adaptive_and_stall import sim_stall          # noqa: E402

TICK = 0.25
H = 1800
MIN_MFE = 2.0
TIME_BARS = 27
SIL_SHARE, SIL_T, STALL_S = 0.022, 60, 30


def leg_both(cx, mv8, Rsec, fb, fill, fill_s, long):
    p = V11
    best = fill
    lbest = fill_s
    lb = fill_s
    d0 = 1 if long else -1
    early_end = cx.bsec[fb + 2] if fb + 2 < len(cx.bsec) else np.iinfo(np.int64).max
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1
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
                and abs(mv8[i]) >= SIL_SHARE * Rsec[i]):
            lb = s
        if (m > best) if long else (m < best):
            best, lbest = m, s
        if s - lbest > STALL_S or s - lb > SIL_T:
            return m, s, cx.bar_of(s), "quiet"
        early = s < early_end
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        if (m <= stop if long else m >= stop):
            xp = min(stop, m) if long else max(stop, m)
            return xp, s, cx.bar_of(s), ("faststop" if early else "stop")
        i += 1
    j = cx.bar_of(int(cx.secs[-1]))
    return cx.c[j], int(cx.secs[-1]), j, "eof"


def sim_both(P, fire_list):
    cx = P["cx"]
    mv8, Rsec = P["_mv8"], P["_Rsec"]
    pnl = []; busy = -1
    for i, d0 in fire_list:
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        fill = float(P["mids"][i]); long = d0 > 0
        px, xs, xb, reason = leg_both(cx, mv8, Rsec, ib, fill, s0, long)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_both(cx, mv8, Rsec, xb, px, xs, not long)
            tot += (px2 - px) if (not long) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + WAIT
    return pnl


W, GAP, WAIT = 2, 45, 1


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

        # A) alive-phase gaps between successive new favorable extremes
        led = leaders(fires[m], secs)
        gaps = []
        for i, d0 in led:
            s0 = int(secs[i]); f0 = float(mids[i])
            j1 = np.searchsorted(secs, s0, "right")
            j2 = np.searchsorted(secs, s0 + H, "right")
            if j2 - j1 < 10:
                continue
            path = (mids[j1:j2] - f0) * d0
            if path.max() < MIN_MFE:
                continue
            kp = int(np.argmax(path))
            t = secs[j1:j1 + kp + 1] - s0
            pa = path[:kp + 1]
            best = -1e18; lt = 0
            for k in range(len(pa)):
                if pa[k] > best:
                    if k > 0:
                        gaps.append(t[k] - lt)
                    best = pa[k]; lt = t[k]
        g = np.asarray(gaps, float)
        print(f"[{m}] alive-phase gaps between new favorable extremes "
              f"(n={len(g)}): p50 {np.percentile(g,50):.0f}s, p75 "
              f"{np.percentile(g,75):.0f}s, p90 {np.percentile(g,90):.0f}s, "
              f"p95 {np.percentile(g,95):.0f}s")

    print("\nB) Redundancy check - same stack, 2A RTH entries, training months.\n")
    print("| Management | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    per_m = {m: sim_stall(Ps[m], fires[m], STALL_S) for m in Ps}
    print(row(f"stall {STALL_S}s alone", per_m))
    per_m = {m: sim_sil(Ps[m], fires[m], SIL_SHARE, SIL_T) for m in Ps}
    print(row(f"silence {SIL_SHARE}/{SIL_T}s alone", per_m))
    per_m = {m: sim_both(Ps[m], fires[m]) for m in Ps}
    print(row("OR combination (either trips)", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
