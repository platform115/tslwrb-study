#!/usr/bin/env python3
"""
p4_85_burst_share_derivation.py — P4.85 / Strategy 2: deriving the BURST SHARE.
TRAINING MONTHS ONLY.
===============================================================================
The P&L surface (T-EN90) turns at burst share ~0.018-0.022 (ATR14D) / 0.022
(INTRADAY10). The frozen 0.042 was a transcription of the old fixed 50-tick
threshold, not a derivation. Question: does the turn region sit at a STABLE
percentile of the per-8s move distribution in both training months?

Method: on the kept per-second grid (same mask as the detector), form
    q = |8-s move| / R_est          (R_est per scheme, per second)
Then share s corresponds to the percentile P(q < s). If 0.018-0.022 lands at
the same percentile in 2025-10 (quiet) and 2022-02 (wild), that percentile is
the adaptive rule and the share stops being a static number.
HONESTY NOTE: this derivation is reverse-engineered FROM a P&L-chosen region,
so it is weaker than the window derivations (which came from independent
market structure). Instability across the two months = fail, not patchable.

Outputs per month x scheme:
  (a) percentile of q at each share in the grid + the old frozen 0.042
  (b) inverse: the share at fixed round percentiles (stability check)
  (c) the threshold in ticks at 0.018/0.022 (intuition only)

RUN: python3 Tests/P4_entry_determination/p4_85_burst_share_derivation.py  (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
C_N = 22.7
SHARES = (0.014, 0.018, 0.022, 0.026, 0.030, 0.042)
PCTS = (97.0, 98.0, 98.5, 99.0, 99.25, 99.5, 99.75)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        iw = np.searchsorted(secs, secs - 8)
        mv8 = np.abs(mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        Rday = {d: atr14d(d) for d in set(P["sd"])}
        print(f"===== {m} =====")
        for scheme in ("ATR14D", "INTRADAY10"):
            if scheme == "ATR14D":
                Rs = np.array([Rday.get(d) or np.nan for d in P["sd"]])[bar_i]
            else:
                Rs = C_N * atr10[bar_i]
            ok = keep & np.isfinite(Rs) & (Rs > 0)
            q = mv8[ok] / Rs[ok]
            med_R = float(np.median(Rs[ok]))
            print(f"-- {scheme}: {ok.sum()} kept seconds, median R_est {med_R:.0f} ticks")
            print("| share | percentile of q | threshold at median R (ticks) |")
            print("|---|---|---|")
            for s in SHARES:
                pct = float((q < s).mean()) * 100
                tag = " <= old frozen" if s == 0.042 else ""
                print(f"| {s:.3f}{tag} | {pct:.2f}% | {s * med_R:.1f} |")
            print("| pct -> share | " + " | ".join(f"{p:g}" for p in PCTS) + " |")
            print("| share at pct | " + " | ".join(
                f"{np.percentile(q, p):.4f}" for p in PCTS) + " |")
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
