#!/usr/bin/env python3
"""
s6b_burst_timing.py — F1/S6b: WHEN does the biggest favorable burst occur? (new feature, not a knob)
=====================================================================================================
Follow-on chosen by user after S6's robust-null. S6 showed the arms' favorable-movement TEXTURE is
identical (max_run 7.0 vs 7.0 tk, n_runs 10 vs 10, total_fav 24.5 vs 24.8) — concentration can't
separate. This probes TIMING: mechanism (h1 null everywhere, h2 clears) predicts reaches' biggest
burst comes LATER.

EXPECTATION ON RECORD: "late burst" overlaps h2_net_vel / fav_net_vel near-mechanically -> HIGH rho,
shadow likely. A clear + low rho is the surprise outcome. Logged either way (exploration framing).

PRE-REGISTERED GRID (tunables tested, not decided): timing ANCHOR x3 {START, CENTER, END of the max
run, seconds from entry} X run-rule x2 {ADV-ONLY, STRICT}. Floor fixed at total_fav>=4tk (S6 showed
the floor axis is flat; it only gates validity here). Window fixed 60s, survivors (hold>=60) DECISIVE.
Direction registered: reach LATER -> AUC>0.5. Pattern rule per run-rule: >=2 same-direction clears ->
lead (Feb list); single -> lead-weak; none -> robust-null. 6 cells = 6 looks, one registry row.
REFERENCE CELL: ADV-ONLY / CENTER — redundancy rho vs h2_net_vel (direct shadow suspect) and
fav_net_vel, locked (-0.4,0.4)/|0.6| convention.

RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
      06-14_discretionary_factors/s6b_burst_timing.py --config config.toml --wrb wrb_1m.parquet
Registry: T-DF09 · family=speed · grid · code_ref=06-14_discretionary_factors/s6b_burst_timing.py
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from velocity_acceleration import pathlen_tk
from s2_directional_velocity import s2_feats, PRE_W
from s4_speed_profile import profile_feats
from fav_net_vel_confirm import spearman_boot_ci

TAU = 60
MIN_WIN = 5
FLOOR = 4.0
N_MIN = 8
ANCHORS = ["START", "CENTER", "END"]
RULES = ["ADV-ONLY", "STRICT"]
REF = ("ADV-ONLY", "CENTER")


def max_run_times(sec, mid, entry, exit_, side):
    """Per rule: (start_s, end_s) of the MAX favorable run + total_fav. NaN if window <MIN_WIN s."""
    t0 = np.int64(pd.Timestamp(entry).value // 1_000_000_000)
    t_end = min(pd.Timestamp(entry) + S(TAU), pd.Timestamp(exit_))
    t1 = np.int64(pd.Timestamp(t_end).value // 1_000_000_000)
    out = {"total_fav": np.nan}
    for rl in RULES:
        out[rl] = (np.nan, np.nan)
    if t1 - t0 < MIN_WIN:
        return out
    a = np.searchsorted(sec, t0, "left"); b = np.searchsorted(sec, t1, "right")
    if b - a < 3:
        return out
    o = (mid[a:b] if side == "long" else -mid[a:b]) / TICK
    el = (sec[a:b] - t0).astype(float)
    d = np.diff(o)
    out["total_fav"] = float(d[d > 0].sum())
    for rl in RULES:
        best = (0.0, np.nan, np.nan)          # (value, start_s, end_s)
        cur = 0.0; cs = np.nan; in_run = False
        for i, x in enumerate(d):
            adverse = x < 0
            breaks = adverse if rl == "ADV-ONLY" else (x <= 0)
            if breaks:
                if in_run and cur > best[0]:
                    best = (cur, cs, el[i])
                cur = 0.0; in_run = False; cs = np.nan
            else:
                if x > 0 and not in_run:
                    in_run = True; cs = el[i]
                cur += max(x, 0.0)
        if in_run and cur > best[0]:
            best = (cur, cs, el[-1])
        out[rl] = (best[1], best[2]) if best[0] > 0 else (np.nan, np.nan)
    return out


def anchor_time(times, anchor):
    s, e = times
    if not (np.isfinite(s) and np.isfinite(e)):
        return np.nan
    return {"START": s, "CENTER": (s + e) / 2.0, "END": e}[anchor]


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    surv = g[g.hold >= TAU].copy()
    print(f"[arms] reach {len(g[g.grp=='reach'])} / stall {len(g[g.grp=='stall'])} | "
          f"SURV {len(surv[surv.grp=='reach'])}R/{len(surv[surv.grp=='stall'])}S — decisive frame")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    T = [max_run_times(sec, mid, r.entry, r.exit, r.side) for _, r in surv.iterrows()]
    surv["total_fav"] = [t["total_fav"] for t in T]
    for rl in RULES:
        surv[rl] = [t[rl] for t in T]
    ok = surv[surv.total_fav >= FLOOR]
    print(f"[floor total_fav>={FLOOR:.0f}tk] surviving: "
          f"{len(ok[ok.grp=='reach'])}R/{len(ok[ok.grp=='stall'])}S")

    clears = {rl: [] for rl in RULES}
    print(f"\n  rule      anchor  AUC (survivors, floor-ok)      medians R/S (s)")
    for rl in RULES:
        for an in ANCHORS:
            v = ok[rl].apply(lambda t: anchor_time(t, an))
            rv = v[ok.grp == "reach"].dropna().values; sv = v[ok.grp == "stall"].dropna().values
            if len(rv) < N_MIN or len(sv) < N_MIN:
                print(f"  {rl:9s} {an:6s}  UNINFORMATIVE (nR={len(rv)} nS={len(sv)})"); continue
            ci = two_sample_boot_ci(rv, sv, seed=seed)
            if ci["clears"]:
                direction = "R later" if ci["auc"] > 0.5 else "S later"
                mark = f"** ({direction})"
                clears[rl].append((an, direction))
            else:
                mark = "  "
            ref = "  <<< REFERENCE CELL" if (rl, an) == REF else ""
            print(f"  {rl:9s} {an:6s}  {ci['auc']:.3f}[{ci['lo']:.3f},{ci['hi']:.3f}]{mark}  "
                  f"{np.nanmedian(rv):.0f}/{np.nanmedian(sv):.0f}{ref}")

    print("\n=== PATTERN READ (rule fixed pre-output; registered dir = reach LATER) ===")
    for rl in RULES:
        cs = clears[rl]
        if not cs:
            print(f"  {rl:9s}: no clears -> robust-null")
        else:
            dirs = set(d for _, d in cs)
            if len(cs) >= 2 and len(dirs) == 1:
                print(f"  {rl:9s}: clears {cs} -> LEAD ({dirs.pop()}; Feb list)")
            else:
                print(f"  {rl:9s}: clears {cs} -> lead-weak (logged, Feb list, found-by-sweep provenance)")

    # ---- reference cell redundancy ----
    rl, an = REF
    print(f"\n=== REFERENCE CELL ({rl}/{an}) — redundancy (shadow expectation ON RECORD) ===")
    ok2 = ok.copy()
    ok2["burst_time"] = ok2[rl].apply(lambda t: anchor_time(t, an))
    P = pd.DataFrame([profile_feats(sec, mid, r.entry, r.exit, r.side) for _, r in ok2.iterrows()], index=ok2.index)
    ok2["h2_net_vel"] = P["h2_net_vel"].values
    F2 = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, TAU, r.side) for _, r in ok2.iterrows()], index=ok2.index)
    ok2["fav_net_vel"] = F2["fav_net_vel"].values

    def verdict(lo, hi):
        if -0.4 < lo and hi < 0.4:
            return "NEW AXIS (CI inside +/-0.4)"
        if hi < -0.6 or lo > 0.6:
            return "REDUNDANT (CI beyond |0.6|)"
        return "INDETERMINATE (logged as such)"

    for other in ("h2_net_vel", "fav_net_vel"):
        rho, lo, hi, n = spearman_boot_ci(ok2["burst_time"].values, ok2[other].values, seed=seed)
        print(f"  rho(burst_time, {other}) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n}\n    -> {verdict(lo, hi)}")

    print("\nREAD: 6 cells = 6 looks (T-DF09). Registered dir: reach's max burst LATER (from h1-null/"
          "h2-clear). Shadow expectation on record: high rho vs h2/fnv likely -> a clear would then be "
          "the known axis re-expressed in time units; clear + LOW rho = genuinely new timing axis.")


def selftest(config, wrb):
    print("=== SELF-TEST: constructed early vs late bursts ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 130)).astype(np.int64)
    entry = base + S(60); exit_ = base + S(125)
    pre = np.full(60, 5000.0)
    # early burst at 5-8s (+8tk) then flat with one adverse at 30s
    eb = np.full(70, 5000.0); eb[5:9] = 5000 + np.array([.5, 1., 1.5, 2.]); eb[9:30] = 5002.0
    eb[30] = 5001.75; eb[31:] = 5001.75
    t = max_run_times(sec, np.concatenate([pre, eb])[:130], entry, exit_, "long")
    ct = anchor_time(t["ADV-ONLY"], "CENTER")
    print(f"  early burst: ADV-ONLY run [{t['ADV-ONLY'][0]:.0f},{t['ADV-ONLY'][1]:.0f}]s center={ct:.1f} (expect ~5-30 span, center ~17)")
    assert t["ADV-ONLY"][0] <= 6 and 10 <= ct <= 20
    st = anchor_time(t["STRICT"], "CENTER")
    print(f"  early burst: STRICT center={st:.1f} (pause breaks -> tight around 5-9s)")
    assert 4 <= st <= 10
    # late burst at 45-48s
    lb = np.full(70, 5000.0); lb[10] = 4999.75; lb[11:45] = 4999.75
    lb[45:49] = 4999.75 + np.array([.5, 1., 1.5, 2.]); lb[49:] = 5001.75
    t2 = max_run_times(sec, np.concatenate([pre, lb])[:130], entry, exit_, "long")
    ct2 = anchor_time(t2["STRICT"], "CENTER")
    print(f"  late burst : STRICT center={ct2:.1f} (expect ~45-48)")
    assert 43 <= ct2 <= 50
    assert anchor_time(t2["STRICT"], "START") < ct2 < anchor_time(t2["STRICT"], "END")
    # no favorable movement -> NaN
    t3 = max_run_times(sec, np.concatenate([pre, np.full(70, 5000.0)])[:130], entry, exit_, "long")
    assert np.isnan(anchor_time(t3["ADV-ONLY"], "CENTER"))
    print("  flat trade -> NaN OK")
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
