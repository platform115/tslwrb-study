#!/usr/bin/env python3
"""
p4_9_refine.py — P4.9: the entry score, version 2 (user corrections, 2026-11-15).
==================================================================================
Three user corrections to the six-condition score of p4_8:
  1. The zone-agreement condition was overkill (needed 3 of the 10/15m-heavy set).
     NEW C2: the signal's zone overlaps a same-direction zone on AT LEAST ONE of
     the 3m or 5m charts (his small timeframes; the 1m zone is the signal's own).
  2. The two tick thresholds (body >= 11 tk, 5-min path >= 62 tk, both medians)
     were arbitrary - and fixed tick numbers mean different things in quiet and
     wild months (Feb-2022 vs Oct-2025), which likely weakened the rule in Feb.
     NEW: size is measured against the market's own recent typical range, ATR
     (average true range over the prior 20 one-minute bars - Wilder 1978):
       C3: signal body >= 1 x ATR20  (the body alone beats a typical full bar)
       C4: last-5-min ground covered >= 5 x ATR20  (faster than typical tape)
     The threshold is the natural "bigger than typical = 1", not a picked number.
     A x0.75 / x1.0 / x1.25 sweep is printed to show the rule is not knife-edge.
  3. (Direction is handled in p4_10_direction.py.)
C1 (event within 15 min), C5 (flow leaning the signal's way), C6 (template
minute) unchanged. Same readout as p4_8. Constructive step - reserved years test.

RUN: python3 Tests/P4_entry_determination/p4_9_refine.py            (repo root)
     python3 Tests/P4_entry_determination/p4_9_refine.py --selftest
OUT: p4_9_score_v2.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS   # noqa: E402
from p4_2b_zone_mtf import zone_tables                # noqa: E402

TICK = 0.25
ATR_N = 20
SMALL_TFS = (3, 5)
V2_COLS = ["c1_kme_born15", "c2_small_tf_zone", "c3_body_vs_atr",
           "c4_tape_vs_atr", "c5_flow_with", "c6_template"]


def atr(bars: pd.DataFrame, n=ATR_N) -> np.ndarray:
    """ATR over the PRIOR n bars (signal bar excluded), ticks. Wilder's true range."""
    h, l, c = bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    pc = np.r_[np.nan, c[:-1]]
    tr = np.maximum(h, pc) - np.minimum(l, pc)
    tr[0] = h[0] - l[0]
    return (pd.Series(tr).rolling(n).mean().shift(1).to_numpy()) / TICK


def small_tf_overlap(sig_m, zt, comp_ns):
    """True when the signal's own zone overlaps a same-direction zone formed in the
    prior 2 days on the 3m or 5m chart (same intersection test as p4_3b)."""
    out = np.zeros(len(sig_m), bool)
    has = sig_m.has_whg.fillna(False).to_numpy()
    b_arr, t_arr = sig_m.whg_bottom.to_numpy(), sig_m.whg_top.to_numpy()
    d_arr = sig_m.direction.to_numpy()
    zc = {tf: (pd.DatetimeIndex(zt[tf].ts_event).as_unit("ns").asi8,
               zt[tf].whg_bottom.to_numpy(), zt[tf].whg_top.to_numpy(),
               zt[tf].direction.to_numpy()) for tf in SMALL_TFS}
    for i, cns in enumerate(comp_ns):
        if not has[i]:
            continue
        for tf in SMALL_TFS:
            zts, zb, ztp, zd = zc[tf]
            m = (zts + tf * 60e9 <= cns) & (zts >= cns - 2 * 86400e9)
            ov = m & ~((ztp < b_arr[i]) | (zb > t_arr[i])) & (zd == d_arr[i])
            if ov.any():
                out[i] = True
                break
    return out


def build(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_8_synthesis.csv"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    parts = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
        a20 = atr(bars_m)
        zt = zone_tables(bars_m, month)
        sm = df[df.month == month].reset_index(drop=True)
        comp_ns = sm.comp_ns.to_numpy(np.int64)
        ts_ns = comp_ns - 60_000_000_000          # bar open
        ib = np.searchsorted(bts, ts_ns)
        ok = (ib < len(bts)) & (bts[np.clip(ib, 0, len(bts) - 1)] == ts_ns)
        sm["atr20_tk"] = np.where(ok, a20[np.clip(ib, 0, len(bts) - 1)], np.nan)
        sm["c2_small_tf_zone"] = small_tf_overlap(sm, zt, comp_ns)
        parts.append(sm)
    df = pd.concat(parts, ignore_index=True)
    df["c3_body_vs_atr"] = df.body_tk >= df.atr20_tk
    df["c4_tape_vs_atr"] = df.en08_path_5m_tk >= 5 * df.atr20_tk
    df["score_v2"] = df[V2_COLS].sum(axis=1)
    return df


def readout(df, score_col, cond_cols, label):
    base = df.taken.mean()
    print(f"\n===== {label}: take rate by score =====")
    g = df.groupby(score_col).agg(n=("taken", "size"), tk=("taken", "sum"))
    for s, r in g.iterrows():
        print(f"  score {s}: {int(r.n):5d} signals, {int(r.tk):3d} taken, take rate {r.tk/r.n:6.1%}")
    print(f"\n{'k':>2} {'flagged':>8} {'entries captured':>17} {'take rate':>10} {'lift':>6}")
    for k in range(1, len(cond_cols) + 1):
        f = df[df[score_col] >= k]
        if not len(f):
            continue
        print(f"{k:>2} {len(f):>8} {f.taken.sum()/df.taken.sum():>16.1%} {f.taken.mean():>9.1%} {f.taken.mean()/base:>5.1f}x")
    for month in df.month.unique():
        d = df[df.month == month]; b = d.taken.mean()
        for k in (3, 4):
            f = d[d[score_col] >= k]
            print(f"  {month} k={k}: flagged {len(f)}, captures {f.taken.sum()/d.taken.sum():.0%},"
                  f" take rate {f.taken.mean():.1%} ({f.taken.mean()/b:.1f}x month base)")


def run(repo):
    df = build(repo)
    df.to_csv(os.path.join(HERE, "p4_9_score_v2.csv"), index=False)
    print(f"signals={len(df)} taken={int(df.taken.sum())} base={df.taken.mean():.1%}"
          f" | ATR20 median: {df.atr20_tk.median():.1f} tk"
          f" | per month: " + " ".join(f"{m}={df[df.month==m].atr20_tk.median():.1f}tk"
                                       for m in df.month.unique()))
    print("condition frequency (share of signals where true):")
    for c in V2_COLS:
        T, K = df[df.taken], df[~df.taken]
        print(f"  {c:18s} all {df[c].mean():5.1%} | taken {T[c].mean():5.1%} | skipped {K[c].mean():5.1%}")
    readout(df, "score_v2", V2_COLS, "SCORE v2 (user-corrected conditions)")
    print("\n===== threshold robustness: ATR multiplier sweep on C3/C4 (k=4 rule) =====")
    base = df.taken.mean()
    for mlt in (0.75, 1.0, 1.25):
        d = df.copy()
        d["c3x"] = d.body_tk >= mlt * d.atr20_tk
        d["c4x"] = d.en08_path_5m_tk >= mlt * 5 * d.atr20_tk
        sc = d[["c1_kme_born15", "c2_small_tf_zone", "c3x", "c4x",
                "c5_flow_with", "c6_template"]].sum(axis=1)
        f = d[sc >= 4]
        print(f"  x{mlt:4.2f}: flagged {len(f):4d}, captures {f.taken.sum()/d.taken.sum():5.1%},"
              f" take rate {f.taken.mean():5.1%} ({f.taken.mean()/base:.1f}x)")
    print("\nREAD: v2 is the frozen rule IF it holds up at least as well as v1 per month;")
    print("constructed on discovery months - reserved years are the test.")


def selftest():
    print("=== SELF-TEST ===")
    b = pd.DataFrame(dict(high=[10.0, 11, 12], low=[9.0, 10, 11], close=[9.5, 10.5, 11.5]))
    a = atr(b, n=2)
    # TR = [1.0, 1.5, 1.5]; mean2 of first two = 1.25 -> shifted to bar 2 -> /tick
    assert np.isnan(a[0]) and np.isnan(a[1]) and abs(a[2] - 1.25 / TICK) < 1e-9, a
    print("  ATR prior-bars-only OK")
    sig = pd.DataFrame(dict(has_whg=[True], whg_bottom=[5000.0], whg_top=[5002.0],
                            direction=["bullish"]))
    zt = {tf: pd.DataFrame(dict(
        ts_event=[pd.Timestamp("2025-10-06 13:00", tz="UTC")],
        whg_bottom=[5001.0], whg_top=[5003.0], direction=["bullish"])) for tf in SMALL_TFS}
    cns = np.array([pd.Timestamp("2025-10-06 14:00", tz="UTC").value])
    assert small_tf_overlap(sig, zt, cns)[0]
    zt2 = {tf: zt[tf].assign(direction="bearish") for tf in SMALL_TFS}
    assert not small_tf_overlap(sig, zt2, cns)[0]
    zt3 = {tf: zt[tf].assign(whg_bottom=5003.0, whg_top=5005.0) for tf in SMALL_TFS}
    assert not small_tf_overlap(sig, zt3, cns)[0]
    print("  small-TF overlap: hit / wrong-direction / disjoint OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
