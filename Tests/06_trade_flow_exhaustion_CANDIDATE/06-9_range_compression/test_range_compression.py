#!/usr/bin/env python3
"""
test_range_compression.py — #2: during-trade RANGE compression (volatility), forward
-------------------------------------------------------------------------------
Distinct from body-progress (1-A/1-B): that measured net favorable DISPLACEMENT; this measures total
RANGE (whippiness). A trade can be wide-range with zero displacement, so these are different signals.
Distinct from 08-bar: that was EXIT-anchored (losers were on WIDER bars at the cut); this is FORWARD
(does range go quiet EARLY predict the outcome).

FEATURE
  developing_range(tau) = (max mid - min mid) over per-second mids in [entry, min(entry+tau, exit))
  baseline_range        = mean(high-low) of the 3 one-minute bars BEFORE entry
  compression_ratio(tau) = developing_range(tau) / baseline_range     (<1 quieter than recent; >1 wilder)
  Still-open only at each tau (exit > entry+tau) -> non-circular, truncation-free (like 1-B).

DIRECTION: TWO-SIDED, genuinely unknown. Compression could be coil-before-WRB (runner) OR going-dead
(dud); 08 showed losers EXPAND at the cut. No pre-committed sign — calibration shows which way, if any.

INSTRUMENT NOTE: numerator = per-second MID range (understates true high-low extreme); denominator =
bar true-range. Absolute ratio biased LOW, but AUC (ranks) and QUARTILE calibration are unaffected by a
consistent bias -> calibration is by quartile, not fixed cutoffs.

REPORTS: checkpoint @60s (AUC + cluster-boot CI) ; hazard curve AUC across tau ; quartile calibration
P(eventual cut | compression quartile) @60s. Both populations (clean 16/47, pt1 40/52). Deterministic.
Read-only. n small; October discovery. Not financial advice.

RUN (from its subfolder inside the 06 folder; SSD mounted)
  python3 test_range_compression.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
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
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "high", "low"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.high.to_numpy(), d.low.to_numpy()


def baseline_range(bar_sec, hi, lo, entry_ts):
    e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
    j = int(np.searchsorted(bar_sec, e_s, "left"))
    return float(np.mean(hi[j-3:j] - lo[j-3:j])) if j >= 3 else np.nan


def compression_at(sec, mid, entry_ts, exit_ts, base, tau):
    """developing per-second mid range over [entry, entry+tau) / baseline; NaN unless still open."""
    cp = entry_ts + S(tau)
    if cp >= exit_ts or base is None or np.isnan(base) or base <= 0:
        return np.nan
    e_s = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
    c_s = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
    i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, c_s, "left")
    if i1 - i0 < 2:
        return np.nan
    seg = mid[i0:i1]
    return float(seg.max() - seg.min()) / base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    g, windowed, es1m = load(args.config, args.wrb)
    bar_sec, hi, lo = load_bars(es1m)
    g["base"] = [baseline_range(bar_sec, hi, lo, e) for e in g["entry"]]
    t_min = g["entry"].min() - M(5); t_max = g["exit"].max() + M(1)
    print(f"[#2] streaming per-second mid in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[#2] per-second rows: {len(sec):,}  bars: {len(bar_sec):,}")

    pops = {
        "clean (losing16 vs reached47)": (g[g.is_loser], g[(g.group == "target_reached") & (~g.is_loser)]),
        "pt1   (failed40 vs reached52)": (g[g.group == "failed_trades"], g[g.group == "target_reached"]),
    }
    for pop_name, (cut, spared) in pops.items():
        print(f"\n================ {pop_name} ================")
        print(f"  HAZARD CURVE — AUC(reached compression > cut compression), still-open at tau (TWO-SIDED)")
        print(f"  {'tau(s)':>6} {'AUC':>6} {'cut-open':>9} {'run-open':>9}")
        for tau in TAUS:
            cv = np.array([compression_at(sec, mid, r.entry, r.exit, r.base, tau) for _, r in cut.iterrows()])
            sv = np.array([compression_at(sec, mid, r.entry, r.exit, r.base, tau) for _, r in spared.iterrows()])
            cv = cv[~np.isnan(cv)]; sv = sv[~np.isnan(sv)]
            auc, _, _ = spine.rank_auc(sv, cv)
            flag = "" if len(cv) >= 8 else "  <cut-n<8>"
            star = "  <<< primary" if tau == TAU_PRIMARY else ""
            print(f"  {tau:>6} {auc:>6.3f} {len(cv):>9} {len(sv):>9}{flag}{star}")

        # checkpoint @primary: CI + direction + quartile calibration
        cvP = np.array([compression_at(sec, mid, r.entry, r.exit, r.base, TAU_PRIMARY) for _, r in cut.iterrows()])
        svP = np.array([compression_at(sec, mid, r.entry, r.exit, r.base, TAU_PRIMARY) for _, r in spared.iterrows()])
        cvP = cvP[~np.isnan(cvP)]; svP = svP[~np.isnan(svP)]
        per_cut = [float((np.sum(svP > c) + 0.5 * np.sum(svP == c)) / len(svP)) for c in cvP] if len(svP) else []
        ci = spine.cluster_boot_ci(per_cut, seed=args.seed)
        direction = ("reached MORE volatile" if ci["mean"] > 0.5 else "reached MORE compressed") if not np.isnan(ci["mean"]) else "n/a"
        print(f"\n  @tau={TAU_PRIMARY}s: AUC={ci['mean']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
              f"({'excl' if ci['excludes_half'] else 'incl'} 0.5)  -> {direction}  cut={len(cvP)} run={len(svP)}")
        print(f"    median compression: reached={np.median(svP):.2f}  cut={np.median(cvP):.2f}  "
              f"(<1 = quieter than recent bars)")

        # quartile calibration (robust to mid-vs-true-range scaling)
        allv = np.concatenate([cvP, svP]); lab = np.concatenate([np.ones(len(cvP)), np.zeros(len(svP))])
        if len(allv) >= 8:
            qs = np.quantile(allv, [0.25, 0.5, 0.75])
            edges = [-np.inf, qs[0], qs[1], qs[2], np.inf]
            print(f"  CALIBRATION @tau={TAU_PRIMARY}s — P(eventual cut) by compression quartile (Q1=most compressed):")
            for qi in range(4):
                m = (allv >= edges[qi]) & (allv < edges[qi+1])
                n = int(m.sum())
                print(f"    Q{qi+1} comp in [{edges[qi]:.2f},{edges[qi+1]:.2f}): P(cut)={lab[m].mean() if n else float('nan'):.2f}  n={n}")
            print(f"    (monotone P(cut) across quartiles in EITHER direction = signal; flat = none.)")

    print(f"\n[#2] READ: does range going quiet (or wild) early separate cuts from runners, BEYOND")
    print(f"  displacement (1-A) and adverse (S2)? Two-sided. If AUC~0.5 / flat calibration -> closes")
    print(f"  the range-compression idea: the action is in displacement + adverse, not raw volatility.")


if __name__ == "__main__":
    main()
