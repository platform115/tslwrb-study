#!/usr/bin/env python3
"""
test_wrb_progress_B_hazard.py — #1-B: failure-to-extend HAZARD curve (non-circular)
-------------------------------------------------------------------------------
The time-resolved companion to #1-A. NON-CIRCULAR by construction: at each elapsed tau, reads only
trades STILL OPEN at tau (exit > entry+tau), measures body_ratio(tau) BEFORE the trade resolves, and
asks whether low body at tau predicts the EVENTUAL cut. No reading at exit (which would make the cut
arm trivially low-body = its loss), no truncation, no outcome leak.

WHY NOT cut-time-matched (the originally-floated B): reading each cut AT its exit makes cut-body =
the realized loss by definition -> circular. This reads at tau < resolution instead.

DISTINCT FROM #1-A: A gave AUC at 3 fixed checkpoints. B gives (1) the discrimination CURVE across a
tau grid, and (2) the CALIBRATION you would actually trade: P(eventual cut | body_ratio bin) at the
primary tau -> "at tau s, body below Y => Z% likely to be cut."

FEATURE: body_ratio(tau) = (mid_at[entry+tau] - entry_price)*sign / prior_body_max  (same as #1-A).
LABEL: eventual cut (clean: losing_trade; pt1: failed_trades) vs runner (reached). AUC(runner>cut).
TAU GRID: 15..180s step 15. NOTE: losers exit fast (median ~102s) -> the still-open CUT sample shrinks
with tau; AUC at tau where cut-n < 8 is uninformative (flagged). That shrinkage is itself the answer to
"how long can it stay flat" — doomed trades don't survive to be measured late.

Deterministic (seed 0). Read-only. n small; October discovery. Not financial advice.

RUN (from 06-7_wrb_progress inside the 06 folder)
  python3 test_wrb_progress_B_hazard.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
TAUS = list(range(15, 181, 15)); TAU_PRIMARY = 60


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["run"]["resolved"]["windowed_parquet"], cfg["paths"]["es_1m_front"]


def load_bars(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "open", "close"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.open.to_numpy(), d.close.to_numpy()


def prior_body_max(bar_sec, bopen, bclose, entry_ts):
    e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
    j = int(np.searchsorted(bar_sec, e_s, "left"))
    return float(np.abs(bclose[j-3:j] - bopen[j-3:j]).max()) if j >= 3 else np.nan


def mid_at(sec, mid, t_ts):
    t_s = np.int64(pd.Timestamp(t_ts).value // 1_000_000_000)
    i = int(np.searchsorted(sec, t_s, "right") - 1)
    return float(mid[i]) if i >= 0 else np.nan


def body_ratio_at(sec, mid, entry_ts, exit_ts, side, ep, pbm, tau):
    """body_ratio at entry+tau, ONLY if still open (exit > entry+tau). Else NaN (not in still-open set)."""
    cp = entry_ts + S(tau)
    if cp >= exit_ts or pbm is None or np.isnan(pbm) or pbm <= 0:
        return np.nan
    m = mid_at(sec, mid, cp)
    if np.isnan(m):
        return np.nan
    return ((m - ep) * (1.0 if side == "long" else -1.0)) / pbm


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    g, windowed, es1m = load(args.config, args.wrb)
    bar_sec, bopen, bclose = load_bars(es1m)
    t_min = g["entry"].min() - M(5); t_max = g["exit"].max() + M(1)
    print(f"[1B] streaming per-second mid in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[1B] per-second rows: {len(sec):,}  bars: {len(bar_sec):,}")
    g["pbm"] = [prior_body_max(bar_sec, bopen, bclose, e) for e in g["entry"]]

    pops = {
        "clean (losing16 vs reached47)": (g[g.is_loser], g[(g.group == "target_reached") & (~g.is_loser)]),
        "pt1   (failed40 vs reached52)": (g[g.group == "failed_trades"], g[g.group == "target_reached"]),
    }
    for pop_name, (cut, spared) in pops.items():
        print(f"\n================ {pop_name} ================")
        print(f"  HAZARD CURVE — discrimination AUC(runner body > cut body) among STILL-OPEN trades at tau")
        print(f"  {'tau(s)':>6} {'AUC':>6} {'cut-open':>9} {'run-open':>9}")
        for tau in TAUS:
            cv = np.array([body_ratio_at(sec, mid, r.entry, r.exit, r.side, r.entry_price, r.pbm, tau)
                           for _, r in cut.iterrows()])
            sv = np.array([body_ratio_at(sec, mid, r.entry, r.exit, r.side, r.entry_price, r.pbm, tau)
                           for _, r in spared.iterrows()])
            cv = cv[~np.isnan(cv)]; sv = sv[~np.isnan(sv)]
            auc, _, _ = spine.rank_auc(sv, cv)
            flag = "" if len(cv) >= 8 else "  <cut-n<8: uninformative>"
            star = "  <<< primary" if tau == TAU_PRIMARY else ""
            print(f"  {tau:>6} {auc:>6.3f} {len(cv):>9} {len(sv):>9}{flag}{star}")

        # bootstrap CI + calibration at primary tau
        cvP = np.array([body_ratio_at(sec, mid, r.entry, r.exit, r.side, r.entry_price, r.pbm, TAU_PRIMARY)
                        for _, r in cut.iterrows()])
        svP = np.array([body_ratio_at(sec, mid, r.entry, r.exit, r.side, r.entry_price, r.pbm, TAU_PRIMARY)
                        for _, r in spared.iterrows()])
        cvP = cvP[~np.isnan(cvP)]; svP = svP[~np.isnan(svP)]
        per_cut = [float((np.sum(svP > c) + 0.5 * np.sum(svP == c)) / len(svP)) for c in cvP] if len(svP) else []
        ci = spine.cluster_boot_ci(per_cut, seed=args.seed)
        print(f"\n  @tau={TAU_PRIMARY}s: AUC={ci['mean']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
              f"({'excl' if ci['excludes_half'] else 'incl'} 0.5)  cut-open={len(cvP)} run-open={len(svP)}")

        # CALIBRATION: P(eventual cut | body_ratio bin) among still-open at primary tau
        print(f"  CALIBRATION @tau={TAU_PRIMARY}s — P(eventual cut | body_ratio bin), still-open trades:")
        allv = np.concatenate([cvP, svP]); lab = np.concatenate([np.ones(len(cvP)), np.zeros(len(svP))])
        bins = [(-np.inf, 0.0), (0.0, 0.5), (0.5, 1.0), (1.0, np.inf)]
        for lob, hib in bins:
            m = (allv >= lob) & (allv < hib)
            n = int(m.sum()); pcut = (lab[m].mean() if n else np.nan)
            lbl = f"[{lob:+.1f},{hib:+.1f})".replace("-inf", "  -inf").replace("+inf", "  +inf")
            print(f"    body_ratio {lbl:>16}: P(cut)={pcut:.2f}  n={n}")
        print(f"    (monotonic P(cut) falling as body rises = usable live hazard: low body @60s => likely cut.)")

    print(f"\n[1B] DONE. The discrimination curve shows WHEN the signal is readable; the calibration shows")
    print(f"  the live rule. Note cut-open shrinking at high tau = doomed trades exit fast (the 1.7-min cut).")


if __name__ == "__main__":
    main()
