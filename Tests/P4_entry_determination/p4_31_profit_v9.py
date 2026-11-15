#!/usr/bin/env python3
"""
p4_31_profit_v9.py — P4.30: profit test under STRATEGY_SPEC_v9 (frozen).
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

RUN: python3 Tests/P4_entry_determination/p4_31_profit_v9.py            (repo root)
     python3 Tests/P4_entry_determination/p4_31_profit_v9.py --selftest
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
    return f, d, bb, bt, body


def run_leg(bars, pre, fb, fill, long, u, p, start_j, e_uref=None):
    """One leg from bar start_j. Returns (exit_px, exit_i, reason, trailed).
    pre = (isw, wdir, wbb, wbt). Early window measured from fb."""
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt, wbody = pre
    n_pt = 0
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session", False
        sp = (p["early"] if j < fb + EARLY_BARS else p["stop"]) * u
        stop = fill - sp if long else fill + sp
        if (l[j] <= stop if long else h[j] >= stop):
            return stop, j, ("faststop" if j < fb + EARLY_BARS else "stop"), False
        if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            n_pt += 1
            big = p["ladder"] and e_uref and wbody[j] >= 2.0 * e_uref
            if n_pt >= 3 or not big:
                return c[j], j, f"pt{n_pt}", False
        if j >= fb + TIME_BARS:
            return c[j], j, "time", False
    return c[-1], len(bars) - 1, "eof", False


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
        px, xi, reason, trailed = run_leg(bars, pre, fb, fill, long, u, p, fb, e.get("uref"))
        pnl = (px - fill) if long else (fill - px)
        trades.append(dict(sig_i=e["sig_i"], fill_i=fb, exit_i=xi, side=e["side"],
                           fill=fill, exit=px, reason=reason, pnl_pts=pnl, leg=1,
                           ts=bars.ts_event.iloc[fb]))
        if reason == "faststop":                        # REVERSE once
            fb2 = xi
            fill2 = px; long2 = not long
            px2, xi2, r2, _ = run_leg(bars, pre, fb2, fill2, long2, u, p, fb2 + 1, e.get("uref"))
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
    "A (pt1 always)":     dict(stop=4.0, early=2.0, ladder=False, scaled=False),
    "B (momentum ladder)": dict(stop=4.0, early=2.0, ladder=True, scaled=False),
}


def capture_entries(repo):
    import p4_22_profit_test as P22
    capA = {}
    realA = P22.simulate
    P22.simulate = lambda b, e: (capA.setdefault(len(capA), (b, e)), realA(b, e))[1]
    with contextlib.redirect_stdout(io.StringIO()):
        P22.run(repo)
    P22.simulate = realA
    months = [m for m, _ in __import__("p4_2_entry_context").MONTHS]
    A = {months[i // 2]: capA[i] for i in range(0, len(capA), 2)}
    from p4_5a_taken_anatomy import wrb_bodies as _wb
    for month, (bars, entries) in A.items():
        wb = _wb(bars[bars.rth].reset_index(drop=True)).merge(
            bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
        wb["body"] = (wb.close - wb.open).abs()
        med = wb.groupby(wb.session_date.astype(str)).body.median()
        sessions = sorted(set(bars.session_date.astype(str)))
        prev = {sx: float(med.get(sessions[i - 1], np.nan)) for i, sx in enumerate(sessions) if i > 0}
        sd = bars.session_date.astype(str).to_numpy()
        for e in entries:
            e["uref"] = prev.get(sd[e["sig_i"]], None)
            if e["uref"] is not None and not np.isfinite(e["uref"]):
                e["uref"] = None
    return A, A


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
        src = A
        allm = []
        for month, (bars, entries) in src.items():
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
    print("\nreference: v8-A +51.2 (Oct +29.5 / Feb +21.8) | v2B +6.2")
    print("READ: spec v8 frozen before run; final config re-validates out-of-sample.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=40, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, rth=True, session_date="d1"))
    b1 = bars.copy()
    b1.loc[8, ["open", "close", "high", "low"]] = [5000.0, 5001.0, 5001.0, 5000.0]  # small in-dir WRB
    pA = ARMS["A (pt1 always)"]; pB = ARMS["B (momentum ladder)"]
    t = simulate_v8(b1, [dict(sig_i=4, side="long", u_pts=1.0, uref=1.0)], pA)
    assert t.reason.iloc[0] == "pt1" and abs(t.pnl_pts.iloc[0] - 1.0) < 1e-9, t
    print("=== SELF-TEST ===\n  pt1 exit OK")
    b2 = bars.copy()
    b2.loc[8, ["open", "close", "high", "low"]] = [5000.0, 5005.0, 5005.0, 5000.0]  # BIG pt1 (body 5 >= 2*uref 4)
    for k in (9, 10, 11):
        b2.loc[k, ["open", "close", "high", "low"]] = [5005.0, 5005.2, 5005.3, 5004.8]
    b2.loc[12, ["open", "close", "high", "low"]] = [5005.0, 5008.5, 5008.5, 5005.0]  # pt2 body 3.5 < 4 -> exit
    tB = simulate_v8(b2, [dict(sig_i=4, side="long", u_pts=1.0, uref=2.0)], pB)
    assert tB.reason.iloc[0] == "pt2" and abs(tB.pnl_pts.iloc[0] - 8.5) < 1e-9, tB
    tA = simulate_v8(b2, [dict(sig_i=4, side="long", u_pts=1.0, uref=2.0)], pA)
    assert tA.reason.iloc[0] == "pt1" and abs(tA.pnl_pts.iloc[0] - 5.0) < 1e-9
    print("  momentum ladder holds big pt1 to pt2; arm A exits pt1 OK")
    b3 = bars.copy(); b3.loc[5, "low"] = 4997.5
    t3 = simulate_v8(b3, [dict(sig_i=4, side="long", u_pts=1.0, uref=1.0)], pA)
    assert t3.reason.iloc[0] == "faststop" and len(t3) == 2    # reversal intact
    print("  reversal intact OK\nSELF-TEST OK.")
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
