#!/usr/bin/env python3
"""
test_06-6_mae_reproduction.py — REPRODUCTION: does a fixed adverse-stop reproduce his exits?
-------------------------------------------------------------------------------
06-5 showed losing exits SEPARATE from runners on adverse excursion (MAE Design A P=0.227).
Separation != reproduction. This asks CURRENT_STATE Question 4: does a SINGLE deterministic
rule "exit when adverse excursion from entry >= X" actually FIRE at (roughly) his exit times,
catching losers while sparing runners? Framing 2 (reproduction) x instrument (b) per-second mid.

WHY PER-SECOND MID (not 1m bars): reproduction is a TIMING question (losers held ~1.7 min; bar
resolution can't tell "fired at his exit" from "fired 50s earlier"). Per-second MID is finer price
sampling, NOT order-flow/depth — it buys timing precision without smuggling in microstructure info.
Measuring from the exact entry timestamp also FIXES the entry-bar-inclusion approximation of 06-5.

WHAT IS ACTUALLY NEW vs 06-5
  The classification half (losers hit X more than reached) == 06-5 separation re-expressed as a
  sweepable curve; NOT new. NEW = (1) threshold in POINTS + precision/recall (operational), and
  (2) TIMING: when adverse first crosses X, did he cut THEN (gap~0 => X is his de-facto stop) or
  hold PAST it (gap large => tolerated more / cut for another reason). 06-5 could not see timing.

DECISIVE STAT = OVERLAP, not medians. Reproduction lives/dies on whether RUNNERS dip into the same
adverse band losers exit at. If many reached transiently hit -X before running to target, a stop at
X kills winners and does NOT reproduce him, regardless of median gap. So we report:
  loser EXIT-adverse distribution (= |loss| pts)  vs  reached MAX pre-pt1 adverse distribution.

PRE-REGISTERED READ (declared before numbers)
  reproduction-PLAUSIBLE: exists X with sensitivity high (catches losers) AND specificity high
    (spares reached before pt1) AND tight loser timing gaps (cut near the X-crossing).
  reproduction-FAILS: sensitivity and false-kills rise together (no clean X), OR losers cut at
    scattered adverse levels (no consistent stop).
  The X-sweep is a DIAGNOSTIC CURVE. We do NOT pick a "best X" (= fitting October). Any operating
  threshold is holdout-validated elsewhere.

CONTRAST (06-4 relabel): losing_trade (16) vs reached_target (47). below_target_win (29) reported
  as CONTEXT (what a stop would do to his profitable early-exits).

INSTRUMENT CAVEAT: frozen reader gives LAST mid per second -> slightly under-measures the intra-
second extreme a real stop triggers on. Exploratory first cut; refine to per-second min/max-mid if
reproduction looks real. n=16 losers, one month, discovery.

RUN (from 06-6_reproduction/)
  python3 test_06-6_mae_reproduction.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
TICK = 0.25


def scalar(v):
    return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    ep_path = cfg["paths"]["episodes"]; windowed = cfg["run"]["resolved"]["windowed_parquet"]
    g = build_groups(ep_path, wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(ep_path)
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, windowed


def running_adverse(sec, mid, entry_ts, anchor_ts, side, entry_price):
    """Per-second running max adverse excursion (points, >=0) from entry over [entry, anchor).
    Returns (secs_rel, run_adv) or None. secs_rel = seconds since entry."""
    e_s = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
    a_s = np.int64(pd.Timestamp(anchor_ts).value // 1_000_000_000)
    if a_s <= e_s:
        return None
    i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, a_s, "left")
    if i1 <= i0:
        return None
    s = sec[i0:i1]; mz = mid[i0:i1]
    adv = (entry_price - mz) if side == "long" else (mz - entry_price)
    adv = np.maximum(0.0, adv)
    return (s - e_s).astype(float), np.maximum.accumulate(adv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    args = ap.parse_args()

    g, windowed = load(args.config, args.wrb)
    losers = g[g.is_loser].copy()
    reached = g[(g.group == "target_reached") & (~g.is_loser)].copy()
    btw = g[(g.group == "failed_trades") & (~g.is_loser)].copy()   # below_target_win, context
    print(f"[06-6] losing_trade={len(losers)}  reached_target={len(reached)}  below_target_win={len(btw)}")
    assert len(losers) == 16 and len(reached) == 47, "contrast drift vs relabel 16/47"

    t_min = g["first_entry_utc"].min() if "first_entry_utc" in g else g["entry"].min()
    t_max = g["exit"].max() + M(1)
    print(f"[06-6] streaming per-second mid in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[06-6] per-second rows: {len(sec):,}")

    # ---- per-trade adverse paths ----
    # loser: walk [entry, exit]; exit-adverse + MAE + fire time per X
    L = []
    for _, r in losers.iterrows():
        out = running_adverse(sec, mid, r.entry, r.exit, r.side, r.entry_price)
        if out is None:
            continue
        srel, run = out
        L.append(dict(uid=r.uid, mae=float(run[-1]), exit_adv=float(run[-1]),
                      exit_sec=float(srel[-1]), srel=srel, run=run, loss_pts=abs(r.realized_pnl)))
    # reached: walk [entry, pt1_completion = entry + pt1_open_el + 60]; max pre-pt1 adverse
    R = []
    for _, r in reached.iterrows():
        anchor = r.entry + S(float(r.pt1_open_el) + 60.0)
        out = running_adverse(sec, mid, r.entry, anchor, r.side, r.entry_price)
        if out is None:
            continue
        srel, run = out
        R.append(dict(uid=r.uid, max_adv=float(run[-1]), srel=srel, run=run))
    # below_target_win: context, walk [entry, exit]
    B = []
    for _, r in btw.iterrows():
        out = running_adverse(sec, mid, r.entry, r.exit, r.side, r.entry_price)
        if out is not None:
            B.append(float(out[1][-1]))

    print(f"[06-6] scored losers={len(L)}/16  reached={len(R)}/47  btw={len(B)}/29")

    # ---- DECISIVE: overlap of loser exit-adverse vs reached max pre-pt1 adverse ----
    loser_exit_adv = np.array([d["exit_adv"] for d in L])
    reached_max_adv = np.array([d["max_adv"] for d in R])
    print("\n===== DECISIVE: adverse-excursion OVERLAP (points) =====")
    def q(a): return np.percentile(a, [10, 25, 50, 75, 90])
    print(f"  loser EXIT-adverse   p10/25/50/75/90 = {np.round(q(loser_exit_adv),2)}")
    print(f"  reached MAX pre-pt1   p10/25/50/75/90 = {np.round(q(reached_max_adv),2)}")
    print(f"  loser median exit-adverse  = {np.median(loser_exit_adv):.2f} pts")
    print(f"  reached median pre-pt1 max = {np.median(reached_max_adv):.2f} pts")
    print(f"  (context) below_target_win median MAE = {np.median(B):.2f} pts")

    # ---- X-sweep: sensitivity / specificity / loser timing gap (DIAGNOSTIC, not a chosen X) ----
    print("\n===== X-SWEEP (diagnostic; NOT a chosen threshold) =====")
    print(f"  {'X(pts)':>7} {'sens(losers fire)':>18} {'spec(reached spared)':>21} "
          f"{'med loser gap(s)':>17}")
    xs = np.arange(0.5, 8.01, 0.5)
    for X in xs:
        sens = np.mean(loser_exit_adv >= X)
        spec = np.mean(reached_max_adv < X)
        # timing gap: among losers that fire (mae>=X), seconds held PAST first X-crossing
        gaps = []
        for d in L:
            if d["mae"] >= X:
                fire_sec = d["srel"][np.searchsorted(d["run"], X, "left")]
                gaps.append(d["exit_sec"] - fire_sec)
        gap = np.median(gaps) if gaps else np.nan
        print(f"  {X:>7.1f} {sens:>18.2f} {spec:>21.2f} {gap:>17.0f}")

    print("\n  READ: a region where sens AND spec are both high AND median gap ~0 => stop reproduces him.")
    print("  sens and (1-spec) rising together => no clean X => losers/reached overlap => NOT a simple stop.")
    print("  large gaps => he held PAST the level (the X-crossing is not his trigger).")
    print("\n[06-6] DONE. Diagnostic only — no threshold is selected; holdout would validate any X.")


if __name__ == "__main__":
    main()
