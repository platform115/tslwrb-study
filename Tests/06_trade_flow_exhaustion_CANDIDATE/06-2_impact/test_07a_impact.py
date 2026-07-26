#!/usr/bin/env python3
"""
test_07a_impact.py  — 07a: PLAIN price impact (undirected), the unambiguous λ test
-------------------------------------------------------------------------------
QUESTION
  Does price move MORE per unit of traded volume right before a cut than mid-flight
  in a runner? High impact = thin/easy-to-push = vulnerable (Kyle 1985 depth read);
  low impact = volume absorbed without price moving = absorption. TWO-SIDED, because
  those two documented mechanisms point opposite ways and we do not pre-commit a sign.

WHY "PLAIN" / UNDIRECTED
  The Amihud (2002) ratio Σ|Δmid| / Σvolume is inherently unsigned. The Kyle λ slope
  (Δmid regressed on signed flow) is unchanged by orienting to the trade (the sign
  cancels). So 07a is direction-agnostic by construction — `side` is unused. The
  orientation/subset work is 07b's job, not 07a's. This is the clean, unambiguous λ.

ESTIMATORS (both reported; no primary frozen on discovery)
  Per second within the window, aligned to the diff seconds i=1..n-1:
    Δmid_i (ticks) = (mid_i - mid_{i-1}) / TICK
    vol_i          = buy_vol_i + sell_vol_i           (total traded size that second)
    sflow_i        = buy_vol_i - sell_vol_i           (signed aggressor flow)
  RATIO (Amihud-family, PRIMARY-candidate): Σ|Δmid_i| / Σ vol_i  — impact per unit volume.
  SLOPE (Kyle λ, confirming):               OLS slope of Δmid_i on sflow_i (Cov/Var).
  Reference: Kyle (1985); Amihud (2002); OFI family Cont-Kukanov-Stoikov (2014).
  NB this is a reduced-form EMPIRICAL impact coefficient over short windows, NOT a
  structural Kyle λ — do not relabel it "Kyle's λ" in any freeze.

NECESSARY-vs-SUFFICIENT CHECK vs 08 (baked in, pre-registered)
  08-bar separated Design A at P=0.348 (failed>reached compression), driven by raw
  current-bar RANGE (TR), not by the volume baseline. 07a's ratio NUMERATOR (Σ|Δmid|)
  is the same price-movement family at per-second resolution. So we also report the
  NUMERATOR-ONLY AUC. If the full ratio's AUC ≈ the numerator-only AUC, then dividing
  by volume adds nothing and 07a is 08 re-expressed at finer resolution — MBP-10 has
  not earned its complexity HERE. If the ratio separates beyond the numerator alone,
  the liquidity/volume normalization is doing real work. The spine coherence block
  (Σnum vs Σden per arm) shows which half drives any ratio gap.

PRE-REGISTRATION: two-sided; read = does the 95% CI exclude 0.5 and in which direction.
PRIMARY window = Design A (52/40). A1/anchor = context (inherits pt1 coil confound).
POPULATION: 52 target_reached vs 40 failed_trades. Deterministic (seed=0). Read-only.

RUN
  python3 test_07a_impact.py --config ../../config.toml --wrb ../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---
import argparse
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import read_per_second, S, M, TICK, MAX_GAP_S, ROLL_JUMP_TICKS


def impact_core(sec, buyv, sellv, mid, ws, we):
    """Per-window impact ingredients on the diff seconds. None if unscoreable/flagged."""
    ws_s = np.int64(pd.Timestamp(ws).value // 1_000_000_000)
    we_s = np.int64(pd.Timestamp(we).value // 1_000_000_000)
    a = np.searchsorted(sec, ws_s, "left"); b = np.searchsorted(sec, we_s, "left")
    s = sec[a:b]; bv = buyv[a:b]; sv = sellv[a:b]; mz = mid[a:b]
    n = len(s)
    if n < 2:
        return None
    # tripwire (same thresholds as frozen machinery): session/halt gap or roll jump
    if np.diff(s).max() > MAX_GAP_S:
        return None
    dmid = np.diff(mz)
    if (np.abs(dmid) / TICK).max() > ROLL_JUMP_TICKS:
        return None
    dmid_tk = dmid / TICK                       # i = 1..n-1
    vol = (bv + sv)[1:].astype(float)           # volume during the diff second
    sflow = (bv - sv)[1:].astype(float)         # signed flow during the diff second
    num = float(np.abs(dmid_tk).sum())
    den = float(vol.sum())
    ratio = num / den if den > 0 else np.nan
    if len(sflow) >= 2 and sflow.var() > 0:
        slope = float(np.cov(sflow, dmid_tk)[0, 1] / sflow.var())
    else:
        slope = np.nan
    return dict(num=num, den=den, ratio=ratio, slope=slope, n=int(n))


def make_feature_fns(sec, buyv, sellv, mid):
    def core(ws, we):
        return impact_core(sec, buyv, sellv, mid, ws, we)

    def f_ratio(side, ws, we):
        r = core(ws, we)
        if r is None:
            return {"value": np.nan}
        return {"value": r["ratio"], "num": r["num"], "den": r["den"], "n": r["n"]}

    def f_slope(side, ws, we):
        r = core(ws, we)
        return {"value": np.nan} if r is None else {"value": r["slope"]}

    def f_num(side, ws, we):                    # numerator-only = raw per-second movement
        r = core(ws, we)
        return {"value": np.nan} if r is None else {"value": r["num"]}

    return f_ratio, f_slope, f_num


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--W", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    failed, reached, g, ep_path, windowed = spine.load_and_group(args.config, args.wrb)
    print(f"[07a] target_reached={len(reached)}  failed_trades={len(failed)}  (expect 52 / 40)")

    t_min = g["a1_s"].min(); t_max = g["exit"].max() + M(1)
    print(f"[07a] streaming per-second ESZ5 trade flow in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[07a] per-second rows: {len(sec):,} ({len(sec)/3600:.1f} grid-hours)")

    f_ratio, f_slope, f_num = make_feature_fns(sec, buyv, sellv, mid)
    W = S(args.W)

    # ---- PRIMARY-candidate: Amihud ratio, Design A, two-sided ----
    res_ratio = spine.designA_perCut(failed, reached, f_ratio, W, seed=args.seed)
    spine.report_designA("07a  RATIO  Σ|Δmid| / Σvol  (impact per unit volume)", res_ratio)
    spine.report_coherence("07a ratio: Σnum=Σ|Δmid|(ticks)  Σden=Σvol",
                           res_ratio["coh_cut"], res_ratio["coh_peer"])

    # ---- confirming: Kyle λ slope ----
    res_slope = spine.designA_perCut(failed, reached, f_slope, W, seed=args.seed)
    spine.report_designA("07a  SLOPE  λ = Δmid on signed flow  (confirming)", res_slope)

    # ---- necessary-vs-sufficient: numerator-only (is the ratio just raw movement = 08?) ----
    res_num = spine.designA_perCut(failed, reached, f_num, W, seed=args.seed)
    spine.report_designA("07a  NUMERATOR-ONLY  Σ|Δmid|  (raw movement; cf. 08's TR driver)", res_num)

    print("\n  [read vs 08]  08-bar Design A was P=0.348 (failed>reached, TR-driven).")
    print("    * If RATIO P ≈ NUMERATOR-ONLY P  -> volume normalization adds nothing; 07a ~ 08 finer-res.")
    print("    * If RATIO P separates beyond NUMERATOR-ONLY -> the liquidity normalization earns the data.")
    print("    * Coherence: a ratio gap with similar Σden but differing Σnum = numerator(movement)-driven.")

    # ---- CONTEXT: A1 (we=entry) and anchor, ratio, population two-sided ----
    print("\n  [context] population-level two-sided AUC on the RATIO (inherits coil confound at anchor):")
    for label, ws_col, we_col in [("A1 pre-entry", "a1_s", "a1_e"),
                                   ("anchor (A2/B)", "a2_s", "a2_e")]:
        r = spine.population_auc(failed, reached, f_ratio, ws_col, we_col)
        spine.report_population(label, r)

    print("\n[07a] DONE. Read order: RATIO Design A (the test), then NUMERATOR-ONLY (the 08 check),")
    print("      then SLOPE (confirming), then coherence (which half drives any gap).")


if __name__ == "__main__":
    main()
