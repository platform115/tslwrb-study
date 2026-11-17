#!/usr/bin/env python3
"""
p4_83_signal_reaudit.py — P4.83 / Strategy 2: the old-signal requirement
RE-AUDITIONED under the adaptive stack, with the TBBO speed conditions broken
out. TRAINING MONTHS ONLY.
=============================================================================
The T-EN68 verdict (signal requirement costs money) predates every current
setting - this is its retrial under the lead configs (ATR14D / INTRADAY10,
2-min thrust, 45 s gap, 1-bar wait). Gates tested on each burst fire:
  none (reference) | any score>=6 signal in prior 5 min | same-direction
  signal | same-dir score >= 7 | >= 8 |
  FLOW SPEED alone: signed volume toward the trade > 2.0 contracts/s over the
  last 5 min | flow speed AND not exhausted (15-min rate <= 4.6 c/s)
Flow rates = (buy - sell volume) summed over the window / window seconds,
signed toward the trade direction (plain definition, stated).

RUN: python3 Tests/P4_entry_determination/p4_83_signal_reaudit.py         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_66_context_ablation import prep, sim, row      # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
W, GAP, WAIT = 2, 45, 1


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    kept_all = {}
    for m, P in Ps.items():
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{m}_full.parquet"))
        sv = (f.buyv - f.sellv).to_numpy(float)
        csv_ = np.concatenate([[0.0], np.cumsum(sv)])
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        Rday = {d: atr14d(d) for d in set(P["sd"])}
        ret2 = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        sg = cx.sig[cx.sig.score >= 6]
        sig_s = sg.comp_ns.to_numpy(np.int64) // 10**9
        sig_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
        sig_sc = sg.score.to_numpy()
        oo = np.argsort(sig_s); sig_s, sig_d, sig_sc = sig_s[oo], sig_d[oo], sig_sc[oo]
        for scheme in ("ATR14D", "INTRADAY10"):
            if scheme == "ATR14D":
                Rs = np.array([Rday.get(d) or np.nan for d in P["sd"]])[bar_i]
            else:
                Rs = C_N * atr10[bar_i]
            bt = BURST_SHARE * Rs
            kept = []
            last = -10**18
            for i in np.flatnonzero(keep & np.isfinite(bt)):
                if abs(mv8[i]) < bt[i]:
                    continue
                if secs[i] - last <= GAP:
                    continue
                last = int(secs[i])
                ib = bar_i[i]
                if ib < 60 or not cx.rth[ib]:
                    continue
                d0 = int(np.sign(mv8[i]))
                tthr = THRUST_SHARE * np.sqrt(W / 5) * Rs[i]
                if not (np.isfinite(tthr) and d0 * ret2[ib] >= tthr):
                    continue
                s0 = int(secs[i])
                a2, b2 = np.searchsorted(sig_s, s0 - 300), np.searchsorted(sig_s, s0, side="right")
                any_sig = b2 > a2
                same = bool((sig_d[a2:b2] == d0).any())
                best = float(sig_sc[a2:b2][sig_d[a2:b2] == d0].max()) if same else 0.0
                i300, i900 = np.searchsorted(secs, s0 - 300), np.searchsorted(secs, s0 - 900)
                i1 = np.searchsorted(secs, s0, "right")
                fl5 = d0 * (csv_[i1] - csv_[i300]) / 300.0
                fl15 = d0 * (csv_[i1] - csv_[i900]) / 900.0
                kept.append((i, d0, any_sig, same, best, fl5, fl15))
            kept_all[(m, scheme)] = kept

    gates = [
        ("none (reference)", lambda a, s, b, f5, f15: True),
        ("any score>=6 signal, prior 5 min", lambda a, s, b, f5, f15: a),
        ("same-direction signal", lambda a, s, b, f5, f15: s),
        ("same-dir score >= 7", lambda a, s, b, f5, f15: b >= 7),
        ("same-dir score >= 8", lambda a, s, b, f5, f15: b >= 8),
        ("flow speed > 2 c/s (5 min)", lambda a, s, b, f5, f15: f5 > 2.0),
        ("flow > 2 AND not exhausted (15m <= 4.6)", lambda a, s, b, f5, f15: f5 > 2.0 and f15 <= 4.6),
    ]
    for scheme in ("ATR14D", "INTRADAY10"):
        print(f"===== {scheme} + current lead settings =====")
        print("| Gate | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
        print("|---|---|---|---|---|---|")
        for name, g in gates:
            per_m = {}
            for m, P in Ps.items():
                sel = [(i, d0) for i, d0, a, s, b, f5, f15 in kept_all[(m, scheme)]
                       if g(a, s, b, f5, f15)]
                per_m[m] = sim(P, sel, lambda *x: True, cooldown=WAIT)
            print(row(name, per_m))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
