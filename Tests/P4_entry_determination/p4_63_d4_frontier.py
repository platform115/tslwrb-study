#!/usr/bin/env python3
"""
p4_63_d4_frontier.py — P4.63 / Strategy 2 (pre-v1): D4 universe + the
precision frontier + any-WRB boundary check.
=======================================================================
1. D4 (sustained one-sided flow run) gets the same treatment as D1: fires at
   the 99th-percentile run length, labeled his/not-his, full feature battery.
2. BOTH universes now carry wrb_any_dist: tick distance to the nearest body
   top/bottom of ANY 1-min WRB completed in the last 60 min (not just
   post-KME reaction WRBs) - the user's boundary-level check.
3. PRECISION FRONTIER per universe: enumerate threshold combinations over the
   discriminating features and report the best precision achievable while
   keeping at least 20 / 10 / 5 of his fires (coverage deliberately
   sacrificed; false fires minimized).
HARDCODED - FLAGGED FOR VARIATION: 99th pct per detector, 120 s clustering
and matching, 60-min WRB-level life, the frontier's threshold grids.
Training months only. Exploratory (grids searched on the labels).

RUN: python3 Tests/P4_entry_determination/p4_63_d4_frontier.py            (repo root)
"""
import argparse, itertools, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_4_probes import rank_auc, boot_ci              # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies             # noqa: E402
from p4_60_drawing_board import month_features         # noqa: E402

TICK = 0.25
Q, CLUST, MATCH_S = 99.0, 120, 120
LIFE_NS = 60 * int(60e9)


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    rows = {"D1": [], "D4": []}
    days = 0
    for month, sym in MONTHS:
        cx, bars, feats, c = month_features(repo, month)
        lo, hi = month_bounds(month)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64); mids = f.mid.to_numpy(float)
        sv = (f.buyv - f.sellv).to_numpy(float)
        rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
        keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        days += len(np.unique(secs[keep] // 86400))
        i10 = np.searchsorted(secs, secs - 10)
        mv10 = (mids - mids[np.maximum(i10, 0)]) / TICK
        runl = np.zeros(len(secs)); cur = 0; last_sign = 0
        for i in range(len(secs)):
            s = np.sign(sv[i])
            if s != 0 and s == last_sign:
                cur += 1
            elif s != 0:
                cur = 1; last_sign = s
            runl[i] = cur * (last_sign if last_sign else 0)
        # any-WRB boundary levels (1m, full month, 60-min life)
        w = wrb_bodies(bars[bars.rth].reset_index(drop=True))
        w = w.merge(bars[["ts_event", "open", "close"]], on="ts_event", how="left")
        wc = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + int(60e9)
        wlv = np.concatenate([np.minimum(w.open, w.close).to_numpy(),
                              np.maximum(w.open, w.close).to_numpy()])
        wct = np.concatenate([wc, wc])
        o = np.argsort(wct); wct, wlv = wct[o], wlv[o]
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])
        sig_s = cx.sig.comp_ns.to_numpy(np.int64) // 10**9
        sig_d = np.where(cx.sig.direction.to_numpy() == "bullish", 1, -1)
        sig_sc = cx.sig.score.to_numpy()
        oo = np.argsort(sig_s); sig_s, sig_d, sig_sc = sig_s[oo], sig_d[oo], sig_sc[oo]
        for uni, stat, sgn in [("D1", np.abs(mv10), np.sign(mv10)),
                               ("D4", np.abs(runl), np.sign(runl))]:
            thr = np.percentile(stat[keep & np.isfinite(stat)], Q)
            fire = keep & (stat >= thr)
            fs_i = []; last = -10**18
            for i in np.flatnonzero(fire):
                if secs[i] - last > CLUST:
                    fs_i.append(i); last = secs[i]
            print(f"[{month}] {uni} threshold = {thr:.1f} | fires: {len(fs_i)}")
            for i in fs_i:
                s0 = int(secs[i]); d0 = int(sgn[i])
                if d0 == 0:
                    continue
                his = bool(((np.abs(hs - s0) <= MATCH_S) & (hd == d0)).any())
                ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
                if ib < 60 or not cx.rth[ib]:
                    continue
                row = dict(month=month, his=his, **feats(ib, d0, s0))
                s_ns = s0 * 10**9
                a, b = np.searchsorted(wct, s_ns - LIFE_NS), np.searchsorted(wct, s_ns, side="right")
                row["wrb_any_dist"] = float(np.abs(mids[i] - wlv[a:b]).min() / TICK) if b > a else np.nan
                a2, b2 = np.searchsorted(sig_s, s0 - 300), np.searchsorted(sig_s, s0, side="right")
                m = sig_d[a2:b2] == d0
                row["old_signal"] = bool(m.any())
                row["old_score"] = float(sig_sc[a2:b2][m].max()) if m.any() else 0.0
                rows[uni].append(row)
    for uni in ("D1", "D4"):
        d = pd.DataFrame(rows[uni])
        T, K = d[d.his], d[~d.his]
        print(f"\n===== {uni} universe: {len(d)} fires ({len(d)/days:.1f}/day) | "
              f"his {len(T)} | others {len(K)} | base precision {d.his.mean():.0%} =====")
        print("| Feature | AUC | His median | Others median |")
        print("|---|---|---|---|")
        res = []
        for k in [c_ for c_ in d.columns if c_ not in ("month", "his")]:
            a_t = T[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
            a_k = K[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
            if len(a_t) < 20:
                continue
            auc = rank_auc(a_t, a_k)
            ci = boot_ci(a_t, a_k) if auc > 0.5 else boot_ci(-a_t, -a_k)
            res.append((abs(auc - 0.5), k, auc, ci["clears"], a_t.median(), a_k.median()))
        for _, k, auc, sig_, mt, mk in sorted(res, reverse=True)[:10]:
            print(f"| {k} | {auc:.3f}{'*' if sig_ else ' '} | {mt:.2f} | {mk:.2f} |")
        print(f"\nwrb_any_dist (his vs others, median ticks): "
              f"{T.wrb_any_dist.median():.1f} vs {K.wrb_any_dist.median():.1f}")
        # precision frontier
        grids = {
            "ret5m": [None, 20, 30, 40],
            "vol5_r": [None, 4, 8, 12],
            "old_score": [None, 6, 7, 8],
            "day_rng_tk_max": [None, 150, 200],
            "wrb_any_dist_max": [None, 2, 4],
            "min_into_sess_max": [None, 1050],
        }
        best = {20: None, 10: None, 5: None}
        for combo in itertools.product(*grids.values()):
            r5, v5, osc, drm, wdm, mis = combo
            m = pd.Series(True, index=d.index)
            if r5: m &= d.ret5m >= r5
            if v5: m &= d.vol5_r >= v5
            if osc: m &= d.old_score >= osc
            if drm: m &= d.day_rng_tk < drm
            if wdm: m &= d.wrb_any_dist <= wdm
            if mis: m &= d.min_into_sess <= mis
            g = d[m.fillna(False)]
            if not len(g):
                continue
            hk = int(g.his.sum()); pr = g.his.mean()
            for floor in best:
                if hk >= floor and (best[floor] is None or pr > best[floor][0]):
                    best[floor] = (pr, hk, len(g), combo)
        print("\nPRECISION FRONTIER (best precision with at least N of his kept):")
        print("| Keep >= N of his | Precision | His kept | Fires kept (total) | Per day | Gate |")
        print("|---|---|---|---|---|---|")
        names = list(grids)
        for floor, v in best.items():
            if v is None:
                continue
            pr, hk, fk, combo = v
            gate = ", ".join(f"{n}={c}" for n, c in zip(names, combo) if c)
            print(f"| {floor} | {pr:.0%} | {hk} | {fk} | {fk/days:.1f} | {gate} |")
        d.to_csv(os.path.join(HERE, f"p4_63_{uni}_fires.csv"), index=False)
    print("\nOUT: p4_63_D1_fires.csv, p4_63_D4_fires.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
