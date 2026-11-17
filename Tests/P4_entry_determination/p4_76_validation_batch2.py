#!/usr/bin/env python3
"""
p4_76_validation_batch2.py — P4.76 / Strategy 2: AUTHORIZED VALIDATION BATCH 2
(2021-09, 2024-11): D1 with the adaptive stack, especially INTRADAY.
===============================================================================
Six frozen configs, nothing tuned after training:
  scheme in {ATR14D, INTRADAY10}  (burst 0.042 x R_est, 8 s window)
  x window rule in {static w=2 | rolling N=30, w in [1,4] (Amendment 3) |
                    21-session rule, w clamped [2,3] (Amendment 2)}
  thrust threshold = 0.17 x sqrt(w/5) x R_est, w live per rule.
21-session rule input: directional run lengths pooled over the trailing 21
RTH sessions from the full front-month series (reaches before month start).
All else frozen: direction = burst sign, no signal, no session cut, 120 s
clustering, 5-bar cooldown, v11 sketch management, mid fills.
Reference lines (already validated, T-EN75, w=5): ATR14D +26.2/+28.0;
INTRADAY10 +4.9/+34.1.

RUN: python3 Tests/P4_entry_determination/p4_76_validation_batch2.py      (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_66_context_ablation import prep, sim           # noqa: E402
from p4_69_adaptation_plan import session_history      # noqa: E402
from p4_75_rolling_window import rolling_window_series  # noqa: E402

TICK = 0.25
CLUST, MATCH_S = 120, 120
BURST_SHARE, THRUST_SHARE, C_N = 0.042, 0.17, 22.7
VAL_MONTHS = ["2021-09", "2024-11"]


def sess_w21(repo):
    """Per session: w = clamp(75th-pct run length pooled over trailing 21 sessions, 2, 3)."""
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    r = es[es.session == "RTH"].sort_values("ts_event")
    sd = r.session_date.astype(str).to_numpy()
    sgn = np.sign(r.close.diff().fillna(0).to_numpy())
    runs_by_sess = {}
    cur = 0; last = 0; cs = None
    for i in range(len(sd)):
        if sd[i] != cs:
            if cur and cs is not None:
                runs_by_sess.setdefault(cs, []).append(cur)
            cs = sd[i]; cur = 0; last = 0
        s = sgn[i]
        if s != 0 and s == last:
            cur += 1
        elif s != 0:
            if cur:
                runs_by_sess.setdefault(cs, []).append(cur)
            cur = 1; last = s
    sessions = sorted(runs_by_sess)
    w21 = {}
    for j, s_ in enumerate(sessions):
        pool = sum((runs_by_sess[x] for x in sessions[max(0, j - 21):j]), [])
        w21[s_] = int(np.clip(np.ceil(np.percentile(pool, 75)), 2, 3)) if pool else 2
    return w21


def run(repo):
    SH = session_history(repo)
    dates = list(SH.index)
    pos = {d: i for i, d in enumerate(dates)}

    def atr14d(d):
        i = pos.get(d)
        return float(SH.rth.iloc[max(0, i - 14):i].mean()) if i and i > 0 else None

    W21 = sess_w21(repo)
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    results = {}
    for month in VAL_MONTHS:
        P = prep(repo, month, insample=False)
        cx = P["cx"]
        secs, mids, keep = P["secs"], P["mids"], P["keep"]
        iw = np.searchsorted(secs, secs - 8)
        mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
        bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
        pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
        tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
        atr10 = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()
        Rday = {d: atr14d(d) for d in set(P["sd"])}
        retw = {w: np.concatenate([[0.0] * w, (cx.c[w:] - cx.c[:-w]) / TICK])
                for w in (1, 2, 3, 4)}
        wroll = rolling_window_series(cx, 30, 1, 4)
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
            fl = []; last = -10**18
            for i in np.flatnonzero(keep & np.isfinite(bt)):
                if abs(mv8[i]) < bt[i]:
                    continue
                if secs[i] - last > CLUST:
                    fl.append(i); last = secs[i]
            for wrule in ("static w=2", "rolling N=30 [1,4]", "21-session [2,3]"):
                kept = []
                for i in fl:
                    ib = bar_i[i]
                    if ib < 60 or not cx.rth[ib]:
                        continue
                    d0 = int(np.sign(mv8[i]))
                    if wrule == "static w=2":
                        w = 2
                    elif wrule.startswith("rolling"):
                        w = int(wroll[ib])
                    else:
                        w = W21.get(P["sd"][ib], 2)
                    R = Rs[i]
                    if not np.isfinite(R):
                        continue
                    tthr = THRUST_SHARE * np.sqrt(w / 5) * R
                    if d0 * retw[w][ib] >= tthr:
                        kept.append((i, d0))
                pnl = sim(P, kept, lambda *a: True)
                matched = sum(1 for i, s in kept
                              if ((np.abs(hs - int(secs[i])) <= MATCH_S) & (hd == s)).any())
                a = np.asarray(pnl); wn = a > 0
                dd0 = -min(0.0, float(np.min(np.cumsum(a)))) if len(a) else 0.0
                results.setdefault(f"{scheme} + {wrule}", {})[month] = (len(a), matched, wn, a, dd0)
    print("| Config | " + " | ".join(
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
    print("\nReference (T-EN75, w=5): ATR14D +26.2 / +28.0 | INTRADAY10 +4.9 / +34.1")
    print("HIS (all entries, as parsed): 2021-09 +477 (173 tr) | 2024-11 +450 (69 tr)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
