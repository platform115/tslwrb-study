#!/usr/bin/env python3
"""
s3_time_to_ticks.py — F1/S3: first-passage time to +N favorable ticks
======================================================================
"Did it take off or trudge": seconds from entry until price first trades +N ticks in the trade's favor
(first-passage time, standard stochastic-processes concept; ATR threshold per Wilder 1978, ATR-scaled
distances per LeBeau's Chandelier lineage).

PRE-REGISTERED (locked with user):
  Thresholds N: +4 tk PRIMARY, +8 tk secondary, N_rel = 1.0 x ATR(20) of 1m bars strictly BEFORE the
    entry minute (es_1m_front, completed bars only; ATR in ticks). k=1.0 hardcoded (no k-sweep).
  Horizons: 60s PRIMARY, 90s, 120s robustness. B-design windows [entry, min(entry+H, exit)], >=5s floor.
    Survivor subset (hold>=H) DECISIVE per horizon; exits-within-H printed. 120s survivor frame ~41/13
    -> directional only.
  PRIMARY CELL: N=+4 @ 60s, survivor frame. Everything else = robustness (18 cells exist by user's
    D1/D2 additions; without one pre-named primary, "something clears somewhere" is guaranteed).
  READS per cell (user D3: multiple separate reads, NO censoring blend):
    (i)  attainment fraction per arm + bootstrap CI on (reach - stall) difference. Expect reach HIGHER.
    (ii) time-to-N among ATTAINERS only, AUC (reach FASTER = lower time -> AUC<0.5 matches),
         requires >=8 attainers per arm else UNINFORMATIVE. Selection-conditioned; counts printed.
  REDUNDANCY vs fav_net_vel (survivors@60, thresholds LOCKED pre-output):
    rho (pair-bootstrap CI): CI inside (-0.4,+0.4) -> NEW AXIS; CI beyond |0.6| -> REDUNDANT
    (logged "directional-progress axis robust to operationalization", NO candidate status);
    else INDETERMINATE (logged as such, no narrative rescue). Expected sign NEGATIVE for time-vs-netvel.
    Secondary: rho vs velocity_ratio. Attainment indicator rho reported too (Spearman on 0/1).

REUSES: build_arms (forward_battery) · S, TICK, read_per_second (trade_flow_exhaustion) ·
        rank_auc, two_sample_boot_ci (range_expansion) · pathlen_tk (velocity_acceleration) ·
        s2_feats, spearman (s2_directional_velocity) · spearman_boot_ci (fav_net_vel_confirm).
RUN (from 06_ root):
  PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/s3_time_to_ticks.py \
      --config config.toml --wrb wrb_1m.parquet
Registry: T-DF03 · family=speed · code_ref=06-14_discretionary_factors/s3_time_to_ticks.py
"""

import argparse
import numpy as np
import pandas as pd

try:
    import tomllib
except ImportError:                                    # py<3.11
    import tomli as tomllib

from trade_flow_exhaustion import S, TICK, read_per_second
from forward_battery import build_arms
from range_expansion import rank_auc, two_sample_boot_ci
from velocity_acceleration import pathlen_tk
from s2_directional_velocity import s2_feats, PRE_W
from fav_net_vel_confirm import spearman_boot_ci

HORIZONS = [60, 90, 120]
MIN_WIN = 5
N_MIN = 8
ATR_LOOKBACK = 20
ATR_K = 1.0


def load_atr_ticks(config_path, entries):
    """ATR(20) in TICKS per entry, from 1m bars strictly BEFORE the entry minute (completed bars only)."""
    cfg = tomllib.load(open(config_path, "rb"))
    path = cfg["paths"]["es_1m_front"] if "paths" in cfg and "es_1m_front" in cfg.get("paths", {}) \
        else cfg.get("es_1m_front") or next(v for k, v in _flat(cfg) if k.endswith("es_1m_front"))
    df = pd.read_parquet(path, columns=["ts_event", "high", "low", "close"]).sort_values("ts_event")
    ts = df["ts_event"].values
    h = df["high"].values; l = df["low"].values; c = df["close"].values
    tr = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - c[:-1]), np.abs(l[1:] - c[:-1])))
    tr_ts = ts[1:]
    out = {}
    for e in entries:
        cut = np.datetime64(pd.Timestamp(e).floor("1min").tz_convert("UTC").tz_localize(None))
        i = np.searchsorted(tr_ts.astype("datetime64[ns]"), cut, "left")   # bars with open < entry minute
        if i < ATR_LOOKBACK:
            out[e] = np.nan; continue
        out[e] = float(np.mean(tr[i - ATR_LOOKBACK:i]) / TICK)
    return out


def _flat(d, pre=""):
    for k, v in d.items():
        if isinstance(v, dict):
            yield from _flat(v, pre + k + ".")
        else:
            yield pre + k, v


def first_passage(sec, mid, entry, exit_, H, side, n_ticks):
    """(attained: bool|nan, t_sec: float|nan) — first second oriented displacement >= n_ticks within
    [entry, min(entry+H, exit)]; window >= MIN_WIN s else (nan, nan)."""
    if not np.isfinite(n_ticks) or n_ticks <= 0:
        return np.nan, np.nan
    t0 = np.int64(pd.Timestamp(entry).value // 1_000_000_000)
    t_end = min(pd.Timestamp(entry) + S(H), pd.Timestamp(exit_))
    t1 = np.int64(pd.Timestamp(t_end).value // 1_000_000_000)
    if t1 - t0 < MIN_WIN:
        return np.nan, np.nan
    a = np.searchsorted(sec, t0, "left"); b = np.searchsorted(sec, t1, "right")
    if b - a < 3:
        return np.nan, np.nan
    o = (mid[a:b] if side == "long" else -mid[a:b]) / TICK
    disp = o - o[0]
    hit = np.nonzero(disp >= n_ticks)[0]
    if len(hit) == 0:
        return False, np.nan
    return True, max(float(sec[a + hit[0]] - t0), 1.0)


def attain_diff_ci(r_att, s_att, seed=0, B=10000):
    """bootstrap CI on attainment-fraction difference (reach - stall)."""
    r = np.asarray(r_att, float); s = np.asarray(s_att, float)
    r = r[np.isfinite(r)]; s = s[np.isfinite(s)]
    d = r.mean() - s.mean()
    rng = np.random.default_rng(seed); boot = np.empty(B)
    for i in range(B):
        boot[i] = r[rng.integers(0, len(r), len(r))].mean() - s[rng.integers(0, len(s), len(s))].mean()
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return d, lo, hi, (lo > 0 or hi < 0)


def run(config, wrb_path, seed=0):
    stall, reach, windowed = build_arms(config, wrb_path)
    g = pd.concat([stall.assign(grp="stall"), reach.assign(grp="reach")], ignore_index=True)
    print(f"[arms] reach {len(reach)} / stall {len(stall)}")
    atr = load_atr_ticks(config, g.entry.tolist())
    g["atr_tk"] = [atr[e] for e in g.entry]
    g["n_rel"] = ATR_K * g["atr_tk"]
    print(f"[ATR(20),1m,pre-entry] ticks: med={np.nanmedian(g.atr_tk):.1f} "
          f"q25={np.nanquantile(g.atr_tk,.25):.1f} q75={np.nanquantile(g.atr_tk,.75):.1f} "
          f"nan={int(g.atr_tk.isna().sum())}  -> N_rel = {ATR_K:.1f}x")
    t_min = g.entry.min() - S(PRE_W + 5); t_max = g.exit.max() + S(5)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    thresholds = [("N=+4tk", lambda r: 4.0), ("N=+8tk", lambda r: 8.0), ("N=ATRrel", lambda r: r.n_rel)]
    t4_60 = None   # survivors@60 attainers' time for redundancy read

    for H in HORIZONS:
        surv_mask = g.hold >= H
        print(f"\n#################### horizon H={H}s  "
              f"(survivors {int((surv_mask & (g.grp=='reach')).sum())}R/{int((surv_mask & (g.grp=='stall')).sum())}S; "
              f"exits<H: R{int(((~surv_mask) & (g.grp=='reach')).sum())}/S{int(((~surv_mask) & (g.grp=='stall')).sum())})"
              f" ####################{'  <<< PRIMARY HORIZON' if H == 60 else '  [robustness]'}")
        for tname, nfun in thresholds:
            res = [first_passage(sec, mid, r.entry, r.exit, H, r.side, float(nfun(r))) for _, r in g.iterrows()]
            att = pd.Series([a for a, t in res], index=g.index, dtype="object")
            tt = pd.Series([t for a, t in res], index=g.index, dtype=float)
            for frame, fmask in (("ALL(B)", pd.Series(True, index=g.index)), ("SURV", surv_mask)):
                m = fmask & att.notna()
                rA = m & (g.grp == "reach"); sA = m & (g.grp == "stall")
                ratt = att[rA].astype(float).values; satt = att[sA].astype(float).values
                if len(ratt) < N_MIN or len(satt) < N_MIN:
                    print(f"  [{tname:9s} {frame:6s}] UNINFORMATIVE (n<{N_MIN})"); continue
                d, lo, hi, clears = attain_diff_ci(ratt, satt, seed=seed)
                star = "**" if clears and d > 0 else ("!!" if clears else "  ")
                prim = "  <<< PRIMARY CELL" if (H == 60 and tname == "N=+4tk" and frame == "SURV") else ""
                print(f"  [{tname:9s} {frame:6s}] attain: R {ratt.mean():.2f} vs S {satt.mean():.2f}  "
                      f"diff {d:+.2f} CI[{lo:+.2f},{hi:+.2f}] {star}{prim}")
                r_t = tt[rA & (att == True)].dropna().values; s_t = tt[sA & (att == True)].dropna().values
                if len(r_t) >= N_MIN and len(s_t) >= N_MIN:
                    ci = two_sample_boot_ci(r_t, s_t, seed=seed)
                    star2 = "**" if ci["clears"] and ci["auc"] < 0.5 else ("!!" if ci["clears"] else "  ")
                    print(f"             {'':6s}  time|attained: AUC={ci['auc']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
                          f"Rmed={np.nanmedian(r_t):.0f}s Smed={np.nanmedian(s_t):.0f}s "
                          f"(attainers R{len(r_t)}/S{len(s_t)}) {star2} (AUC<0.5 = reach faster)")
                else:
                    print(f"             {'':6s}  time|attained: UNINFORMATIVE (attainers R{len(r_t)}/S{len(s_t)} < {N_MIN})")
                if H == 60 and tname == "N=+4tk" and frame == "SURV":
                    t4_60 = (m, tt, att)

    # ---- redundancy (locked thresholds) on survivors@60, N=+4 ----
    print("\n=== REDUNDANCY (locked pre-output): survivors@60, N=+4 ===")
    m, tt, att = t4_60
    sub = g[m].copy(); sub["t4"] = tt[m]; sub["att4"] = att[m].astype(float)
    F = pd.DataFrame([s2_feats(sec, mid, r.entry, r.exit, 60, r.side) for _, r in sub.iterrows()], index=sub.index)
    sub["fav_net_vel"] = F["fav_net_vel"].values
    vr = []
    for _, r in sub.iterrows():
        fwd = pathlen_tk(sec, mid, r.entry, pd.Timestamp(r.entry) + S(60))
        pre = pathlen_tk(sec, mid, pd.Timestamp(r.entry) - S(PRE_W), r.entry)
        vr.append((fwd / 60) / (pre / PRE_W) if (fwd is not None and np.isfinite(fwd) and pre and pre > 0) else np.nan)
    sub["velocity_ratio"] = np.array(vr, float)

    def verdict(lo, hi):
        if -0.4 < lo and hi < 0.4:
            return "NEW AXIS (CI inside +/-0.4)"
        if hi < -0.6 or lo > 0.6:
            return "REDUNDANT (CI beyond |0.6|) -> NO candidate status; axis robust to operationalization"
        return "INDETERMINATE (logged as such)"

    at = sub[sub.att4 == 1.0]
    rho, lo, hi, n = spearman_boot_ci(at["t4"].values, at["fav_net_vel"].values, seed=seed)
    print(f"  rho(t4 | attainers, fav_net_vel) = {rho:+.3f} CI[{lo:+.3f},{hi:+.3f}] n={n} (expect NEGATIVE)"
          f"\n    -> {verdict(lo, hi)}")
    rho2, lo2, hi2, n2 = spearman_boot_ci(sub["att4"].values, sub["fav_net_vel"].values, seed=seed)
    print(f"  rho(attained4 indicator, fav_net_vel) = {rho2:+.3f} CI[{lo2:+.3f},{hi2:+.3f}] n={n2}")
    rho3, lo3, hi3, n3 = spearman_boot_ci(at["t4"].values, at["velocity_ratio"].values, seed=seed)
    print(f"  rho(t4 | attainers, velocity_ratio) = {rho3:+.3f} CI[{lo3:+.3f},{hi3:+.3f}] n={n3} (secondary)")

    print("\nREAD: PRIMARY CELL = [N=+4 SURV @60s]. (i) attainment diff clearing (reach higher) = the "
          "'whether'; (ii) time|attained AUC<0.5 clearing = the 'how fast', selection-conditioned. "
          "Redundancy verdicts are locked; REDUNDANT means no third candidate regardless of what cleared. "
          "90/120s and +8/ATR cells are robustness only; 120s survivor frame is thin (directional only).")


def selftest(config, wrb):
    print("=== SELF-TEST ===")
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC")
    sec = (base.value // 1_000_000_000 + np.arange(0, 130)).astype(np.int64)
    pre = np.full(60, 5000.0)
    up = 5000.0 + np.cumsum(np.full(60, 0.125))          # +0.5tk/s -> +4tk at 8s, +8tk at 16s
    mid = np.concatenate([pre, [5000.0], up])[:130]
    entry = base + S(60); exit_ = base + S(125)
    a, t = first_passage(sec, mid, entry, exit_, 60, "long", 4.0)
    print(f"  +4tk @ 0.5tk/s: attained={a} t={t:.0f}s (expect ~8-9)"); assert a and 7 <= t <= 10
    a8, t8 = first_passage(sec, mid, entry, exit_, 60, "long", 8.0)
    print(f"  +8tk: attained={a8} t={t8:.0f}s (expect ~16-17)"); assert a8 and 15 <= t8 <= 18 and t8 > t
    an, tn = first_passage(sec, mid, entry, exit_, 60, "long", 40.0)
    print(f"  +40tk: attained={an} (expect False, t nan={np.isnan(tn)})"); assert an is False and np.isnan(tn)
    a_s, t_s = first_passage(sec, 2 * 5000.0 - mid, entry, exit_, 60, "short", 4.0)   # mirrored path
    print(f"  short mirror +4tk: attained={a_s} t={t_s:.0f}s"); assert a_s and 7 <= t_s <= 10
    a_c, t_c = first_passage(sec, mid, entry, entry + S(3), 60, "long", 4.0)
    print(f"  <5s window: nan={a_c is np.nan or (isinstance(a_c,float) and np.isnan(a_c))}"); assert not (a_c is True or a_c is False)
    d, lo, hi, clears = attain_diff_ci(np.ones(40), np.r_[np.ones(10), np.zeros(10)], seed=0, B=2000)
    print(f"  attain diff 1.0 vs 0.5: d={d:+.2f} CI[{lo:+.2f},{hi:+.2f}] clears={clears}"); assert clears and d > 0
    # ATR: synthetic via public math (TR then mean) sanity only — real load tested on the user's machine
    tr_synth = np.abs(np.diff(np.sin(np.arange(30)))) + 1.0
    assert np.isfinite(np.mean(tr_synth[-20:]))
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
