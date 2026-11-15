#!/usr/bin/env python3
"""
p4_7_trailing_flow.py — P4.7: T-EN09, trailing oriented order flow before entries.
===================================================================================
USER FRAME (2026-11-15): the exit-confirmed flow patterns (T-DF10 0.805 / T-DF11
0.683) measured in the time LEADING UP to his entries; taken trades first, skipped
pool as yardstick. All windows are TRAILING, ending at the entry/signal moment.

DATA: Data/inputs/flow_per_sec_{2025-10,2022-02}.parquet — per-second aggressor
flow (buyv, sellv, mid last) reduced on the user's Mac from the windowed MBP-10
extracts by Tests/P4_entry_determination/reduce_flow_device.py (copy committed
here), instrument-filtered (ESZ5 294973 / ESH2 5782). Same construction as the
exit program's read_per_second. Checksums in Data/inputs/CHECKSUMS.sha256.

MEASURE (same construction as the exit program's score()): oriented per-second
signed flow = (buyv - sellv) * (+1 long / -1 short), level = mean over seconds
PRESENT in the window; window flagged -> NaN when the max gap between present
seconds exceeds 120 s (window reaches outside the extract or dead tape) or a
mid jump exceeds 40 ticks. Orientation: trade side for entries; the signal
WRB's own direction for signals (p4_6 docstring choice, fixed before stats).
CELLS (pre-registered in T-EN09): oriented_flow_5m [PRIMARY], oriented_flow_15m.
Direction: taken > skipped. Descriptive: 60-min profile in 5-min buckets.

RUN: python3 Tests/P4_entry_determination/p4_7_trailing_flow.py            (repo root)
     python3 Tests/P4_entry_determination/p4_7_trailing_flow.py --selftest
OUT: p4_7_trailing_flow.csv (per-signal) + printed anatomy and probe tables.
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS   # noqa: E402
from p4_4_probes import rank_auc, boot_ci             # noqa: E402

TICK = 0.25
MAX_GAP_S = 120
ROLL_JUMP_TICKS = 40


def flow_level(sec, buyv, sellv, mid, end_ns, win_s, long_side):
    """Mean oriented per-second flow over [end-win, end); NaN + flag like the exit
    program's score(): gap > MAX_GAP_S or mid jump > ROLL_JUMP_TICKS -> NaN."""
    e = np.int64(end_ns // 1_000_000_000)
    a = np.searchsorted(sec, e - win_s, "left")
    b = np.searchsorted(sec, e, "left")
    s, bv, sv, mz = sec[a:b], buyv[a:b], sellv[a:b], mid[a:b]
    if len(s) < 1:
        return np.nan
    if len(s) >= 2 and (np.diff(s).max() > MAX_GAP_S or
                        (np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS):
        return np.nan
    sgn = 1.0 if long_side else -1.0
    return float(np.mean((bv - sv).astype(float) * sgn))


def load_flow(repo, month):
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}.parquet"))
    return (f.sec.to_numpy(np.int64), f.buyv.to_numpy(np.int64),
            f.sellv.to_numpy(np.int64), f.mid.to_numpy(float))


def run(repo):
    sig = pd.read_csv(os.path.join(HERE, "p4_3b_signal_table.csv"))
    sig["comp_ns"] = pd.DatetimeIndex(pd.to_datetime(sig.comp, utc=True)).as_unit("ns").asi8
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))

    print("===== Part 1: TAKEN-TRADE ANATOMY (313 entries, oriented by trade side) =====")
    prof_rows = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        sec, bv, sv, mz = load_flow(repo, month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        f5, f15, prof = [], [], []
        for _, t in e.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            is_long = t.side == "long"
            f5.append(flow_level(sec, bv, sv, mz, en, 300, is_long))
            f15.append(flow_level(sec, bv, sv, mz, en, 900, is_long))
            prof.append([flow_level(sec, bv, sv, mz, en - k * 300_000_000_000, 300, is_long)
                         for k in range(11, -1, -1)])   # buckets -60..-55 ... -5..0 min
        f5, f15 = np.array(f5), np.array(f15)
        pm = np.nanmedian(np.array(prof, float), axis=0)
        prof_rows.append(pm)
        print(f"[{month}] entries={len(e)}  oriented flow, median (contracts/sec):"
              f" last 5 min {np.nanmedian(f5):+.2f} | last 15 min {np.nanmedian(f15):+.2f}"
              f" | positive share 5m {np.nanmean(f5 > 0):.0%} (n valid {np.isfinite(f5).sum()})")
        print("  60-min profile toward entry (median oriented flow per 5-min bucket):")
        print("   " + " ".join(f"{v:+.2f}" for v in pm) + "   (oldest -> entry)")

    print("\n===== Part 2: T-EN09 probe — signals, taken vs skipped (oriented by signal direction) =====")
    rows = []
    for month, sym in MONTHS:
        sec, bv, sv, mz = load_flow(repo, month)
        sm = sig[sig.month == month]
        for _, srow in sm.iterrows():
            is_long = srow.direction == "bullish"
            rows.append(dict(month=month, taken=bool(srow.taken),
                             flow_5m=flow_level(sec, bv, sv, mz, int(srow.comp_ns), 300, is_long),
                             flow_15m=flow_level(sec, bv, sv, mz, int(srow.comp_ns), 900, is_long)))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "p4_7_trailing_flow.csv"), index=False)
    T, K = df[df.taken], df[~df.taken]
    print(f"[frame] taken={len(T)} skipped={len(K)}; windows flagged/outside extract -> NaN "
          f"(valid: taken {T.flow_5m.notna().sum()}/{len(T)}, skipped {K.flow_5m.notna().sum()}/{len(K)})")
    print(f"\n{'cell':34s} {'AUC':>6} {'95% CI':>16} {'clears':>7}   taken vs skipped (median, contracts/sec)")
    for col, name in [("flow_5m", "oriented flow, last 5 min [PRIMARY]"),
                      ("flow_15m", "oriented flow, last 15 min")]:
        ci = boot_ci(T[col], K[col])
        flag = "** YES" if ci["clears"] else "no"
        print(f"{name:34s} {ci['auc']:>6.3f} [{ci['lo']:.3f},{ci['hi']:.3f}] {flag:>7}   "
              f"{np.nanmedian(T[col]):+.2f} vs {np.nanmedian(K[col]):+.2f}")
    print("\nper-month robustness (AUC, primary):")
    for month in df.month.unique():
        d = df[df.month == month]
        print(f"  {month}: flow_5m={rank_auc(d[d.taken].flow_5m, d[~d.taken].flow_5m):.3f}")
    print("\nREAD: orientation caveat (registry): oriented-by-chosen-side vs oriented-by-")
    print("signal-direction partly reflects side choice. Day clustering applies. Reserved")
    print("years decide for real.")


def selftest():
    print("=== SELF-TEST ===")
    sec = np.arange(1000, 1300, dtype=np.int64)          # 300 s of tape
    bv = np.full(300, 5, np.int64); sv = np.full(300, 2, np.int64)
    mid = np.full(300, 5000.0)
    end = np.int64(1300) * 1_000_000_000
    lv = flow_level(sec, bv, sv, mid, end, 300, True)
    assert abs(lv - 3.0) < 1e-9, lv                      # (5-2)*+1 per second
    assert abs(flow_level(sec, bv, sv, mid, end, 300, False) + 3.0) < 1e-9
    print("  oriented level long/short OK")
    sec2 = np.array([1000, 1290], np.int64)              # 290 s gap -> flagged
    assert np.isnan(flow_level(sec2, bv[:2], sv[:2], mid[:2], end, 300, True))
    print("  gap tripwire -> NaN OK")
    mid3 = np.array([5000.0, 5020.0])                    # 80-tick mid jump -> flagged
    sec3 = np.array([1250, 1260], np.int64)
    assert np.isnan(flow_level(sec3, bv[:2], sv[:2], mid3, end, 300, True))
    print("  roll-jump tripwire -> NaN OK")
    assert np.isnan(flow_level(sec, bv, sv, mid, np.int64(500) * 1_000_000_000, 300, True))
    print("  empty window -> NaN OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
