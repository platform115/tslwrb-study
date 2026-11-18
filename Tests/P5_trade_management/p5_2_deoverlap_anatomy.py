#!/usr/bin/env python3
"""
p5_2_deoverlap_anatomy.py — P5.2 / Management phase: excursion anatomy on
DE-OVERLAPPED fires (the charter's realistic baseline). TRAINING MONTHS ONLY.
===============================================================================
T-EX02 counted every gap-deduped fire, so several fires riding one move
double-counted that move's path. Realistic correction (stated rule, flagged):
an EPISODE LEADER is a fire with no same-direction fire in the prior 10
minutes; only leaders are measured. 10 min = the move-development window from
T-EX02 (median peaks 16-19 min; adverse resolution inside 10 min). Opposite-
direction fires start new episodes (a reversal is a new situation).
Fill note (charter bracket rule): entries here are at the fire-second mid;
an entry 1 tick against shifts EVERY points figure down by exactly 0.25 -
a constant, printed rather than duplicated as a second table.
All other measurement definitions identical to p5_1 (30-min horizon capped
at session block end; points, + = favorable).

RUN: python3 Tests/P5_trade_management/p5_2_deoverlap_anatomy.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
P4 = os.path.join(os.path.dirname(HERE), "P4_entry_determination")
sys.path.insert(0, HERE); sys.path.insert(0, P4)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_66_context_ablation import prep                # noqa: E402
import p5_1_excursion_anatomy as X                     # noqa: E402

TICK = 0.25
LEAD_WIN = 600


def leaders(kept, secs):
    out = []
    last_by_dir = {1: -10**18, -1: -10**18}
    for i, d0 in kept:
        s0 = int(secs[i])
        if s0 - last_by_dir[d0] > LEAD_WIN:
            out.append((i, d0))
        last_by_dir[d0] = s0
    return out


def report(tag, A):
    if not len(A):
        print(f"-- {tag}: no fires\n"); return
    q = lambda v, p: float(np.percentile(v, p))
    rows = [("Best reached in 30 min (pts)", A[:, 0]),
            ("Worst against in 30 min (pts)", A[:, 1]),
            ("Minutes to the favorable peak", A[:, 2] / 60),
            ("Standing at 30 min (pts)", A[:, 3]),
            ("Best before 1 pt against", A[:, 4]),
            ("Best before 2 pts against", A[:, 5]),
            ("Best before 3 pts against", A[:, 6])]
    print(f"### {tag}")
    print("| Measure | 25th | median | 75th | 90th | mean |")
    print("|---|---|---|---|---|---|")
    for name, v in rows:
        print(f"| {name} | {q(v,25):+.2f} | {q(v,50):+.2f} | {q(v,75):+.2f} "
              f"| {q(v,90):+.2f} | {v.mean():+.2f} |")
    print(f"| Reaches +1 pt before -1 pt | {A[:,7].mean():.0%} of episodes | | | | |")
    print()


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
        sd_sec = np.asarray(P["sd"])[bar_i]
        typ = np.where(glbx[bar_i], 1, 0)
        blk = pd.Series(list(zip(sd_sec, typ)))
        blk_id = np.cumsum((blk != blk.shift(1)).to_numpy())
        end_by_id = pd.Series(secs).groupby(blk_id).transform("max").to_numpy()
        print(f"===== {m} (episode leaders only; same-direction 10-min rule) =====")
        for tag, base, allow in [("RTH", P["keep"], np.asarray(cx.rth)),
                                 ("OVERNIGHT", in_month, glbx)]:
            P["_base_keep"] = base
            kept = X.fires_2a(P, allow)
            led = leaders(kept, secs)
            print(f"[{tag}] fires {len(kept)} -> episode leaders {len(led)}")
            report(f"{m} {tag} - de-overlapped", X.anatomy(P, led, end_by_id))
    print("Fill bracket (charter rule): entry 1 tick against shifts every "
          "points figure DOWN by exactly 0.25; percentages unchanged except "
          "near thresholds.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
