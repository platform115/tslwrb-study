#!/usr/bin/env python3
"""
test_07b_impact.py  — 07b: WITH-TRADE-FLOW-ONLY impact + combined Reading-A verdict
-------------------------------------------------------------------------------
QUESTION
  Restrict to the seconds where aggressor flow is WITH the trade (oriented flow > 0),
  and ask: when the trade's own side is buying (long) / selling (short), how much does
  price move per unit of that with-trade volume? This is the absorption-vs-thinning
  read in its cleanest form:
    low impact on with-trade flow  = volume absorbed, move being capped  = stall/absorption
    high impact on with-trade flow = with-trade volume pushes price easily = thin/vulnerable
  TWO-SIDED (both mechanisms documented, sign not pre-committed).

WHY THIS IS THE DIRECTIONAL TEST (unlike 07a)
  07a is undirected: the Amihud ratio and the λ slope both cancel orientation. 07b uses
  the trade sign to SUBSET the seconds (keep only oriented_flow > 0). The sign therefore
  does real work here — 07b is the only impact test that is genuinely directional.

ESTIMATORS (both reported; no primary frozen on discovery), on the SUBSET seconds:
  RATIO = Σ|Δmid| / Σvol over {oriented_flow > 0}            (absorption = low)
  SLOPE = OLS of oriented_Δmid on oriented_flow over the same subset (favorable move per
          unit with-trade flow; computed on oriented quantities so long/short are comparable).
  Reference: Kyle (1985); Amihud (2002); OFI family Cont-Kukanov-Stoikov (2014).

CARRIED FLAGS (pre-registered, do not drop)
  (1) MAY BE UNINFORMATIVE BY CONSTRUCTION: 07b only sees the oriented-flow seconds.
      The descriptive pass put that at median ~26/60 (p10 ~17-20), so it should be
      estimable — but this script reports the live subset-second medians per arm, and a
      window with <1 subset sec (ratio) / <2 (slope) returns NaN, never a 1-point value.
  (2) RATIO MAY INHERIT 07a's VOLUME-SCALING FLATNESS: 07a showed the impact RATIO sat at
      chance (P=0.424) because |Δmid| and volume co-scale on active bars; subsetting changes
      WHICH seconds, not that co-scaling. So a flat 07b ratio is EXPECTED, not surprising;
      the SLOPE on the subset is the more likely place for a directional signal here.

COMBINED READING-A VERDICT (pre-registered)
  The impact LENS = {07a ratio, 07a slope, 07b ratio, 07b slope}. Decision rule: the lens
  is INFORMATIVE if ANY of the four 95% CIs excludes 0.5 at >=8 cuts; else the lens is NULL.
  This script RECOMPUTES the 07a estimators on the same loaded arrays (should reproduce
  test_07a_impact.py's 0.424 / 0.434 exactly) so the combined verdict is one reproducible
  artifact, not an eyeball across two runs. The 07a numerator-only (raw movement, 0.242) is
  NOT part of the impact lens — it is the 08 price-movement signal, reported only as context.

PRIMARY window = Design A (52/40). POPULATION: 52 reached vs 40 failed. Deterministic (seed=0).
Read-only.

RUN
  python3 test_07b_impact.py --config ../../config.toml --wrb ../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---
import argparse
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import read_per_second, S, M, TICK, MAX_GAP_S, ROLL_JUMP_TICKS


def aligned(sec, buyv, sellv, mid, ws, we, side):
    """Per-window aligned diff-second arrays + orientation. None if unscoreable/flagged."""
    ws_s = np.int64(pd.Timestamp(ws).value // 1_000_000_000)
    we_s = np.int64(pd.Timestamp(we).value // 1_000_000_000)
    a = np.searchsorted(sec, ws_s, "left"); b = np.searchsorted(sec, we_s, "left")
    s = sec[a:b]; bv = buyv[a:b]; sv = sellv[a:b]; mz = mid[a:b]
    n = len(s)
    if n < 2:
        return None
    if np.diff(s).max() > MAX_GAP_S:
        return None
    dmid = np.diff(mz)
    if (np.abs(dmid) / TICK).max() > ROLL_JUMP_TICKS:
        return None
    sgn = 1.0 if side == "long" else -1.0
    dmid_tk = dmid / TICK                        # i = 1..n-1
    vol = (bv + sv)[1:].astype(float)
    sflow = (bv - sv)[1:].astype(float)
    return dict(dmid_tk=dmid_tk, vol=vol, sflow=sflow,
                oriented_flow=sflow * sgn, oriented_dmid=dmid_tk * sgn, n=int(n))


def _ratio(dmid_tk, vol):
    den = vol.sum()
    return (np.abs(dmid_tk).sum() / den) if den > 0 and len(vol) >= 1 else np.nan


def _slope(x, y):
    if len(x) >= 2 and x.var() > 0:
        return float(np.cov(x, y)[0, 1] / x.var())
    return np.nan


def make_feature_fns(sec, buyv, sellv, mid):
    def A(ws, we, side):
        return aligned(sec, buyv, sellv, mid, ws, we, side)

    # ---- 07b: subset to oriented_flow > 0 ----
    def b_ratio(side, ws, we):
        d = A(ws, we, side)
        if d is None:
            return {"value": np.nan}
        m = d["oriented_flow"] > 0
        if m.sum() < 1:
            return {"value": np.nan, "n": 0}
        return {"value": _ratio(d["dmid_tk"][m], d["vol"][m]),
                "num": float(np.abs(d["dmid_tk"][m]).sum()),
                "den": float(d["vol"][m].sum()), "n": int(m.sum())}

    def b_slope(side, ws, we):
        d = A(ws, we, side)
        if d is None:
            return {"value": np.nan}
        m = d["oriented_flow"] > 0
        if m.sum() < 2:
            return {"value": np.nan}
        return {"value": _slope(d["oriented_flow"][m], d["oriented_dmid"][m])}

    # ---- 07a recomputed (no subset) for the combined verdict ----
    def a_ratio(side, ws, we):
        d = A(ws, we, side)
        return {"value": np.nan} if d is None else {"value": _ratio(d["dmid_tk"], d["vol"])}

    def a_slope(side, ws, we):
        d = A(ws, we, side)
        return {"value": np.nan} if d is None else {"value": _slope(d["sflow"], d["dmid_tk"])}

    return b_ratio, b_slope, a_ratio, a_slope


def subset_size_report(failed, reached, b_ratio, W):
    """Live 'uninformative by construction' check: subset-second medians per Design-A arm."""
    def med_n(windows):
        ns = []
        for w in windows:
            r = b_ratio(w["side"], w["ws"], w["we"])
            if r and "n" in r and not np.isnan(r["value"]):
                ns.append(r["n"])
        return (np.median(ns) if ns else np.nan), len(ns)
    cut_w = spine.designA_cut_windows(failed, W)
    peer_w = []
    for _, f in failed.iterrows():
        peer_w += spine.designA_peer_windows_for(f, reached, W)
    mc, nc = med_n(cut_w); mp, npn = med_n(peer_w)
    print(f"\n  [uninformative-by-construction check] median subset (oriented>0) seconds/window:")
    print(f"    failed cut   = {mc:.0f}  (scored {nc}/{len(cut_w)})")
    print(f"    reached peer = {mp:.0f}  (scored {npn}/{len(peer_w)})")
    print(f"    (descriptive pass expected ~26; if these collapse toward ~1-3, 07b is uninformative.)")


def combined_verdict(items):
    print("\n" + "=" * 78)
    print("COMBINED READING-A VERDICT — impact LENS = {07a ratio, 07a slope, 07b ratio, 07b slope}")
    print("Rule (pre-registered): lens INFORMATIVE if ANY 95% CI excludes 0.5 at >=8 cuts; else NULL.")
    print("=" * 78)
    any_sep = False
    for name, ci in items:
        ok = (not np.isnan(ci["mean"])) and ci["excludes_half"] and ci["n"] >= 8
        any_sep = any_sep or ok
        tag = "SEPARATES" if ok else "null"
        print(f"  {name:22s} P={ci['mean']:.3f}  CI[{ci['lo']:.3f}, {ci['hi']:.3f}]  cuts={ci['n']}  -> {tag}")
    print("-" * 78)
    if any_sep:
        print("  VERDICT: impact lens shows separation in >=1 estimator (see which, above).")
    else:
        print("  VERDICT: impact lens is NULL on October — no volume-normalized impact estimator separates.")
    print("  CONTEXT (not part of the lens): 07a numerator-only (raw |Δmid|) separated at P=0.242,")
    print("  same direction as 08 (P=0.348). A null impact lens beside a separating raw-movement signal")
    print("  reads as: price MOVES more before cuts, but NOT in a volume-normalized / liquidity sense.")
    print("  That is evidence the impact LENS does not earn the MBP-10 complexity here — raw movement does.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--W", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    failed, reached, g, ep_path, windowed = spine.load_and_group(args.config, args.wrb)
    print(f"[07b] target_reached={len(reached)}  failed_trades={len(failed)}  (expect 52 / 40)")

    t_min = g["a1_s"].min(); t_max = g["exit"].max() + M(1)
    print(f"[07b] streaming per-second ESZ5 trade flow in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[07b] per-second rows: {len(sec):,} ({len(sec)/3600:.1f} grid-hours)")

    b_ratio, b_slope, a_ratio, a_slope = make_feature_fns(sec, buyv, sellv, mid)
    W = S(args.W)

    subset_size_report(failed, reached, b_ratio, W)

    # ---- 07b primary: subset ratio + slope, Design A, two-sided ----
    res_br = spine.designA_perCut(failed, reached, b_ratio, W, seed=args.seed)
    spine.report_designA("07b  RATIO (subset oriented>0)  Σ|Δmid|/Σvol  (absorption=low)", res_br)
    spine.report_coherence("07b ratio: Σnum=Σ|Δmid|(ticks)  Σden=Σvol  (subset seconds only)",
                           res_br["coh_cut"], res_br["coh_peer"])
    res_bs = spine.designA_perCut(failed, reached, b_slope, W, seed=args.seed)
    spine.report_designA("07b  SLOPE (subset)  oriented Δmid on oriented flow", res_bs)

    # ---- 07a recomputed (combined verdict; should match test_07a: 0.424 / 0.434) ----
    res_ar = spine.designA_perCut(failed, reached, a_ratio, W, seed=args.seed)
    res_as = spine.designA_perCut(failed, reached, a_slope, W, seed=args.seed)
    print(f"\n  [reproducibility] 07a recomputed here: ratio P={res_ar['ci']['mean']:.3f} "
          f"slope P={res_as['ci']['mean']:.3f}  (expect ~0.424 / ~0.434 from test_07a_impact.py)")

    combined_verdict([
        ("07a ratio", res_ar["ci"]), ("07a slope", res_as["ci"]),
        ("07b ratio", res_br["ci"]), ("07b slope", res_bs["ci"]),
    ])

    # ---- context ----
    print("\n  [context] population-level two-sided AUC on 07b subset RATIO (coil confound at anchor):")
    for label, ws_col, we_col in [("A1 pre-entry", "a1_s", "a1_e"), ("anchor (A2/B)", "a2_s", "a2_e")]:
        r = spine.population_auc(failed, reached, b_ratio, ws_col, we_col)
        spine.report_population(label, r)

    print("\n[07b] DONE.")


if __name__ == "__main__":
    main()
