#!/usr/bin/env python3
"""
s3b_atr5_variant.py — F1/S3 variant: ATR-relative threshold with lookback 5 (post-hoc second read)
====================================================================================================
USER-REQUESTED variant after seeing T-DF03 output: N_rel = 1.0 x ATR(5) instead of ATR(20).
LOGGED AS A POST-HOC PARAMETER CHANGE (registry T-DF04) — the second look at the ATRrel family.

Pre-registered expectation (stated before output): lookback changes RESPONSIVENESS not SIZE; median
N_rel should land near ATR(20)'s (~12tk) unless entries cluster after bursts/quiet. If attainer counts
were the problem, k (threshold multiplier) is the lever, not lookback. Hypothesis unchanged: reach
attains more (diff>0) / faster (AUC<0.5 among attainers). Survivor frame DECISIVE; ALL(B) ATRrel is
construction-suspect (capped windows mechanically depress attainment for early-cut stalls — T-DF03).

Only the ATRrel cells are recomputed (the +4/+8 cells are untouched T-DF03 results).

RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
      06-14_discretionary_factors/s3b_atr5_variant.py --config config.toml --wrb wrb_1m.parquet
Registry: T-DF04 · family=speed · code_ref=06-14_discretionary_factors/s3b_atr5_variant.py
"""

import argparse
import numpy as np
import pandas as pd

try:
    import tomllib
except ImportError:
    import tomli as tomllib

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import two_sample_boot_ci
from s2_directional_velocity import PRE_W
from s3_time_to_ticks import first_passage, attain_diff_ci, _flat

HORIZONS = [60, 90, 120]
N_MIN = 8
ATR_LOOKBACK = 5
ATR_K = 1.0


def load_atr_ticks(config_path, entries, lookback):
    cfg = tomllib.load(open(config_path, "rb"))
    path = cfg["paths"]["es_1m_front"] if "paths" in cfg and "es_1m_front" in cfg.get("paths", {}) \
        else cfg.get("es_1m_front") or next(v for k, v in _flat(cfg) if k.endswith("es_1m_front"))
    df = pd.read_parquet(path, columns=["ts_event", "high", "low", "close"]).sort_values("ts_event")
    ts = df["ts_event"].values
    h = df["high"].values; l = df["low"].values; c = df["close"].values
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    tr_ts = ts[1:].astype("datetime64[ns]")
    out = {}
    for e in entries:
        cut = np.datetime64(pd.Timestamp(e).floor("1min").tz_convert("UTC").tz_localize(None))
        i = np.searchsorted(tr_ts, cut, "left")
        out[e] = float(np.mean(tr[i - lookback:i]) / TICK) if i >= lookback else np.nan
    return out


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    atr = load_atr_ticks(config, g.entry.tolist(), ATR_LOOKBACK)
    g["n_rel"] = ATR_K * pd.Series([atr[e] for e in g.entry], index=g.index)
    print(f"[ATR({ATR_LOOKBACK}),1m,pre-entry] ticks: med={np.nanmedian(g.n_rel):.1f} "
          f"q25={np.nanquantile(g.n_rel,.25):.1f} q75={np.nanquantile(g.n_rel,.75):.1f} "
          f"nan={int(g.n_rel.isna().sum())}  (T-DF03 ATR(20) med was 12.5)")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for H in HORIZONS:
        surv_mask = g.hold >= H
        res = [first_passage(sec, mid, r.entry, r.exit, H, r.side, float(r.n_rel)) for _, r in g.iterrows()]
        att = pd.Series([a for a, t in res], index=g.index, dtype="object")
        tt = pd.Series([t for a, t in res], index=g.index, dtype=float)
        print(f"\n===== H={H}s  [N=ATR(5)rel] ====={'  <<< PRIMARY HORIZON' if H == 60 else '  [robustness]'}")
        for frame, fmask in (("ALL(B) [construction-suspect]", pd.Series(True, index=g.index)),
                             ("SURV   [DECISIVE]", surv_mask)):
            m = fmask & att.notna()
            rA = m & (g.grp == "reach"); sA = m & (g.grp == "stall")
            ratt = att[rA].astype(float).values; satt = att[sA].astype(float).values
            if len(ratt) < N_MIN or len(satt) < N_MIN:
                print(f"  [{frame}] UNINFORMATIVE (n<{N_MIN})"); continue
            d, lo, hi, clears = attain_diff_ci(ratt, satt, seed=seed)
            star = "**" if clears and d > 0 else ("!!" if clears else "  ")
            print(f"  [{frame}] attain: R {ratt.mean():.2f} vs S {satt.mean():.2f}  "
                  f"diff {d:+.2f} CI[{lo:+.2f},{hi:+.2f}] {star}")
            r_t = tt[rA & (att == True)].dropna().values; s_t = tt[sA & (att == True)].dropna().values
            if len(r_t) >= N_MIN and len(s_t) >= N_MIN:
                ci = two_sample_boot_ci(r_t, s_t, seed=seed)
                star2 = "**" if ci["clears"] and ci["auc"] < 0.5 else ("!!" if ci["clears"] else "  ")
                print(f"      time|attained: AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
                      f"Rmed={np.nanmedian(r_t):.0f}s Smed={np.nanmedian(s_t):.0f}s "
                      f"(attainers R{len(r_t)}/S{len(s_t)}) {star2} (AUC<0.5 = reach faster)")
            else:
                print(f"      time|attained: UNINFORMATIVE (attainers R{len(r_t)}/S{len(s_t)} < {N_MIN})")

    print("\nREAD: post-hoc second look at the ATRrel family (T-DF04). Decisive = SURV lines only; ALL(B)"
          " clears carry the T-DF03 construction-suspect flag. If SURV cells remain thin/non-clearing,"
          " the ATRrel operationalization is closed at k=1.0 regardless of lookback; a k change would be"
          " a THIRD look and should be weighed as such.")


def selftest(config, wrb):
    print("=== SELF-TEST: hand-computed ATR(5) ===")
    # 8 bars, known OHLC; TR by hand; cut after bar 7 -> ATR(5) = mean(TR of bars 3..7)
    ts = pd.date_range("2025-10-06 14:00", periods=8, freq="1min", tz="UTC")
    h = np.array([10, 11, 12, 11, 13, 12, 14, 15.]) + 5000
    l = np.array([9, 10, 10, 10, 11, 11, 12, 13.]) + 5000
    c = np.array([9.5, 10.5, 11, 10.5, 12, 11.5, 13, 14.]) + 5000
    # TR_i (i>=1) = max(h-l, |h-prev_c|, |l-prev_c|):
    # bar1: max(1, 1.5, .5)=1.5  bar2: max(2,1.5,.5)=2  bar3: max(1,0,1)=1  bar4: max(2,2.5,.5)=2.5
    # bar5: max(1,0,1)=1  bar6: max(2,2.5,.5)=2.5  bar7: max(2,2,0)=2
    # cut before bar open 14:07? entry at 14:07:30 -> floor 14:07 -> TR bars with open<14:07 = bars1..6
    # ATR(5) = mean(TR bars2..6) = (2+1+2.5+1+2.5)/5 = 1.8 pts = 7.2 ticks
    import tempfile, os
    df = pd.DataFrame(dict(ts_event=ts, high=h, low=l, close=c))
    p = "/tmp/atr5_selftest.parquet"; df.to_parquet(p)
    cfgp = "/tmp/atr5_cfg.toml"
    open(cfgp, "w").write(f'[paths]\nes_1m_front = "{p}"\nepisodes = "x"\n')
    atr = load_atr_ticks(cfgp, [pd.Timestamp("2025-10-06 14:07:30", tz="UTC")], 5)
    got = list(atr.values())[0]
    print(f"  hand ATR(5)=7.20 tk, loader={got:.2f} tk")
    assert abs(got - 7.2) < 1e-9, got
    a, t = first_passage(np.array([]), np.array([]), pd.Timestamp("2025-10-06", tz="UTC"),
                         pd.Timestamp("2025-10-06", tz="UTC"), 60, "long", np.nan)
    assert np.isnan(t)
    print("SELF-TEST OK (ATR hand-verified; imports resolve).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
