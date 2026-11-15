#!/usr/bin/env python3
"""
p4_19_v6_freeze.py — P4.19: v6 — v5 plus the four vetted additions, frozen.
============================================================================
The additions, each with independent evidence:
  C7  AT THE LEVELS: signal price within E ticks of the 1m reaction-WRB body edge
      (twins, p=0.004: taken sit 7.6 tk closer than near-identical untaken twins;
      the user's levels claim). E swept over {8, 12, 16, 24}.
  C8  10-MINUTE CHART: the signal's zone overlaps a same-direction 10m zone
      (twins, p=0.0001).
  C9  NOT EXHAUSTED: 15-min oriented flow below 4.6 contracts/sec (tree: above it
      0/59 taken - the move already left; unknown flow passes).
  C10 VOLATILITY ALREADY UP: the 15 minutes ending 5 min before the signal
      covered MORE ground than typical (> 1.0x its trailing-2h median).
      HISTORY RECORDED: first framed as quiet-then-burst; the data said the
      opposite (taken 41% quiet vs skipped 60%) and his narration agrees -
      "contracting volatility" is when he STANDS ASIDE ("will try again when
      volatility increases"). Inverted before freezing; both variants tested
      (drop 0.264 / inverted 0.269), inverted kept.
Score = v5's six conditions + these four (0..10); cutoff k swept 3..8.
Objective unchanged (max F1, declared); read on ALL signals and PRESENT-ONLY.
Search set by design; v5 AND v6 both go to the reserved years.

RUN: python3 Tests/P4_entry_determination/p4_19_v6_freeze.py            (repo root)
OUT: p4_19_v6_table.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS     # noqa: E402
from p4_16_twins_nearmiss import v5_score               # noqa: E402
from p4_17_chat_alignment import mins_since_prev        # noqa: E402

TICK = 0.25
E_GRID = (8, 12, 16, 24)
FLOW15_CAP = 4.6
TRAIL = 120


def quiet_before(bars_m, comp_ns):
    """True when the 15 minutes ending 5 min before the signal covered <= 1.0x the
    trailing-2h median of that same 15-min measure (volatility contracting)."""
    bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
    tr15 = ((bars_m.high - bars_m.low) / TICK).rolling(15).sum()
    ref = tr15.rolling(TRAIL).median().shift(1)
    lag = tr15.shift(5).to_numpy(); refv = ref.shift(5).to_numpy()
    ib = np.searchsorted(bts, comp_ns - 60_000_000_000)
    ok = (ib < len(bts)) & (bts[np.clip(ib, 0, len(bts) - 1)] == comp_ns - 60_000_000_000)
    i = np.clip(ib, 0, len(bts) - 1)
    return np.where(ok, lag[i] <= refv[i], False), np.where(ok, lag[i] / refv[i], np.nan)


def run(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_12_features.csv"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    msg_ns = np.sort(pd.DatetimeIndex(msg.datetime_utc).as_unit("ns").asi8)
    parts = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        sm = df[df.month == month].reset_index(drop=True)
        q, _ = quiet_before(bars_m, sm.comp_ns.to_numpy(np.int64))
        sm["c10_vol_up"] = ~q
        parts.append(sm)
    df = pd.concat(parts, ignore_index=True)
    df["sc_v5"] = v5_score(df)
    df["c8_ov10"] = df.ov10.astype(bool)
    df["c9_not_exhausted"] = ~(df.flow_15m > FLOW15_CAP)      # NaN passes
    df["present30"] = np.array([mins_since_prev(msg_ns, int(t)) for t in df.comp_ns]) <= 30
    taken = df.taken.to_numpy(bool); base = taken.mean()
    print(f"signals={len(df)} taken={int(taken.sum())} base={base:.1%}")
    print("addition frequencies (all / taken / skipped):")
    for c in ["c8_ov10", "c9_not_exhausted", "c10_vol_up"]:
        print(f"  {c:18s} {df[c].mean():5.1%} / {df[taken][c].mean():5.1%} / {df[~taken][c].mean():5.1%}")

    best = None
    for E in E_GRID:
        c7 = df.en05_tf1_edge_tk.to_numpy(float) <= E
        sc = (df.sc_v5 + c7.astype(int) + df.c8_ov10.astype(int)
              + df.c9_not_exhausted.astype(int) + df.c10_vol_up.astype(int))
        for k in range(3, 9):
            fl = sc >= k
            if fl.sum() < 30:
                continue
            prec = taken[fl].mean(); rec = taken[fl].sum() / taken.sum()
            f1v = 2 * prec * rec / (prec + rec) if prec + rec else 0
            if best is None or f1v > best[0]:
                best = (f1v, E, k, int(fl.sum()), prec, rec, sc.copy())
    f1v, E, k, nf, prec, rec, sc = best
    print(f"\n===== v6 FROZEN: edge tolerance E={E} tk, require {k} of 10 =====")
    print(f"all signals:   flags {nf}, captures {rec:.1%}, precision {prec:.1%} ({prec/base:.1f}x)"
          f"  F1 {f1v:.3f}  (v5 was 0.289)")
    df["score_v6"] = sc
    for month in df.month.unique():
        d = df[df.month == month]; b = d.taken.mean()
        f = d[d.score_v6 >= k]
        print(f"  {month}: flags {len(f)}, captures {f.taken.sum()/d.taken.sum():.0%},"
              f" precision {f.taken.mean():.1%} ({f.taken.mean()/b:.1f}x month base)")
    p = df[df.present30]
    fp = p[p.score_v6 >= k]
    print(f"present-only:  base {p.taken.mean():.1%}; flags {len(fp)}, captures "
          f"{fp.taken.sum()/p.taken.sum():.0%}, precision {fp.taken.mean():.1%}"
          f" ({fp.taken.mean()/p.taken.mean():.1f}x)")
    df.to_csv(os.path.join(HERE, "p4_19_v6_table.csv"), index=False)
    print("\nREAD: v6 frozen at these settings; v5 AND v6 both go to the reserved years.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
