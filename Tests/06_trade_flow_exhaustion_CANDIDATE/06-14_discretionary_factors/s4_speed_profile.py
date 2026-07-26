#!/usr/bin/env python3
"""
s4_speed_profile.py — F1/S4: directional speed-profile (sustained vs decayed)
==============================================================================
DUPLICATE GUARD: the UNSIGNED two-half ratio was already tested NULL (`acceleration`,
velocity_acceleration.py, T-SR19 script). S4 is the DIRECTIONAL profile — the pointed test of
pop-and-fade (S2 decomp + S3 null triangulated: stalls initiate like reaches but don't retain).
Standing caveat ON RECORD: a positive here is corroboration-by-reconstruction on the same October
trades, not independent evidence.

PRE-REGISTERED (locked with user):
  Window: [entry, entry+60s] split 30/30. Survivors (hold>=60) DECISIVE; ALL(B) frame includes trades
  with >=5s of H2 (hold>=35s) — S4 is survivor-primary BY CONSTRUCTION (an early cut has no 2nd half).
  Features (raw tk/s, DIFFERENCES not ratios — h1~0 is common, ratios blow up; no normalization
  columns per S1's null):
    h2_net_vel (PRIMARY)   = oriented net displacement over [entry+30, entry+60] / 30. The
                             follow-through leg (continuation-validates-initiation logic; O'Neil's
                             follow-through day is precedent for the LOGIC, daily-timescale — flagged,
                             not a citation for 30s halves).
    fade_delta (secondary) = h2_net_vel - h1_net_vel. Pop-and-fade direct: stall negative, reach >= 0.
  Direction: reach > stall on both. AUC + two-sample bootstrap CI (seed 0, 10000).
  CONDITIONAL (pre-registered extra, the mechanism isolator): fade_delta AUC on the subset with
  h1_net_vel > 0 (both arms made 1st-half progress; does the 2nd half distinguish?). >=8/arm floor.
  REDUNDANCY (locked): rho vs fav_net_vel CENTRAL — HIGH BY CONSTRUCTION expected (h2 is a component
  of fav_net_vel's 60s endpoint). CI inside (-0.4,0.4) new axis / beyond |0.6| REDUNDANT -> no third
  candidate; disposition then = "retention signal concentrated in the follow-through leg" (a
  refinement of candidate #2, tells a rule WHEN to look). Else indeterminate. Secondary rho vs VR.

RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
      06-14_discretionary_factors/s4_speed_profile.py --config config.toml --wrb wrb_1m.parquet
Registry: T-DF06 · family=speed · code_ref=06-14_discretionary_factors/s4_speed_profile.py
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
HALF = 30
MIN_H2 = 5
N_MIN = 8


def profile_feats(sec, mid, entry, exit_, side):
    """h1_net_vel, h2_net_vel, fade_delta (tk/s). H2 needs >=MIN_H2 s inside the capped window."""
    t0 = np.int64(pd.Timestamp(entry).value // 1_000_000_000)
    t_end = min(pd.Timestamp(entry) + S(TAU), pd.Timestamp(exit_))
    t1 = np.int64(pd.Timestamp(t_end).value // 1_000_000_000)
    out = dict(h1_net_vel=np.nan, h2_net_vel=np.nan, fade_delta=np.nan)
    if t1 - t0 < HALF + MIN_H2:
        return out
    a = np.searchsorted(sec, t0, "left"); b = np.searchsorted(sec, t1, "right")
    if b - a < 3:
        return out
    o = (mid[a:b] if side == "long" else -mid[a:b]) / TICK
    el = (sec[a:b] - t0).astype(float)
    disp = o - o[0]
    i_half = np.searchsorted(el, HALF, "right") - 1
    if i_half < 1:
        return out
    d1 = float(disp[i_half]); t_h1 = max(float(el[i_half]), 1.0)
    d2 = float(disp[-1]) - d1; t_h2 = max(float(el[-1] - el[i_half]), 1.0)
    out["h1_net_vel"] = d1 / t_h1
    out["h2_net_vel"] = d2 / t_h2
    out["fade_delta"] = out["h2_net_vel"] - out["h1_net_vel"]
    return out


def auc_line(name, rv, sv, seed, indent="  ", prim=""):
    rv = np.asarray(rv, float); sv = np.asarray(sv, float)
    ci = two_sample_boot_ci(rv, sv, seed=seed)
    flag = "** CLEARS (reach>stall, pre-reg dir)" if ci["clears"] and ci["auc"] > 0.5 else (
        "!! clears WRONG-WAY" if ci["clears"] else "-")
    print(f"{indent}{name:12s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"Rmed={np.nanmedian(rv):+.3f} Smed={np.nanmedian(sv):+.3f} "
          f"(nR={np.isfinite(rv).sum()} nS={np.isfinite(sv).sum()}) {flag}{prim}")


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    F = pd.DataFrame([profile_feats(sec, mid, r.entry, r.exit, r.side) for _, r in g.iterrows()],
                     index=g.index)
    g = g.join(F)
    allb = g[g.h2_net_vel.notna()]                      # hold>=35s by construction
    surv = g[g.hold >= TAU]
    print(f"[frames] ALL(B, hold>=35s): {len(allb[allb.grp=='reach'])}R/{len(allb[allb.grp=='stall'])}S | "
          f"SURV(hold>=60): {len(surv[surv.grp=='reach'])}R/{len(surv[surv.grp=='stall'])}S")

    for fname, frame in (("ALL(B) descriptive", allb), ("SURV — DECISIVE", surv)):
        print(f"\n===== {fname} =====")
        rA = frame[frame.grp == "reach"]; sA = frame[frame.grp == "stall"]
        for c, prim in (("h2_net_vel", "  <<< PRIMARY" if "DECISIVE" in fname else ""), ("fade_delta", "")):
            auc_line(c, rA[c].values, sA[c].values, seed, prim=prim)
        # pre-registered conditional: fade among h1-positive trades (mechanism isolator)
        pos = frame[frame.h1_net_vel > 0]
        rp = pos[pos.grp == "reach"]["fade_delta"].dropna().values
        sp = pos[pos.grp == "stall"]["fade_delta"].dropna().values
        if len(rp) >= N_MIN and len(sp) >= N_MIN:
            auc_line("fade|h1>0", rp, sp, seed, indent="  ")
        else:
            print(f"  fade|h1>0    UNINFORMATIVE (nR={len(rp)} nS={len(sp)} < {N_MIN})")

    # ---- redundancy (locked) on survivors ----
    print("\n=== REDUNDANCY (locked): survivors@60 ===")
    sv = surv.copy()
    F2 = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, TAU, r.side) for _, r in sv.iterrows()], index=sv.index)
    sv["fav_net_vel"] = F2["fav_net_vel"].values
    vr = []
    for _, r in sv.iterrows():
        fwd = pathlen_tk(sec, mid, r.entry, pd.Timestamp(r.entry) + S(TAU))
        pre = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(PRE_W), r.entry)
        vr.append((fwd / TAU) / (pre / PRE_W) if (fwd is not None and np.isfinite(fwd) and pre and pre > 0) else np.nan)
    sv["velocity_ratio"] = np.array(vr, float)

    def verdict(lo, hi):
        if -0.4 < lo and hi < 0.4:
            return "NEW AXIS (CI inside +/-0.4)"
        if hi < -0.6 or lo > 0.6:
            return "REDUNDANT (CI beyond |0.6|) -> refinement of candidate #2, NOT a third candidate"
        return "INDETERMINATE (logged as such)"

    for c in ("h2_net_vel", "fade_delta"):
        rho, lo, hi, n = spearman_boot_ci(sv[c].values, sv["fav_net_vel"].values, seed=seed)
        print(f"  rho({c}, fav_net_vel) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n} "
              f"[h2 is a COMPONENT of fav_net_vel -> high expected by construction]\n    -> {verdict(lo, hi)}")
    rho, lo, hi, n = spearman_boot_ci(sv["h2_net_vel"].values, sv["velocity_ratio"].values, seed=seed)
    print(f"  rho(h2_net_vel, velocity_ratio) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n} (secondary)")

    print("\nREAD: PRIMARY = h2_net_vel SURV. fade|h1>0 is the mechanism isolator (both arms progressed in "
          "H1 — does H2 distinguish?). REDUNDANT verdict -> retention signal concentrated in the "
          "follow-through leg (WHEN to look), a refinement of fav_net_vel, no 3rd candidate. Standing "
          "caveat: positive = corroboration-by-reconstruction on the same October trades.")


def selftest(config, wrb):
    print("=== SELF-TEST: constructed profiles ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 130)).astype(np.int64)
    entry = base + S(60); exit_ = base + S(125)
    pre = np.full(60, 5000.0)
    # sustained: +0.05pt/s (0.2tk/s) for 60s
    sus = 5000.0 + np.cumsum(np.full(70, 0.05))
    f = profile_feats(sec, np.concatenate([pre, sus])[:130], entry, exit_, "long")
    print(f"  sustained: h1={f['h1_net_vel']:+.2f} h2={f['h2_net_vel']:+.2f} fade={f['fade_delta']:+.2f} (exp ~0.2/0.2/0)")
    assert abs(f["h1_net_vel"] - 0.2) < 0.03 and abs(f["fade_delta"]) < 0.05
    # pop-and-fade: +0.1pt/s (0.4tk/s) 30s then -0.05pt/s (-0.2tk/s) 30s
    pf = np.concatenate([5000 + np.cumsum(np.full(30, 0.10)), 5003 - np.cumsum(np.full(40, 0.05))])
    f2 = profile_feats(sec, np.concatenate([pre, pf])[:130], entry, exit_, "long")
    print(f"  pop-fade : h1={f2['h1_net_vel']:+.2f} h2={f2['h2_net_vel']:+.2f} fade={f2['fade_delta']:+.2f} (exp ~+0.4/-0.2/-0.6)")
    assert f2["h1_net_vel"] > 0.3 and f2["h2_net_vel"] < -0.1 and f2["fade_delta"] < -0.5
    # short mirror of pop-fade
    f3 = profile_feats(sec, np.concatenate([pre, 2 * 5000.0 - pf])[:130], entry, exit_, "short")
    print(f"  short mir: h1={f3['h1_net_vel']:+.2f} fade={f3['fade_delta']:+.2f} (mirror of pop-fade)")
    assert abs(f3["h1_net_vel"] - f2["h1_net_vel"]) < 0.02
    # capped: exit at +32s -> H2 has <5s -> NaN; exit at +40s -> H2 valid (10s)
    f4 = profile_feats(sec, np.concatenate([pre, sus])[:130], entry, entry + S(32), "long")
    assert np.isnan(f4["h2_net_vel"]), "H2 <5s must be NaN"
    f5 = profile_feats(sec, np.concatenate([pre, sus])[:130], entry, entry + S(40), "long")
    print(f"  capped@40s: h2={f5['h2_net_vel']:+.2f} over 10s (valid, B-design); @32s -> NaN OK")
    assert np.isfinite(f5["h2_net_vel"])
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
