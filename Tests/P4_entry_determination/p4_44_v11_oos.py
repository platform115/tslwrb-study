#!/usr/bin/env python3
"""
p4_44_v11_oos.py — P4.44: spec v11 on the reserved tick months.
================================================================
v11 = v10 + follow-stop (arms at +2.0, follows 2.5 behind best, never backwards)
+ early cut 1.5 (was 2.0). Chosen in-sample on a broad 18-cell ridge (T-EN47).
HONESTY NOTE: 2021-09 / 2024-11 were already read once for v10 (T-EN46), and the
"winners shrank" diagnosis from that read motivated the follow-stop - so this is
a SECOND look at these months, strong evidence but not pristine.

RUN: python3 Tests/P4_entry_determination/p4_44_v11_oos.py --month 2021-09
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_31_profit_v9 import wrb_flags                  # noqa: E402
from p4_42_v10_oos import score_month, WAIT            # noqa: E402
from p4_43_exit_sharpen import run_leg2, BASE          # noqa: E402

V11 = {**BASE, "trail": (2.0, 2.5), "early": 1.5}


def run(repo, month):
    sig, bars, sym = score_month(repo, month)
    print(f"[{month}] {sym}: {len(sig)} completions, flagged>=6: {(sig.score >= 6).sum()}")
    bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
    cl = bars.close.to_numpy(); o = bars.open.to_numpy()
    h, l = bars.high.to_numpy(), bars.low.to_numpy()
    pre = wrb_flags(bars)
    pnl = []; busy = -1
    for _, r in sig[sig.score >= 6].sort_values("comp_ns").iterrows():
        ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
        if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
            continue
        fb0 = ib + 1
        if fb0 >= len(bts) or not bars.rth.iloc[fb0] or fb0 <= busy:
            continue
        mv = cl[ib] - cl[ib - 5]
        if mv == 0:
            continue
        long = mv > 0
        uref = r.uref if np.isfinite(r.uref) else None
        lvl = h[ib] if long else l[ib]
        fb = None
        for j in range(fb0, min(fb0 + WAIT, len(bars))):
            if not bars.rth.iloc[j]:
                break
            if (h[j] >= lvl) if long else (l[j] <= lvl):
                fb = j
                fill = max(lvl, o[j]) if long else min(lvl, o[j])
                break
        if fb is None:
            continue
        px, xi, reason = run_leg2(bars, pre, fb, fill, long, V11, fb + 1, uref)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xi2, _ = run_leg2(bars, pre, xi, px, not long, V11, xi + 1, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            xi = xi2
        pnl.append(tot)
        busy = xi + 5
    a = np.asarray(pnl); w = a > 0
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    lo, hi = month_bounds(month)
    e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    hw = e_m.realized_pnl > 0
    print("\n| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    print(f"| v11 {month} | {len(a)} | {w.mean():.0%} | "
          f"+{a[w].mean():.2f} / {a[~w].mean():.2f} | {a.sum():+.1f} pts |")
    print(f"| HIS {month} | {len(e_m)} | {hw.mean():.0%} | +{e_m.realized_pnl[hw].mean():.1f} / "
          f"{e_m.realized_pnl[~hw].mean():.1f} (as parsed) | {e_m.realized_pnl.sum():+.0f} (as parsed) |")
    print("\nREAD: second look at a reserved month (v10 already read here once);")
    print("recorded as-is, no retuning against it.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--month", required=True)
    a = ap.parse_args()
    run(a.repo, a.month)
