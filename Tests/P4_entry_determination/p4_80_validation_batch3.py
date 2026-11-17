#!/usr/bin/env python3
"""
p4_80_validation_batch3.py — P4.80 / Strategy 2: VALIDATION BATCH 3
(2021-09, 2024-11): the firing-gap rule + the 1-bar wait candidate.
====================================================================
Frozen from training (T-EN81/82, Amendment 4):
  configs: {ATR14D, INTRADAY10} x 2-min thrust window
  gap: 45 s (the rule's default - no trailing per-second data exists for
       these months, so this is the honest primary) AND the own-month
       half-drift-life value (DIAGNOSTIC - mildly self-referential, labeled)
  wait after exit: {1, 5} bars
Reference (T-EN79, gap 120 s / wait 5): ATR14D +89.4/+95.2;
INTRADAY10 +15.2/+61.5.
Everything else frozen as in batch 2. Per-second engine, v11 sketch, mid fills.

RUN: python3 Tests/P4_entry_determination/p4_80_validation_batch3.py      (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_66_context_ablation import prep, sim           # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402

TICK = 0.25
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
W = 2
MATCH_S = 120
VAL_MONTHS = ["2021-09", "2024-11"]
KS = (30, 60, 90, 120, 150, 180, 240, 300)


def drift_zc(P):
    secs, mids, keep = P["secs"], P["mids"], P["keep"]
    iw = np.searchsorted(secs, secs - 7)
    mv7 = (mids - mids[np.maximum(iw, 0)]) / TICK
    thr = np.percentile(np.abs(mv7)[keep], 99.5)
    idx = np.flatnonzero(keep & (np.abs(mv7) >= thr))
    sel = []; last = -10**18
    for i in idx:
        if secs[i] - last >= 30:
            sel.append(i); last = secs[i]
    sel = np.array(sel, dtype=int)
    means = []
    for K in KS:
        j = np.searchsorted(secs, secs[sel] + K, "right") - 1
        means.append(float(np.mean((mids[j] - mids[sel]) / TICK * np.sign(mv7[sel]))))
    for a in range(1, len(KS)):
        if means[a] <= 0 < means[a - 1]:
            f = means[a - 1] / (means[a - 1] - means[a])
            return KS[a - 1] + f * (KS[a] - KS[a - 1])
    return None


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    results = {}
    for month in VAL_MONTHS:
        P = prep(repo, month, insample=False)
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        zc = drift_zc(P)
        gap_own = int(np.clip((zc or 90) / 2, 30, 60))
        print(f"[{month}] own-month drift zero-crossing: "
              f"{'%.0f s' % zc if zc else 'none<=300s'} -> diagnostic gap {gap_own}s")
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        Rday = {d: atr14d(d) for d in set(P["sd"])}
        ret2 = np.concatenate([[0.0] * W, (cx.c[W:] - cx.c[:-W]) / TICK])
        lo, hi = month_bounds(month)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])
        for scheme in ("ATR14D", "INTRADAY10"):
            if scheme == "ATR14D":
                Rs = np.array([Rday.get(d) or np.nan for d in P["sd"]])[bar_i]
            else:
                Rs = C_N * atr10[bar_i]
            bt = BURST_SHARE * Rs
            for gname, gap in [("gap 45s (rule default)", 45),
                               (f"gap own-month rule", gap_own)]:
                kept = []
                last = -10**18
                for i in np.flatnonzero(keep & np.isfinite(bt)):
                    if abs(mv8[i]) < bt[i]:
                        continue
                    if secs[i] - last <= gap:
                        continue
                    last = secs[i]
                    ib = bar_i[i]
                    if ib < 60 or not cx.rth[ib]:
                        continue
                    d0 = int(np.sign(mv8[i]))
                    tthr = THRUST_SHARE * np.sqrt(W / 5) * Rs[i]
                    if np.isfinite(tthr) and d0 * ret2[ib] >= tthr:
                        kept.append((i, d0))
                for wait in (1, 5):
                    pnl = sim(P, kept, lambda *a: True, cooldown=wait)
                    matched = sum(1 for i, s in kept
                                  if ((np.abs(hs - int(secs[i])) <= MATCH_S) & (hd == s)).any())
                    a = np.asarray(pnl); wn = a > 0
                    dd0 = -min(0.0, float(np.min(np.cumsum(a)))) if len(a) else 0.0
                    results.setdefault(f"{scheme} | {gname} | wait {wait}", {})[month] = \
                        (len(a), matched, wn, a, dd0)
    print("\n| Config | " + " | ".join(
        f"{m}: trades / his / win% / total / DD" for m in VAL_MONTHS) + " | Worst month |")
    print("|---|---|---|---|")
    for name, per in results.items():
        cells = []; worst = None
        for m in VAL_MONTHS:
            n, matched, wn, a, dd0 = per[m]
            tot = a.sum() if n else 0.0
            worst = tot if worst is None else min(worst, tot)
            cells.append(f"{n} / {matched} / {wn.mean():.0%} / {tot:+.1f} / {dd0:.1f}"
                         if n else "0 trades")
        print(f"| {name} | " + " | ".join(cells) + f" | {worst:+.1f} |")
    print("\nReference (T-EN79, gap 120s / wait 5): ATR14D +89.4 / +95.2 | INTRADAY10 +15.2 / +61.5")
    print("HIS (all entries, as parsed): 2021-09 +477 (173 tr) | 2024-11 +450 (69 tr)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
