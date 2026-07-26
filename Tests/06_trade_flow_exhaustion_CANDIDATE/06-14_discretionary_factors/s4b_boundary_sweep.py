#!/usr/bin/env python3
"""
s4b_boundary_sweep.py — F1/S4 sensitivity sweep: where is the follow-through boundary?
========================================================================================
POST-HOC-MOTIVATED (after T-DF06's fade null), logged as such. Question: was the 30/30 split a
mis-parameterization — does a fade/follow-through effect exist at a different boundary?

PRE-REGISTERED INTERPRETATION RULE (fixed before output):
  Sweep the H1/H2 boundary b over {15,20,25,30,35,40,45}s inside the FIXED 60s window, survivors
  (hold>=60) only, 45/24. Per boundary: h1_net_vel, h2_net_vel, fade_delta AUCs + CI (seed 0, 10000).
  Pattern read per feature:
    REGION  = >=3 ADJACENT boundaries clearing in the registered direction -> label `lead` (the
              original null was plausibly mis-parameterized); goes to Feb holdout list.
    SPIKE   = 1-2 clearing cells, non-adjacent or isolated -> label `lead-weak`; still LOGGED and
              goes to the Feb list (exploration = generate candidates; holdout adjudicates), but
              carried with the found-by-sweep flag.
    ALL-NULL -> `robust-null` — a stronger null than T-DF06 alone (parameter-robust).
  Registered directions: h2_net_vel reach>stall (AUC>0.5); fade_delta reach>stall (AUC>0.5);
  h1_net_vel descriptive (closes the T-DF06 gap: is the information concentrated in H2? measured,
  not inferred — expect ~null per S3).
  NOT swept: window length (fixed 60s), feature definitions, frame. One knob, on purpose.
  NOTE the cells are heavily OVERLAPPING (same 69 trades, nested windows) — adjacent-cell agreement
  is partly mechanical, which is why the region rule demands 3, not 2.

RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
      06-14_discretionary_factors/s4b_boundary_sweep.py --config config.toml --wrb wrb_1m.parquet
Registry: T-DF07 · family=speed · sensitivity-sweep · code_ref=06-14_discretionary_factors/s4b_boundary_sweep.py
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from s2_directional_velocity import PRE_W

TAU = 60
BOUNDARIES = [15, 20, 25, 30, 35, 40, 45]
MIN_LEG = 5


def leg_feats(sec, mid, entry, exit_, side, b):
    """h1 (0..b), h2 (b..60), fade = h2-h1, in tk/s; legs need >=MIN_LEG s inside the capped window."""
    t0 = np.int64(pd.Timestamp(entry).value // 1_000_000_000)
    t_end = min(pd.Timestamp(entry) + S(TAU), pd.Timestamp(exit_))
    t1 = np.int64(pd.Timestamp(t_end).value // 1_000_000_000)
    out = dict(h1=np.nan, h2=np.nan, fade=np.nan)
    if t1 - t0 < b + MIN_LEG:
        return out
    a = np.searchsorted(sec, t0, "left"); e = np.searchsorted(sec, t1, "right")
    if e - a < 3:
        return out
    o = (mid[a:e] if side == "long" else -mid[a:e]) / TICK
    el = (sec[a:e] - t0).astype(float)
    disp = o - o[0]
    i_b = np.searchsorted(el, b, "right") - 1
    if i_b < 1:
        return out
    d1 = float(disp[i_b]); t1s = max(float(el[i_b]), 1.0)
    d2 = float(disp[-1]) - d1; t2s = max(float(el[-1] - el[i_b]), 1.0)
    out["h1"] = d1 / t1s; out["h2"] = d2 / t2s; out["fade"] = out["h2"] - out["h1"]
    return out


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    surv = g[g.hold >= TAU].copy()
    print(f"[arms] reach {len(g[g.grp=='reach'])} / stall {len(g[g.grp=='stall'])} | "
          f"SURV(hold>=60) {len(surv[surv.grp=='reach'])}R/{len(surv[surv.grp=='stall'])}S — sweep frame")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    clears = {"h1": [], "h2": [], "fade": []}
    print(f"\n  b(s)   h1_net_vel                 h2_net_vel                 fade_delta")
    for b in BOUNDARIES:
        F = pd.DataFrame([leg_feats(sec, mid, r.entry, r.exit, r.side, b) for _, r in surv.iterrows()],
                         index=surv.index)
        line = f"  {b:>3}   "
        for c in ("h1", "h2", "fade"):
            rv = F.loc[surv.grp == "reach", c].values; sv = F.loc[surv.grp == "stall", c].values
            ci = two_sample_boot_ci(rv, sv, seed=seed)
            mark = "**" if (ci["clears"] and ci["auc"] > 0.5) else ("!!" if ci["clears"] else "  ")
            if ci["clears"] and ci["auc"] > 0.5:
                clears[c].append(b)
            line += f"{ci['auc']:.3f}[{ci['lo']:.3f},{ci['hi']:.3f}]{mark}  "
        print(line)

    def pattern(bs):
        if not bs:
            return "ALL-NULL -> robust-null"
        runs, cur = [], [bs[0]]
        for x in bs[1:]:
            if x - cur[-1] == 5:
                cur.append(x)
            else:
                runs.append(cur); cur = [x]
        runs.append(cur)
        longest = max(len(r) for r in runs)
        if longest >= 3:
            return f"REGION {runs} -> lead (Feb holdout list)"
        return f"SPIKE {bs} -> lead-weak (logged, Feb list, found-by-sweep flag)"

    print("\n=== PATTERN READ (rule fixed pre-output) ===")
    for c in ("h1", "h2", "fade"):
        print(f"  {c:5s}: clears at {clears[c] or 'none'}  ->  {pattern(clears[c])}")
    print("\nNOTE: cells overlap heavily (same 69 trades, nested windows) — adjacent agreement is partly "
          "mechanical; that is why REGION demands >=3. h1 read closes the T-DF06 gap (H2-concentration: "
          "measured). Registry: T-DF07, sensitivity-sweep, post-hoc-motivated.")


def selftest(config, wrb):
    print("=== SELF-TEST: boundary detection on constructed profiles ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 130)).astype(np.int64)
    entry = base + S(60); exit_ = base + S(125)
    pre = np.full(60, 5000.0)
    # pop-until-40s-then-flat: +0.4tk/s to 40s, flat after
    pf = np.concatenate([5000 + np.cumsum(np.full(40, 0.10)), np.full(30, 5004.0)])
    mid = np.concatenate([pre, pf])[:130]
    f30 = leg_feats(sec, mid, entry, exit_, "long", 30)
    f40 = leg_feats(sec, mid, entry, exit_, "long", 40)
    print(f"  pop-to-40: b=30 fade={f30['fade']:+.2f} | b=40 fade={f40['fade']:+.2f} (40 should be more negative)")
    assert f40["fade"] < f30["fade"] < 0
    # sustained: fade ~0 at every boundary
    sus = 5000 + np.cumsum(np.full(70, 0.05))
    mid2 = np.concatenate([pre, sus])[:130]
    for b in (15, 30, 45):
        fb = leg_feats(sec, mid2, entry, exit_, "long", b)
        assert abs(fb["fade"]) < 0.06, (b, fb)
    print("  sustained: fade ~0 at b=15/30/45 OK")
    # leg floor: b=45 with exit at +48 -> h2 leg 3s < 5 -> NaN
    f = leg_feats(sec, mid2, entry, entry + S(48), "long", 45)
    assert np.isnan(f["h2"]); print("  h2 leg <5s -> NaN OK")
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
