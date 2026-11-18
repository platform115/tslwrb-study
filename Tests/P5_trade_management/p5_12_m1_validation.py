#!/usr/bin/env python3
"""
p5_12_m1_validation.py — P5.12 / Management phase: M1 VALIDATION on the
reserved months (2021-09, 2024-11). USER-AUTHORIZED 2026-11-18.
===============================================================================
Frozen before this run (T-EX12/13):
  M1 = stall clock + session close + inert rails (hard stop 4.0, time 27
  bars; early cut OFF i.e. early = stop; NO trail, NO pt clock, NO reversal).
  M1-RTH: S = 30 s. M1-ETH: S = 90 s. (S = inside the session type's
  measured alive-gap band - the band rule, T-EX11/13.)
Entries: Strategy 2A current stack (burst 0.022 x C(day) x TR10, thrust
0.17, gap 45, wait 1), RTH and overnight separately.
Baseline on IDENTICAL fires: M0 (full v11 stack incl. fast-fail reversal).
Per-second engine, mid fills (more optimistic overnight - standing gate).

RUN: python3 Tests/P5_trade_management/p5_12_m1_validation.py             (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_49_sec_engine import leg_sec, V11              # noqa: E402
from p4_82_eth_test import CtxView                     # noqa: E402
from p4_31_profit_v9 import wrb_flags                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_10_stall_stack_dials import leg as leg_m1, simq  # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
VAL = ["2021-09", "2024-11"]
Q_RTH = dict(early=4.0, stop=4.0, time_bars=27, S=30)
Q_ETH = dict(early=4.0, stop=4.0, time_bars=27, S=90)


def run(repo):
    c_day = X.c_day_fun(repo)
    rows_rth, rows_eth = {}, {}
    for m in VAL:
        P = prep(repo, m, insample=False)
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

        # RTH
        P["_base_keep"] = P["keep"]
        f_rth = X.fires_2a(P, np.asarray(cx.rth))
        rows_rth.setdefault("M0 (frozen baseline)", {})[m] = \
            sim(P, f_rth, lambda *a: True, cooldown=WAIT)
        rows_rth.setdefault("M1-RTH (stall 30)", {})[m] = simq(P, f_rth, Q_RTH)

        # OVERNIGHT
        glbx = (bars.session == "GLOBEX").to_numpy()
        lo, hi = month_bounds(m)
        in_month = (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        P["_base_keep"] = in_month
        f_on = X.fires_2a(P, glbx)
        view = CtxView(cx, glbx)
        view.pre = wrb_flags(bars)

        def sim_on(use_m1):
            pnl = []; busy = -1
            uref_map = P.get("prevd") or {}
            for i, d0 in f_on:
                s0 = int(secs[i])
                ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
                if ib < 60 or not glbx[ib] or ib <= busy:
                    continue
                fill = float(mids[i]); long = d0 > 0
                if use_m1:
                    px, xs, xb, reason = leg_m1(view, ib, fill, s0, long, Q_ETH)
                else:
                    uref = uref_map.get(P["sd"][ib], None)
                    uref = uref if uref and np.isfinite(uref) else None
                    px, xs, xb, reason = leg_sec(view, ib, fill, s0, long, V11, uref)
                tot = (px - fill) if long else (fill - px)
                if reason == "faststop" and not use_m1:
                    px2, xs2, xb2, _ = leg_sec(view, xb, px, xs, not long, V11, uref)
                    tot += (px2 - px) if (not long) else (px - px2)
                    xb = xb2
                pnl.append(tot)
                busy = xb + WAIT
            return pnl

        rows_eth.setdefault("M0 (frozen baseline)", {})[m] = sim_on(False)
        rows_eth.setdefault("M1-ETH (stall 90)", {})[m] = sim_on(True)

    print("VALIDATION MONTHS (2021-09, 2024-11) - M1 frozen before the run.")
    print("2A current-stack entries; per-second engine; mid fills.\n")
    for tag, rows in [("RTH", rows_rth), ("OVERNIGHT", rows_eth)]:
        print(f"===== {tag} =====")
        print("| Management | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for name, per_m in rows.items():
            print(row(name, per_m))
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
