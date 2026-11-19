#!/usr/bin/env python3
"""
p6_0_feature_battery.py — THE STANDARD FEATURE BATTERY for the imitation
study (user directive 2026-11-19: measure many windows and condition types,
not a hand-picked few; reuse everything from detectors/management/adapters).
Every feature is computed from data AT OR BEFORE second t (truncation-
harness discipline). Direction-dependent features take d (+1/-1) and are
signed TOWARD d; with d=None they are returned absolute.

Usage:
    C = build_ctx(repo, month)          # once per month
    f = battery(C, t_epoch_sec, d=+1)   # dict of ~30 features
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "P4_entry_determination"))
from p4_66_context_ablation import prep                 # noqa: E402
from p4_3_confluence_news import news_sets              # noqa: E402
import p5_1_excursion_anatomy as X_anat                 # noqa: E402

TICK = 0.25
BURST_SHARE = 0.022


def build_ctx(repo, month):
    P = prep(repo, month)
    cx = P["cx"]
    secs, mids = P["secs"], P["mids"]
    C = dict(P=P, cx=cx, secs=secs, mids=mids)
    C["dif"] = np.diff(mids, prepend=mids[0])
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
    C["csv"] = np.concatenate([[0.0], np.cumsum((f.buyv - f.sellv).to_numpy(float))])
    C["ctv"] = np.concatenate([[0.0], np.cumsum((f.buyv + f.sellv).to_numpy(float))])
    bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
    C["bar_i"] = bar_i
    pc = np.roll(cx.c, 1); pc[0] = cx.c[0]
    tr = np.maximum(cx.h - cx.l, np.maximum(np.abs(cx.h - pc), np.abs(cx.l - pc))) / TICK
    C["atr10"] = pd.Series(tr).shift(1).rolling(10).mean().to_numpy()[bar_i]
    c_day = X_anat.c_day_fun(repo)
    cds = {d: c_day(d) for d in set(P["sd"])}
    C["Cday"] = np.array([cds.get(d) or np.nan for d in P["sd"]])[bar_i]
    C["Rsec"] = C["Cday"] * C["atr10"]
    C["ev"] = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    sg = cx.sig[cx.sig.score >= 6]
    ss = sg.comp_ns.to_numpy(np.int64) // 10**9
    sd_ = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    sc = sg.score.to_numpy()
    oo = np.argsort(ss)
    C["sig"] = (ss[oo], sd_[oo], sc[oo])
    iw = np.searchsorted(secs, secs - 8)
    mv8 = (mids - mids[np.maximum(iw, 0)]) / TICK
    C["mv8"] = mv8
    C["burst"] = np.isfinite(C["Rsec"]) & (np.abs(mv8) >= BURST_SHARE * C["Rsec"])
    C["mins_rth"] = P["mins_rth"]
    C["sd_sec"] = np.asarray(P["sd"])[bar_i]
    return C


def battery(C, t, d=None):
    secs, mids, dif = C["secs"], C["mids"], C["dif"]
    j = int(np.searchsorted(secs, t, "right")) - 1
    if j < 4000:
        return None
    px = mids[j]
    sgn = (lambda v: d * v) if d else (lambda v: abs(v))
    out = {}

    def idx(back):
        return int(np.searchsorted(secs, t - back))
    # moves, many windows (ticks, toward d or absolute)
    for w in (8, 30, 60, 120, 300, 900):
        out[f"mv{w}"] = sgn((px - mids[min(idx(w), j)]) / TICK)
    # ranges & compression at several horizons
    def rng(a, b=0):
        seg = mids[idx(a):(j + 1 if b == 0 else idx(b))]
        return (seg.max() - seg.min()) / TICK if len(seg) > 10 else np.nan
    for w in (120, 300, 900, 1800):
        out[f"rng{w}"] = rng(w)
    base5 = np.nanmedian([rng(300 + k * 300, k * 300) for k in range(1, 12)])
    base15 = np.nanmedian([rng(900 + k * 900, k * 900) for k in range(1, 8)])
    out["comp5"] = out["rng300"] / base5 if base5 and base5 > 0 else np.nan
    out["comp15"] = out["rng900"] / base15 if base15 and base15 > 0 else np.nan
    # vol-of-tape ratios
    v2 = np.nanstd(dif[idx(120):j + 1]); v5 = np.nanstd(dif[idx(300):j + 1])
    v30 = np.nanstd(dif[idx(1800):j + 1])
    out["volr2"] = v2 / v30 if v30 > 0 else np.nan
    out["volr5"] = v5 / v30 if v30 > 0 else np.nan
    # volume rates and ratio
    ctv, csv = C["ctv"], C["csv"]
    for w, nm in ((60, "vrate1"), (300, "vrate5"), (900, "vrate15")):
        out[nm] = (ctv[j + 1] - ctv[idx(w)]) / w
    out["vratio5_30"] = (out["vrate5"] / ((ctv[j + 1] - ctv[idx(1800)]) / 1800)
                         if ctv[j + 1] > ctv[idx(1800)] else np.nan)
    # signed flow toward d (c/s), several windows
    for w, nm in ((60, "flow1"), (300, "flow5"), (900, "flow15")):
        v = (csv[j + 1] - csv[idx(w)]) / w
        out[nm] = sgn(v) if d else v
    # burst activity & quiet metrics (M1-world)
    b = C["burst"]
    out["bursts5"] = int(b[idx(300):j + 1].sum())
    out["bursts15"] = int(b[idx(900):j + 1].sum())
    lb = np.flatnonzero(b[:j + 1])
    out["burst_silence"] = float(t - secs[lb[-1]]) if len(lb) else 1e9
    seg = mids[idx(300):j + 1]
    if len(seg) > 10:
        pk = int(np.argmax(seg)) if (d or 1) > 0 else int(np.argmin(seg))
        out["stall_5m_extreme"] = float(t - secs[idx(300) + pk])
    # session structure
    sd0 = C["sd_sec"][j]
    day = (C["sd_sec"] == sd0) & (secs <= t)
    dm = mids[day]
    if len(dm) > 10:
        hi, lo_ = dm.max(), dm.min()
        out["dist_day_hi"] = (hi - px) / TICK
        out["dist_day_lo"] = (px - lo_) / TICK
        out["day_pos"] = (px - lo_) / (hi - lo_) if hi > lo_ else np.nan
    out["mins_open"] = float(C["mins_rth"][C["bar_i"][j]])
    # context & adapters
    out["Rest"] = C["Rsec"][j]; out["atr10"] = C["atr10"][j]; out["Cday"] = C["Cday"][j]
    kk = np.searchsorted(C["ev"], t * 10**9, "right") - 1
    out["kme_mins_since"] = (t * 10**9 - C["ev"][kk]) / 60e9 if kk >= 0 else 1e9
    ss, sdir, ssc = C["sig"]
    a2, b2 = np.searchsorted(ss, t - 300), np.searchsorted(ss, t, "right")
    if d:
        mask = sdir[a2:b2] == d
        out["sig_samedir_5m"] = float(mask.any())
        out["sig_best_score"] = float(ssc[a2:b2][mask].max()) if mask.any() else 0.0
    else:
        out["sig_any_5m"] = float(b2 > a2)
    return out
