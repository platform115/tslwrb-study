#!/usr/bin/env python3
"""
p5_5_candidate_sims.py — P5.5 / Management phase: FIRST CANDIDATE TRADE SIMS
vs the frozen M0. TRAINING MONTHS ONLY. 2A RTH entries (current stack).
===============================================================================
Real trade simulation (per-second engine; one position at a time, cooldown
1 bar, mid fills, faststop reversal kept exactly as M0): the first exit
candidates from the T-EX02/03/05 anatomy, against M0 unchanged.

  M0  (baseline, FROZEN): 1m WRB clock with big-WRB hold exception, early
      fast-fail 1.5 (reverses), hard stop 4.0, trail 2.0/2.5, time stop
      9 bars, session close.
  C1  "M0 re-timed": identical rules, clock on 3m WRBs, time stop 27 bars
      (3x, matching the clock slowdown; flagged variable). NOTE: the big-WRB
      exception (body >= 2 x uref, uref 1m-based) triggers more often on 3m
      bodies - bias toward holding; stated, not hidden.
  C2  (user idea) "trail + flat at pt3": no pt1/pt2 exits; forced flat at the
      3rd same-direction 3m WRB; trail 2.0/2.5 active; aborts as M0; time 27.
  C3a (user idea) "exit at pt2, trail kept": always out at the 2nd
      same-direction 3m WRB (no big exception); trail may exit earlier.
  C3b "exit at pt2, no trail": pure clock + aborts + time stop.
Clock events = 3m WRB completions (project WRB definition on resampled 3m
bars) with completion second > fill second; exit at the mid of the completion
second (M0 uses the 1m close - difference is cosmetic, stated).

RUN: python3 Tests/P5_trade_management/p5_5_candidate_sims.py             (repo root)
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
from p4_49_sec_engine import leg_sec, V11              # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
BSH, TSH = 0.022, 0.17


def clock3(bars):
    rb = resample(bars, 3)
    w = wrb_bodies(rb)
    comp = (pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + 3 * int(60e9)) // 10**9
    d = np.where(w.direction.to_numpy() == "bullish", 1, -1)
    body = (w.body_top - w.body_bottom).to_numpy()
    o = np.argsort(comp)
    return comp[o], d[o], body[o]


def leg_cand(cx, ck, fb, fill, fill_s, long, mode, uref, time_bars=27):
    """One leg, candidate rules. ck = (comp_sec, dir, body) 3m WRB clock."""
    comp, cdir, cbody = ck
    p = V11
    n_pt = 0
    best = fill
    early_end = cx.bsec[fb + 2] if fb + 2 < len(cx.bsec) else np.iinfo(np.int64).max
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1
    k = int(np.searchsorted(comp, fill_s, "right"))
    while i < len(cx.secs):
        s = int(cx.secs[i])
        while jc < len(cx.bsec) and cx.bsec[jc] + 60 <= s:
            if jc + 1 >= len(cx.bsec) or cx.sd[jc + 1] != cx.sd[fb] or not cx.rth[jc + 1]:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "session"
            if jc >= fb + time_bars:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "time"
            jc += 1
        while k < len(comp) and comp[k] <= s:
            if (cdir[k] == 1) == long:
                n_pt += 1
                m0 = cx.mids[i]
                if mode == "C1":
                    big = uref and cbody[k] >= 2.0 * uref
                    if n_pt >= 3 or not big:
                        return m0, s, cx.bar_of(s), f"pt{n_pt}"
                elif mode == "C2":
                    if n_pt >= 3:
                        return m0, s, cx.bar_of(s), "pt3"
                else:  # C3a / C3b
                    if n_pt >= 2:
                        return m0, s, cx.bar_of(s), "pt2"
            k += 1
        m = cx.mids[i]
        early = s < early_end
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        src = "base"
        if mode != "C3b":
            fav = (best - fill) if long else (fill - best)
            if fav >= p["trail"][0]:
                t = best - p["trail"][1] if long else best + p["trail"][1]
                if (t > stop) if long else (t < stop):
                    stop, src = t, "trail"
        if (m <= stop if long else m >= stop):
            xp = min(stop, m) if long else max(stop, m)
            return xp, s, cx.bar_of(s), ("faststop" if early and src == "base" else "stop")
        best = max(best, m) if long else min(best, m)
        i += 1
    j = cx.bar_of(int(cx.secs[-1]))
    return cx.c[j], int(cx.secs[-1]), j, "eof"


def sim_cand(P, ck, fire_list, mode):
    cx = P["cx"]
    pnl = []; busy = -1
    for i, d0 in fire_list:
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        fill = float(P["mids"][i]); long = d0 > 0
        uref = P["prevd"].get(P["sd"][ib], None)
        uref = uref if uref and np.isfinite(uref) else None
        px, xs, xb, reason = leg_cand(cx, ck, ib, fill, s0, long, mode, uref)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_cand(cx, ck, xb, px, xs, not long, mode, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + WAIT
    return pnl


def run(repo):
    c_day = X.c_day_fun(repo)
    Ps, fires, cks = {}, {}, {}
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
        cks[m] = clock3(cx.bars)
        Ps[m] = P

    print("2A RTH entries (current stack), training months. Per-second engine,")
    print("mid fills, faststop reversal kept, cooldown 1 bar. Baseline row must")
    print("reproduce the known quality-lane result (cross-check).\n")
    print("| Management | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    per_m = {m: sim(Ps[m], fires[m], lambda *a: True, cooldown=WAIT) for m in Ps}
    print(row("M0 (frozen baseline, 1m clock)", per_m))
    for mode, name in [("C1", "C1: M0 re-timed to 3m clock, time 27"),
                       ("C2", "C2: trail + flat at 3m-pt3 (user)"),
                       ("C3a", "C3a: exit at 3m-pt2, trail kept (user)"),
                       ("C3b", "C3b: exit at 3m-pt2, no trail")]:
        per_m = {m: sim_cand(Ps[m], cks[m], fires[m], mode) for m in Ps}
        print(row(name, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
