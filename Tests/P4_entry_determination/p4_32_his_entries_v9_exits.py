#!/usr/bin/env python3
"""
p4_32_his_entries_v9_exits.py — P4.32: HIS entries, OUR exits (spec v9), head to head.
=======================================================================================
USER (2026-11-15): "if we just entered where he entered, then followed Spec v9 for
exit, how do the winners, losers, rates etc compare?"
Construction: every one of his 313 discovery entries, at HIS recorded entry price
and minute and side; exits per STRATEGY_SPEC_v9 from the next bar (arm A pt1-always,
arm B momentum ladder; stops, fast-fail and the one-flip reversal included).
Each trade runs independently (no cooldown/one-position constraint - his episodes
are already non-overlapping and this isolates the EXIT stack; recorded choice).
HIS benchmark in the same units: his own points per trade = (last exit price -
first entry price) x side, exact for his single-entry single-exit episodes
(reported subset), so the comparison is pure exit-stack vs exit-stack.

RUN: python3 Tests/P4_entry_determination/p4_32_his_entries_v9_exits.py      (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_31_profit_v9 import wrb_flags, run_leg, ARMS      # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies                # noqa: E402


def row(name, pnl):
    pnl = np.asarray(pnl, float)
    w = pnl > 0
    return (f"| {name} | {len(pnl)} | {w.mean():.0%} | +{pnl[w].mean():.2f} / "
            f"{pnl[~w].mean():.2f} | {pnl.sum():+.1f} pts |")


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    pooled = {a: [] for a in ARMS}; pooled_his = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                  (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bars["rth"] = bars.session == "RTH"
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        pre = wrb_flags(bars)
        wb = wrb_bodies(bars[bars.rth].reset_index(drop=True)).merge(
            bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
        wb["body"] = (wb.close - wb.open).abs()
        med = wb.groupby(wb.session_date.astype(str)).body.median()
        sessions = sorted(set(bars.session_date.astype(str)))
        prev = {sx: float(med.get(sessions[i - 1], np.nan)) for i, sx in enumerate(sessions) if i > 0}
        sd = bars.session_date.astype(str).to_numpy()
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        his_pts = []
        arm_pnl = {a: [] for a in ARMS}
        for _, t in e_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            fb = int(np.searchsorted(bts, (en // 60_000_000_000) * 60_000_000_000))
            if fb >= len(bts) or not bars.rth.iloc[min(fb, len(bts)-1)]:
                continue
            P = float(np.asarray(t.entry_prices).ravel()[0])
            long = t.side == "long"
            uref = prev.get(sd[fb], None)
            if t.n_entries == 1 and t.n_exits == 1:
                X = float(np.asarray(t.exit_prices).ravel()[0])
                his_pts.append((X - P) if long else (P - X))
            for arm, p in ARMS.items():
                px, xi, reason, _ = run_leg(bars, pre, fb, P, long, 1.0, p, fb + 1, uref)
                pnl = (px - P) if long else (P - px)
                tot = pnl
                if reason == "faststop":
                    px2, xi2, r2, _ = run_leg(bars, pre, xi, px, not long, 1.0, p, xi + 1, uref)
                    tot += (px2 - px) if (not long) else (px - px2)
                arm_pnl[arm].append(tot)
        print(row(f"HIS exits {month} (1-in/1-out, exact pts)", his_pts))
        for arm in ARMS:
            print(row(f"v9-{arm[0]} exits on HIS entries {month}", arm_pnl[arm]))
            pooled[arm] += arm_pnl[arm]
        pooled_his += his_pts
    print(row("HIS exits POOLED", pooled_his))
    for arm in ARMS:
        print(row(f"v9-{arm[0]} on HIS entries POOLED", pooled[arm]))
    print("\nNOTE: pnl includes the reversal leg where the fast-fail flipped (spec v9).")
    print("READ: identical entries by construction - every difference is the exit stack.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
