#!/usr/bin/env python3
"""
p5_11_m1_eth.py — P5.11 / Management phase: M1 OVERNIGHT (Globex) config.
TRAINING MONTHS ONLY.
===============================================================================
One-design-two-configs (charter): M1 = stall clock + session-block close
(+ inert rails), instantiated for the overnight session.
A) MEASUREMENT first: the alive-phase new-extreme gap band on OVERNIGHT
   2A leader paths (does the RTH-derived S=30 band carry?).
B) TRADE SIMS on overnight 2A fires (current stack; C(day) applied overnight
   as stated in T-EX02): M0 full stack (via the p4_82 Globex view) as the
   baseline, then M1 with S in {30, 60, 90, 120}. Rails kept at RTH values
   (hard stop 4.0, time 27 bars) - flagged: their adapter form (R_est
   shares) is pending; if they bind overnight it will show in the results.
Positions flat at the Globex block end (the session logic in the leg).
HONESTY: overnight mid fills are MORE optimistic than RTH (wider spreads at
thin hours) - standing note from T-EN85.

RUN: python3 Tests/P5_trade_management/p5_11_m1_eth.py                    (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_49_sec_engine import leg_sec, V11              # noqa: E402
from p4_82_eth_test import CtxView                     # noqa: E402
from p4_31_profit_v9 import wrb_flags                  # noqa: E402
from p4_66_context_ablation import prep, row           # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_2_deoverlap_anatomy import leaders             # noqa: E402
from p5_10_stall_stack_dials import leg as leg_m1      # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
H = 1800
MIN_MFE = 1.0          # overnight scale is ~1/3 of RTH (T-EX02)
STALLS = (30, 60, 90, 120)
BASEQ = dict(early=4.0, stop=4.0, time_bars=27)   # early=stop: no early cut (M1)


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
        glbx = (bars.session == "GLOBEX").to_numpy()
        lo, hi = month_bounds(m)
        in_month = (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        P["_base_keep"] = in_month
        fires = X.fires_2a(P, glbx)
        view = CtxView(cx, glbx)
        view.pre = wrb_flags(bars)

        # A) overnight alive-gap band
        led = leaders(fires, secs)
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
        print(f"[{m}] OVERNIGHT alive-phase new-extreme gaps (n={len(g)}): "
              f"p50 {np.percentile(g,50):.0f}s, p75 {np.percentile(g,75):.0f}s, "
              f"p90 {np.percentile(g,90):.0f}s, p95 {np.percentile(g,95):.0f}s")

        # B) sims
        def sim_with(legfun, q=None):
            pnl = []; busy = -1
            uref_map = P.get("prevd") or {}
            for i, d0 in fires:
                s0 = int(secs[i])
                ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
                if ib < 60 or not glbx[ib] or ib <= busy:
                    continue
                fill = float(mids[i]); long = d0 > 0
                if q is None:
                    uref = uref_map.get(P["sd"][ib], None)
                    uref = uref if uref and np.isfinite(uref) else None
                    px, xs, xb, reason = leg_sec(view, ib, fill, s0, long, V11, uref)
                else:
                    px, xs, xb, reason = legfun(view, ib, fill, s0, long, q)
                tot = (px - fill) if long else (fill - px)
                if reason == "faststop" and q is None:
                    px2, xs2, xb2, _ = leg_sec(view, xb, px, xs, not long, V11, uref)
                    tot += (px2 - px) if (not long) else (px - px2)
                    xb = xb2
                pnl.append(tot)
                busy = xb + WAIT
            return pnl

        P.setdefault("_rows", {})
        P["_rows"]["M0 (full v11 stack)"] = sim_with(None)
        for S in STALLS:
            q = dict(BASEQ); q["S"] = S
            P["_rows"][f"M1, stall S={S}s"] = sim_with(leg_m1, q)
        globals().setdefault("_ALL", {})[m] = P["_rows"]

    print("\nOVERNIGHT (Globex) trade sims - 2A current-stack fires, training months.")
    print("Mid fills (MORE optimistic overnight), cooldown 1, flat at block end.\n")
    print("| Management | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    names = list(next(iter(_ALL.values())).keys())
    for name in names:
        per_m = {m: _ALL[m][name] for m in _ALL}
        print(row(name, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
