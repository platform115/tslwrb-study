#!/usr/bin/env python3
"""
speed_leads_robustness.py — lock-in diagnostic for the SPEED leads (the one live vein)
=======================================================================================
CONTEXT: the trader's own account is that the MOVEMENT/SPEED of price action drives his cut/hold.
Order-flow framings (sign/OFI/persistence/book) were all null. The only positive is a SPEED result:
among REACHES, stronger early flow_level (-0.46) and higher ER (-0.36) -> reach pt1 FASTER
(continuous_outcome.py, tau=30s, n=47). This script stress-tests that single result before we lean on
it, and settles the distance question with numbers.

THREE CHECKS (reaches only; no stall arm — this is a speed-among-winners effect, NOT a hit/miss test):
  1. WINDOW ROBUSTNESS. Re-measure Spearman(feature, time_to_pt1) at tau in {30,60,120}s, each on the
     CLEAN subset pt1_open_el >= tau so the early window strictly PRECEDES pt1 (no peeking at/after the
     event). A real effect should not depend on one window. n shrinks as tau grows — reported.
  2. DISTANCE CHARACTERISATION. entry->pt1 distance (ticks) = oriented (pt1-bar favorable extreme -
     entry px). pt1 is a WRB (wide-range bar) by construction, so distance is NOT a fixed small target.
     Report distribution + Spearman(time_to_pt1, distance): if >=0, faster is NOT "closer" (settles the
     objection); a strong negative would be the confound.
  3. DISTANCE CONTROL. First-order partial Spearman(flow_level, time_to_pt1 | distance). If the speed
     effect survives partialling distance out, it is not a distance artifact. (Mechanistic note: strong
     signed flow is WHAT drives price into a wide bar, so flow->faster-pt1 is partly momentum confirming
     itself — Lillo & Farmer 2004 order-flow persistence. Real effect, not necessarily a novel one.)

PRE-REGISTERED: feature->time_to_pt1 NEGATIVE at all tau; time_to_pt1<->distance NON-negative;
partial(flow_level,t2pt1|distance) stays NEGATIVE and CI excludes 0 if the effect is distance-robust.

REUSES: build_arms, read_trade_full, window_features (forward_battery); spearman, spearman_ci,
avg_rank (continuous_outcome); S, TICK (trade_flow_exhaustion).

RUN:  python3 speed_leads_robustness.py --config config.toml --wrb wrb_1m.parquet
      python3 speed_leads_robustness.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK
from forward_battery import build_arms, read_trade_full, window_features
from continuous_outcome import spearman, spearman_ci

TAUS = [30, 60, 120]
SYMBOL = "ESZ5"
WRB_TF = "1m"
floor_min = lambda t: t.floor("min")


def partial_spearman(x, y, z):
    """First-order partial Spearman of x,y controlling z."""
    x, y, z = map(lambda a: np.asarray(a, float), (x, y, z))
    ok = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
    x, y, z = x[ok], y[ok], z[ok]
    if len(x) < 6:
        return np.nan, 0
    rxy = spearman(x, y)[0]; rxz = spearman(x, z)[0]; ryz = spearman(y, z)[0]
    d = np.sqrt((1 - rxz ** 2) * (1 - ryz ** 2))
    return ((rxy - rxz * ryz) / d if d > 0 else np.nan), len(x)


def partial_spearman_ci(x, y, z, seed=0, B=10000):
    x, y, z = map(lambda a: np.asarray(a, float), (x, y, z))
    ok = ~(np.isnan(x) | np.isnan(y) | np.isnan(z)); x, y, z = x[ok], y[ok], z[ok]
    r, n = partial_spearman(x, y, z)
    if not np.isfinite(r) or n < 6:
        return dict(r=np.nan, lo=np.nan, hi=np.nan, n=n, excl0=False)
    rng = np.random.default_rng(seed); boot = np.empty(B)
    for i in range(B):
        idx = rng.integers(0, n, n)
        boot[i] = partial_spearman(x[idx], y[idx], z[idx])[0]
    lo, hi = float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5))
    return dict(r=r, lo=lo, hi=hi, n=n, excl0=(lo > 0 or hi < 0))


def pt1_distance_ticks(wrb, side, entry, entry_px):
    """Oriented entry->pt1 distance in ticks, using the pt1 WRB bar's favorable extreme.
    Re-derives pt1 exactly as build_groups (first in-direction bar at/after entry minute)."""
    want = "bullish" if side == "long" else "bearish"
    cand = wrb[(wrb.direction == want) & (wrb.ts_event >= floor_min(entry))]
    if len(cand) == 0:
        return np.nan
    bar = cand.iloc[0]
    fav = bar.high if side == "long" else bar.low
    return ((fav - entry_px) if side == "long" else (entry_px - fav)) / TICK


def run(config, wrb_path, seed=0):
    import tomllib
    cfg = tomllib.load(open(config, "rb"))
    _, reach, windowed = build_arms(config, wrb_path)
    print(f"[arms] reaches n={len(reach)} (stall arm not used — speed-among-winners effect)")

    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep.source_file + "::" + ep.episode_id.astype(str)
    px = dict(zip(ep.uid, ep.entry_prices.map(lambda a: float(np.asarray(a).ravel()[0]))))
    reach = reach.copy(); reach["entry_px"] = reach.uid.map(px)

    wrb = pd.read_parquet(wrb_path)
    if "timeframe" in wrb: wrb = wrb[wrb.timeframe == WRB_TF]
    wrb = wrb[wrb.symbol == SYMBOL].sort_values("ts_event")
    reach["dist"] = [pt1_distance_ticks(wrb, r.side, r.entry, r.entry_px) for _, r in reach.iterrows()]

    el = reach.pt1_open_el
    print("\n=== pt1_open_el (time entry->pt1, s) among reaches ===")
    print(f"  min {el.min():.0f}  p25 {el.quantile(.25):.0f}  med {el.median():.0f}  "
          f"p75 {el.quantile(.75):.0f}  max {el.max():.0f}")
    print(f"  clean-window n (pt1_open_el>=tau):  " + "  ".join(f"tau{t}:{int((el>=t).sum())}" for t in TAUS))

    print("\n=== entry->pt1 DISTANCE (ticks; pt1 = first in-dir WRB favorable extreme) ===")
    d = reach.dist
    print(f"  min {d.min():.1f}  p25 {d.quantile(.25):.1f}  med {d.median():.1f}  "
          f"p75 {d.quantile(.75):.1f}  max {d.max():.1f}")
    ci = spearman_ci(reach.pt1_open_el, reach.dist, seed=seed)
    print(f"  Spearman(time_to_pt1, distance) = {ci['rho']:+.3f}  CI[{ci['lo']:+.3f},{ci['hi']:+.3f}]")
    print("    >=0 => faster is NOT 'closer' (distance objection settled); strong - would be the confound.")

    # early features per tau (clean subset), read MBP once over the max span
    t_min = reach.entry.min() - S(2); t_max = (reach.entry + S(max(TAUS))).max()
    ts_ns, rs, sz, mid = read_trade_full(windowed, t_min, t_max)

    print("\n=== 1. WINDOW ROBUSTNESS: Spearman(feature, time_to_pt1), clean subset pt1_open_el>=tau ===")
    print("(pre-registered NEGATIVE: stronger/cleaner early flow -> faster to pt1)")
    feats_at = {}
    for tau in TAUS:
        sub = reach[reach.pt1_open_el >= tau].copy()
        rows = [window_features(ts_ns, rs, sz, mid, r.side, r.entry, r.entry + S(tau)) or {}
                for _, r in sub.iterrows()]
        F = pd.DataFrame(rows, index=sub.index)
        print(f"  --- tau={tau}s  (n={len(sub)}) ---")
        for f in ("flow_level", "ER_abs"):
            sub[f] = F[f].values if f in F else np.nan
            c = spearman_ci(sub[f], sub.pt1_open_el, seed=seed)
            flag = "** holds" if (c["excl0"] and c["rho"] < 0) else ("(clears, wrong sign)" if c["excl0"] else "  -")
            print(f"     {f:11s} rho={c['rho']:+.3f}  CI[{c['lo']:+.3f},{c['hi']:+.3f}]  n={c['n']:>2}  {flag}")
        if tau == 30:
            feats_at[30] = (sub["flow_level"].values, sub.pt1_open_el.values, sub.dist.values)

    print("\n=== 3. DISTANCE CONTROL: partial Spearman(flow_level, time_to_pt1 | distance), tau=30 ===")
    fx, ty, dz = feats_at[30]
    raw = spearman_ci(fx, ty, seed=seed)
    pc = partial_spearman_ci(fx, ty, dz, seed=seed)
    print(f"  raw     flow_level vs time_to_pt1   {raw['rho']:+.3f}  CI[{raw['lo']:+.3f},{raw['hi']:+.3f}]")
    print(f"  partial (| distance)               {pc['r']:+.3f}  CI[{pc['lo']:+.3f},{pc['hi']:+.3f}]  "
          f"{'** survives — not a distance artifact' if (pc['excl0'] and pc['r']<0) else 'collapses under distance'}")
    print("\nREAD: effect that holds across tau AND survives the distance partial = a robust, locked speed "
          "lead (among winners). If it collapses at larger tau or under distance, it was fragile/mechanical.")


def selftest(config, wrb):
    print("=== SELF-TEST: partial_spearman + pt1_distance ===")
    rng = np.random.default_rng(0)
    z = rng.normal(0, 1, 300); x = z + rng.normal(0, .3, 300); y = z + rng.normal(0, .3, 300)
    r_raw = spearman(x, y)[0]; r_par = partial_spearman(x, y, z)[0]
    print(f"  common-cause z: raw(x,y)={r_raw:+.3f} (high)  partial(x,y|z)={r_par:+.3f} (~0)")
    assert r_raw > 0.6 and abs(r_par) < 0.2
    a = rng.normal(0, 1, 300); b = a.copy(); w = rng.normal(0, 1, 300)
    print(f"  x==y indep of z: partial={partial_spearman(a,b,w)[0]:+.3f} (~+1)")
    assert partial_spearman(a, b, w)[0] > 0.95
    wrb = pd.DataFrame({"direction": ["bullish", "bullish"],
                        "ts_event": pd.to_datetime(["2025-10-06 14:00", "2025-10-06 14:02"], utc=True),
                        "high": [5012.0, 5020.0], "low": [4995.0, 5000.0], "symbol": "ESZ5", "timeframe": "1m"})
    dist = pt1_distance_ticks(wrb, "long", pd.Timestamp("2025-10-06 14:00:20", tz="UTC"), 5000.0)
    print(f"  pt1 distance long entry 5000, first-bar high 5012: {dist:.1f} ticks (expect 48)")
    assert abs(dist - 48) < 1e-9
    dist_s = pt1_distance_ticks(wrb.assign(direction="bearish"), "short",
                                pd.Timestamp("2025-10-06 14:00:20", tz="UTC"), 5000.0)
    print(f"  pt1 distance short entry 5000, first-bar low 4995: {dist_s:.1f} ticks (expect 20)")
    assert abs(dist_s - 20) < 1e-9
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
