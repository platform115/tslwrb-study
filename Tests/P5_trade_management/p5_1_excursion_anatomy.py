#!/usr/bin/env python3
"""
p5_1_excursion_anatomy.py — P5.1 / Management phase: EXCURSION ANATOMY after
Strategy 2A fires. TRAINING MONTHS ONLY.
===============================================================================
Charter step 1. No trades, no exits, no P&L: for every 2A fire (current
stack: burst 0.022 x R_est, thrust 0.17, R_est = C(day) x mean TR of last 10
bars, 45 s gap), track the per-second price path forward and measure what
there is to capture. Fires are gap-deduped signals, NOT positions (no
wait-after-exit — that is a trade construct; noted for count comparisons).

Measured per fire, horizon H = 30 min (capped at the session block's end),
in POINTS, signed so + is favorable to the fire's direction:
  MFE/MAE within H; final value at H; time to the favorable peak;
  MFE before the path first goes 1 / 2 / 3 points adverse;
  which comes first, +1 pt or -1 pt; "non-mover" shares under several
  definitions (never +/-0.5, 1, 1.5 pt within 10 min) - thresholds REPORTED
  across choices, not chosen.
RTH and OVERNIGHT fires measured separately (the charter's RTH-vs-ETH
question). Overnight fires use the SAME current 2A stack; note: C(day) is an
RTH-measured ratio applied overnight here for consistency with the adopted
lane - a stated choice, the constant-22.7 alternative can be compared later.

RUN: python3 Tests/P5_trade_management/p5_1_excursion_anatomy.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
from p4_89_cn_adaptive import session_ratio_table, NSESS  # noqa: E402

TICK = 0.25
W, GAP = 2, 45
BSH, TSH = 0.022, 0.17
H = 1800          # 30-min horizon, seconds
NM_WIN = 600      # non-mover observation window, seconds


def c_day_fun(repo):
    RT = session_ratio_table(repo)
    dates = list(RT.index)
    pos = {d: i for i, d in enumerate(dates)}

    def c_day(d):
        i = pos.get(d)
        if not i or i <= 0:
            return None
        w = RT.iloc[max(0, i - NSESS):i]
        return float(w.rng.mean() / w.mtr.mean()) if len(w) and w.mtr.mean() > 0 else None
    return c_day


def fires_2a(P, allow_mask):
    """2A fires on seconds where allow_mask (per bar) is True."""
    cx = P["cx"]
    secs, keep = P["secs"], P["keep"]
    R = P["_Cday"] * P["_atr10"]
    bt = BSH * R
    kept = []
    last = -10**18
    base = P["_base_keep"]
    for i in np.flatnonzero(base & np.isfinite(bt)):
        if abs(P["_mv8"][i]) < bt[i]:
            continue
        if secs[i] - last <= GAP:
            continue
        last = int(secs[i])
        ib = P["_bar_i"][i]
        if ib < 60 or not allow_mask[ib]:
            continue
        d0 = int(np.sign(P["_mv8"][i]))
        if d0 * P["_ret2"][ib] >= TSH * np.sqrt(W / 5) * R[i]:
            kept.append((i, d0))
    return kept


def anatomy(P, kept, block_end_sec):
    """Per-fire forward path measurements. block_end_sec: per-second array of
    the last second of the fire's session block (path capped there)."""
    secs, mids = P["secs"], P["mids"]
    out = []
    for i, d0 in kept:
        s0 = int(secs[i]); f0 = float(mids[i])
        send = min(s0 + H, int(block_end_sec[i]))
        j1 = np.searchsorted(secs, s0, "right")
        j2 = np.searchsorted(secs, send, "right")
        if j2 - j1 < 10:
            continue
        path = (mids[j1:j2] - f0) * d0 / 1.0          # price units
        path_pts = path / 1.0                          # ES: price units ARE points
        t = secs[j1:j2] - s0
        mfe = float(path_pts.max()); mae = float(-path_pts.min())
        tpk = int(t[int(np.argmax(path_pts))])
        fin = float(path_pts[-1])
        # MFE before first -1/-2/-3 pts adverse
        row = [mfe, mae, tpk, fin]
        for a in (1.0, 2.0, 3.0):
            hit = np.flatnonzero(path_pts <= -a)
            row.append(float(path_pts[:hit[0]].max()) if len(hit) and hit[0] > 0
                       else (0.0 if len(hit) else mfe))
        # +1 before -1?
        up = np.flatnonzero(path_pts >= 1.0); dn = np.flatnonzero(path_pts <= -1.0)
        row.append(1 if len(up) and (not len(dn) or up[0] < dn[0]) else 0)
        # non-mover flags within NM_WIN
        w = path_pts[t <= NM_WIN]
        for a in (0.5, 1.0, 1.5):
            row.append(1 if len(w) and np.abs(w).max() < a else 0)
        out.append(row)
    return np.array(out)


def report(tag, A):
    if not len(A):
        print(f"-- {tag}: no fires"); return
    q = lambda v, p: float(np.percentile(v, p))
    mfe, mae, tpk, fin = A[:, 0], A[:, 1], A[:, 2], A[:, 3]
    b1, b2, b3 = A[:, 4], A[:, 5], A[:, 6]
    upfirst = A[:, 7]
    nm = A[:, 8:11]
    print(f"-- {tag}: {len(A)} fires")
    print("|  | 25th pct | median | 75th | 90th | mean |")
    print("|---|---|---|---|---|---|")
    for name, v in [("Best reached in 30 min (MFE, pts)", mfe),
                    ("Worst against in 30 min (MAE, pts)", mae),
                    ("Minutes to the favorable peak", tpk / 60),
                    ("Where it stands at 30 min (pts)", fin),
                    ("Best reached BEFORE 1 pt against", b1),
                    ("Best reached BEFORE 2 pts against", b2),
                    ("Best reached BEFORE 3 pts against", b3)]:
        print(f"| {name} | {q(v,25):+.2f} | {q(v,50):+.2f} | {q(v,75):+.2f} "
              f"| {q(v,90):+.2f} | {v.mean():+.2f} |")
    print(f"| Reaches +1 pt before -1 pt | {upfirst.mean():.0%} of fires |")
    print(f"| Non-mover in first 10 min (never +/-0.5 / 1 / 1.5 pt) | "
          f"{nm[:,0].mean():.0%} / {nm[:,1].mean():.0%} / {nm[:,2].mean():.0%} |")


def run(repo):
    c_day = c_day_fun(repo)
    for m, _ in MONTHS:
        P = prep(repo, m)
        cx = P["cx"]
        bars = cx.bars
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
        P["_ret2"] = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        glbx = (bars.session == "GLOBEX").to_numpy()
        lo, hi = month_bounds(m)
        in_month = (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        # session-block end second per sample: last second whose bar stays in
        # the same session type and same session date
        sd_sec = np.asarray(P["sd"])[bar_i]
        typ = np.where(glbx[bar_i], 1, 0)
        blk = pd.Series(list(zip(sd_sec, typ)))
        new_blk = (blk != blk.shift(1)).to_numpy()
        blk_id = np.cumsum(new_blk)
        end_by_id = pd.Series(secs).groupby(blk_id).transform("max").to_numpy()
        print(f"===== {m} =====")
        # RTH
        P["_base_keep"] = P["keep"]
        k_rth = fires_2a(P, np.asarray(cx.rth))
        report("RTH fires (2A current stack)", anatomy(P, k_rth, end_by_id))
        # OVERNIGHT (current stack refresh)
        P["_base_keep"] = in_month
        k_on = fires_2a(P, glbx)
        report("OVERNIGHT fires (2A current stack, C(day) applied as stated)",
               anatomy(P, k_on, end_by_id))
        print()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
