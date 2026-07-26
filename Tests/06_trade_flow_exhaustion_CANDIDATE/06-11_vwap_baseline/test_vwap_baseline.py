#!/usr/bin/env python3
"""
test_vwap_baseline.py — #5: VWAP / session-reference as a BASELINE COMPETITOR to S1/S2
-------------------------------------------------------------------------------
Nothing in WRB methodology points to VWAP — this is the institutional reflex, included as a generic
BASELINE: does an off-the-shelf distance-from-VWAP rule separate cuts as well as the WRB-derived
body-progress (S1)? Verdict is framed as a benchmark, not "found a VWAP edge."

FEATURE: vwap_dist(τ) = (mid_at[min(entry+τ,exit)] - VWAP_at[checkpoint]) * side_sign  (still-open).
  Positive = price on the favorable side of VWAP for the trade. Two anchors:
    DAILY   VWAP = Σ(typical·vol)/Σvol cumulative within session_date (resets at session boundary)
    ROLLING VWAP = Σ(typical·vol)/Σvol over the trailing N 1m bars (N=30; PARAMETER, re-confirm OOS)
  typical price = (H+L+C)/3 per 1m bar. (Rolling can cross a session seam — nature of rolling VWAP.)
TWO-SIDED: mean-reversion (extended->revert) vs extension cuts ambiguously; no pre-committed sign.

MEASURES:
 (1) EXIT: AUC(reached vwap_dist > cut vwap_dist) hazard across τ, still-open, both populations + CI +
     quartile calibration P(cut | vwap_dist quartile) @primary.
 (2) HEAD-TO-HEAD vs S1: corr(vwap_dist@60, body_ratio@60) + redundancy cross-tab on the 16 losers
     (VWAP flag = vwap_dist@60 < 0 ; S1 flag = body_ratio@60 < 0.5): both / VWAP-only / S1-only / neither.
     VWAP-only > 0 => adds beyond S1; mostly 'both' + high corr => redundant; VWAP weaker => S1 dominates.

Populations: clean 16/47, pt1 52/40. SSD MOUNTED (per-second mid). October ESZ5. n small; in-sample;
holdout-pending. Not financial advice.

RUN (from its subfolder)
  python3 test_vwap_baseline.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
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
TAUS = [30, 60, 90, 120, 180]; TAU_PRIMARY = 60; ROLL_N = 30


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
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "open", "high", "low", "close", "volume", "session_date"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    d["tp"] = (d.high + d.low + d.close) / 3.0
    d["tpv"] = d.tp * d.volume
    # daily VWAP (reset at session_date)
    cum_tpv = d.groupby("session_date").tpv.cumsum(); cum_v = d.groupby("session_date").volume.cumsum()
    d["vwap_daily"] = cum_tpv / cum_v
    # rolling VWAP (trailing N bars)
    d["vwap_roll"] = d.tpv.rolling(ROLL_N, min_periods=5).sum() / d.volume.rolling(ROLL_N, min_periods=5).sum()
    sec = (d.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    return sec, d.vwap_daily.to_numpy(), d.vwap_roll.to_numpy(), d.open.to_numpy(), d.close.to_numpy()


def at_idx(bar_sec, arr, t_s):
    i = int(np.searchsorted(bar_sec, t_s, "right") - 1)
    return float(arr[i]) if i >= 0 else np.nan


def auc_block(label, cut, spared, col, seed):
    print(f"  {label}: AUC(reached {col} > cut), still-open at τ:")
    print(f"  {'τ(s)':>5} {'AUC':>6} {'r-open':>6} {'c-open':>6}")
    for tau in TAUS:
        cv = cut[cut[f"open_{tau}"]][f"{col}_{tau}"].dropna().to_numpy()
        sv = spared[spared[f"open_{tau}"]][f"{col}_{tau}"].dropna().to_numpy()
        auc, _, _ = spine.rank_auc(sv, cv) if len(cv) and len(sv) else (np.nan, 0, 0)
        star = "  <<<" if tau == TAU_PRIMARY else ""
        print(f"  {tau:>5} {auc:>6.3f} {len(sv):>6} {len(cv):>6}{star}")
    cv = cut[cut[f"open_{TAU_PRIMARY}"]][f"{col}_{TAU_PRIMARY}"].dropna().to_numpy()
    sv = spared[spared[f"open_{TAU_PRIMARY}"]][f"{col}_{TAU_PRIMARY}"].dropna().to_numpy()
    if len(cv) and len(sv):
        per = [float((np.sum(sv > c) + 0.5 * np.sum(sv == c)) / len(sv)) for c in cv]
        ci = spine.cluster_boot_ci(per, seed=seed)
        print(f"    @{TAU_PRIMARY}s CI[{ci['lo']:.3f},{ci['hi']:.3f}] ({'excl' if ci['excludes_half'] else 'incl'} 0.5)"
              f"  med reached={np.median(sv):+.2f} cut={np.median(cv):+.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    g, windowed, es1m = load(args.config, args.wrb)
    bsec, vd, vr, bopen, bclose = load_bars(es1m)

    def prior_body_max(entry_ts):
        e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
        j = int(np.searchsorted(bsec, e_s, "left"))
        return float(np.abs(bclose[j-3:j] - bopen[j-3:j]).max()) if j >= 3 else np.nan

    print("[vwap] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    rows = []
    for _, r in g.iterrows():
        sgn = 1.0 if r.side == "long" else -1.0; pbm = prior_body_max(r.entry)
        x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000); e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000)
        rec = dict(uid=r.uid, group=r.group, is_loser=bool(r.is_loser))
        for tau in TAUS:
            cp = min(pd.Timestamp(r.entry) + S(tau), r.exit); cps = np.int64(pd.Timestamp(cp).value // 1_000_000_000)
            m = mid_at(cp)
            rec[f"open_{tau}"] = x_s > e_s + tau
            rec[f"vd_{tau}"] = ((m - at_idx(bsec, vd, cps)) * sgn) if not np.isnan(m) else np.nan
            rec[f"vr_{tau}"] = ((m - at_idx(bsec, vr, cps)) * sgn) if not np.isnan(m) else np.nan
        cp60 = min(pd.Timestamp(r.entry) + S(60), r.exit); m60 = mid_at(cp60)
        rec["br60"] = (((m60 - r.entry_price) * sgn) / pbm) if (pbm and pbm > 0 and not np.isnan(m60)) else np.nan
        rows.append(rec)
    d = pd.DataFrame(rows)

    pops = {
        "clean (losing16 vs reached47)": (d[d.is_loser], d[(d.group == "target_reached") & ~d.is_loser]),
        "pt1   (failed40 vs reached52)": (d[d.group == "failed_trades"], d[d.group == "target_reached"]),
    }
    for anchor, col in [("DAILY VWAP", "vd"), ("ROLLING VWAP (N=30)", "vr")]:
        print(f"\n############### {anchor} ###############")
        for pop_name, (cut, spared) in pops.items():
            print(f"\n  == {pop_name} ==")
            auc_block(anchor, cut, spared, col, args.seed)
            # quartile calibration @primary
            cvP = cut[cut[f"open_{TAU_PRIMARY}"]][f"{col}_{TAU_PRIMARY}"].dropna().to_numpy()
            svP = spared[spared[f"open_{TAU_PRIMARY}"]][f"{col}_{TAU_PRIMARY}"].dropna().to_numpy()
            allv = np.concatenate([cvP, svP]); lab = np.concatenate([np.ones(len(cvP)), np.zeros(len(svP))])
            if len(allv) >= 8:
                qs = np.quantile(allv, [.25, .5, .75]); edges = [-np.inf, *qs, np.inf]
                cal = [f"Q{i+1}:{lab[(allv>=edges[i])&(allv<edges[i+1])].mean():.2f}" for i in range(4)]
                print(f"    calib P(cut) by vwap_dist quartile (Q1=most below VWAP): {'  '.join(cal)}")

    # HEAD-TO-HEAD vs S1 (clean losers)
    print(f"\n############### HEAD-TO-HEAD vs S1 (body_ratio) ###############")
    dd = d.dropna(subset=["br60", "vd_60", "vr_60"])
    if len(dd) >= 5:
        print(f"  corr(vwap_dist@60, body_ratio@60): daily={np.corrcoef(dd.vd_60, dd.br60)[0,1]:+.2f}  "
              f"rolling={np.corrcoef(dd.vr_60, dd.br60)[0,1]:+.2f}")
    los = d[d.is_loser].dropna(subset=["br60", "vd_60"])
    s1 = los.br60 < 0.5
    for col, nm in [("vd_60", "daily"), ("vr_60", "rolling")]:
        vw = los[col] < 0
        both = int((s1 & vw).sum()); s1o = int((s1 & ~vw).sum()); vwo = int((~s1 & vw).sum()); ne = int((~s1 & ~vw).sum())
        print(f"  losers cross-tab (S1<0.5 vs {nm} VWAP-dist<0): both={both} S1-only={s1o} "
              f"VWAP-only={vwo} neither={ne}  (VWAP-only>0 => adds beyond S1)")

    print(f"\n[vwap] READ: baseline competitor. If VWAP-dist AUC << S1 (~0.82 clean) and high corr / no")
    print(f"  VWAP-only losers => S1 dominates, VWAP is a weaker correlate. If VWAP matches S1 => your")
    print(f"  edge isn't WRB-specific. If VWAP-only losers > 0 => VWAP catches some S1 misses (additive).")


if __name__ == "__main__":
    main()
