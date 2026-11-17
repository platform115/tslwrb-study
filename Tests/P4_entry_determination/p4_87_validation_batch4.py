#!/usr/bin/env python3
"""
p4_87_validation_batch4.py — P4.87 / Strategy 2: VALIDATION BATCH 4
(2021-09, 2024-11): the Amendment-5 pool, frozen before this run.
====================================================================
User-authorized 2026-11-17. Configs (gap 45 s, 1-bar wait, all else frozen):
  control  : ATR14D static burst share 0.018, thrust 0.15
  ATR lane : burst = trailing 85th pct of raw |8-s move| (expanding in-month,
             min 1 prior session - the T-EN92 tested form; no pre-month
             per-second data exists), thrust {0.13, 0.15} x ATR14D
  INTRADAY : burst share 0.022 (derived, T-EN91), thrust {0.17, 0.19, 0.21}
  RTH60    : shares {0.014, 0.018}, thrust 0.15 (own R_est for both legs)
  DAYSOFAR : shares {0.014, 0.018}, thrust 0.15 (own R_est for both legs)
Training references (T-EN90/92) printed in the footer.
Per-second engine, v11 exit sketch, mid fills.

RUN: python3 Tests/P4_entry_determination/p4_87_validation_batch4.py      (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_66_context_ablation import prep, sim           # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402
from p4_86_atr_lane_adapt import day_sofar_R, rth60_R  # noqa: E402

TICK = 0.25
C_N = 22.7
W, GAP, WAIT = 2, 45, 1
VAL_MONTHS = ["2021-09", "2024-11"]


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {}
    for m in VAL_MONTHS:
        P = prep(repo, m, insample=False)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        P["_Ratr"] = np.array([{d: atr14d(d) for d in set(P["sd"])}.get(d) or np.nan
                               for d in P["sd"]])[bar_i]
        P["_Rint"] = C_N * atr10[bar_i]
        P["_Rday_sofar"] = day_sofar_R(np.asarray(P["sd"]), tr, np.asarray(cx.rth))[bar_i]
        P["_Rrth60"] = rth60_R(np.asarray(P["sd"]), tr, np.asarray(cx.rth))[bar_i]
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        P["_sd_sec"] = np.asarray(P["sd"])[bar_i]
        Ps[m] = P

    def fires(P, bt, Rthr, tsh):
        cx = P["cx"]
        secs, keep = P["secs"], P["keep"]
        kept = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(bt) & np.isfinite(Rthr)):
            if abs(P["_mv8"][i]) < bt[i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = P["_bar_i"][i]
            if ib < 60 or not cx.rth[ib]:
                continue
            d0 = int(np.sign(P["_mv8"][i]))
            if d0 * P["_ret2"][ib] >= tsh * np.sqrt(W / 5) * Rthr[i]:
                kept.append((i, d0))
        return kept

    def trail85(P):
        secs, keep = P["secs"], P["keep"]
        sd = P["_sd_sec"]
        days = pd.unique(sd[keep])
        thr = np.full(len(secs), np.nan)
        for k, d in enumerate(days):
            prior = keep & np.isin(sd, days[:k])
            if not prior.any():
                continue
            thr[sd == d] = float(np.percentile(np.abs(P["_mv8"])[prior], 85))
        return thr

    cfgs = [
        ("control: ATR14D static 0.018, thrust 0.15",
         lambda P: (0.018 * P["_Ratr"], P["_Ratr"], 0.15)),
        ("ATR lane: trail-pct85 raw ticks, thrust 0.13",
         lambda P: (trail85(P), P["_Ratr"], 0.13)),
        ("ATR lane: trail-pct85 raw ticks, thrust 0.15",
         lambda P: (trail85(P), P["_Ratr"], 0.15)),
        ("INTRADAY10 0.022, thrust 0.17",
         lambda P: (0.022 * P["_Rint"], P["_Rint"], 0.17)),
        ("INTRADAY10 0.022, thrust 0.19",
         lambda P: (0.022 * P["_Rint"], P["_Rint"], 0.19)),
        ("INTRADAY10 0.022, thrust 0.21",
         lambda P: (0.022 * P["_Rint"], P["_Rint"], 0.21)),
        ("RTH60 0.014, thrust 0.15",
         lambda P: (0.014 * P["_Rrth60"], P["_Rrth60"], 0.15)),
        ("RTH60 0.018, thrust 0.15",
         lambda P: (0.018 * P["_Rrth60"], P["_Rrth60"], 0.15)),
        ("DAYSOFAR 0.014, thrust 0.15",
         lambda P: (0.014 * P["_Rday_sofar"], P["_Rday_sofar"], 0.15)),
        ("DAYSOFAR 0.018, thrust 0.15",
         lambda P: (0.018 * P["_Rday_sofar"], P["_Rday_sofar"], 0.15)),
    ]
    print("VALIDATION MONTHS (2021-09, 2024-11) - Amendment-5 pool, frozen "
          "before this run. Gap 45 s, 1-bar wait.\n")
    print("| Config | " + " | ".join(
        f"{m}: trades / win% / total / max below start" for m in VAL_MONTHS)
        + " | Worst month |")
    print("|---|" + "---|" * (len(VAL_MONTHS) + 1))
    for name, f in cfgs:
        cells = []; worst = None
        for m in VAL_MONTHS:
            P = Ps[m]
            bt, Rthr, tsh = f(P)
            a = np.asarray(sim(P, fires(P, bt, Rthr, tsh), lambda *x: True,
                               cooldown=WAIT))
            tot = float(a.sum()) if len(a) else 0.0
            dd0 = -min(0.0, float(np.min(np.cumsum(a)))) if len(a) else 0.0
            worst = tot if worst is None else min(worst, tot)
            cells.append(f"{len(a)} / {(a > 0).mean():.0%} / {tot:+.1f} / {dd0:.1f}"
                         if len(a) else "0 trades")
        print(f"| {name} | " + " | ".join(cells) + f" | {worst:+.1f} |")
    print("\nTraining references (both months pooled, T-EN90/92): "
          "ATR static 0.018/0.15 +742.8 (62%/478) | ATR trail-pct85/0.15 "
          "+762.9 (64%/460) | INTRADAY 0.022/0.17 +404 (72%/160), /0.19 +316 "
          "(74%/103), /0.21 +252 (76%/68) | RTH60 0.014 +452.9 (69%/237), "
          "0.018 +414.2 (69%/234) | DAYSOFAR 0.014 +380.2 (68%/185), 0.018 "
          "+378.8 (66%/182)")
    print("Prior validated lead (T-EN83, shares 0.042/0.17): ATR14D "
          "+140.0/+103.5.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
