#!/usr/bin/env python3
"""
test_behavioral_baseline.py — MAE / time-stop: is his exit just a stop? (separation gate)
-------------------------------------------------------------------------------
THE QUESTION (the one outstanding null could resolve)
  Every exit-anchored microstructure lens came back null (impact) or confound-suspect
  (raw movement = the cut trigger sitting in the window). The simplest competing
  explanation for wrbtrader's cuts is a MECHANICAL RISK RULE with zero order-flow:
  "exit when price has gone against entry by X" (a stop) or "exit after T minutes".
  This is the BEHAVIORAL BASELINE. If a dumb adverse-excursion or duration measure
  separates losing exits from reached trades as well as the tape did, his exits are
  substantially a stop and the exit-microstructure thesis narrows hard.

  This is the SEPARATION gate (framing 1). It asks "does MAE / hold DISTINGUISH the
  groups", reusing the same Design-A + AUC + CI machinery. The harder REPRODUCTION
  test (framing 2: does ONE threshold fire at his actual exit times — CURRENT_STATE
  Question 4) is a SEPARATE later build, run only if this gate separates.

CONTRAST (clean, from the behavioral relabel): losing_trade (16) vs reached_target (47).
  below_target_win (29, profitable early-exits) held OUT — that is the point of the relabel.

FEATURE — MAE (Sweeney, 1996), from ENTRY, BAR-DOMAIN (es_1m_front 1m bars)
  Adverse excursion = how far price ran AGAINST the entry during the holding window.
    long : MAE = max(0, entry_price - min(bar lows in window))      [points]
    short: MAE = max(0, max(bar highs in window) - entry_price)     [points]
  Bar-domain by design: a behavioral baseline built from tick data is not a behavioral
  baseline (same logic that kept 08 on bars). 1m bar lows/highs are what a screen-watcher
  sees. entry_price extracted from entry_prices[0] (Oct verified single-entry, unscaled;
  entry/exit reconcile with realized_pnl at corr 1.0).

CUT-TIME-MATCHED (Design A, but from ENTRY not trailing-W)
  MAE is cumulative-from-entry, so its window is [entry, anchor], NOT the trailing 60s used
  by the flow tests. Matched the same way: each loser's MAE over [entry, cut] vs reached
  peers (still pre-pt1 at tau=loser hold) MAE over [entry, entry+tau]. Same elapsed exposure,
  so this is not "losers held longer" — it is "at equal time in trade, did it go against him
  more". Per-cut AUC = P(reached MAE > loser MAE); cluster-bootstrap CI over the 16 losers.
  Reuses spine.rank_auc / cluster_boot_ci / two_sided (stats), local from-entry windows.

  Pre-registered TWO-SIDED for consistency, but the prior is explicit: losers expected to
  show LARGER adverse excursion (P < 0.5). A clear P<0.5 with CI excluding 0.5 = "adverse
  excursion separates" = stop-consistent.

TIME-STOP (separation, population-level)
  Does hold duration alone separate losing from reached? Population AUC on hold (cannot be
  cut-time-matched — hold IS the matching variable). Reported with both medians so the
  DIRECTION is legible: losers cut FASTER (shorter hold) would mean a time-stop does NOT
  explain them (he exits before any clock fires); losers held LONGER is time-stop-consistent.

Deterministic (seed=0). Read-only. PRIMARY = MAE Design A.

RUN
  python3 test_behavioral_baseline.py --config ../../config.toml --wrb ../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---
import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
TICK = 0.25


def scalar(v):
    return float(np.asarray(v).ravel()[0])


def load_groups_with_prices(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    ep_path = cfg["paths"]["episodes"]; es1m = cfg["paths"]["es_1m_front"]
    g = build_groups(ep_path, wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    # attach entry price from the episodes file (build_groups drops it)
    ep = pd.read_parquet(ep_path)
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, es1m


def load_bars(es1m_path):
    cols = ["ts_event", "instrument_id", "high", "low", "session_date"]
    d = pd.read_parquet(es1m_path, columns=cols)
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    return d.sort_values("ts_event").reset_index(drop=True)


def make_mae_fn(bars):
    bar_sec = (bars["ts_event"].astype("int64") // 1_000_000_000).to_numpy()
    hi = bars["high"].to_numpy(); lo = bars["low"].to_numpy()

    def mae(side, entry_price, t_entry, t_anchor):
        """Max adverse excursion (points, >=0) from entry over bars overlapping [entry, anchor]."""
        e_s = pd.Timestamp(t_entry).value // 1_000_000_000
        a_s = pd.Timestamp(t_anchor).value // 1_000_000_000
        if a_s <= e_s:
            return np.nan
        # bars whose start is < anchor and whose [start, start+60) reaches >= entry
        i0 = int(np.searchsorted(bar_sec, e_s - 60, "left"))
        i1 = int(np.searchsorted(bar_sec, a_s, "left"))     # bars starting before anchor
        if i1 <= i0:
            return np.nan
        H = hi[i0:i1]; L = lo[i0:i1]
        if side == "long":
            return float(max(0.0, entry_price - np.min(L)))
        return float(max(0.0, np.max(H) - entry_price))
    return mae


def mae_designA(losers, reached, mae_fn, seed=0):
    """Cut-time-matched MAE from entry. Per-cut AUC = P(reached MAE > loser MAE)."""
    per_cut = []
    loser_mae, reached_mae_pooled = [], []
    for _, f in losers.iterrows():
        cv = mae_fn(f.side, f.entry_price, f.entry, f.exit)
        if np.isnan(cv):
            continue
        loser_mae.append(cv)
        tau = float(f.hold)
        peers = reached[reached.pt1_open_el > tau]
        pv = []
        for _, r in peers.iterrows():
            anc = r.entry + S(tau)
            v = mae_fn(r.side, r.entry_price, r.entry, anc)
            if not np.isnan(v):
                pv.append(v); reached_mae_pooled.append(v)
        if pv:
            pv = np.asarray(pv, float)
            per_cut.append((np.sum(pv > cv) + 0.5 * np.sum(pv == cv)) / len(pv))
    ci = spine.cluster_boot_ci(per_cut, seed=seed)
    return ci, np.array(loser_mae), np.array(reached_mae_pooled)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    g, es1m = load_groups_with_prices(args.config, args.wrb)
    losers = g[g.is_loser].copy()                                    # losing_trade = 16
    reached = g[(g.group == "target_reached") & (~g.is_loser)].copy()  # reached_target = 47
    print(f"[baseline] losing_trade={len(losers)}  reached_target={len(reached)}  (expect 16 / 47)")
    assert len(losers) == 16 and len(reached) == 47, "contrast drift vs relabel 16/47"

    bars = load_bars(es1m)
    print(f"[baseline] es_1m_front ESZ5 Oct bars: {len(bars):,}")
    mae_fn = make_mae_fn(bars)

    # ---- PRIMARY: MAE cut-time-matched Design A ----
    ci, lmae, rmae = mae_designA(losers, reached, mae_fn, seed=args.seed)
    print(f"\n===== MAE (from entry, bars) — Design A cut-time-matched (PRIMARY, two-sided) =====")
    print(f"  per-cut AUC = P(reached MAE > loser MAE)")
    flag = "CI EXCLUDES 0.5 (separates)" if ci["excludes_half"] else "CI includes 0.5 (no separation)"
    print(f"  point = {ci['mean']:.3f}   95% CI [{ci['lo']:.3f}, {ci['hi']:.3f}]   cuts={ci['n']}   -> {flag}")
    print(f"  prior: losers expected LARGER adverse excursion -> P < 0.5 = stop-consistent.")
    print(f"  pooled MAE (points): loser med={np.nanmedian(lmae):.2f} (n={len(lmae)})  "
          f"reached-peer med={np.nanmedian(rmae):.2f} (n={len(rmae)})")

    # ---- TIME-STOP: hold-duration separation, population-level ----
    print(f"\n===== TIME-STOP: hold duration separation (population, two-sided) =====")
    lh = losers["hold"].to_numpy() / 60.0; rh = reached["hold"].to_numpy() / 60.0
    auc, nr, nl = spine.rank_auc(rh, lh)
    strength, direction = spine.two_sided(auc)
    print(f"  AUC(reached hold > loser hold) = {auc:.3f}  two-sided={strength:.3f} ({direction})")
    print(f"  hold minutes: loser med={np.median(lh):.1f}  reached med={np.median(rh):.1f}")
    print(f"  read: losers SHORTER hold => he cuts before a clock fires (time-stop does NOT explain);")
    print(f"        losers LONGER hold => time-stop-consistent.")

    print(f"\n[baseline] DONE. If MAE separates (P<0.5, CI clear), adverse excursion is a stop-like")
    print(f"  explanation for the cuts -> the REPRODUCTION test (one threshold at his exit times) is")
    print(f"  the worthwhile next build. If MAE does NOT separate, the 'just a stop' story weakens.")


if __name__ == "__main__":
    main()
