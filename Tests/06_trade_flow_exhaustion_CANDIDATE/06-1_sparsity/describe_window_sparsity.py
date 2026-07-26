#!/usr/bin/env python3
"""
describe_window_sparsity.py  — read-only descriptive pass (NOT a test)
-------------------------------------------------------------------------------
PURPOSE
  Before freezing 07's estimator (Amihud-style impact ratio vs OLS slope) and
  before committing to 07b (with-trade-flow-ONLY impact), we need to know one
  empirical fact we have only ASSUMED so far: in a 60s Design-A window, how many
  seconds are actually usable?
    - "usable for 07b" = seconds where oriented (with-trade) flow is present.
    - "usable for an impact ratio" = whether price actually moves in the window.
  If those counts are routinely a handful, 07b's "may be uninformative by
  construction" tag is not a caveat — it is the expected outcome, and the slope
  estimator is dead on arrival. This script reports the distributions so the
  estimator choice is made FROM DATA, not from a prior.

WHAT IT IS NOT
  No AUC. No CI. No separation. No pass/fail. No estimator is frozen here.
  It only counts seconds. Deterministic (no RNG). Read-only on all source data.

POPULATION (this chat): 52 target_reached vs 40 failed_trades  (NOT the loser spine).
WINDOW (primary gate): Design A, W=60s, re-armed for 52/40:
    - failed_trades cut-window  : [max(entry, exit - W), exit)
    - target_reached peer-window: for each failed tau=hold, each reached peer with
                                   pt1_open_el > tau -> [max(entry, entry+tau - W), entry+tau)
  Context block: A1/A2/B 180s windows (one per trade, both arms) for comparison.

PLACEMENT
  Put this file in the SAME directory as trade_flow_exhaustion.py (it imports the
  frozen build_groups / read_per_second / constants from it, so the pt1 rule and
  per-second conventions cannot diverge from the frozen machinery).

RUN
  python3 describe_window_sparsity.py --config config.toml --wrb /path/to/wrb_1m.parquet
  (optional: --W 60   --out window_sparsity.csv)
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---
import argparse
import numpy as np
import pandas as pd

# --- frozen machinery: single source of truth, do not re-implement here ---
from trade_flow_exhaustion import (
    build_groups, read_per_second, load_paths,
    TICK, MAX_GAP_S, ROLL_JUMP_TICKS, S,
)


def describe_window(sec, buyv, sellv, mid, ws, we, side):
    """Count usable seconds in [ws, we). Pure description; mirrors score()'s slicing
    exactly so these counts correspond to the windows the real test will score."""
    ws_s = np.int64(pd.Timestamp(ws).value // 1_000_000_000)
    we_s = np.int64(pd.Timestamp(we).value // 1_000_000_000)
    a = np.searchsorted(sec, ws_s, "left")
    b = np.searchsorted(sec, we_s, "left")
    s = sec[a:b]; bv = buyv[a:b]; sv = sellv[a:b]; mz = mid[a:b]
    n = len(s)
    span = int(we_s - ws_s)  # nominal window length in seconds (<=W)

    flagged = False
    n_midmove_sec = 0
    sum_abs_dmid_ticks = 0.0
    if n >= 2:
        ds = np.diff(s)
        if ds.max() > MAX_GAP_S:
            flagged = True
        dmid = np.abs(np.diff(mz))
        if (dmid / TICK).max() > ROLL_JUMP_TICKS:
            flagged = True
        n_midmove_sec = int((dmid > 0).sum())
        sum_abs_dmid_ticks = float(dmid.sum() / TICK)

    sgn = 1.0 if side == "long" else -1.0
    oriented = (bv - sv).astype(float) * sgn          # >0 = net pressure WITH the trade
    withvol = bv if side == "long" else sv            # with-trade aggressor volume

    return dict(
        span_s=span,
        n_active_sec=int(n),                          # seconds with ANY book/trade row (~wall seconds)
        n_trade_sec=int(((bv + sv) > 0).sum()),       # seconds with any trade print
        n_with_flow_sec=int((oriented > 0).sum()),    # 07b subset (net oriented > 0)
        n_withvol_sec=int((withvol > 0).sum()),       # alt 07b subset (with-aggressor vol present)
        n_midmove_sec=n_midmove_sec,                  # seconds price moved (Amihud numerator support)
        sum_abs_dmid_ticks=sum_abs_dmid_ticks,        # total |dmid| in ticks (Amihud numerator)
        flagged=bool(flagged),
    )


def pctl(series):
    a = np.asarray(series, float); a = a[~np.isnan(a)]
    if len(a) == 0:
        return None
    q = np.percentile(a, [0, 10, 25, 50, 75, 90, 100])
    return dict(n=len(a), mean=float(a.mean()),
                p0=q[0], p10=q[1], p25=q[2], p50=q[3], p75=q[4], p90=q[5], p100=q[6])


def show(label, df, cols):
    print(f"\n-- {label}  (windows: {len(df)}; flagged/excluded from stats below: "
          f"{int(df['flagged'].sum())}) --")
    d = df[~df["flagged"]]
    hdr = f"  {'metric':<20} {'n':>4} {'mean':>7} {'min':>5} {'p10':>5} {'p25':>5} " \
          f"{'p50':>5} {'p75':>5} {'p90':>5} {'max':>5}"
    print(hdr)
    for c in cols:
        s = pctl(d[c])
        if s is None:
            print(f"  {c:<20}  (no valid windows)")
            continue
        print(f"  {c:<20} {s['n']:>4} {s['mean']:>7.1f} {s['p0']:>5.0f} {s['p10']:>5.0f} "
              f"{s['p25']:>5.0f} {s['p50']:>5.0f} {s['p75']:>5.0f} {s['p90']:>5.0f} {s['p100']:>5.0f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--W", type=int, default=60, help="Design A window seconds (frozen primary = 60)")
    ap.add_argument("--out", default="window_sparsity.csv")
    args = ap.parse_args()

    ep_path, windowed = load_paths(args.config)
    g = build_groups(ep_path, args.wrb)          # frozen pt1 / Reading-B grouping

    failed = g[g.group == "failed_trades"].copy()
    reached = g[g.group == "target_reached"].copy()
    print(f"[build] target_reached={len(reached)}  failed_trades={len(failed)}  "
          f"(expected 52 / 40 for Oct ESZ5)")

    W = S(args.W)
    rows = []

    # ---- Design A (PRIMARY GATE) ----
    # failed_trades cut-windows
    for _, f in failed.iterrows():
        ws = max(f.entry, f.exit - W); we = f.exit
        rows.append(("designA_failed_cut", f.uid, f.side, ws, we, "", float(f.hold)))
    # target_reached peer-windows (each failed tau, each eligible still-pre-pt1 peer)
    n_pairings = 0
    for _, f in failed.iterrows():
        tau = float(f.hold)
        elig = reached[reached.pt1_open_el > tau]
        for _, r in elig.iterrows():
            anc = r.entry + S(tau)
            ws = max(r.entry, anc - W); we = anc
            rows.append(("designA_reached_peer", r.uid, r.side, ws, we, f.uid, tau))
            n_pairings += 1
    print(f"[designA] failed cut-windows={len(failed)}  reached peer-windows={n_pairings} "
          f"(same reached trade appears at multiple tau by construction)")

    # ---- A1/A2/B 180s context windows (one per trade, both arms) ----
    for arm_name, arm in [("target_reached", reached), ("failed_trades", failed)]:
        for _, r in arm.iterrows():
            for tag in ["a1", "a2", "b"]:
                rows.append((f"{tag}_{arm_name}", r.uid, r.side, r[f"{tag}_s"], r[f"{tag}_e"], "", np.nan))

    win = pd.DataFrame(rows, columns=["window_class", "uid", "side", "ws", "we", "generated_by", "tau_s"])

    # ---- one streamed per-second read covering every window ----
    t_min = win["ws"].min(); t_max = win["we"].max()
    print(f"[read] streaming per-second ESZ5 trade flow in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[read] per-second rows: {len(sec):,} ({len(sec)/3600:.1f} grid-hours)")

    # ---- describe every window ----
    desc = [describe_window(sec, buyv, sellv, mid, r.ws, r.we, r.side) for _, r in win.iterrows()]
    win = pd.concat([win.reset_index(drop=True), pd.DataFrame(desc)], axis=1)

    metrics = ["span_s", "n_active_sec", "n_trade_sec", "n_with_flow_sec",
               "n_withvol_sec", "n_midmove_sec", "sum_abs_dmid_ticks"]

    print("\n" + "=" * 78)
    print("PRIMARY GATE — Design A, W={}s. The decision metrics are n_with_flow_sec".format(args.W))
    print("(07b subset size) and n_midmove_sec / sum_abs_dmid_ticks (impact-ratio support).")
    print("=" * 78)
    show("Design A — failed_trades cut-windows", win[win.window_class == "designA_failed_cut"], metrics)
    show("Design A — target_reached peer-windows", win[win.window_class == "designA_reached_peer"], metrics)

    print("\n" + "=" * 78)
    print("CONTEXT — A1/A2/B 180s windows (denser by construction; one per trade)")
    print("=" * 78)
    for tag in ["a1", "a2", "b"]:
        for arm in ["failed_trades", "target_reached"]:
            show(f"{tag.upper()} — {arm}", win[win.window_class == f"{tag}_{arm}"], metrics)

    win.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}  ({len(win)} windows)")
    print("\nHOW TO READ (paste the Design A blocks back):")
    print("  * n_with_flow_sec p50 -> typical usable seconds for 07b in a 60s window.")
    print("      >=~20 : slope estimable, ratio comfortable.")
    print("      ~5-15 : ratio (Amihud) viable, slope fragile.")
    print("      <=~5  : 07b uninformative-by-construction is the EXPECTED result; do not freeze slope.")
    print("  * n_midmove_sec / sum_abs_dmid_ticks ~0 -> price barely moves; an impact RATIO has no")
    print("      numerator signal in that window regardless of flow density.")
    print("  * Compare failed vs reached peer columns: a large gap in usable seconds between arms is")
    print("      itself a confound (window-length/activity composition), to be reported, not a result.")


if __name__ == "__main__":
    main()
