#!/usr/bin/env python3
"""
p5_6_burst_silence_discrim.py — P5.6 / Management phase: BURST SILENCE as a
move-death signal - DISCRIMINATION MEASUREMENT (no P&L). TRAINING MONTHS ONLY.
===============================================================================
Candidate #1 from the move-death menu: a live move keeps producing
same-direction 8-second mini-bursts; death = silence. Before any exit rule is
built, measure whether the signal DISCRIMINATES:
  - paths: 2A RTH episode leaders (p5_2 rule) with MFE >= 2 pts, 30-min
    window capped at session end
  - label each in-trade second ALIVE (at or before the favorable peak) or
    DEAD (after the peak)
  - signal at each second: SILENCE = seconds since the last same-direction
    mini-burst (|8s move| >= s x R_est, sign matching the trade; the entry
    fire itself counts as burst zero)
  - mini-burst thresholds s: 0.008 / 0.011 / 0.014 / 0.018 / 0.022
    (entry grade = 0.022 ~ 95th pct of q; lower s = more sensitive bursts)
Reported per month x threshold:
  - AUC of silence predicting DEAD (0.5 = knows nothing)
  - median silence in ALIVE vs DEAD seconds
  - inter-burst gap percentiles DURING ALIVE phases (50/75/90) - the raw
    material for deriving the silence-time T, Amendment-4 style
R_est = current 2A stack (C(day) x mean TR of last 10 bars).

RUN: python3 Tests/P5_trade_management/p5_6_burst_silence_discrim.py      (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402
from p5_2_deoverlap_anatomy import leaders             # noqa: E402

TICK = 0.25
H = 1800
MIN_MFE = 2.0
SHARES = (0.008, 0.011, 0.014, 0.018, 0.022)


def auc(x_alive, x_dead):
    """AUC that silence is higher in DEAD seconds (rank-based)."""
    x = np.concatenate([x_alive, x_dead])
    y = np.concatenate([np.zeros(len(x_alive)), np.ones(len(x_dead))])
    r = pd.Series(x).rank().to_numpy()
    n1, n0 = len(x_dead), len(x_alive)
    if n1 == 0 or n0 == 0:
        return float("nan")
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n0 * n1))


def run(repo):
    c_day = X.c_day_fun(repo)
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
        led = leaders(X.fires_2a(P, np.asarray(cx.rth)), secs)
        R = P["_Cday"] * P["_atr10"]

        print(f"===== {m} =====")
        print("| Mini-burst share | AUC (silence -> dead) | median silence alive | dead "
              "| alive inter-burst gaps p50/p75/p90 (s) |")
        print("|---|---|---|---|---|")
        for s_share in SHARES:
            al, dd, gaps = [], [], []
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
                seg = slice(j1, j2)
                mv = P["_mv8"][seg]
                thr = s_share * R[seg]
                burst = (np.sign(mv) == d0) & (np.abs(mv) >= thr) & np.isfinite(thr)
                t = secs[seg] - s0
                last = np.zeros(len(t))
                lb = 0.0
                bt_prev = None
                for k in range(len(t)):
                    if burst[k]:
                        if bt_prev is not None and k <= kp:
                            gaps.append(t[k] - bt_prev)
                        bt_prev = t[k]
                        lb = t[k]
                    last[k] = t[k] - lb
                al.extend(last[:kp + 1]); dd.extend(last[kp + 1:])
            al = np.asarray(al); dd = np.asarray(dd); gaps = np.asarray(gaps)
            g = (f"{np.percentile(gaps,50):.0f}/{np.percentile(gaps,75):.0f}/"
                 f"{np.percentile(gaps,90):.0f}" if len(gaps) > 20 else "n<20")
            print(f"| {s_share:.3f} | {auc(al, dd):.3f} | {np.median(al):.0f} s "
                  f"| {np.median(dd):.0f} s | {g} |")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
