#!/usr/bin/env python3
"""
p4_30_profit_v8.py — P4.30: profit test under STRATEGY_SPEC_v8 (frozen).
=========================================================================
Reverse-on-fast-fail added to both co-leading configurations:
  Arm A = v2B (fixed: stop 4.0 / fast-fail 2.0 x 2 bars / target 5.75 / time 9,
          direction = 5-min move, no trail) + reversal
  Arm B = v7 (scaled: 1.6U / 0.8U / 2.3U / time 9, both-agree direction +
          exhaustion veto, WRB trail) + reversal
Reversal: the fast-fail stop (early window only) flips the position at the stop
price; the reversed leg runs the same exit stack from the NEXT bar (time counted
from the reversal bar); one flip max. Entry lists are rebuilt by the base specs'
own code (captured), so entries are bit-identical to v2B's and v7's.

RUN: python3 Tests/P4_entry_determination/p4_30_profit_v8.py            (repo root)
     python3 Tests/P4_entry_determination/p4_30_profit_v8.py --selftest
OUT: p4_30_trades.csv
"""
import argparse, io, contextlib, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

EARLY_BARS = 2
TIME_BARS = 9
COOLDOWN_MIN = 5


def wrb_flags(bars):
    o, c = bars.open.to_numpy(), bars.close.to_numpy()
    sd = bars.session_date.astype(str).to_numpy()
    body = np.abs(c - o)
    f = np.zeros(len(bars), bool); d = np.empty(len(bars), object)
    bb = np.minimum(o, c); bt = np.maximum(o, c)
    for i in range(3, len(bars)):
        if (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) and body[i] > 0 and \
           body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]:
            f[i] = True; d[i] = "bullish" if c[i] > o[i] else "bearish"
    return f, d, bb, bt


def run_leg(bars, pre, fb, fill, long, u, p, start_j):
    """One leg from bar start_j. Returns (exit_px, exit_i, reason, trailed).
    pre = (isw, wdir, wbb, wbt). Early window measured from fb."""
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt = pre
    tgt = fill + p["tgt"] * u if long else fill - p["tgt"] * u
    trail = None; trailed = False
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session", trailed
        sp = (p["early"] if j < fb + EARLY_BARS else p["stop"]) * u
        base = fill - sp if long else fill + sp
        stop = base if trail is None else (max(base, trail) if long else min(base, trail))
        if (l[j] <= stop if long else h[j] >= stop):
            if trail is not None and stop != base:
                return stop, j, "trail", trailed
            return stop, j, ("faststop" if j < fb + EARLY_BARS else "stop"), trailed
        if (h[j] >= tgt if long else l[j] <= tgt):
            return tgt, j, "target", trailed
        if j >= fb + TIME_BARS:
            return c[j], j, "time", trailed
        if p["trail"] and j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            nt = wbb[j] if long else wbt[j]
            trail = nt if trail is None else (max(trail, nt) if long else min(trail, nt))
            trailed = True
    return c[-1], len(bars) - 1, "eof", trailed


def simulate_v8(bars, entries, p):
    o = bars.open.to_numpy(); rth = bars.rth.to_numpy()
    pre = wrb_flags(bars)
    trades, busy_until = [], -1
    for e in entries:
        fb = e["sig_i"] + 1
        if fb >= len(bars) or not rth[fb] or fb <= busy_until:
            continue
        u = e.get("u_pts", 1.0)
        long = e["side"] == "long"
        fill = o[fb]
        px, xi, reason, trailed = run_leg(bars, pre, fb, fill, long, u, p, fb)
        pnl = (px - fill) if long else (fill - px)
        trades.append(dict(sig_i=e["sig_i"], fill_i=fb, exit_i=xi, side=e["side"],
                           fill=fill, exit=px, reason=reason, pnl_pts=pnl, leg=1,
                           ts=bars.ts_event.iloc[fb]))
        if reason == "faststop":                        # REVERSE once
            fb2 = xi
            fill2 = px; long2 = not long
            px2, xi2, r2, _ = run_leg(bars, pre, fb2, fill2, long2, u, p, fb2 + 1)
            pnl2 = (px2 - fill2) if long2 else (fill2 - px2)
            r2 = "rev-" + r2
            trades.append(dict(sig_i=e["sig_i"], fill_i=fb2, exit_i=xi2,
                               side="short" if long else "long", fill=fill2, exit=px2,
                               reason=r2, pnl_pts=pnl2, leg=2,
                               ts=bars.ts_event.iloc[fb2]))
            xi = xi2
        busy_until = xi + COOLDOWN_MIN
    return pd.DataFrame(trades)


ARMS = {
    "A (v2B + reverse)": dict(stop=4.0, early=2.0, tgt=5.75, trail=False, scaled=False),
    "B (v7 + reverse)":  dict(stop=1.6, early=0.8, tgt=2.3, trail=True, scaled=True),
}


def capture_entries(repo):
    """Entry lists bit-identical to the base specs': capture via their own run()."""
    import p4_22_profit_test as P22
    import p4_28_profit_v7 as P28
    capA, capB = {}, {}
    realA, realB = P22.simulate, P28.simulate_v7
    P22.simulate = lambda b, e: (capA.setdefault(len(capA), (b, e)), realA(b, e))[1]
    P28.simulate_v7 = lambda b, e: (capB.setdefault(len(capB), (b, e)), realB(b, e))[1]
    with contextlib.redirect_stdout(io.StringIO()):
        P22.run(repo); P28.run(repo)
    P22.simulate, P28.simulate_v7 = realA, realB
    months = [m for m, _ in __import__("p4_2_entry_context").MONTHS]
    A = {months[i // 2]: capA[i] for i in range(0, len(capA), 2)}   # p4_22 sims twice/month
    B = {months[i]: capB[i] for i in range(len(capB))}
    return A, B


def summarize_row(name, tr):
    if not len(tr):
        return f"| {name} | 0 | - | - | - |"
    w = tr.pnl_pts > 0
    return (f"| {name} | {len(tr)} | {w.mean():.0%} | +{tr.pnl_pts[w].mean():.2f} / "
            f"{tr.pnl_pts[~w].mean():.2f} | {tr.pnl_pts.sum():+.1f} pts |")


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    A, B = capture_entries(repo)
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    out = []
    for arm, p in ARMS.items():
        src = A if arm.startswith("A") else B
        allm = []
        for month, (bars, entries) in src.items():
            if p["scaled"]:
                entries = [e for e in entries if "u_pts" in e]
            else:
                entries = [dict(e, u_pts=1.0) for e in entries]
            tr = simulate_v8(bars, entries, p)
            tr["month"] = month; tr["arm"] = arm
            allm.append(tr)
            lo = bars.ts_event.iloc[0] + pd.Timedelta(days=4)
            print(summarize_row(f"v8 {arm} {month}", tr))
            rev = tr[tr.leg == 2]
            if len(rev):
                print(f"|   reversal legs {month} | {len(rev)} | {(rev.pnl_pts>0).mean():.0%} | "
                      f"avg {rev.pnl_pts.mean():+.2f} | {rev.pnl_pts.sum():+.1f} pts |")
        allt = pd.concat(allm, ignore_index=True)
        out.append(allt)
        print(summarize_row(f"v8 {arm} POOLED", allt))
    full = pd.concat(out, ignore_index=True)
    full.to_csv(os.path.join(HERE, "p4_30_trades.csv"), index=False)
    for month in sorted(set(full.month)):
        e_m = ep[ep.first_entry_utc.dt.strftime("%Y-%m") == month]
        w = e_m.realized_pnl > 0
        print(f"| HIS {month} | {len(e_m)} | {w.mean():.0%} | +{e_m.realized_pnl[w].mean():.1f} / "
              f"{e_m.realized_pnl[~w].mean():.1f} (as parsed) | {e_m.realized_pnl.sum():+.0f} (as parsed) |")
    print("\nreference: v2B +6.2 | v7 -24.9 (Oct +23.6/Feb -48.5) | v4B +4.5")
    print("READ: spec v8 frozen before run; final config re-validates out-of-sample.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=40, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, rth=True, session_date="d1"))
    p = ARMS["A (v2B + reverse)"]
    b1 = bars.copy()
    b1.loc[5, "low"] = 4997.5          # early-window 2.0 stop hits on fill bar
    for k in (6, 7, 8):                # keep the reversed short alive (highs below its stop)
        b1.loc[k, ["open", "close", "high", "low"]] = [4997.5, 4997.0, 4997.6, 4996.5]
    b1.loc[8, "low"] = 4992.0          # reversed short rides down to its 5.75 target
    t = simulate_v8(b1, [dict(sig_i=4, side="long", u_pts=1.0)], p)
    assert len(t) == 2 and t.reason.tolist() == ["faststop", "rev-target"], t
    assert abs(t.pnl_pts.iloc[0] + 2.0) < 1e-9 and abs(t.pnl_pts.iloc[1] - 5.75) < 1e-9
    print("=== SELF-TEST ===\n  fast-fail -> reversal -> reversed target OK")
    b2 = bars.copy()
    b2.loc[9, "low"] = 4995.5          # late stop (after early window) -> flat, no reversal
    t2 = simulate_v8(b2, [dict(sig_i=4, side="long", u_pts=1.0)], p)
    assert len(t2) == 1 and t2.reason.iloc[0] == "stop"
    print("  late stop stays flat (no reversal) OK")
    b3 = bars.copy()
    b3.loc[5, "low"] = 4997.5          # default highs (5000.5 >= rev stop 5000) fast-fail the short
    t3 = simulate_v8(b3, [dict(sig_i=4, side="long", u_pts=1.0)], p)
    assert len(t3) == 2 and t3.reason.iloc[1] == "rev-faststop"
    print("  reversed leg's fast-fail exits flat (one flip max) OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
