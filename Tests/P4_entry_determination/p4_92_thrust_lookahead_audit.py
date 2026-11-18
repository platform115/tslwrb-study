#!/usr/bin/env python3
"""
p4_92_thrust_lookahead_audit.py — P4.92: THE THRUST GATE CONTAINS LOOKAHEAD.
Found 2026-11-18 while writing the Pine translation spec. TRAINING MONTHS.
===============================================================================
THE BUG: every adaptive-era fire condition tests
    d0 * ret2[ib] >= thr,   ret2[k] = close[k] - close[k-2],
    ib = the bar CONTAINING the fire second (bts stamped at bar OPEN,
         searchsorted(...,"right")-1).
close[ib] is the close of the bar STILL FORMING at the fire second - up to
59 seconds of future data inside the entry gate. The burst fires mid-move;
"thrust confirmation" using the forming bar's final close selects precisely
the fires after which the move CONTINUED. The edge was the peeking.

THIS SCRIPT preserves the three-way comparison that established it, with the
adopted M1-RTH exits on each fire set:
  1. as-researched (contaminated): thrust at ib        -> the known results
  2. honest, completed bars: thrust at ib-1            -> fires collapse
     97->28 / 147->37 (overlap 13/12); P&L -27.6 / -21.6, win 27/33%
  3. honest, per-second mids: mid(t) - mid(>= t-120s)  -> -44.6 / +6.1,
     win 33/42% - the CONCEPT measured honestly also has no edge.
CONCLUSION: Strategy 2A's measured entry edge was substantially an artifact
of the lookahead, in-sample AND on the reserved months (same gate ran
everywhere). Scope: every result with the thrust/ret context from the
adaptive era onward. Clean components: the 8s burst trigger (per-second,
honest), atr10 (shift(1)), C(day) (prior sessions), the gap clock, flow
features, old signal gates (completion-stamped before s0).

RUN: python3 Tests/P4_entry_determination/p4_92_thrust_lookahead_audit.py (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P5 = os.path.join(os.path.dirname(HERE), "P5_trade_management")
sys.path.insert(0, HERE); sys.path.insert(0, P5)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, row           # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_10_stall_stack_dials import simq               # noqa: E402

TICK = 0.25
W, GAP, WAIT = 2, 45, 1
BSH, TSH = 0.022, 0.17
Q = dict(early=4.0, stop=4.0, time_bars=27, S=30)


def run(repo):
    c_day = X.c_day_fun(repo)
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        i120 = np.searchsorted(secs, secs - 120)
        mv120 = (mids - mids[np.maximum(i120, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1,
                        0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc),
                                                np.abs(cx.l - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()[bar_i]
        cds = {d: c_day(d) for d in set(P["sd"])}
        P["_Cday"] = np.array([cds.get(d) or np.nan for d in P["sd"]])[bar_i]
        ret2 = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        R = P["_Cday"] * P["_atr10"]
        bt = BSH * R

        def fires(mode):
            kept = []; last = -10**18
            for i in np.flatnonzero(P["keep"] & np.isfinite(bt)):
                if abs(P["_mv8"][i]) < bt[i]:
                    continue
                if secs[i] - last <= GAP:
                    continue
                last = int(secs[i]); ib = P["_bar_i"][i]
                if ib < 61 or not cx.rth[ib]:
                    continue
                d0 = int(np.sign(P["_mv8"][i]))
                thr = TSH * np.sqrt(W / 5) * R[i]
                v = (ret2[ib] if mode == "leak" else
                     ret2[ib - 1] if mode == "closed" else mv120[i])
                if d0 * v >= thr:
                    kept.append((i, d0))
            return kept

        print(f"===== {m} =====")
        for mode, name in [("leak", "as-researched (FORMING-bar close: lookahead)"),
                           ("closed", "honest: last completed bar"),
                           ("sec", "honest: per-second mids, 120s")]:
            f = fires(mode)
            print(row(f"{name} [{len(f)} fires]", {m: simq(P, f, Q)}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
