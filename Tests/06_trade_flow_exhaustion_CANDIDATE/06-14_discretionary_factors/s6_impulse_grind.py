#!/usr/bin/env python3
"""
s6_impulse_grind.py — F1/S6: impulse-vs-grind (favorable-movement concentration), pre-registered GRID
======================================================================================================
impulse_frac = largest favorable RUN (tk) / total favorable movement (tk) over [entry, entry+60s].
(0,1]: 1.0 = one burst; low = distributed grind. "Impulsive vs corrective" is documented practitioner
vocabulary (Elliott tradition; general price action); run-length analysis is standard statistics; THIS
RATIO IS OUR CONSTRUCTION — flagged.

GRID-FIRST DESIGN (user directive: tunables are tested, not decided). 6 cells, ONE registry row —
look-count transparent. Validity constraints held fixed (not tunables): survivor frame decisive,
seed 0, existence of a denominator floor, 60s window (S4b already mapped sub-window structure).

PRE-REGISTERED:
  Tunable grid: run-break rule x2 {ADV-ONLY: only an adverse second breaks a run (flats continue);
                STRICT: any non-favorable second breaks} X denominator floor x3 {total_fav >= 2, 4, 6 tk}.
  Prediction on record: STRICT collapses toward tiny runs on sparse ES seconds and separates nothing
  (tested, not asserted).
  DIRECTION UNREGISTERED (user framing): AUC computed reach-positive; a clear in EITHER direction is a
  lead with observed direction + "direction unregistered" provenance recorded.
  Pattern rule (fixed pre-output, per run-rule): >=2/3 floors clear in the SAME direction -> `lead`
  (Feb list); single-cell clear -> `lead-weak` (logged, Feb list, found-by-sweep provenance);
  none -> `robust-null`.
  REFERENCE CELL (named now, not post-hoc): ADV-ONLY / floor 4 / survivors — redundancy block lives
  here: rho vs fav_net_vel and velocity_ratio, locked (-0.4,0.4) new / |0.6| redundant / else
  indeterminate. Descriptive extras at reference cell only: median max_run_tk and n_runs per arm.
  Frames: SURVIVORS (hold>=60, 45/24) decisive for all cells; ALL(B) printed at reference cell only.

RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
      06-14_discretionary_factors/s6_impulse_grind.py --config config.toml --wrb wrb_1m.parquet
Registry: T-DF08 · family=speed · grid · code_ref=06-14_discretionary_factors/s6_impulse_grind.py
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from velocity_acceleration import pathlen_tk
from s2_directional_velocity import s2_feats, PRE_W
from fav_net_vel_confirm import spearman_boot_ci

TAU = 60
MIN_WIN = 5
FLOORS = [2.0, 4.0, 6.0]
N_MIN = 8
REF = ("ADV-ONLY", 4.0)


def runs_stats(sec, mid, entry, exit_, side):
    """Per trade: total favorable tk + per-rule (max_run_tk, n_runs). NaNs if window <MIN_WIN s."""
    t0 = np.int64(pd.Timestamp(entry).value // 1_000_000_000)
    t_end = min(pd.Timestamp(entry) + S(TAU), pd.Timestamp(exit_))
    t1 = np.int64(pd.Timestamp(t_end).value // 1_000_000_000)
    out = dict(total_fav=np.nan, adv_max=np.nan, adv_n=np.nan, strict_max=np.nan, strict_n=np.nan)
    if t1 - t0 < MIN_WIN:
        return out
    a = np.searchsorted(sec, t0, "left"); b = np.searchsorted(sec, t1, "right")
    if b - a < 3:
        return out
    o = (mid[a:b] if side == "long" else -mid[a:b]) / TICK
    d = np.diff(o)                                     # per-second oriented increments (tk)
    out["total_fav"] = float(d[d > 0].sum())
    # ADV-ONLY: runs delimited by adverse seconds (d<0); flats continue; run value = sum of favorable inc
    cur = 0.0; mx = 0.0; n = 0; in_run = False
    for x in d:
        if x < 0:
            if in_run:
                mx = max(mx, cur); n += 1
            cur = 0.0; in_run = False
        else:
            if x > 0:
                in_run = True
            cur += max(x, 0.0)
    if in_run:
        mx = max(mx, cur); n += 1
    out["adv_max"] = mx; out["adv_n"] = n
    # STRICT: contiguous d>0 only
    cur = 0.0; mx = 0.0; n = 0
    for x in d:
        if x > 0:
            cur += x
        else:
            if cur > 0:
                mx = max(mx, cur); n += 1
            cur = 0.0
    if cur > 0:
        mx = max(mx, cur); n += 1
    out["strict_max"] = mx; out["strict_n"] = n
    return out


def impulse_frac(row, rule, floor):
    tf = row["total_fav"]
    if not np.isfinite(tf) or tf < floor:
        return np.nan
    mx = row["adv_max"] if rule == "ADV-ONLY" else row["strict_max"]
    return mx / tf if np.isfinite(mx) else np.nan


def cell_line(rv, sv, seed):
    ci = two_sample_boot_ci(rv, sv, seed=seed)
    if ci["clears"]:
        direction = "R>S" if ci["auc"] > 0.5 else "S>R"
        mark = f"** ({direction})"
    else:
        mark = "  "
    return ci, mark


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    surv = g[g.hold >= TAU].copy()
    print(f"[arms] reach {len(g[g.grp=='reach'])} / stall {len(g[g.grp=='stall'])} | "
          f"SURV {len(surv[surv.grp=='reach'])}R/{len(surv[surv.grp=='stall'])}S — decisive frame")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    RS = pd.DataFrame([runs_stats(sec, mid, r.entry, r.exit, r.side) for _, r in g.iterrows()], index=g.index)
    g = g.join(RS); surv = g[g.hold >= TAU]

    clears = {rule: [] for rule in ("ADV-ONLY", "STRICT")}
    print(f"\n  rule      floor  AUC (survivors)              nR/nS surviving floor")
    for rule in ("ADV-ONLY", "STRICT"):
        for fl in FLOORS:
            v = surv.apply(lambda r: impulse_frac(r, rule, fl), axis=1)
            rv = v[surv.grp == "reach"].dropna().values; sv = v[surv.grp == "stall"].dropna().values
            if len(rv) < N_MIN or len(sv) < N_MIN:
                print(f"  {rule:9s} >={fl:.0f}tk  UNINFORMATIVE (nR={len(rv)} nS={len(sv)})"); continue
            ci, mark = cell_line(rv, sv, seed)
            ref = "  <<< REFERENCE CELL" if (rule, fl) == REF else ""
            print(f"  {rule:9s} >={fl:.0f}tk  {ci['auc']:.3f}[{ci['lo']:.3f},{ci['hi']:.3f}]{mark}  "
                  f"Rmed={np.nanmedian(rv):.2f} Smed={np.nanmedian(sv):.2f}  {len(rv)}/{len(sv)}{ref}")
            if ci["clears"]:
                clears[rule].append((fl, "R>S" if ci["auc"] > 0.5 else "S>R"))

    print("\n=== PATTERN READ (rule fixed pre-output; direction unregistered) ===")
    for rule in ("ADV-ONLY", "STRICT"):
        cs = clears[rule]
        if not cs:
            print(f"  {rule:9s}: no clears -> robust-null")
        else:
            dirs = set(d for _, d in cs)
            if len(cs) >= 2 and len(dirs) == 1:
                print(f"  {rule:9s}: clears {cs} -> LEAD (observed dir {dirs.pop()}; direction-unregistered provenance; Feb list)")
            else:
                print(f"  {rule:9s}: clears {cs} -> lead-weak (logged, Feb list, found-by-sweep provenance)")

    # ---- reference cell: ALL(B) line, extras, redundancy ----
    rule, fl = REF
    print(f"\n=== REFERENCE CELL ({rule}, floor {fl:.0f}tk) ===")
    vA = g.apply(lambda r: impulse_frac(r, rule, fl), axis=1)
    rv = vA[g.grp == "reach"].dropna().values; sv = vA[g.grp == "stall"].dropna().values
    ci, mark = cell_line(rv, sv, seed)
    print(f"  ALL(B) descriptive: {ci['auc']:.3f}[{ci['lo']:.3f},{ci['hi']:.3f}]{mark} ({len(rv)}/{len(sv)})")
    sm = surv[surv.total_fav >= fl]
    for arm in ("reach", "stall"):
        h = sm[sm.grp == arm]
        print(f"  {arm:5s} extras: max_run med {np.nanmedian(h.adv_max):.1f}tk | n_runs med {np.nanmedian(h.adv_n):.0f} | total_fav med {np.nanmedian(h.total_fav):.1f}tk")
    vS = surv.apply(lambda r: impulse_frac(r, rule, fl), axis=1)
    sv2 = surv.copy(); sv2["impulse_frac"] = vS
    F2 = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, TAU, r.side) for _, r in sv2.iterrows()], index=sv2.index)
    sv2["fav_net_vel"] = F2["fav_net_vel"].values
    vr = []
    for _, r in sv2.iterrows():
        fwd = pathlen_tk(sec, mid, r.entry, pd.Timestamp(r.entry) + S(TAU))
        pre = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(PRE_W), r.entry)
        vr.append((fwd / TAU) / (pre / PRE_W) if (fwd is not None and np.isfinite(fwd) and pre and pre > 0) else np.nan)
    sv2["velocity_ratio"] = np.array(vr, float)

    def verdict(lo, hi):
        if -0.4 < lo and hi < 0.4:
            return "NEW AXIS (CI inside +/-0.4)"
        if hi < -0.6 or lo > 0.6:
            return "REDUNDANT (CI beyond |0.6|)"
        return "INDETERMINATE (logged as such)"

    for other in ("fav_net_vel", "velocity_ratio"):
        rho, lo, hi, n = spearman_boot_ci(sv2["impulse_frac"].values, sv2[other].values, seed=seed)
        print(f"  rho(impulse_frac, {other}) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n}\n    -> {verdict(lo, hi)}")

    print("\nREAD: 6 cells, one registry row (T-DF08) — count them as 6 looks in the Deflated-Sharpe N. "
          "Prediction on record: STRICT collapses on sparse seconds. Clears in either direction = leads "
          "with observed direction + direction-unregistered provenance. Floors condition on progress; "
          "surviving nR/nS printed per cell.")


def selftest(config, wrb):
    print("=== SELF-TEST: constructed concentration profiles ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 130)).astype(np.int64)
    entry = base + S(60); exit_ = base + S(125)
    pre = np.full(60, 5000.0)
    # one-burst: +8tk in 4s at t=10, flat elsewhere
    ob = np.full(70, 5000.0); ob[10:14] = 5000 + np.array([.5, 1.0, 1.5, 2.0]); ob[14:] = 5002.0
    r1 = runs_stats(sec, np.concatenate([pre, ob])[:130], entry, exit_, "long")
    f1 = impulse_frac(r1, "ADV-ONLY", 4.0)
    print(f"  one-burst: total_fav={r1['total_fav']:.0f}tk adv_max={r1['adv_max']:.0f} frac={f1:.2f} (exp 1.00)")
    assert abs(f1 - 1.0) < 1e-9
    # grind: +1tk every 8s, 7 bursts separated by ADVERSE dips (so both rules see 7 runs)
    gr = np.full(70, 5000.0); lvl = 5000.0
    for k in range(7):
        lvl += 0.25; gr[8 * k + 2: 8 * k + 6] = lvl; gr[8 * k + 6] = lvl - 0.25; gr[8 * k + 7:] = lvl
    r2 = runs_stats(sec, np.concatenate([pre, gr])[:130], entry, exit_, "long")
    f2a = impulse_frac(r2, "ADV-ONLY", 4.0)
    print(f"  grind    : total_fav={r2['total_fav']:.0f}tk adv_max={r2['adv_max']:.0f} n={r2['adv_n']:.0f} frac={f2a:.2f} (exp low, ~1/7 of total)")
    assert f2a < 0.35 and r2["adv_n"] >= 6
    # pause distinguishes rules: +4tk, 5s flat, +4tk, then one adverse tick
    pz = np.full(70, 5000.0); pz[5:9] = 5000 + np.array([.25, .5, .75, 1.0]); pz[9:14] = 5001.0
    pz[14:18] = 5001 + np.array([.25, .5, .75, 1.0]); pz[18] = 5001.75; pz[19:] = 5001.75
    r3 = runs_stats(sec, np.concatenate([pre, pz])[:130], entry, exit_, "long")
    fa = impulse_frac(r3, "ADV-ONLY", 4.0); fs = impulse_frac(r3, "STRICT", 4.0)
    print(f"  pause    : ADV-ONLY frac={fa:.2f} (pause continues -> ~1.0) | STRICT frac={fs:.2f} (pause breaks -> ~0.5)")
    assert fa > 0.9 and 0.4 < fs < 0.6
    # floor: total_fav < floor -> NaN
    tiny = np.full(70, 5000.0); tiny[10] = 5000.25
    r4 = runs_stats(sec, np.concatenate([pre, tiny])[:130], entry, exit_, "long")
    assert np.isnan(impulse_frac(r4, "ADV-ONLY", 4.0)) and np.isfinite(impulse_frac(r4, "ADV-ONLY", 0.5))
    print("  floor: total_fav 1tk -> NaN at >=4tk, finite at >=0.5tk OK")
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
