#!/usr/bin/env python3
"""
p4_49_sec_engine.py — P4.49: the per-second fill engine (the standard from here).
==================================================================================
Implements the standing engine rule (P4_DESIGN, T-EN51):
  - 1-min bars remain the source for closed-bar constructs ONLY: signal
    detection and score, direction, entry level, WRB/pt definitions, the
    time-stop count, and close-based exit prices.
  - Every TRIGGER and FILL runs on the per-second top-of-book mid path:
    entry stop orders, early cut, full stop, follow-stop. A trigger fires
    when the mid crosses the level; the fill is the worse of (level, the
    crossing second's mid). Exits are evaluated from the fill second onward,
    so the remainder of the fill bar is no longer blind.
  - Close-based exits (pt ladder, time stop, session end) fire at bar closes,
    at the bar's close price, exactly as before.
  - Reversal on an early cut: immediate, at the exit fill, same engine, once.
Known approximations (recorded): triggers use the quote MID (ES spread is one
tick, so half-a-tick precision); seconds with no book update carry no price
change; close-based exits fill at the 1-min close print.

RUN: python3 Tests/P4_entry_determination/p4_49_sec_engine.py            (repo root)
     --inspect N   dump per-second detail for N sample trades (hand checks)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_31_profit_v9 import wrb_flags                  # noqa: E402
from p4_33_losscuts import month_ctx                   # noqa: E402
from p4_42_v10_oos import score_month                  # noqa: E402

WAIT = 5
V10 = dict(early=2.0, stop=4.0, time_bars=9, trail=None)
V11 = dict(early=1.5, stop=4.0, time_bars=9, trail=(2.0, 2.5))
ALL_MONTHS = [("2025-10", True), ("2022-02", True), ("2021-09", False), ("2024-11", False)]


class Ctx:
    def __init__(self, repo, month, insample):
        es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
        if insample:
            sym = dict(MONTHS)[month]
            bars, _, prev, lo, hi = month_ctx(es, month, sym)
            sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
            sig = sig[(sig.month == month) & (sig.score >= 6)]
        else:
            sig, bars, sym = score_month(repo, month)
            sig = sig[sig.score >= 6]
        self.month, self.sym, self.bars, self.sig = month, sym, bars, sig
        self.bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        self.bsec = self.bts // 1_000_000_000
        self.o = bars.open.to_numpy(); self.c = bars.close.to_numpy()
        self.h = bars.high.to_numpy(); self.l = bars.low.to_numpy()
        self.rth = bars.rth.to_numpy()
        self.sd = bars.session_date.astype(str).to_numpy()
        self.pre = wrb_flags(bars)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        self.secs = f.sec.to_numpy(np.int64)
        self.mids = f.mid.to_numpy(float)

    def bar_of(self, s):
        return int(np.searchsorted(self.bsec, s, "right")) - 1


def leg_sec(cx, fb, fill_px, fill_s, long, p, uref, log=None):
    """One leg on the per-second path. Returns (exit_px, exit_s, exit_bar, reason)."""
    isw, wdir, wbb, wbt, wbody = cx.pre
    n_pt = 0
    best = fill_px
    early_end = cx.bsec[fb + 2] if fb + 2 < len(cx.bsec) else np.iinfo(np.int64).max
    i = int(np.searchsorted(cx.secs, fill_s, "right"))
    jc = fb + 1                                      # next bar whose close is pending
    while i < len(cx.secs):
        s = int(cx.secs[i])
        # bar closes that happened at or before this second
        while jc < len(cx.bsec) and cx.bsec[jc] + 60 <= s:
            if jc + 1 >= len(cx.bsec) or cx.sd[jc + 1] != cx.sd[fb] or not cx.rth[jc + 1]:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "session"
            if jc > fb and isw[jc] and ((wdir[jc] == "bullish") == long):
                n_pt += 1
                big = uref and wbody[jc] >= 2.0 * uref
                if n_pt >= 3 or not big:
                    return cx.c[jc], cx.bsec[jc] + 60, jc, f"pt{n_pt}"
            if jc >= fb + p["time_bars"]:
                return cx.c[jc], cx.bsec[jc] + 60, jc, "time"
            jc += 1
        m = cx.mids[i]
        early = s < early_end
        sp = p["early"] if early else p["stop"]
        stop = fill_px - sp if long else fill_px + sp
        src = "base"
        tr = p.get("trail")
        if tr:
            fav = (best - fill_px) if long else (fill_px - best)
            if fav >= tr[0]:
                t = best - tr[1] if long else best + tr[1]
                if (t > stop) if long else (t < stop):
                    stop, src = t, "trail"
        if (m <= stop if long else m >= stop):
            xp = min(stop, m) if long else max(stop, m)
            if log is not None:
                log.append(f"    stop hit {pd.Timestamp(s, unit='s', tz='UTC')} mid {m} "
                           f"stop {stop} ({src}) fill {xp}")
            # reversal only follows the early LOSS cut (spec: "1.5 pts against");
            # a trail exit in the early window is a profit-protect, not a fail
            return xp, s, cx.bar_of(s), ("faststop" if early and src == "base" else "stop")
        best = max(best, m) if long else min(best, m)
        i += 1
    j = cx.bar_of(int(cx.secs[-1]))
    return cx.c[j], int(cx.secs[-1]), j, "eof"


def simulate(cx, p, collect=None, log_n=0):
    pnl = []; busy = -1; logs = []
    for _, r in cx.sig.sort_values("comp_ns").iterrows():
        ib = int(np.searchsorted(cx.bts, int(r.comp_ns) - 60_000_000_000))
        if ib >= len(cx.bts) or cx.bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
            continue
        fb0 = ib + 1
        if fb0 >= len(cx.bts) or not cx.rth[fb0] or fb0 <= busy:
            continue
        mv = cx.c[ib] - cx.c[ib - 5]
        if mv == 0:
            continue
        long = mv > 0
        uref = r.uref if np.isfinite(r.uref) else None
        lvl = cx.h[ib] if long else cx.l[ib]
        # entry: per-second stop order, valid through bar fb0+WAIT-1, RTH only
        jmax = fb0
        while jmax + 1 < len(cx.bsec) and jmax + 1 < fb0 + WAIT and cx.rth[jmax + 1]:
            jmax += 1
        i = int(np.searchsorted(cx.secs, cx.bsec[fb0]))
        end_s = cx.bsec[jmax] + 60
        fill = fill_s = fb = None
        while i < len(cx.secs) and cx.secs[i] < end_s:
            m = cx.mids[i]
            if (m >= lvl) if long else (m <= lvl):
                fill = max(lvl, m) if long else min(lvl, m)
                fill_s = int(cx.secs[i]); fb = cx.bar_of(fill_s)
                break
            i += 1
        if fill is None:
            continue
        log = [] if len(logs) < log_n else None
        px, xs, xb, reason = leg_sec(cx, fb, fill, fill_s, long, p, uref, log)
        tot = (px - fill) if long else (fill - px)
        legs = [(("L" if long else "S"), fill, px, reason)]
        if reason == "faststop":
            px2, xs2, xb2, r2 = leg_sec(cx, xb, px, xs, not long, p, uref, log)
            tot += (px2 - px) if (not long) else (px - px2)
            legs.append((("S" if long else "L"), px, px2, r2))
            xb = xb2
        pnl.append(tot)
        if collect is not None:
            collect.append(dict(month=cx.month, ts=pd.Timestamp(fill_s, unit="s", tz="UTC"),
                                side="long" if long else "short", fill=fill,
                                pnl=tot, reason=" -> ".join(x[3] for x in legs)))
        if log is not None:
            logs.append((pd.Timestamp(fill_s, unit="s", tz="UTC"), legs, tot, log))
        busy = xb + 5
    for t, legs, tot, log in logs:
        print(f"  TRADE {t} total {tot:+.2f}")
        for sde, f0, x0, rsn in legs:
            print(f"    {sde} in {f0} out {x0} ({rsn})")
        for ln in log:
            print(ln)
    return np.asarray(pnl)


def drawdown(a):
    eq = np.cumsum(a)
    return float(np.max(np.maximum.accumulate(eq) - eq)) if len(a) else 0.0


def his_stats(repo, month, trades):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    lo, hi = month_bounds(month)
    e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    caught = 0
    if len(trades):
        tt = np.array([t["ts"].value for t in trades])
        sides = np.array([t["side"] for t in trades])
        for _, r in e.iterrows():
            en = pd.Timestamp(r.first_entry_utc).value
            m = (np.abs(tt - en) <= 5 * 60_000_000_000) & (sides == r.side)
            caught += int(m.any())
    return e, caught


def run(repo, inspect_n):
    print("| Configuration | Trades | Wins | Losses | Win rate | Avg win / loss | Total | Max DD |")
    print("|---|---|---|---|---|---|---|---|")
    rows_his = []
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        for name, p in [("v10", V10), ("v11", V11)]:
            coll = []
            a = simulate(cx, p, coll, log_n=(inspect_n if name == "v11" else 0))
            w = a > 0
            print(f"| {name} {month} (per-second fills) | {len(a)} | {int(w.sum())} | "
                  f"{int((~w).sum())} | {w.mean():.0%} | +{a[w].mean():.2f} / {a[~w].mean():.2f} "
                  f"| {a.sum():+.1f} | {drawdown(a):.1f} |")
            if name == "v11":
                e, caught = his_stats(repo, month, coll)
                hw = e.realized_pnl > 0
                rows_his.append(
                    f"| HIS {month} | {len(e)} | {int(hw.sum())} | {int((~hw).sum())} | "
                    f"{hw.mean():.0%} | +{e.realized_pnl[hw].mean():.1f} / "
                    f"{e.realized_pnl[~hw].mean():.1f} (as parsed) | "
                    f"{e.realized_pnl.sum():+.0f} (as parsed) | - | caught by v11: {caught} |")
    for r in rows_his:
        print(r)
    print("\nREAD: triggers/fills on per-second mid; closed-bar logic unchanged.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--inspect", type=int, default=0)
    a = ap.parse_args()
    run(a.repo, a.inspect)
