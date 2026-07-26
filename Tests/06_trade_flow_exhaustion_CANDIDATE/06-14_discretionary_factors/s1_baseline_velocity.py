#!/usr/bin/env python3
"""
s1_baseline_velocity.py — F1/S1: baseline-relative velocity (session-scale normalizers)
=========================================================================================
A controlled experiment on velocity_ratio (VR, T-SR19) more than a new-candidate hunt. VR's sweep
(T-SR22) showed the signal lives ENTIRELY in its normalization (raw forward velocity wrong-way
0.42-0.49). S1 keeps VR's NUMERATOR (per-second path length, unsigned, entry-forward) and swaps the
denominator from the 60s pre-entry pace to SESSION-SCALE baselines: "fast for this market today"
(ATR: Wilder 1978; realized path over a long pre-window).

PRE-REGISTERED (locked with user):
  Columns (numerator identical: pathlen[entry, min(entry+tau, exit)] / window_s, tk/s; B-design, >=5s):
    s1_atr20    = fwd_vel / (ATR(20,1m,pre-entry)/60)     <- PRIMARY (backlog definition)
    s1_atr5     = fwd_vel / (ATR(5,1m,pre-entry)/60)      <- user-added; near-duplicate of atr20 expected
    s1_longpath = fwd_vel / (pathlen[entry-30min, entry]/1800)  <- same primitive as VR, timescale-only swap
  Windows: tau=60 PRIMARY, 30 secondary. NO longer horizons (S3's cell-sprawl lesson).
  Direction: reach > stall (AUC>0.5). PREDICTION ON RECORD: null-to-wrong-way expected — a session-scale
  denominator is ~constant within a day, so S1 ~ raw forward velocity with cross-day vol removed, and
  raw was wrong-way. S1-null localizes VR's signal to "change vs own IMMEDIATE pace" (useful);
  S1-clear = movement-vs-day matters independently (new).
  Frames: survivor (hold>=tau) DECISIVE; ALL(B) descriptive; exits-within-tau printed.
  REDUNDANCY (locked): rho vs velocity_ratio CENTRAL — shared numerator makes correlation PARTLY
  MECHANICAL, flagged. CI inside (-0.4,0.4) new axis / beyond |0.6| redundant -> no candidate /
  else indeterminate. Secondary rho vs fav_net_vel. Survivors@60.

REUSES: build_arms (forward_battery) · S, TICK, read_per_second (trade_flow_exhaustion) · rank_auc,
two_sample_boot_ci (range_expansion) · pathlen_tk (velocity_acceleration) · s2_feats (s2_directional_
velocity) · spearman_boot_ci (fav_net_vel_confirm) · load_atr_ticks(lookback) (s3b_atr5_variant).
RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
      06-14_discretionary_factors/s1_baseline_velocity.py --config config.toml --wrb wrb_1m.parquet
Registry: T-DF05 · family=speed · code_ref=06-14_discretionary_factors/s1_baseline_velocity.py
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from velocity_acceleration import pathlen_tk
from s2_directional_velocity import s2_feats, spearman, PRE_W
from fav_net_vel_confirm import spearman_boot_ci
from s3b_atr5_variant import load_atr_ticks

TAUS = [60, 30]
MIN_WIN = 5
LONG_PRE_S = 1800          # 30-minute pre-entry path baseline (windowed parquet carries 60 min)
N_MIN = 8
COLS = ["s1_atr20", "s1_atr5", "s1_longpath"]


def fwd_vel_tks(sec, mid, entry, exit_, tau):
    """B-design forward velocity: pathlen over [entry, min(entry+tau, exit)] / window_s, in tk/s."""
    t_end = min(pd.Timestamp(entry) + S(tau), pd.Timestamp(exit_))
    win = (t_end - pd.Timestamp(entry)).total_seconds()
    if win < MIN_WIN:
        return np.nan
    pl = pathlen_tk(sec, mid, entry, t_end)
    return pl / win if (pl is not None and np.isfinite(pl)) else np.nan


def s1_cols(sec, mid, r, tau):
    fv = fwd_vel_tks(sec, mid, r.entry, r.exit, tau)
    out = dict.fromkeys(COLS, np.nan)
    if not np.isfinite(fv):
        return out
    if np.isfinite(r.atr20_tk) and r.atr20_tk > 0:
        out["s1_atr20"] = fv / (r.atr20_tk / 60.0)
    if np.isfinite(r.atr5_tk) and r.atr5_tk > 0:
        out["s1_atr5"] = fv / (r.atr5_tk / 60.0)
    lp = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(LONG_PRE_S), r.entry)
    if lp is not None and np.isfinite(lp) and lp > 0:
        out["s1_longpath"] = fv / (lp / LONG_PRE_S)
    return out


def auc_line(name, rv, sv, seed, indent="  ", prim=""):
    ci = two_sample_boot_ci(rv, sv, seed=seed)
    flag = "** CLEARS (reach>stall, pre-reg dir)" if ci["clears"] and ci["auc"] > 0.5 else (
        "!! clears WRONG-WAY (predicted possibility)" if ci["clears"] else "-")
    print(f"{indent}{name:12s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"Rmed={np.nanmedian(rv):.2f} Smed={np.nanmedian(sv):.2f} "
          f"(nR={np.isfinite(rv).sum()} nS={np.isfinite(sv).sum()}) {flag}{prim}")


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    a20 = load_atr_ticks(config, g.entry.tolist(), 20)
    a5 = load_atr_ticks(config, g.entry.tolist(), 5)
    g["atr20_tk"] = [a20[e] for e in g.entry]; g["atr5_tk"] = [a5[e] for e in g.entry]
    print(f"[ATR20 med {np.nanmedian(g.atr20_tk):.1f}tk | ATR5 med {np.nanmedian(g.atr5_tk):.1f}tk | "
          f"rho(atr20,atr5) across entries: {spearman(g.atr20_tk.values, g.atr5_tk.values):+.2f}]")
    t_min = g.entry.min() - S(LONG_PRE_S + 10); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    surv60_frame = None
    for tau in TAUS:
        F = pd.DataFrame([s1_cols(sec, mid, r, tau) for _, r in g.iterrows()], index=g.index)
        sub = g.join(F)
        surv = sub[sub.hold >= tau]
        tag = "  <<< PRIMARY tau" if tau == 60 else ""
        print(f"\n========== tau={tau}s  ALL {len(sub[sub.grp=='reach'])}R/{len(sub[sub.grp=='stall'])}S | "
              f"SURV {len(surv[surv.grp=='reach'])}R/{len(surv[surv.grp=='stall'])}S "
              f"(exits<tau R{int((sub.grp.eq('reach') & (sub.hold<tau)).sum())}/S{int((sub.grp.eq('stall') & (sub.hold<tau)).sum())}) =========={tag}")
        print("  [ALL(B) descriptive]")
        for c in COLS:
            auc_line(c, sub[sub.grp == "reach"][c].values, sub[sub.grp == "stall"][c].values, seed, indent="    ")
        print("  [SURV — DECISIVE]")
        for c in COLS:
            prim = "  <<< PRIMARY CELL" if (tau == 60 and c == "s1_atr20") else ""
            auc_line(c, surv[surv.grp == "reach"][c].values, surv[surv.grp == "stall"][c].values, seed,
                     indent="    ", prim=prim)
        if tau == 60:
            surv60_frame = surv.copy()

    # ---- redundancy on survivors@60 (locked) ----
    print("\n=== REDUNDANCY (locked): survivors@60 ===")
    sv = surv60_frame
    vr = []
    for _, r in sv.iterrows():
        fwd = pathlen_tk(sec, mid, r.entry, pd.Timestamp(r.entry) + S(60))
        pre = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(PRE_W), r.entry)
        vr.append((fwd / 60) / (pre / PRE_W) if (fwd is not None and np.isfinite(fwd) and pre and pre > 0) else np.nan)
    sv["velocity_ratio"] = np.array(vr, float)
    F2 = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, 60, r.side) for _, r in sv.iterrows()], index=sv.index)
    sv["fav_net_vel"] = F2["fav_net_vel"].values

    def verdict(lo, hi):
        if -0.4 < lo and hi < 0.4:
            return "NEW AXIS (CI inside +/-0.4)"
        if hi < -0.6 or lo > 0.6:
            return "REDUNDANT (CI beyond |0.6|) -> NO candidate status"
        return "INDETERMINATE (logged as such)"

    for c in COLS:
        rho, lo, hi, n = spearman_boot_ci(sv[c].values, sv["velocity_ratio"].values, seed=seed)
        print(f"  rho({c}, velocity_ratio) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n} "
              f"[shared numerator -> partly MECHANICAL]\n    -> {verdict(lo, hi)}")
    rho, lo, hi, n = spearman_boot_ci(sv["s1_atr20"].values, sv["fav_net_vel"].values, seed=seed)
    print(f"  rho(s1_atr20, fav_net_vel) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n} (secondary)")

    print("\nREAD: PRIMARY CELL = s1_atr20 SURV@60. Registered dir reach>stall; prediction on record was "
          "null-to-wrong-way (session denominator ~ raw velocity with cross-day vol removed). NULL here "
          "localizes VR's signal to change-vs-IMMEDIATE-pace (60s pre-entry is load-bearing) — a "
          "robustness statement about VR, not a failure. CLEAR here = movement-vs-day matters "
          "independently. Redundancy verdicts mechanical-discounted per the shared-numerator flag.")


def selftest(config, wrb):
    print("=== SELF-TEST ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    n_pre = LONG_PRE_S + 10
    sec = (base.value // 1_000_000_000 + np.arange(0, n_pre + 70)).astype(np.int64)
    # pre 30min: alternate +-0.25 every sec -> pathlen rate = 1 tk/s; forward 60s: +0.5 tk/s ramp
    pre = 5000 + 0.25 * (np.arange(n_pre) % 2)
    fwd = pre[-1] + np.cumsum(np.full(70, 0.125))
    mid = np.concatenate([pre, fwd])
    entry = base + S(n_pre); exit_ = base + S(n_pre + 65)
    fv = fwd_vel_tks(sec, mid, entry, exit_, 60)
    print(f"  fwd_vel = {fv:.3f} tk/s (expect ~0.5)"); assert abs(fv - 0.5) < 0.05
    lp = pathlen_tk(sec, mid, entry - S(LONG_PRE_S), entry) / LONG_PRE_S
    print(f"  longpath rate = {lp:.3f} tk/s (expect ~1.0)"); assert abs(lp - 1.0) < 0.05
    r = pd.Series(dict(entry=entry, exit=exit_, atr20_tk=12.0, atr5_tk=6.0))
    c = s1_cols(sec, mid, r, 60)
    print(f"  s1_atr20 = {c['s1_atr20']:.2f} (expect ~0.5/(12/60)=2.5) | s1_atr5 = {c['s1_atr5']:.2f} "
          f"(expect ~5.0) | s1_longpath = {c['s1_longpath']:.2f} (expect ~0.5)")
    assert abs(c["s1_atr20"] - 2.5) < 0.25 and abs(c["s1_atr5"] - 5.0) < 0.5 and abs(c["s1_longpath"] - 0.5) < 0.05
    # capped window: exit at +20s -> velocity still ~0.5
    fv2 = fwd_vel_tks(sec, mid, entry, entry + S(20), 60)
    print(f"  capped@20s fwd_vel = {fv2:.3f} (B-design)"); assert abs(fv2 - 0.5) < 0.08
    assert np.isnan(fwd_vel_tks(sec, mid, entry, entry + S(3), 60)), "floor"
    print("  <5s floor -> NaN OK")
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
