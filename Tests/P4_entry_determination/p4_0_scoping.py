#!/usr/bin/env python3
"""
p4_0_scoping.py — P4.0: the counting gate for the entry-determination phase.
=============================================================================
COUNTS ONLY — no statistics, no features, no hypotheses judged. Output of this
script sizes the discovery frame (Oct-2025 + Feb-2022) and records, for the
record, the full-history reservoir kept for later validation.

Prints:
  1. Episode table: full span, per-year counts, quality flags (NaT, pnl_ok),
     discovery-month counts, entries/day, entry time-of-day (CT), hold lengths.
  2. WRB signal counts for the two discovery months (right symbol each), split:
     inside/outside his daily active window (grid pad {0,30,60} min before the
     day's first entry), and in-trade-masked (mechanically unavailable) vs free.
     "Active window" per day = [first entry - pad, last exit].
  3. KME coverage per discovery month (timestamped USD events).

RUN: python3 Tests/P4_entry_determination/p4_0_scoping.py            (repo root)
     python3 Tests/P4_entry_determination/p4_0_scoping.py --selftest
"""
import argparse, os
import numpy as np
import pandas as pd

MONTHS = [("2025-10", "ESZ5"), ("2022-02", "ESH2")]
PADS_MIN = [0, 30, 60]


def month_bounds(month):
    lo = pd.Timestamp(f"{month}-01", tz="UTC")
    return lo, lo + pd.offsets.MonthBegin(1)


def signal_counts(wrb, ep, month, symbol, pad_min):
    """Counts of 1m WRB signals vs his activity, one discovery month, one pad."""
    lo, hi = month_bounds(month)
    w = wrb[(wrb.ts_event >= lo) & (wrb.ts_event < hi) & (wrb.symbol == symbol)]
    if "timeframe" in w.columns:
        w = w[w.timeframe == "1m"]
    e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    # daily active windows
    e = e.assign(day=e.first_entry_utc.dt.date)
    day_win = e.groupby("day").agg(t0=("first_entry_utc", "min"), t1=("last_exit_utc", "max"))
    day_win["t0"] = day_win.t0 - pd.Timedelta(minutes=pad_min)
    sig_ts = w.ts_event
    sig_day = sig_ts.dt.date
    t0 = sig_day.map(day_win.t0); t1 = sig_day.map(day_win.t1)
    in_active = sig_ts.notna() & t0.notna() & (sig_ts >= t0) & (sig_ts <= t1)
    # in-trade mask: signal bar inside any [entry, exit] of that month
    iv_s = e.first_entry_utc.to_numpy(); iv_e = e.last_exit_utc.to_numpy()
    ts = sig_ts.to_numpy()
    in_trade = np.zeros(len(ts), bool)
    for s_, e_ in zip(iv_s, iv_e):
        in_trade |= (ts >= s_) & (ts <= e_)
    n_act = int(in_active.sum())
    n_act_intrade = int((in_active.to_numpy() & in_trade).sum())
    return dict(total=len(w), active=n_act, active_in_trade=n_act_intrade,
                active_free=n_act - n_act_intrade, days_traded=len(day_win), n_trades=len(e))


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    wrb = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    kme = pd.read_parquet(os.path.join(repo, "Data/inputs/kme_calendar.parquet"))

    print("===== 1. EPISODE TABLE =====")
    print(f"rows={len(ep)}  span={ep.first_entry_utc.min()} -> {ep.first_entry_utc.max()}")
    print(f"NaT entries={int(ep.first_entry_utc.isna().sum())}  NaT exits={int(ep.last_exit_utc.isna().sum())}  "
          f"pnl_ok={int(ep.pnl_ok.sum()) if 'pnl_ok' in ep else 'n/a'}  "
          f"scaled={int(ep.scaled.sum()) if 'scaled' in ep else 'n/a'}")
    print("per-year counts:")
    print(ep.groupby(ep.first_entry_utc.dt.year).size().to_string())
    ok = ep.dropna(subset=["first_entry_utc", "last_exit_utc"]).copy()
    hold = (ok.last_exit_utc - ok.first_entry_utc).dt.total_seconds()
    print(f"hold(s): p25={hold.quantile(.25):.0f} med={hold.median():.0f} p75={hold.quantile(.75):.0f} "
          f"max={hold.max():.0f}")
    ct = ok.first_entry_utc.dt.tz_convert("America/Chicago")
    hrs = ct.dt.hour + ct.dt.minute / 60
    print(f"entry time-of-day (CT): p5={hrs.quantile(.05):.2f} p25={hrs.quantile(.25):.2f} "
          f"med={hrs.median():.2f} p75={hrs.quantile(.75):.2f} p95={hrs.quantile(.95):.2f}")
    tpd = ok.groupby(ok.first_entry_utc.dt.date).size()
    print(f"trades/day: med={tpd.median():.0f} p90={tpd.quantile(.9):.0f} max={tpd.max()} "
          f"days-traded={len(tpd)}")

    print("\n===== 2. WRB SIGNALS vs ACTIVITY (discovery months) =====")
    for month, sym in MONTHS:
        print(f"-- {month} ({sym}) --")
        for pad in PADS_MIN:
            c = signal_counts(wrb, ep, month, sym, pad)
            print(f"  pad={pad:>2}min: signals total={c['total']}  in-active-window={c['active']}  "
                  f"of which in-trade(masked)={c['active_in_trade']}  FREE(decision pool)={c['active_free']}"
                  + (f"   [trades={c['n_trades']} days={c['days_traded']}]" if pad == 0 else ""))

    print("\n===== 3. KME COVERAGE (discovery months) =====")
    for month, _ in MONTHS:
        lo, hi = month_bounds(month)
        k = kme[(kme.ts_utc >= lo) & (kme.ts_utc < hi) & (kme.currency == "USD")]
        print(f"  {month}: timestamped USD events = {len(k)}")
    print("\nREAD: counts only. 'FREE' = signals in his active window while flat — the")
    print("taken-vs-skipped decision pool. Taken-side matching to specific signals is P4.2's")
    print("job (characterization), not assumed here.")


def selftest():
    print("=== SELF-TEST ===")
    ts = pd.Timestamp("2025-10-06 14:00", tz="UTC")
    ep = pd.DataFrame(dict(first_entry_utc=[ts, ts + pd.Timedelta(hours=2)],
                           last_exit_utc=[ts + pd.Timedelta(minutes=10), ts + pd.Timedelta(hours=2, minutes=5)]))
    wrb = pd.DataFrame(dict(
        ts_event=[ts - pd.Timedelta(minutes=45), ts + pd.Timedelta(minutes=5),
                  ts + pd.Timedelta(minutes=30), ts + pd.Timedelta(hours=5)],
        symbol=["ESZ5"] * 4, timeframe=["1m"] * 4))
    c0 = signal_counts(wrb, ep, "2025-10", "ESZ5", 0)
    # active window [14:00, 16:05]: signals at 14:05 (in-trade), 14:30 (free); 13:15 & 19:00 outside
    assert c0 == dict(total=4, active=2, active_in_trade=1, active_free=1, days_traded=1, n_trades=2), c0
    print(f"  pad=0 counts OK: {c0}")
    c60 = signal_counts(wrb, ep, "2025-10", "ESZ5", 60)
    assert c60["active"] == 3 and c60["active_free"] == 2, c60   # 13:15 signal now inside
    print(f"  pad=60 counts OK: {c60}")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
