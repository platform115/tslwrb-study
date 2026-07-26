#!/usr/bin/env python3
"""
test_vwap_sigma_bands.py — VWAP sigma-bands as DISCRETE LEVELS (mechanism test)
-------------------------------------------------------------------------------
Hypothesis (institutional construct, documented — VWAP standard-deviation bands): far-from-VWAP is not
just "far" — the +/-1sigma, +/-2sigma bands are specific levels where behavior changes. So WHICH BAND a
trade sits in at 60s might predict cut vs reached as a STEP function, beyond the smooth z-score
(continuous z already ~0.78 @60s, N=20). This tests for a level/step effect.

PRE-SPECIFIED N=20 (from the MIDDLE of the short-N plateau in the sweep, not the in-sample peak — a fixed
choice, not a swept one).
  z(60) = (mid@60 - rolling_vwap_20) * side_sign / rolling_sigma_20   (still-open)
  bands: (-inf,0]  (0,1]  (1,2]  (2,inf]   = below VWAP / 0-1sigma / 1-2sigma / >2sigma extended favorable.

Reports P(cut) per band (the step function) + occupancy + the continuous-z AUC for reference. Clean
population (losing16 vs reached47). HONEST LIMIT: 16 losers across 4 bands = ~4/band — this CANNOT
establish a nonlinear level effect; it is descriptive. A real step vs smooth needs far more data.
Two-sided. SSD MOUNTED. October in-sample. Not financial advice.

RUN (from its subfolder)
  python3 test_vwap_sigma_bands.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end ---

import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
N = 20; TAU = 60
BANDS = [(-np.inf, 0.0, "<=0sigma (below VWAP)"), (0.0, 1.0, "0-1sigma"),
         (1.0, 2.0, "1-2sigma"), (2.0, np.inf, ">2sigma (extended)")]


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
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "high", "low", "close", "volume"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    d["tp"] = (d.high + d.low + d.close) / 3.0; d["tpv"] = d.tp * d.volume
    vwap = (d.tpv.rolling(N, min_periods=5).sum() / d.volume.rolling(N, min_periods=5).sum()).to_numpy()
    sigma = d.tp.rolling(N, min_periods=5).std().to_numpy()
    sec = (d.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    return sec, vwap, sigma


def at_idx(bsec, arr, t_s):
    i = int(np.searchsorted(bsec, t_s, "right") - 1)
    return float(arr[i]) if i >= 0 else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    g, windowed, es1m = load(args.config, args.wrb)
    bsec, vwap, sigma = load_bars(es1m)

    print(f"[bands] streaming per-second mid ... (N={N}, tau={TAU}s)")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    rows = []
    for _, r in g.iterrows():
        x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000); e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000)
        if not (x_s > e_s + TAU):  # still-open only
            continue
        sgn = 1.0 if r.side == "long" else -1.0
        cp = min(pd.Timestamp(r.entry) + S(TAU), r.exit); cps = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
        m = mid_at(cp)
        if np.isnan(m): continue
        vw = at_idx(bsec, vwap, cps); sg = at_idx(bsec, sigma, cps)
        if not (sg and sg > 0): continue
        z = ((m - vw) * sgn) / sg
        rows.append(dict(uid=r.uid, is_loser=bool(r.is_loser), group=r.group, z=z))
    d = pd.DataFrame(rows)
    clean = d[d.is_loser | ((d.group == "target_reached") & ~d.is_loser)]
    print(f"[bands] clean still-open @{TAU}s: {len(clean)} (losers {int(clean.is_loser.sum())}, "
          f"reached {int((~clean.is_loser).sum())})")

    print(f"\n  SIGMA-BAND step function — P(cut) by band (z = favorable extension in sigma units):")
    print(f"  {'band':>22} {'n':>3} {'losers':>6} {'P(cut)':>7}")
    for lo, hi, lbl in BANDS:
        m = (clean.z > lo) & (clean.z <= hi) if lo != -np.inf else (clean.z <= hi)
        if hi == np.inf: m = clean.z > lo
        sub = clean[m]; n = len(sub); nl = int(sub.is_loser.sum())
        pc = (nl / n) if n else float("nan")
        print(f"  {lbl:>22} {n:>3} {nl:>6} {pc:>7.2f}")
    print(f"    (step-like P(cut) dropping across bands = level effect; smooth = just the continuous z.)")
    print(f"    *** {int(clean.is_loser.sum())} losers across 4 bands (~{int(clean.is_loser.sum())//4}/band):")
    print(f"        DESCRIPTIVE ONLY — cannot establish a nonlinear level effect at this n. ***")

    # continuous z AUC for reference
    cv = clean[clean.is_loser].z.to_numpy(); sv = clean[~clean.is_loser].z.to_numpy()
    auc, _, _ = spine.rank_auc(sv, cv)
    per = [float((np.sum(sv > c) + 0.5 * np.sum(sv == c)) / len(sv)) for c in cv]
    ci = spine.cluster_boot_ci(per, seed=args.seed)
    print(f"\n  continuous z AUC (reference, N={N}): {auc:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}]")
    print(f"\n[bands] READ: if P(cut) steps down cleanly across bands, the institutional band LEVELS may")
    print(f"  carry structure beyond the smooth z — but n forbids concluding that here. Mechanism noted,")
    print(f"  level-vs-smooth is a holdout question.")


if __name__ == "__main__":
    main()
