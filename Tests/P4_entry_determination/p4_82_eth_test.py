#!/usr/bin/env python3
"""
p4_82_eth_test.py — P4.82 / Strategy 2: the overnight (Globex) variant.
TRAINING MONTHS ONLY.
========================================================================
Lead settings frozen (2-min thrust, 45 s gap, 1-bar wait, shares 0.042/0.17),
applied to GLOBEX hours only. Per user instruction the day-range adapters use
the ETH range: ATR14D-ETH = trailing-14-session mean OVERNIGHT range;
INTRADAY10 unchanged (last-10-bars TR is naturally local). Positions are
flat before the RTH open and at the maintenance close (the session logic
exits a trade at the last Globex bar of its block). pt-ladder reference
(uref) stays the prior session's RTH median WRB body (noted).
HONESTY NOTE: overnight spreads are wider at thin hours, so mid fills
flatter these results MORE than RTH results.
Reference (same settings, RTH, T-EN84): ATR14D +362.2 | INTRADAY10 +272.8.

RUN: python3 Tests/P4_entry_determination/p4_82_eth_test.py               (repo root)
"""
import argparse, os, sys, types
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_49_sec_engine import leg_sec, V11              # noqa: E402
from p4_66_context_ablation import prep, row           # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
W, GAP, WAIT = 2, 45, 1
VAL = False


class CtxView:
    """cx with the allowed-session mask swapped (GLOBEX instead of RTH)."""
    def __init__(self, cx, mask):
        for k in ("bts", "bsec", "c", "h", "l", "o", "sd", "secs", "mids", "pre"):
            if hasattr(cx, k):
                setattr(self, k, getattr(cx, k))
        self.rth = mask
        self._cx = cx

    def bar_of(self, s):
        return self._cx.bar_of(s)


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d_eth(d):
        i = pos.get(d)
        if not i or i <= 0:
            return None
        v = SH.on.iloc[max(0, i - 14):i].dropna()
        return float(v.mean()) if len(v) else None

    per_m = {"ATR14D-ETH": {}, "INTRADAY10": {}}
    month_list = [(m, True) for m, _ in MONTHS] if not VAL else \
                 [("2021-09", False), ("2024-11", False)]
    for m, insample in month_list:
        P = prep(repo, m, insample=insample)
        cx = P["cx"]
        bars = cx.bars
        glbx = (bars.session == "GLOBEX").to_numpy()
        secs, mids = P["secs"], P["mids"]
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        lo, hi = month_bounds(m)
        keep_eth = glbx[bar_i] & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        Reth = {d: atr14d_eth(d) for d in set(P["sd"])}
        ret2 = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        view = CtxView(cx, glbx)
        from p4_31_profit_v9 import wrb_flags
        view.pre = wrb_flags(bars)
        wmed = P.get("prevd") or {}
        for scheme in ("ATR14D-ETH", "INTRADAY10"):
            if scheme == "ATR14D-ETH":
                Rs = np.array([Reth.get(d) or np.nan for d in P["sd"]])[bar_i]
            else:
                Rs = C_N * atr10[bar_i]
            bt = BURST_SHARE * Rs
            pnl = []
            busy = -1
            last = -10**18
            for i in np.flatnonzero(keep_eth & np.isfinite(bt)):
                if abs(mv8[i]) < bt[i]:
                    continue
                if secs[i] - last <= GAP:
                    continue
                last = int(secs[i])
                ib = bar_i[i]
                if ib < 60 or not glbx[ib] or ib <= busy:
                    continue
                d0 = int(np.sign(mv8[i]))
                tthr = THRUST_SHARE * np.sqrt(W / 5) * Rs[i]
                if not (np.isfinite(tthr) and d0 * ret2[ib] >= tthr):
                    continue
                fill = float(mids[i]); long = d0 > 0
                px, xs, xb, reason = leg_sec(view, ib, fill, int(secs[i]), long, V11, None)
                tot = (px - fill) if long else (fill - px)
                if reason == "faststop":
                    px2, xs2, xb2, _ = leg_sec(view, xb, px, xs, not long, V11, None)
                    tot += (px2 - px) if (not long) else (px - px2)
                    xb = xb2
                pnl.append(tot)
                busy = xb + WAIT
            per_m[scheme][m] = pnl
    print("GLOBEX HOURS ONLY, training months. Flat before the RTH open and at the")
    print("maintenance close. ETH-range adapters per user instruction. Mid fills -")
    print("MORE optimistic overnight than in RTH (wider spreads at thin hours).\n")
    print("| Config | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for scheme, pm in per_m.items():
        print(row(f"{scheme}, Globex only", pm))
    print("| RTH reference (T-EN84): ATR14D +362.2 (269 tr, 57%) | INTRADAY10 +272.8 (105 tr, 69%) |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--val", action="store_true",
                    help="run on the reserved months (2021-09, 2024-11) instead")
    a = ap.parse_args()
    if a.val:
        VAL = True
        print("VALIDATION MONTHS (frozen settings, first overnight look)\n")
    run(a.repo)
