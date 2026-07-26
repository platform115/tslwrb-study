#!/usr/bin/env python3
"""
continuous_outcome.py  — A2 (continuous outcome) + clean survival-intent (A1 without censoring)
================================================================================================
WHY: the reach/stall binary at pt1 may be a LOSSY threshold. If early-window features track a GRADED
development outcome even when they don't cleanly separate the binary, the threshold (not the features)
was the problem. Two graded outcomes, both leakage-free (predictor = first 30s; outcome realized later):
  MFE_ticks  = max favorable excursion over the trade (from entry price, 1m-bar highs/lows). ALL 76
               non-losers. "How FAR it developed."  (Tomasini & Jaekle; MFE/MAE standard.)
  time_to_pt1 = seconds entry->pt1, REACHES ONLY (47). No censoring (only trades with the event).
               "How FAST it developed." This is the CLEAN survival-intent read.

WHY NOT literal Cox (A1): a stall is censored at HIS exit, but his exit IS the event we study ->
INFORMATIVE censoring -> naive Cox can bias/flip, not just widen CIs. The clean development-speed
question (time_to_pt1 among reaches) has no censoring. Full competing-risks cause-specific hazard
(Fine & Gray 1999) is possible but heavy/assumption-laden at n=76 -> opt-in, not default.

EARLY WINDOW = [entry, entry+30s] (tau=30s): every trade's hold>=35s, so FULL window for all 76,
no exit-capping, no length confound, no whole-life leakage. (120s was where the binary hurst lean
was strongest, but it caps short stalls -> not clean for a graded predictive read; 30s is honest.)

PRE-REGISTERED DIRECTIONS (frozen; reported two-sided via CI):
  vs MFE        : "organized/persistent" early flow -> develops further -> POSITIVE Spearman
                  (hurst, rho1, flow_level, ER_abs). intensity_level: no committed direction.
  vs time_to_pt1: more organized -> reaches FASTER -> NEGATIVE Spearman (among reaches).
A feature "tracks development" if its Spearman 95% bootstrap CI excludes 0.

STATISTIC: Spearman rank correlation; 95% CI by pair bootstrap (resample (feature,outcome) pairs,
seed 0, 10000). Two-sided. Discovery = report; Feb = validate. Logged trials (feed Deflated-Sharpe N).

REUSES: build_arms, read_trade_full, window_features (forward_battery); S, TICK (trade_flow_exhaustion).

RUN:  python3 continuous_outcome.py --config config.toml --wrb wrb_1m.parquet
      python3 continuous_outcome.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK
from forward_battery import build_arms, read_trade_full, window_features

TAU_S = 30
SYMBOL = "ESZ5"
FEATS = ["hurst", "rho1", "flow_level", "ER_abs", "intensity_level", "intensity_slope"]
POS_EXPECT = {"hurst", "rho1", "flow_level", "ER_abs"}   # expected POSITIVE vs MFE


def avg_rank(a):
    a = np.asarray(a, float)
    order = np.argsort(a, kind="mergesort")
    r = np.empty(len(a)); r[order] = np.arange(1, len(a) + 1)
    # average ties
    u, inv, cnt = np.unique(a, return_inverse=True, return_counts=True)
    sums = np.zeros(len(u)); np.add.at(sums, inv, r)
    return (sums / cnt)[inv]


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    if len(x) < 5:
        return np.nan, 0
    rx, ry = avg_rank(x), avg_rank(y)
    rx -= rx.mean(); ry -= ry.mean()
    d = np.sqrt((rx * rx).sum() * (ry * ry).sum())
    return (float((rx * ry).sum() / d) if d > 0 else np.nan), len(x)


def spearman_ci(x, y, seed=0, B=10000):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y)); x, y = x[ok], y[ok]
    rho, n = spearman(x, y)
    if not np.isfinite(rho) or n < 5:
        return dict(rho=np.nan, lo=np.nan, hi=np.nan, n=n, excl0=False)
    rng = np.random.default_rng(seed)
    boot = np.empty(B)
    for i in range(B):
        idx = rng.integers(0, n, n)
        boot[i] = spearman(x[idx], y[idx])[0]
    lo, hi = float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5))
    return dict(rho=rho, lo=lo, hi=hi, n=n, excl0=(lo > 0 or hi < 0))


def mfe_ticks(bars, entry_px, side, entry, exit_):
    seg = bars[(bars.ts_event >= entry.floor("min")) & (bars.ts_event <= exit_)]
    if len(seg) == 0:
        return np.nan
    return ((seg.high.max() - entry_px) if side == "long" else (entry_px - seg.low.min())) / TICK


def run(config, wrb, seed=0):
    import tomllib
    cfg = tomllib.load(open(config, "rb"))
    stall, reach, windowed = build_arms(config, wrb)
    g = pd.concat([stall, reach], ignore_index=True)

    # entry price by uid
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep.source_file + "::" + ep.episode_id.astype(str)
    px = dict(zip(ep.uid, ep.entry_prices.map(lambda a: float(np.asarray(a).ravel()[0]))))
    g["entry_px"] = g.uid.map(px)

    # MFE from 1m bars
    bars = pd.read_parquet(cfg["paths"]["es_1m_front"])
    bars = bars[bars.symbol == SYMBOL]
    g["MFE"] = [mfe_ticks(bars, r.entry_px, r.side, r.entry, r.exit) for _, r in g.iterrows()]
    print(f"[arms] n={len(g)} (stall {len(stall)} reach {len(reach)})  MFE NaN: {int(g.MFE.isna().sum())}")
    print(f"[MFE ticks] reach med={g[g.group=='target_reached'].MFE.median():.1f}  "
          f"stall med={g[g.group=='failed_trades'].MFE.median():.1f}")

    # early features (tau=30s, clean for all)
    t_min = g.entry.min() - S(2); t_max = (g.entry + S(TAU_S)).max()
    ts_ns, rs, sz, mid = read_trade_full(windowed, t_min, t_max)
    rows = []
    for _, r in g.iterrows():
        f = window_features(ts_ns, rs, sz, mid, r.side, r.entry, min(r.entry + S(TAU_S), r.exit))
        rows.append(f if f else {})
    F = pd.DataFrame(rows)
    for c in FEATS:
        g[c] = F[c].values if c in F else np.nan

    print(f"\n=== A2: Spearman(early-30s feature, MFE)  — all {len(g)} non-losers ===")
    print(f"{'feature':16s} {'rho':>7s} {'95% CI':>18s}  exp  flag")
    for f in FEATS:
        ci = spearman_ci(g[f], g.MFE, seed=seed)
        exp = "+" if f in POS_EXPECT else "?"
        flag = "** tracks MFE" if ci["excl0"] else "  -"
        print(f"{f:16s} {ci['rho']:+7.3f}  [{ci['lo']:+.3f},{ci['hi']:+.3f}]   {exp}   {flag}")

    rdf = g[g.group == "target_reached"].copy()
    rdf["t2pt1"] = rdf.pt1_open_el
    print(f"\n=== A1-clean: Spearman(early-30s feature, time_to_pt1) — reaches only n={len(rdf)} ===")
    print("(more organized early flow -> reaches FASTER -> expect NEGATIVE)")
    for f in FEATS:
        ci = spearman_ci(rdf[f], rdf.t2pt1, seed=seed)
        flag = "** tracks speed" if ci["excl0"] else "  -"
        print(f"{f:16s} {ci['rho']:+7.3f}  [{ci['lo']:+.3f},{ci['hi']:+.3f}]       {flag}")
    print("\nREAD: if a feature tracks MFE/speed (CI excludes 0) even though its binary AUC didn't "
          "clear, the pt1 THRESHOLD hid graded signal. If all straddle 0, the threshold wasn't the issue.")


def selftest(config, wrb):
    print("=== SELF-TEST: spearman + MFE ===")
    x = np.arange(50.0); y = x * 2 + 3
    print(f"  monotonic up:   rho={spearman(x,y)[0]:+.3f} (expect +1)")
    print(f"  monotonic down: rho={spearman(x,-y)[0]:+.3f} (expect -1)")
    assert abs(spearman(x, y)[0] - 1) < 1e-9 and abs(spearman(x, -y)[0] + 1) < 1e-9
    rng = np.random.default_rng(0); a = rng.normal(0, 1, 200); b = rng.normal(0, 1, 200)
    ci = spearman_ci(a, b, seed=0)
    print(f"  random pairs:   rho={ci['rho']:+.3f} CI[{ci['lo']:+.3f},{ci['hi']:+.3f}] excl0={ci['excl0']} (expect False)")
    assert not ci["excl0"]
    bars = pd.DataFrame({"ts_event": pd.to_datetime(["2025-10-06 14:00","2025-10-06 14:01"], utc=True),
                         "high": [5005.0, 5010.0], "low": [4998.0, 5001.0]})
    m = mfe_ticks(bars, 5000.0, "long", pd.Timestamp("2025-10-06 14:00:30", tz="UTC"),
                  pd.Timestamp("2025-10-06 14:01:30", tz="UTC"))
    print(f"  MFE long entry 5000, max high 5010: {m:.1f} ticks (expect 40)")
    assert abs(m - 40) < 1e-9
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
