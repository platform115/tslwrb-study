#!/usr/bin/env python3
"""
p4_24_profit_v3.py — P4.23: profit test under STRATEGY_SPEC_v3 (frozen).
=========================================================================
Changes vs v1 (all derived from his measured trade geometry, see the spec):
stop 4.0 pts (arm B: 2.0 for the first 2 bars, then 4.0) · target fixed 5.75 ·
time stop 9 bars. Entries/direction/fill/session identical to v1, so the same
entry list is reused from p4_22's machinery via import.

RUN: python3 Tests/P4_entry_determination/p4_24_profit_v3.py            (repo root)
     python3 Tests/P4_entry_determination/p4_24_profit_v3.py --selftest
OUT: p4_23_trades.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

STOP_PTS = 4.0
EARLY_STOP = 2.0
EARLY_BARS = 2
TIME_BARS = 9
COOLDOWN_MIN = 0          # v3: no cooldown


def wrb_flags(bars):
    """Per-bar: completes a WRB? (body > prior 3 bodies, same session, no doji)
    + its direction. Same definition as everywhere."""
    o, c = bars.open.to_numpy(), bars.close.to_numpy()
    sd = bars.session_date.astype(str).to_numpy()
    body = np.abs(c - o)
    f = np.zeros(len(bars), bool); d = np.empty(len(bars), object)
    for i in range(3, len(bars)):
        if (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) and body[i] > 0 and            body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]:
            f[i] = True; d[i] = "bullish" if c[i] > o[i] else "bearish"
    return f, d


def simulate_v2(bars, entries, early_fail=False):
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir = wrb_flags(bars)
    trades, busy_until = [], -1
    for e in entries:
        fb = e["sig_i"] + 1
        if fb >= len(bars) or not rth[fb] or fb <= busy_until:
            continue
        fill = o[fb]; long = e["side"] == "long"
        exit_px = exit_i = reason = None; wrb_rel = ""
        for j in range(fb, len(bars)):
            if sd[j] != sd[fb] or not rth[j]:
                exit_px, exit_i, reason = c[j - 1], j - 1, "session"; break
            sp = EARLY_STOP if (early_fail and j < fb + EARLY_BARS) else STOP_PTS
            stop = fill - sp if long else fill + sp
            if (l[j] <= stop if long else h[j] >= stop):
                exit_px, exit_i, reason = stop, j, "stop"; break
            if isw[j]:                                     # v3 target: new WRB completes
                exit_px, exit_i, reason = c[j], j, "wrb"
                wrb_rel = "with" if ((wdir[j] == "bullish") == long) else "against"
                break
            if j >= fb + TIME_BARS:
                exit_px, exit_i, reason = c[j], j, "time"; break
        if exit_px is None:
            exit_px, exit_i, reason = c[-1], len(bars) - 1, "eof"
        pnl = (exit_px - fill) if long else (fill - exit_px)
        trades.append(dict(sig_i=e["sig_i"], fill_i=fb, exit_i=exit_i, side=e["side"],
                           fill=fill, exit=exit_px, reason=reason, wrb_rel=wrb_rel,
                           pnl_pts=pnl, ts=bars.ts_event.iloc[fb]))
        busy_until = exit_i + COOLDOWN_MIN
    return pd.DataFrame(trades)


def run(repo):
    import p4_22_profit_test as P1
    from p4_2_entry_context import month_bounds, MONTHS
    # rebuild the identical entry lists by monkey-patching p4_22's simulate to capture
    captured = {}
    real_sim = P1.simulate
    def capture(bars, entries):
        captured[len(captured)] = (bars, entries)
        return real_sim(bars, entries)
    P1.simulate = capture
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        P1.run(repo)
    P1.simulate = real_sim
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    months = [m for m, _ in MONTHS]
    # p4_22 calls simulate twice per month (far-edge, fixed); entry lists identical
    per_month = {months[i // 2]: captured[i] for i in range(0, len(captured), 2)}
    all_tr = []
    for month, (bars, entries) in per_month.items():
        lo, hi = month_bounds(month)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        his_ns = np.sort(pd.DatetimeIndex(e_m.first_entry_utc).as_unit("ns").asi8)
        print(f"\n===== {month} (entries attempted: {len(entries)}) =====")
        for label, ef in [("arm A: stop 4.0 / exit on new WRB / time 9", False),
                          ("arm B: + fast-fail 2.0 first 2 bars", True)]:
            tr = simulate_v2(bars, entries, early_fail=ef)
            tr["month"] = month; tr["arm"] = "B" if ef else "A"
            P1.summarize(tr, label)
            t_ns = pd.DatetimeIndex(tr.ts).as_unit("ns").asi8
            j = np.searchsorted(his_ns, t_ns)
            near = np.minimum(np.abs(his_ns[np.clip(j, 0, len(his_ns) - 1)] - t_ns),
                              np.abs(his_ns[np.clip(j - 1, 0, None)] - t_ns)) / 60e9
            im = tr[near <= 5]
            P1.summarize(im, f"  imitation (shared moments, his win rate {((e_m.realized_pnl>0).mean()):.0%})")
            wx = tr[tr.reason == "wrb"]
            if len(wx):
                for rel, g in wx.groupby("wrb_rel"):
                    print(f"    WRB exits {rel:7s}: {len(g):3d} trades, avg {g.pnl_pts.mean():+.2f} pts, total {g.pnl_pts.sum():+.1f}")
            all_tr.append(tr)
    allt = pd.concat(all_tr, ignore_index=True)
    allt.to_csv(os.path.join(HERE, "p4_23_trades.csv"), index=False)
    print("\n===== POOLED =====")
    for arm in ("A", "B"):
        P1.summarize(allt[allt.arm == arm], f"arm {arm}, both months")
    print("\nREAD: spec v2, frozen before run; numbers derived from his winners' measured")
    print("geometry. Amendments -> spec v3+ per the recorded-amendment rule.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=30, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, rth=True, session_date="d1"))
    bars.loc[6, "low"] = 4997.5       # 2.5 adverse on bar 6 (within first 2 bars of fill 5)
    a = simulate_v2(bars, [dict(sig_i=4, side="long")], early_fail=False)
    b = simulate_v2(bars, [dict(sig_i=4, side="long")], early_fail=True)
    assert a.reason.iloc[0] == "time"          # 4.0 stop survives the 2.5 dip
    assert b.reason.iloc[0] == "stop" and abs(b.pnl_pts.iloc[0] + 2.0) < 1e-9
    print("=== SELF-TEST ===\n  early-fail arm stops at 2.0, arm A survives OK")
    bars2 = bars.copy()
    bars2.loc[9, ["close", "high"]] = [5003.0, 5003.0]     # bar 9 completes a bullish WRB
    t2 = simulate_v2(bars2, [dict(sig_i=4, side="long")])
    assert t2.reason.iloc[0] == "wrb" and t2.wrb_rel.iloc[0] == "with" and abs(t2.pnl_pts.iloc[0] - 3.0) < 1e-9
    t3 = simulate_v2(bars2, [dict(sig_i=4, side="long"), dict(sig_i=11, side="long")])
    assert len(t3) == 2, "no cooldown: second entry allowed right after exit"
    print("  WRB exit + no-cooldown re-entry OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
