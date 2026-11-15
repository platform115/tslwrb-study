#!/usr/bin/env python3
"""
p4_33_losscuts.py — P4.33: quick loss-management test (user, 2026-11-15).
==========================================================================
His loss handling is traction-based, not price-based: he cuts when a trade is
not properly working - sometimes small-up-then-fading, sometimes slightly down -
long before a price stop (his avg loss -1.71 vs our -3.92 on identical entries).
Two mechanizations, added to spec v9-B (momentum ladder, reversal kept on the
price fast-fail only; these new cuts exit FLAT):
  NT  no-traction: at the close of bar fill+2, unrealized <= 0 -> exit at close
  GB  give-back: once up >= 1.0 pt, closing back <= 0 -> exit at close
Arms: v9-B baseline · +NT · +GB · +NT+GB. Frames: our own entries AND his 313
entries (his exits benchmark: 74% win, +6.25/-1.71, +1275.8).

RUN: python3 Tests/P4_entry_determination/p4_33_losscuts.py            (repo root)
     python3 Tests/P4_entry_determination/p4_33_losscuts.py --selftest
"""
import argparse, io, contextlib, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_31_profit_v9 import wrb_flags, ARMS               # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies                # noqa: E402

EARLY_BARS = 2
TIME_BARS = 9
COOLDOWN_MIN = 5
NT_BAR = 2
GB_ARM = 1.0


def run_leg(bars, pre, fb, fill, long, p, start_j, uref):
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt, wbody = pre
    n_pt = 0; armed = False
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session"
        sp = p["early"] if j < fb + EARLY_BARS else p["stop"]
        stop = fill - sp if long else fill + sp
        if (l[j] <= stop if long else h[j] >= stop):
            return stop, j, ("faststop" if j < fb + EARLY_BARS else "stop")
        if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            n_pt += 1
            big = p["ladder"] and uref and wbody[j] >= 2.0 * uref
            if n_pt >= 3 or not big:
                return c[j], j, f"pt{n_pt}"
        up = (c[j] - fill) if long else (fill - c[j])
        if p.get("gb") and up >= GB_ARM:
            armed = True
        if p.get("gb") and armed and up <= 0:
            return c[j], j, "giveback"
        if p.get("nt") and j == fb + NT_BAR and up <= 0:
            return c[j], j, "notraction"
        if j >= fb + TIME_BARS:
            return c[j], j, "time"
    return c[-1], len(bars) - 1, "eof"


def month_ctx(es, month, sym):
    lo, hi = month_bounds(month)
    bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
              (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
    bars["rth"] = bars.session == "RTH"
    pre = wrb_flags(bars)
    wb = wrb_bodies(bars[bars.rth].reset_index(drop=True)).merge(
        bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
    wb["body"] = (wb.close - wb.open).abs()
    med = wb.groupby(wb.session_date.astype(str)).body.median()
    sessions = sorted(set(bars.session_date.astype(str)))
    prev = {sx: float(med.get(sessions[i - 1], np.nan)) for i, sx in enumerate(sessions) if i > 0}
    return bars, pre, prev, lo, hi


def row(name, pnl):
    pnl = np.asarray(pnl, float)
    if not len(pnl):
        return f"| {name} | 0 | - | - | - |"
    w = pnl > 0
    return (f"| {name} | {len(pnl)} | {w.mean():.0%} | +{pnl[w].mean():.2f} / "
            f"{pnl[~w].mean():.2f} | {pnl.sum():+.1f} pts |")


VARIANTS = {"v9-B baseline": {}, "+NT": {"nt": 1}, "+GB": {"gb": 1}, "+NT+GB": {"nt": 1, "gb": 1}}


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    base = dict(ARMS["B (momentum ladder)"])
    # frame 2: our own entries (captured from v2B's builder, as v9 does)
    import p4_30_profit_v8 as V8
    A, _ = V8.capture_entries(repo) if hasattr(V8, "capture_entries") else (None, None)
    import p4_31_profit_v9 as V9
    with contextlib.redirect_stdout(io.StringIO()):
        A, _ = V9.capture_entries(repo)
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    for vname, extra in VARIANTS.items():
        p = dict(base, **extra)
        his_frame, own_frame = [], []
        for month, sym in MONTHS:
            bars, pre, prev, lo, hi = month_ctx(es, month, sym)
            bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
            sd = bars.session_date.astype(str).to_numpy()
            # HIS entries
            e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
            for _, t in e_m.iterrows():
                en = pd.Timestamp(t.first_entry_utc).value
                fb = int(np.searchsorted(bts, (en // 60_000_000_000) * 60_000_000_000))
                if fb >= len(bts) or not bars.rth.iloc[min(fb, len(bts) - 1)]:
                    continue
                P = float(np.asarray(t.entry_prices).ravel()[0]); long = t.side == "long"
                uref = prev.get(sd[fb], None)
                px, xi, r = run_leg(bars, pre, fb, P, long, p, fb + 1, uref)
                tot = (px - P) if long else (P - px)
                if r == "faststop":
                    px2, _, _ = run_leg(bars, pre, xi, px, not long, p, xi + 1, uref)
                    tot += (px2 - px) if (not long) else (px - px2)
                his_frame.append(tot)
            # OUR entries
            bars2, entries = A[month]
            busy = -1
            o2 = bars2.open.to_numpy()
            pre2 = wrb_flags(bars2)
            bsd2 = bars2.session_date.astype(str).to_numpy()
            for e in entries:
                fb = e["sig_i"] + 1
                if fb >= len(bars2) or not bars2.rth.iloc[fb] or fb <= busy:
                    continue
                fill = o2[fb]; long = e["side"] == "long"
                uref = e.get("uref")
                px, xi, r = run_leg(bars2, pre2, fb, fill, long, p, fb, uref)
                tot = (px - fill) if long else (fill - px)
                if r == "faststop":
                    px2, xi2, _ = run_leg(bars2, pre2, xi, px, not long, p, xi + 1, uref)
                    tot += (px2 - px) if (not long) else (px - px2)
                    xi = xi2
                own_frame.append(tot)
                busy = xi + COOLDOWN_MIN
        print(row(f"{vname} | HIS entries", his_frame))
        print(row(f"{vname} | our entries", own_frame))
    print(row("HIS OWN EXITS (benchmark)", []))
    print("| HIS OWN EXITS (benchmark) | 306 | 74% | +6.25 / -1.71 | +1275.8 pts |")
    print("\nREAD: quick search-mode test; a surviving variant becomes spec v10 and")
    print("re-validates out-of-sample later.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=40, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, rth=True, session_date="d1"))
    pre = wrb_flags(bars)
    p = dict(ARMS["B (momentum ladder)"], nt=1)
    px, xi, r = run_leg(bars, pre, 5, 5000.0, True, p, 6, 1.0)
    assert r == "notraction" and xi == 7, (r, xi)       # flat at fb+2 -> cut
    print("=== SELF-TEST ===\n  no-traction cut at bar+2 OK")
    b2 = bars.copy()
    b2.loc[5, ["open", "close", "high"]] = [5000.0, 5000.75, 5000.8]   # equal small bodies -
    b2.loc[6, ["open", "close", "high"]] = [5000.75, 5001.5, 5001.5]   # no WRB forms on the rise
    b2.loc[7, ["open", "close", "high"]] = [5000.75, 5001.5, 5001.5]
    b2.loc[8, ["open", "close", "low"]] = [5001.4, 4999.8, 4999.8]     # back below entry -> giveback
    p2 = dict(ARMS["B (momentum ladder)"], gb=1)
    px, xi, r = run_leg(b2, pre_b2 := wrb_flags(b2), 5, 5000.0, True, p2, 6, 99.0)
    assert r == "giveback" and xi == 8, (r, xi)
    print("  give-back cut OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
