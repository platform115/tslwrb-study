#!/usr/bin/env python3
"""
s2_directional_velocity.py — F1/S2: directional (favorable-leg) velocity, entry-forward
========================================================================================
PHASE 06-14 discretionary factors. velocity_ratio (T-SR19, AUC 0.660) is UNSIGNED path-length rate;
S2 asks whether DIRECTION carries signal: how fast did price move IN THE TRADE'S FAVOR after entry.

PRE-REGISTERED (locked with user):
  Windows: B-design (user decision) — [entry, min(entry+tau, exit)], ALL 47/29 trades included,
           window >= 5s floor. tau=60 PRIMARY, 30 secondary. CAVEAT: for early-cut trades the window
           length is the trader's own exit decision -> feature partially encodes exit timing. A
           survivor-subset (hold>=tau) line is printed alongside for A-design comparability with
           velocity_ratio (45/24).
  Features (4 columns, one pass):
    fav_peak_vel  (PRIMARY)  = max favorable displacement in window (ticks) / seconds to that peak.
                               If peak <= 0 (never favorable): 0.0 by definition.
    fav_net_vel   (secondary)= oriented net displacement at window end (ticks) / window seconds.
    *_norm                   = each divided by pre-entry per-second path rate over [entry-60s, entry]
                               (same denominator as velocity_ratio).
  Direction: reach > stall on ALL columns (faster favorable movement -> reached).
  Stats: rank AUC + two-sample bootstrap CI (seed 0, 10000). Redundancy: Spearman of each column vs
  velocity_ratio on the survivor subset (velocity_ratio only exists there).
  Prediction on record: raw forward UNSIGNED velocity was wrong-way (T-SR22); if raw S2 clears where
  unsigned didn't, direction itself is the signal (new). If only *_norm clears, we likely re-found
  velocity_ratio -> the Spearman is the probe's real output.

  CIRCULARITY GUARD (pre-registered): velocity_ratio's own spec chose UNSIGNED precisely because signed
  favorable velocity is partly circular with the reach label when target attainment falls INSIDE the
  measurement window (reaches exit at/after target; a capped window then measures the run TO the label).
  Quantified per run: exits-within-tau printed per arm (~2/47 reaches at tau=60). Therefore the
  SURVIVOR-SUBSET (hold>=tau) line is the ANTI-CIRCULARITY CONTROL, not just A-comparability:
  **S2 counts as a finding only if it clears on the survivor subset.** The all-trades B-design line is
  the descriptive view and cannot headline alone.

REUSES: build_arms (forward_battery) · read_per_second, S, TICK (trade_flow_exhaustion) ·
        rank_auc, two_sample_boot_ci (range_expansion) · pathlen_tk (velocity_acceleration).
RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/s2_directional_velocity.py \
      --config config.toml --wrb wrb_1m.parquet
  ... --selftest for synthetic checks.
Registry: T-DF01 · family=speed · code_ref=06-14_discretionary_factors/s2_directional_velocity.py
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from velocity_acceleration import pathlen_tk

TAUS = [60, 30]
MIN_WIN = 5          # seconds; rate over <5s is noise (pre-registered floor)
PRE_W = 60           # pre-entry normalization window (same as velocity_ratio)
COLS = ["fav_peak_vel", "fav_net_vel", "fav_peak_vel_norm", "fav_net_vel_norm"]


def s2_feats(sec, mid, entry, exit_, tau, side):
    """4 pre-registered S2 columns for one trade. Window [entry, min(entry+tau, exit)], >=MIN_WIN s."""
    t0 = np.int64(pd.Timestamp(entry).value // 1_000_000_000)
    t_end = min(pd.Timestamp(entry) + S(tau), pd.Timestamp(exit_))
    t1 = np.int64(pd.Timestamp(t_end).value // 1_000_000_000)
    win = t1 - t0
    out = dict.fromkeys(COLS, np.nan); out["win_s"] = float(win)
    if win < MIN_WIN:
        return out
    a = np.searchsorted(sec, t0, "left"); b = np.searchsorted(sec, t1, "right")
    if b - a < 3:
        return out
    o = (mid[a:b] if side == "long" else -mid[a:b]) / TICK
    disp = o - o[0]                                   # favorable displacement (ticks), signed
    elapsed = (sec[a:b] - t0).astype(float)
    # primary: rate to the favorable peak
    k = int(np.argmax(disp))
    peak = float(disp[k]); t_peak = max(float(elapsed[k]), 1.0)
    out["fav_peak_vel"] = (peak / t_peak) if peak > 0 else 0.0
    # secondary: net displacement rate over the (capped) window
    out["fav_net_vel"] = float(disp[-1]) / max(float(elapsed[-1]), 1.0)
    # pre-entry normalization (same denominator as velocity_ratio)
    pre = pathlen_tk(sec, mid, pd.Timestamp(entry) - S(PRE_W), pd.Timestamp(entry))
    if pre is not None and pre > 0:
        pre_rate = pre / PRE_W
        out["fav_peak_vel_norm"] = out["fav_peak_vel"] / pre_rate
        out["fav_net_vel_norm"] = out["fav_net_vel"] / pre_rate
    return out


def spearman(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 8:
        return np.nan
    rx = pd.Series(x[m]).rank().values; ry = pd.Series(y[m]).rank().values
    return float(np.corrcoef(rx, ry)[0, 1])


def auc_line(name, r, s, seed, indent="  "):
    ci = two_sample_boot_ci(r, s, seed=seed)
    flag = "** CLEARS (reach>stall, pre-reg dir)" if ci["clears"] and ci["auc"] > 0.5 else (
        "!! clears OPPOSITE" if ci["clears"] else "-")
    print(f"{indent}{name:20s} AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"Rmed={np.nanmedian(r):.3f} Smed={np.nanmedian(s):.3f} (nR={np.isfinite(r).sum()} nS={np.isfinite(s).sum()}) {flag}")


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}  (B-design: all included, capped windows)")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    for tau in TAUS:
        F = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, tau, r.side) for _, r in g.iterrows()],
                         index=g.index)
        sub = g.join(F)
        ok = sub[sub.win_s >= MIN_WIN]
        dropped = len(sub) - len(ok)
        rA = ok[ok.grp == "reach"]; sA = ok[ok.grp == "stall"]
        tag = "  <<< PRIMARY" if tau == 60 else ""
        exin_r = int((rA.hold < tau).sum()); exin_s = int((sA.hold < tau).sum())
        print(f"\n========== tau={tau}s  reach={len(rA)} stall={len(sA)}  (dropped<{MIN_WIN}s: {dropped}) =========={tag}")
        print(f"  [circularity size] exits within tau: reach {exin_r}, stall {exin_s} "
              f"(these reach windows can contain target attainment)")
        for c in COLS:
            auc_line(c, rA[c].values, sA[c].values, seed)
        # ANTI-CIRCULARITY CONTROL (pre-registered decisive read): survivors only (hold >= tau) —
        # no reach in this subset attained target inside the window; also = velocity_ratio's arms.
        surv = ok[ok.hold >= tau]
        rS = surv[surv.grp == "reach"]; sS = surv[surv.grp == "stall"]
        print(f"  --- ANTI-CIRCULARITY / survivor subset (hold>={tau}s): reach={len(rS)} stall={len(sS)} — DECISIVE ---")
        for c in COLS:
            auc_line(c, rS[c].values, sS[c].values, seed, indent="    ")
        # redundancy vs velocity_ratio on survivors
        vr = []
        for _, r in surv.iterrows():
            fwd = pathlen_tk(sec, mid, r.entry, pd.Timestamp(r.entry) + S(tau))
            pre = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(PRE_W), r.entry)
            vr.append((fwd / tau) / (pre / PRE_W) if (fwd is not None and pre and pre > 0) else np.nan)
        vr = np.array(vr, float)
        print("  --- redundancy: Spearman vs velocity_ratio (survivors) ---")
        for c in COLS:
            print(f"    rho({c}, velocity_ratio) = {spearman(surv[c].values, vr):+.3f}")

    print("\nREAD (pre-registered): the SURVIVOR-SUBSET lines are DECISIVE — S2 counts as a finding only "
          "if it clears there (windows free of target attainment). All-trades B-design lines are the "
          "descriptive view; divergence between the two = the circularity/exit-timing component. Raw "
          "columns clearing (survivors) -> DIRECTION itself is signal (unsigned raw was wrong-way, "
          "T-SR22) = new. Only *_norm clears + high rho -> re-found velocity_ratio; the rho is the finding.")


def selftest(config, wrb):
    print("=== SELF-TEST: synthetic paths ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 130)).astype(np.int64)
    # flat 60s pre-entry with pathlen 15 ticks (rate .25/s); entry at t=60
    rng = np.random.default_rng(0)
    pre = 5000 + np.cumsum(rng.choice([-.0625, .0625], 60))    # |step|=.0625 -> .25tk/s
    # forward: +10 ticks in 20s (peak), then fade to +4 by t=120; exit at t=120 (hold 60)
    up = np.linspace(0, 2.5, 21)[1:]                            # +10 ticks over 20s
    fade = np.linspace(2.5, 1.0, 50)
    mid = np.concatenate([pre, [pre[-1]], pre[-1] + up, pre[-1] + fade])[:130]
    entry = base + S(60); exit_ = base + S(120)
    f = s2_feats(sec, mid, entry, exit_, 60, "long")
    print(f"  long peak10tk@20s: fav_peak_vel={f['fav_peak_vel']:.3f} (exp ~0.50)  fav_net_vel={f['fav_net_vel']:.3f}")
    assert abs(f["fav_peak_vel"] - 0.5) < 0.06
    assert f["fav_net_vel"] < f["fav_peak_vel"]                 # faded -> net < peak
    # capped window: exit at entry+20s -> window 20s, peak rate similar
    f2 = s2_feats(sec, mid, entry, entry + S(20), 60, "long")
    print(f"  capped@20s:        fav_peak_vel={f2['fav_peak_vel']:.3f} win={f2['win_s']:.0f}s (B-design)")
    assert f2["win_s"] == 20 and abs(f2["fav_peak_vel"] - 0.5) < 0.08
    # never-favorable long (falls) -> peak_vel == 0 by definition; net negative
    mid3 = np.concatenate([pre, [pre[-1]], pre[-1] - up, pre[-1] - fade])[:130]
    f3 = s2_feats(sec, mid3, entry, exit_, 60, "long")
    print(f"  never-favorable:   fav_peak_vel={f3['fav_peak_vel']:.3f} (exp 0)  fav_net_vel={f3['fav_net_vel']:.3f} (<0)")
    assert f3["fav_peak_vel"] == 0.0 and f3["fav_net_vel"] < 0
    # short side mirror: falling price is favorable
    f4 = s2_feats(sec, mid3, entry, exit_, 60, "short")
    assert abs(f4["fav_peak_vel"] - 0.5) < 0.06
    print(f"  short mirror:      fav_peak_vel={f4['fav_peak_vel']:.3f} (exp ~0.50)")
    # window floor
    f5 = s2_feats(sec, mid, entry, entry + S(3), 60, "long")
    assert np.isnan(f5["fav_peak_vel"]), "sub-5s window must be NaN"
    print("  <5s window -> NaN OK")
    assert rank_auc([0, 1, 2], [3, 4, 5]) == 0.0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
