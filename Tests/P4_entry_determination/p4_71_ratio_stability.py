#!/usr/bin/env python3
"""
p4_71_ratio_stability.py — P4.71: is the day-range / minute-TR ratio (the
frozen 22.7) actually stable across regimes?
=============================================================================
Computed from 1-minute bars only, across the full front-month history - no
strategy is run and no reserved month's per-second data is touched. Per month:
median over RTH sessions of (session range / mean 1-min true range). If the
ratio is flat across years while volatility levels swing, freezing it is
justified; if it drifts, it joins the adaptive set (trailing version) by plan
amendment BEFORE validation.

RUN: python3 Tests/P4_entry_determination/p4_71_ratio_stability.py        (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

TICK = 0.25


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    r = es[es.session == "RTH"].copy()
    r["sd"] = r.session_date.astype(str)
    r = r.sort_values("ts_event")
    pc = r.groupby("sd").close.shift(1)
    tr = np.maximum(r.high - r.low,
                    np.maximum((r.high - pc).abs(), (r.low - pc).abs())) / TICK
    r["tr"] = tr.fillna((r.high - r.low) / TICK)
    g = r.groupby("sd")
    day = pd.DataFrame({"rng": (g.high.max() - g.low.min()) / TICK,
                        "mtr": g.tr.mean()})
    day = day[(day.mtr > 0) & (day.rng > 0)]
    day["ratio"] = day.rng / day.mtr
    day["ym"] = [s[:7] for s in day.index]
    by_m = day.groupby("ym").agg(ratio_med=("ratio", "median"),
                                 rng_med=("rng", "median"), n=("ratio", "size"))
    by_y = day.assign(y=[s[:4] for s in day.index]).groupby("y").agg(
        ratio_med=("ratio", "median"), ratio_iqr_lo=("ratio", lambda x: np.percentile(x, 25)),
        ratio_iqr_hi=("ratio", lambda x: np.percentile(x, 75)),
        rng_med=("rng", "median"))
    print("Per YEAR: median (day range / mean 1-min TR), with the median day range")
    print("alongside to show how much the volatility LEVEL moved while the ratio did/didn't:\n")
    print("| Year | Ratio: median (middle half) | Median day range (ticks) | Sessions |")
    print("|---|---|---|---|")
    ny = day.assign(y=[s[:4] for s in day.index]).groupby("y").size()
    for y, rr in by_y.iterrows():
        print(f"| {y} | {rr.ratio_med:.1f} ({rr.ratio_iqr_lo:.1f}-{rr.ratio_iqr_hi:.1f}) "
              f"| {rr.rng_med:.0f} | {ny[y]} |")
    tm = by_m.loc[[m for m in by_m.index if m in ("2025-10", "2022-02", "2021-09",
                                                  "2024-11", "2023-02", "2023-07",
                                                  "2025-04", "2026-03")]]
    print("\nKey months:")
    for m, rr in tm.iterrows():
        print(f"  {m}: ratio {rr.ratio_med:.1f} | median day range {rr.rng_med:.0f} ticks")
    print(f"\nAll months: ratio median {by_m.ratio_med.median():.1f}, "
          f"range {by_m.ratio_med.min():.1f}-{by_m.ratio_med.max():.1f}; "
          f"day-range medians span {by_m.rng_med.min():.0f}-{by_m.rng_med.max():.0f} ticks")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
