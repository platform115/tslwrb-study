#!/usr/bin/env python3
"""
p4_62_selection_on_fires.py — P4.62 / Strategy 2 (pre-v1): selection on the
D1 trigger universe, one detector at a time.
============================================================================
Universe: every D1 fire (10-sec displacement burst at the 99th-percentile
threshold, clustered to one per 120 s) in the training months. Label: a fire
is HIS if one of his entries sits within 120 s, same direction. Then: what
separates his fires from the rest - with PRECISION as the target (a gate that
passes almost only his, low coverage acceptable; rejected fires may be good
trades he didn't see).
Features per fire: the drawing-board context set (returns toward fire
direction at 6 horizons, activity/volume vs day norm, day position, path
efficiency, time), level state (distance to live knowable level, seconds
since last touch), burst shape (magnitude, 30s move, signed vol, fires in
the last 30 min), and the OLD selection layer re-auditioning as one feature:
a score>=6 completion in the prior 5 min, same direction (+ its best score).

HARDCODED - FLAGGED FOR VARIATION TESTING (none settled):
  D1 threshold = 99th percentile per month | fire clustering 120 s |
  his-match window 120 s | 10 s burst window | 60-min level life |
  gate cut points below (chosen after the battery - exploratory).

RUN: python3 Tests/P4_entry_determination/p4_62_selection_on_fires.py     (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_4_probes import rank_auc, boot_ci              # noqa: E402
from p4_53_anchor_sweep import month_anchors           # noqa: E402
from p4_60_drawing_board import month_features         # noqa: E402

TICK = 0.25
Q, CLUST, MATCH_S = 99.0, 120, 120
LIFE_NS = 60 * int(60e9)
KNOWABLE = ["firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    rows = []
    days = 0
    for month, sym in MONTHS:
        cx, bars, feats, c = month_features(repo, month)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        pts = sorted(sum((W[k] for k in KNOWABLE), []))
        lt = np.array([t for t, _ in pts], dtype=np.int64)
        lp = np.array([p for _, p in pts])
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64); mids = f.mid.to_numpy(float)
        sv = (f.buyv - f.sellv).to_numpy(float)
        csv_ = np.concatenate([[0.0], np.cumsum(sv)])
        rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
        keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        days += len(np.unique(secs[keep] // 86400))
        i10 = np.searchsorted(secs, secs - 10)
        i30 = np.searchsorted(secs, secs - 30)
        mv10 = (mids - mids[np.maximum(i10, 0)]) / TICK
        mv30 = (mids - mids[np.maximum(i30, 0)]) / TICK
        sv30 = csv_[np.arange(1, len(secs) + 1)] - csv_[i30]
        thr = np.percentile(np.abs(mv10)[keep], Q)
        fire = keep & (np.abs(mv10) >= thr)
        fs_i = []
        last = -10**18
        for i in np.flatnonzero(fire):
            if secs[i] - last > CLUST:
                fs_i.append(i); last = secs[i]
        print(f"[{month}] D1 threshold = {thr:.1f} ticks/10s | fires: {len(fs_i)}")
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])
        sig_s = cx.sig.comp_ns.to_numpy(np.int64) // 10**9
        sig_d = np.where(cx.sig.direction.to_numpy() == "bullish", 1, -1)
        sig_sc = cx.sig.score.to_numpy()
        o = np.argsort(sig_s); sig_s, sig_d, sig_sc = sig_s[o], sig_d[o], sig_sc[o]
        fsec = secs[np.array(fs_i, dtype=int)]
        for i in fs_i:
            s0 = int(secs[i]); d0 = int(np.sign(mv10[i]))
            his = bool(((np.abs(hs - s0) <= MATCH_S) & (hd == d0)).any())
            ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
            if ib < 60 or not cx.rth[ib]:
                continue
            row = dict(month=month, his=his, **feats(ib, d0, s0))
            row["burst_mv10"] = abs(mv10[i])
            row["burst_mv30"] = d0 * mv30[i]
            row["burst_sv30"] = d0 * sv30[i]
            row["fires_30m"] = int(((fsec >= s0 - 1800) & (fsec < s0)).sum())
            s_ns = s0 * 10**9
            a, b = np.searchsorted(lt, s_ns - LIFE_NS), np.searchsorted(lt, s_ns, side="right")
            row["lvl_dist"] = float(np.abs(mids[i] - lp[a:b]).min() / TICK) if b > a else np.nan
            a2, b2 = np.searchsorted(sig_s, s0 - 300), np.searchsorted(sig_s, s0, side="right")
            m = sig_d[a2:b2] == d0
            row["old_signal"] = bool(m.any())
            row["old_score"] = float(sig_sc[a2:b2][m].max()) if m.any() else 0.0
            rows.append(row)
    d = pd.DataFrame(rows)
    T, K = d[d.his], d[~d.his]
    print(f"\nD1 fires: {len(d)} total ({len(d)/days:.1f}/day) | HIS: {len(T)} | not his: {len(K)}")
    print(f"base precision {d.his.mean():.0%}\n")
    print("AUC battery, his fires vs other fires (* = CI clears 0.5):")
    print("| Feature | AUC | CI | His median | Others median |")
    print("|---|---|---|---|---|")
    skip = {"month", "his"}
    res = []
    for k in [c for c in d.columns if c not in skip]:
        a_t = T[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
        a_k = K[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
        if len(a_t) < 25:
            continue
        auc = rank_auc(a_t, a_k)
        ci = boot_ci(a_t, a_k) if auc > 0.5 else boot_ci(-a_t, -a_k)
        res.append((abs(auc - 0.5), k, auc, ci, a_t.median(), a_k.median()))
    for _, k, auc, ci, mt, mk in sorted(res, reverse=True):
        star = "*" if ci["clears"] else " "
        print(f"| {k} | {auc:.3f}{star} | [{ci['lo']:.3f},{ci['hi']:.3f}] | {mt:.2f} | {mk:.2f} |")
    print(f"\nold_signal present: his {T.old_signal.mean():.0%} vs others {K.old_signal.mean():.0%}")
    print("\nPRECISION-TARGETED gates (exploratory - cut points chosen after the battery):")
    print("| Gate | Fires kept (total) | Per day | His kept | Precision |")
    print("|---|---|---|---|---|")
    gates = {
        "vol5_r >= 4": d.vol5_r >= 4,
        "vol5_r >= 4 AND old_signal": (d.vol5_r >= 4) & d.old_signal,
        "vol5_r >= 4 AND old_score >= 7": (d.vol5_r >= 4) & (d.old_score >= 7),
        "vol5_r >= 8 AND old_score >= 7": (d.vol5_r >= 8) & (d.old_score >= 7),
        "vol5_r >= 4 AND old_score >= 7 AND lvl_dist <= 8": (d.vol5_r >= 4) & (d.old_score >= 7) & (d.lvl_dist <= 8),
    }
    for nm, m in gates.items():
        g = d[m.fillna(False)]
        print(f"| {nm} | {len(g)} | {len(g)/days:.1f} | {int(g.his.sum())}/{int(d.his.sum())} "
              f"| {g.his.mean():.0%} |")
    d.to_csv(os.path.join(HERE, "p4_62_fires_labeled.csv"), index=False)
    print("\nOUT: p4_62_fires_labeled.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
