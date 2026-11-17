#!/usr/bin/env python3
"""
p4_89_cn_adaptive.py — P4.89 / Strategy 2: C_N constant vs MEASURED-RATIO.
TRAINING MONTHS ONLY (--val for the reserved months).
===============================================================================
C_N converts the 10-bar mean minute-TR into a day-range estimate. Frozen at
22.7. At fixed shares a different CONSTANT is trade-for-trade identical to
rescaling the shares (already mapped), so the only real variant is adaptive:
    C(day) = mean(trailing 14 sessions' RTH day range)
             / mean(trailing 14 sessions' mean RTH minute-TR)
(ratio of trailing means, matching the ATR14D style). Sessions from the full
front series; roll days excluded where flagged. Applied in the QUALITY LANE
(the adopted volume lane does not use C_N): INTRADAY10, burst share 0.022,
thrust 0.17, 45 s gap, 1-bar wait. Expectation stated up front: if the ratio
is as stable as the yearly measurements, adaptive ~ constant, and that match
is the result (dial confirmed insensitive).

RUN: python3 Tests/P4_entry_determination/p4_89_cn_adaptive.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402

TICK = 0.25
C0 = 22.7
W, GAP, WAIT = 2, 45, 1
BSH, TSH = 0.022, 0.17
NSESS = 14


def session_ratio_table(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    if "is_roll_day" in es.columns:
        es = es[~es.is_roll_day]
    es = es.sort_values("ts_event")
    pc = es.close.shift(1)
    tr = np.maximum(es.high - es.low,
                    np.maximum((es.high - pc).abs(), (es.low - pc).abs())) / TICK
    es = es.assign(_tr=tr, _sd=es.session_date.astype(str))
    r = es[es.session == "RTH"].groupby("_sd").agg(
        rng=("high", "max"), lo=("low", "min"), mtr=("_tr", "mean"))
    r["rng"] = (r.rng - r.lo) / TICK
    return r[["rng", "mtr"]].sort_index()


def run(repo, val=False):
    month_list = [(m, True) for m, _ in MONTHS] if not val else \
                 [("2021-09", False), ("2024-11", False)]
    RT = session_ratio_table(repo)
    dates = list(RT.index)
    pos = {d: i for i, d in enumerate(dates)}

    def c_day(d):
        i = pos.get(d)
        if not i or i <= 0:
            return None
        w = RT.iloc[max(0, i - NSESS):i]
        return float(w.rng.mean() / w.mtr.mean()) if len(w) and w.mtr.mean() > 0 else None

    Ps = {}
    for m, insample in month_list:
        P = prep(repo, m, insample=insample)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        iw = np.searchsorted(secs, secs - 8)
        P["_mv8"] = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        P["_bar_i"] = bar_i
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        P["_atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()[bar_i]
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        cds = {d: c_day(d) for d in set(P["sd"])}
        P["_Cday"] = np.array([cds.get(d) or np.nan for d in P["sd"]])[bar_i]
        got = sorted(v for v in cds.values() if v)
        print(f"[{m}] measured C(day): min {got[0]:.1f}, median "
              f"{np.median(got):.1f}, max {got[-1]:.1f}  (frozen constant {C0})")
        Ps[m] = P

    def fires(P, Cs):
        cx = P["cx"]
        secs, keep = P["secs"], P["keep"]
        R = Cs * P["_atr10"]
        bt = BSH * R
        kept = []
        last = -10**18
        for i in np.flatnonzero(keep & np.isfinite(bt)):
            if abs(P["_mv8"][i]) < bt[i]:
                continue
            if secs[i] - last <= GAP:
                continue
            last = int(secs[i])
            ib = P["_bar_i"][i]
            if ib < 60 or not cx.rth[ib]:
                continue
            d0 = int(np.sign(P["_mv8"][i]))
            if d0 * P["_ret2"][ib] >= TSH * np.sqrt(W / 5) * R[i]:
                kept.append((i, d0))
        return kept

    print("\nQuality lane (INTRADAY10, burst 0.022, thrust 0.17, gap 45, wait 1).")
    print("| C_N form | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for name, f in [("constant 22.7 (baseline)", lambda P: np.full(len(P["secs"]), C0)),
                    (f"C(day) = trailing-{NSESS}-session measured ratio",
                     lambda P: P["_Cday"])]:
        per_m = {m: sim(Ps[m], fires(Ps[m], f(Ps[m])), lambda *a: True, cooldown=WAIT)
                 for m in Ps}
        print(row(name, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--val", action="store_true",
                    help="run on the reserved months (2021-09, 2024-11)")
    a = ap.parse_args()
    if a.val:
        print("VALIDATION MONTHS - settings frozen\n")
    run(a.repo, val=a.val)
