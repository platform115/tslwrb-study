#!/usr/bin/env python3
"""
p4_26_profit_v5.py — P4.23: profit test under STRATEGY_SPEC_v5 (frozen).
=========================================================================
Changes vs v1 (all derived from his measured trade geometry, see the spec):
stop 4.0 pts (arm B: 2.0 for the first 2 bars, then 4.0) · target fixed 5.75 ·
time stop 9 bars. Entries/direction/fill/session identical to v1, so the same
entry list is reused from p4_22's machinery via import.

RUN: python3 Tests/P4_entry_determination/p4_26_profit_v5.py            (repo root)
     python3 Tests/P4_entry_determination/p4_26_profit_v5.py --selftest
OUT: p4_23_trades.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TIME_BARS = 20
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


def simulate_v2(bars, entries):
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt = wrb_flags(bars)
    trades, busy_until = [], -1
    for e in entries:
        fb = e["sig_i"] + 1
        if fb >= len(bars) or not rth[fb] or fb <= busy_until:
            continue
        fill = o[fb]; long = e["side"] == "long"
        exit_px = exit_i = reason = None
        trail = None; trailed = False; n_with = 0
        for j in range(fb, len(bars)):
            if sd[j] != sd[fb] or not rth[j]:
                exit_px, exit_i, reason = c[j - 1], j - 1, "session"; break
            if trail is not None and (l[j] <= trail if long else h[j] >= trail):
                exit_px, exit_i, reason = trail, j, "trail"; break
            if isw[j] and j > fb and ((wdir[j] == "bullish") != long):
                exit_px, exit_i, reason = c[j], j, "opp-wrb"; break
            if isw[j] and j > fb and ((wdir[j] == "bullish") == long):
                n_with += 1
                if n_with >= 2:
                    exit_px, exit_i, reason = c[j], j, "2nd-wrb"; break
                nt = wbb[j] if long else wbt[j]
                trail = nt if trail is None else (max(trail, nt) if long else min(trail, nt))
                trailed = True
            if j >= 5:
                net5 = c[j] - c[j - 5]
                if net5 != 0 and ((net5 > 0) != long):
                    exit_px, exit_i, reason = c[j], j, "speed-flip"; break
            if j >= fb + TIME_BARS:
                exit_px, exit_i, reason = c[j], j, "time"; break
        if exit_px is None:
            exit_px, exit_i, reason = c[-1], len(bars) - 1, "eof"
        pnl = (exit_px - fill) if long else (fill - exit_px)
        trades.append(dict(sig_i=e["sig_i"], fill_i=fb, exit_i=exit_i, side=e["side"],
                           fill=fill, exit=exit_px, reason=reason, pnl_pts=pnl,
                           trailed=trailed, ts=bars.ts_event.iloc[fb]))
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
        for label, ef in [("v5: event-based exits only", False)]:
            tr = simulate_v2(bars, entries)
            tr["month"] = month; tr["arm"] = "v5"
            P1.summarize(tr, label)
            t_ns = pd.DatetimeIndex(tr.ts).as_unit("ns").asi8
            j = np.searchsorted(his_ns, t_ns)
            near = np.minimum(np.abs(his_ns[np.clip(j, 0, len(his_ns) - 1)] - t_ns),
                              np.abs(his_ns[np.clip(j - 1, 0, None)] - t_ns)) / 60e9
            im = tr[near <= 5]
            P1.summarize(im, f"  imitation (shared moments, his win rate {((e_m.realized_pnl>0).mean()):.0%})")
            all_tr.append(tr)
    allt = pd.concat(all_tr, ignore_index=True)
    allt.to_csv(os.path.join(HERE, "p4_23_trades.csv"), index=False)
    print("\n===== POOLED =====")
    P1.summarize(allt, "v5, both months")
    print("\nREAD: spec v2, frozen before run; numbers derived from his winners' measured")
    print("geometry. Amendments -> spec v3+ per the recorded-amendment rule.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=40, freq="1min", tz="UTC")
    base = dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5, close=5000.0,
                rth=True, session_date="d1")
    b1 = pd.DataFrame(base)
    b1.loc[8, ["open", "close", "low"]] = [5000.5, 4997.0, 4997.0]   # opposite (bearish) WRB
    t1 = simulate_v2(b1, [dict(sig_i=4, side="long")])
    assert t1.reason.iloc[0] == "opp-wrb" and t1.exit_i.iloc[0] == 8
    print("=== SELF-TEST ===\n  opposite-WRB cut OK")
    b2 = pd.DataFrame(base)
    b2.loc[5, "close"] = 5000.25            # equal small bodies: no accidental WRBs
    for k, px in [(6, 5001.0), (7, 5002.0), (8, 5002.5)]:
        b2.loc[k, ["close", "high"]] = [px, px]
        b2.loc[k, ["open", "low"]] = [px - 0.25, px - 0.5]   # bodies all 0.25
    b2.loc[9, ["close", "high"]] = [5000.2, 5002.5]   # from 9 on, drift down -> speed flips
    for k in (10, 11, 12):
        b2.loc[k, "close"] = 5000.1 - 0.05 * (k - 9)
    t2 = simulate_v2(b2, [dict(sig_i=4, side="long")])
    assert t2.reason.iloc[0] == "speed-flip", t2
    print("  speed-flip cut OK")
    b3 = pd.DataFrame(base)
    b3.loc[8, ["open", "close", "high", "low"]] = [5000.0, 5003.0, 5003.0, 5000.0]  # 1st with-WRB
    for k in (9, 10, 11):
        px = 5003.0 + 0.5 * (k - 8)
        b3.loc[k, ["open", "close", "high", "low"]] = [px - 0.25, px, px, px - 0.5]
    b3.loc[12, ["open", "close", "high", "low"]] = [5004.5, 5009.0, 5009.0, 5004.5]  # 2nd with-WRB
    t3 = simulate_v2(b3, [dict(sig_i=4, side="long")])
    assert t3.reason.iloc[0] == "2nd-wrb" and abs(t3.pnl_pts.iloc[0] - 9.0) < 1e-9, t3
    print("  trail on 1st, exit on 2nd with-WRB OK\nSELF-TEST OK.")
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
