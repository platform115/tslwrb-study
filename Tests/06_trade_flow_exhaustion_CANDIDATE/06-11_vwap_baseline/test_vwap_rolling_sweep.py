#!/usr/bin/env python3
"""
test_vwap_rolling_sweep.py — rolling-VWAP N-sweep DIAGNOSTIC (not an optimizer)
-------------------------------------------------------------------------------
Rolling VWAP-distance looked strong (~0.74 @60s, clean). This explores its STRUCTURE across lookback N
and a volatility-normalized variant. IT DOES NOT PICK THE BEST N. On 16 losers in-sample, selecting the
peak N is overfitting (Bailey & Lopez de Prado, multiple testing). The trustworthy read is the SHAPE of
the AUC-vs-N curve: a broad PLATEAU = a real, robust signal; a single SPIKE amid noise = an artifact.

Two features, swept over N:
  raw  vwap_dist(60) = (mid@60 - rolling_vwap_N) * side_sign
  zdist vwap_z(60)   = raw / rolling_sigma_N         (sigma = rolling std of typical price; VWAP-band units)
Held at the HONEST 60s horizon (cut arm still ~13; avoids the late-τ cut-survival inflation that made the
0.93 tail). Clean population (losing16 vs reached47); pt1 was null already. Two-sided. SSD MOUNTED.
October in-sample; holdout-pending. Not financial advice. Selecting N for use = a pre-registered decision
that belongs to the operator, made BEFORE holdout, justified by plateau-stability not in-sample peak.

RUN (from its subfolder)
  python3 test_vwap_rolling_sweep.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
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
N_GRID = [10, 15, 20, 30, 45, 60, 90, 120]
HORIZONS = [60, 90]


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
    sec = (d.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    return d, sec


def vwap_sigma_for_N(d, N):
    vwap = (d.tpv.rolling(N, min_periods=5).sum() / d.volume.rolling(N, min_periods=5).sum()).to_numpy()
    sigma = d.tp.rolling(N, min_periods=5).std().to_numpy()
    return vwap, sigma


def at_idx(bsec, arr, t_s):
    i = int(np.searchsorted(bsec, t_s, "right") - 1)
    return float(arr[i]) if i >= 0 else np.nan


def calib_monotone(cv, sv):
    allv = np.concatenate([cv, sv]); lab = np.concatenate([np.ones(len(cv)), np.zeros(len(sv))])
    if len(allv) < 8: return "n/a"
    qs = np.quantile(allv, [.25, .5, .75]); ed = [-np.inf, *qs, np.inf]
    ps = [lab[(allv >= ed[i]) & (allv < ed[i+1])].mean() for i in range(4)]
    mono = all(ps[i] >= ps[i+1] for i in range(3)) or all(ps[i] <= ps[i+1] for i in range(3))
    return ("MONO " if mono else "noisy") + " ".join(f"{p:.2f}" for p in ps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    g, windowed, es1m = load(args.config, args.wrb)
    d, bsec = load_bars(es1m)

    print("[sweep] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    # per-trade: checkpoint times, mid, still-open, side sign
    base = []
    for _, r in g.iterrows():
        x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000); e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000)
        sgn = 1.0 if r.side == "long" else -1.0
        rec = dict(is_loser=bool(r.is_loser), group=r.group, sgn=sgn)
        for H in HORIZONS:
            cp = min(pd.Timestamp(r.entry) + S(H), r.exit)
            rec[f"cps_{H}"] = int(np.int64(pd.Timestamp(cp).value // 1_000_000_000))
            rec[f"mid_{H}"] = mid_at(cp); rec[f"open_{H}"] = x_s > e_s + H
        base.append(rec)
    B = pd.DataFrame(base)
    cl = B.is_loser; rch = (B.group == "target_reached") & ~B.is_loser

    for feat in ["raw", "zdist"]:
        print(f"\n############### ROLLING VWAP — {feat} distance — clean (losing16 vs reached47) ###############")
        print(f"  {'N':>4} | " + "  ".join(f"AUC@{H}(c-open)" for H in HORIZONS) + "   calib@60(quartile P(cut))")
        aucs60 = []
        for N in N_GRID:
            vwap, sigma = vwap_sigma_for_N(d, N)
            line = f"  {N:>4} | "
            cv60 = sv60 = None
            for H in HORIZONS:
                vals = np.full(len(B), np.nan)
                for i, r in B.iterrows():
                    m = r[f"mid_{H}"]
                    if np.isnan(m): continue
                    vw = at_idx(bsec, vwap, r[f"cps_{H}"])
                    if feat == "raw":
                        vals[i] = (m - vw) * r.sgn
                    else:
                        sg = at_idx(bsec, sigma, r[f"cps_{H}"])
                        vals[i] = ((m - vw) * r.sgn) / sg if (sg and sg > 0) else np.nan
                op = B[f"open_{H}"].to_numpy()
                cv = vals[(cl.to_numpy()) & op]; sv = vals[(rch.to_numpy()) & op]
                cv = cv[~np.isnan(cv)]; sv = sv[~np.isnan(sv)]
                auc, _, _ = spine.rank_auc(sv, cv) if len(cv) and len(sv) else (np.nan, 0, 0)
                line += f"{auc:.3f}({len(cv):>2})      "
                if H == 60: cv60, sv60 = cv, sv; aucs60.append(auc)
            line += "  " + calib_monotone(cv60, sv60)
            print(line)
        arr = np.array([a for a in aucs60 if not np.isnan(a)])
        print(f"  STABILITY @60s across N: mean={arr.mean():.3f} min={arr.min():.3f} max={arr.max():.3f} "
              f"spread={arr.max()-arr.min():.3f}")
        print(f"    (broad plateau / low spread = robust signal; one spike amid noise = overfit artifact.)")

    print(f"\n[sweep] READ the CURVE SHAPE, not the peak. A signal robust across N (flat-ish, low spread,")
    print(f"  calibration MONO at most N) is real; AUC that jumps around with N is noise. Any N chosen for")
    print(f"  use must be picked for plateau-stability and PRE-REGISTERED before holdout — not max in-sample.")


if __name__ == "__main__":
    main()
