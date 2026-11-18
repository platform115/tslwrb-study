#!/usr/bin/env python3
"""
p5_8_adaptive_and_stall.py — P5.8 / Management phase: ADAPTIVE-T silence exit
+ STALL-CLOCK head-to-head. TRAINING MONTHS ONLY. 2A RTH entries.
===============================================================================
1) ADAPTIVE T for the burst-silence exit (T-EX09 winner was fixed T=60s,
   which matched the measured alive-gap p90 - this wires that as a rule):
     T(day) = clamp( p90 of same-direction consecutive mini-burst gaps
                     over all PRIOR in-month sessions, 30..90 s )
   - mini-burst = |8s move| >= 0.022 x R_est (entry-grade, already derived)
   - only gaps <= 300 s count (within-episode proxy; across dead zones a gap
     says nothing about liveness) - STATED CHOICE
   - expanding in-month, min 1 prior session (the tested trailing form);
     first session falls back to the clamp midpoint 60 s - STATED
2) STALL CLOCK head-to-head (candidate #4; its discrimination stage is
   label-leaking by construction, so rule-level comparison is the honest
   test): exit when no NEW favorable extreme for S seconds,
   S in {30, 60, 90, 120}.
Both run in the same stack as T-EX09: early fast-fail 1.5 (reverses, rule
active on the reversal leg), hard stop 4.0, time 27 bars, session close,
NO trail, NO pt clock. References: M0 frozen; fixed silence 0.022/60s.

RUN: python3 Tests/P5_trade_management/p5_8_adaptive_and_stall.py         (repo root)
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
from p5_7_silence_exit_sim import leg_sil, sim_sil     # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
BSH = 0.022
GAP_CAP, CLAMP_LO, CLAMP_HI, T_DEFAULT = 300, 30, 90, 60
STALLS = (30, 60, 90, 120)
TIME_BARS = 27


def leg_stall(cx, fb, fill, fill_s, long, S):
    p = V11
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
            if jc >= fb + TIME_BARS:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "time"
            jc += 1
        m = cx.mids[i]
        if (m > best) if long else (m < best):
            best, lbest = m, s
        elif s - lbest > S:
            return m, s, cx.bar_of(s), "stall"
        early = s < early_end
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        if (m <= stop if long else m >= stop):
            xp = min(stop, m) if long else max(stop, m)
            return xp, s, cx.bar_of(s), ("faststop" if early else "stop")
        i += 1
    j = cx.bar_of(int(cx.secs[-1]))
    return cx.c[j], int(cx.secs[-1]), j, "eof"


def sim_stall(P, fire_list, S):
    cx = P["cx"]
    pnl = []; busy = -1
    for i, d0 in fire_list:
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        fill = float(P["mids"][i]); long = d0 > 0
        px, xs, xb, reason = leg_stall(cx, ib, fill, s0, long, S)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_stall(cx, xb, px, xs, not long, S)
            tot += (px2 - px) if (not long) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + WAIT
    return pnl


def t_by_day(P):
    """Adaptive T per session date (expanding in-month, min 1 prior session)."""
    secs, keep = P["secs"], P["keep"]
    mv8, Rsec = P["_mv8"], P["_Rsec"]
    sd = np.asarray(P["sd"])[P["_bar_i"]]
    burst = keep & np.isfinite(Rsec) & (np.abs(mv8) >= BSH * Rsec)
    days = pd.unique(sd[keep])
    out = {}
    hist = []
    for d in days:
        out[d] = (float(np.clip(np.percentile(hist, 90), CLAMP_LO, CLAMP_HI))
                  if len(hist) >= 20 else float(T_DEFAULT))
        m = burst & (sd == d)
        for dirn in (1, -1):
            bs = secs[m & (np.sign(mv8) == dirn)]
            g = np.diff(bs)
            hist.extend(g[(g > 0) & (g <= GAP_CAP)].tolist())
    return out


def sim_sil_adaptive(P, fire_list, tmap):
    cx = P["cx"]
    mv8, Rsec = P["_mv8"], P["_Rsec"]
    pnl = []; busy = -1
    for i, d0 in fire_list:
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        T = tmap.get(P["sd"][ib], T_DEFAULT)
        fill = float(P["mids"][i]); long = d0 > 0
        px, xs, xb, reason = leg_sil(cx, mv8, Rsec, ib, fill, s0, long, BSH, T)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_sil(cx, mv8, Rsec, xb, px, xs, not long, BSH, T)
            tot += (px2 - px) if (not long) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + WAIT
    return pnl


def run(repo):
    c_day = X.c_day_fun(repo)
    Ps, fires, tmaps = {}, {}, {}
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
        tmaps[m] = t_by_day(P)
        tv = list(tmaps[m].values())
        print(f"[{m}] adaptive T(day): min {min(tv):.0f}s, median "
              f"{np.median(tv):.0f}s, max {max(tv):.0f}s")
        Ps[m] = P

    print("\n2A RTH entries, training months, per-second engine, mid fills,")
    print("faststop reversal kept, cooldown 1, time 27 bars.\n")
    print("| Management | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    per_m = {m: sim(Ps[m], fires[m], lambda *a: True, cooldown=WAIT) for m in Ps}
    print(row("M0 (frozen baseline)", per_m))
    per_m = {m: sim_sil(Ps[m], fires[m], BSH, 60) for m in Ps}
    print(row("silence FIXED 0.022 / 60s (T-EX09 best)", per_m))
    per_m = {m: sim_sil_adaptive(Ps[m], fires[m], tmaps[m]) for m in Ps}
    print(row("silence ADAPTIVE T (trailing p90 rule)", per_m))
    for S in STALLS:
        per_m = {m: sim_stall(Ps[m], fires[m], S) for m in Ps}
        print(row(f"stall clock: no new extreme for {S}s", per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
