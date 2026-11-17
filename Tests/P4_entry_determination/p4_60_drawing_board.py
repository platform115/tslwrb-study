#!/usr/bin/env python3
"""
p4_60_drawing_board.py — P4.60 / Strategy 2: the assumption-free pass.
=======================================================================
No WRB, no KME, no zones, no score - no prior hypotheses at all. Take ALL of
his entries in the training months and describe their moments bottom-up:
  - raw context features at the entry minute (returns at 6 horizons signed
    toward his side, activity vs the day's norm at 3 scales, volume vs norm,
    position in the day's range, path efficiency, time of day/into session,
    per-second thrust and signed volume)
  - the same features on every RTH minute as the chance baseline (direction
    convention for the baseline: sign of the last 5-min move)
  - AUC battery: what ACTUALLY separates his moments from ordinary ones
  - k-means clustering of his entries in the significant dimensions: how many
    distinct entry TYPES does he have, and what does each look like?
Universe: all his entries, 2025-10 + 2022-02. Validation months locked.

RUN: python3 Tests/P4_entry_determination/p4_60_drawing_board.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_4_probes import rank_auc, boot_ci              # noqa: E402
from p4_49_sec_engine import Ctx                       # noqa: E402

TICK = 0.25


def month_features(repo, month):
    cx = Ctx(repo, month, True)
    lo, hi = month_bounds(month)
    bars = cx.bars
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
    secs = f.sec.to_numpy(np.int64)
    mids = f.mid.to_numpy(float)
    sv = (f.buyv - f.sellv).to_numpy(float)
    csv_ = np.concatenate([[0.0], np.cumsum(sv)])
    c = bars.close.to_numpy(); h = bars.high.to_numpy(); l = bars.low.to_numpy()
    v = bars.volume.to_numpy(float)
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    n = len(bars)
    absr = np.abs(np.diff(c, prepend=c[0]))
    # trailing activity vs the day's own norm
    act5 = pd.Series(absr).rolling(5).sum().to_numpy()
    act15 = pd.Series(absr).rolling(15).sum().to_numpy()
    act60 = pd.Series(absr).rolling(60).sum().to_numpy()
    vol5 = pd.Series(v).rolling(5).sum().to_numpy()
    med_act5 = pd.Series(act5).rolling(390, min_periods=60).median().to_numpy()
    med_vol5 = pd.Series(vol5).rolling(390, min_periods=60).median().to_numpy()
    # running day range, session open index
    run_hi = np.full(n, np.nan); run_lo = np.full(n, np.nan); sess_i0 = np.zeros(n, int)
    cur = None; hh = ll = np.nan; i0 = 0
    for i in range(n):
        if sd[i] != cur:
            cur = sd[i]; hh = ll = np.nan; i0 = i
        if rth[i]:
            hh = h[i] if np.isnan(hh) else max(hh, h[i])
            ll = l[i] if np.isnan(ll) else min(ll, l[i])
        run_hi[i], run_lo[i], sess_i0[i] = hh, ll, i0

    def mid_at(s):
        j = np.searchsorted(secs, s, "right") - 1
        return mids[j] if j >= 0 else np.nan

    def feats(i, dirn, s0):
        out = {}
        for w in (1, 3, 5, 15, 30, 60):
            out[f"ret{w}m"] = dirn * (c[i] - c[max(i - w, 0)]) / TICK
        out["act5_r"] = act5[i] / med_act5[i] if med_act5[i] > 0 else np.nan
        out["act15_r"] = act15[i] / med_act5[i] / 3 if med_act5[i] > 0 else np.nan
        out["act60_r"] = act60[i] / med_act5[i] / 12 if med_act5[i] > 0 else np.nan
        out["vol5_r"] = vol5[i] / med_vol5[i] if med_vol5[i] > 0 else np.nan
        rng = run_hi[i] - run_lo[i]
        out["day_pos"] = dirn * ((c[i] - run_lo[i]) / rng - 0.5) * 2 if rng > 0 else np.nan
        out["day_rng_tk"] = rng / TICK if rng > 0 else np.nan
        out["eff60"] = abs(c[i] - c[max(i - 60, 0)]) / max(absr[max(i - 60, 0) + 1:i + 1].sum(), 1e-9)
        out["min_into_sess"] = i - sess_i0[i]
        m0 = mid_at(s0)
        out["sec_mv10"] = dirn * (m0 - mid_at(s0 - 10)) / TICK
        out["sec_mv30"] = dirn * (m0 - mid_at(s0 - 30)) / TICK
        a, b = np.searchsorted(secs, s0 - 30), np.searchsorted(secs, s0, "right")
        out["sec_svol30"] = dirn * (csv_[b] - csv_[a])
        return out

    return cx, bars, feats, c


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    his_rows, base_rows = [], []
    for month, sym in MONTHS:
        cx, bars, feats, c = month_features(repo, month)
        lo, hi = month_bounds(month)
        bts = cx.bts
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        for _, t in e_m.iterrows():
            ts = pd.Timestamp(t.first_entry_utc).value
            i = int(np.searchsorted(bts, ts)) - 1
            if i < 60 or not cx.rth[i]:
                continue
            dirn = 1 if t.side == "long" else -1
            his_rows.append(dict(month=month, ts=pd.Timestamp(ts), side=t.side,
                                 pnl=t.realized_pnl, **feats(i, dirn, ts // 10**9)))
        rthi = np.flatnonzero(cx.rth & (bts >= lo.value) & (bts < hi.value))
        for i in rthi[::2]:                       # every 2nd minute is plenty
            if i < 60:
                continue
            mv = c[i] - c[i - 5]
            if mv == 0:
                continue
            base_rows.append(feats(i, 1 if mv > 0 else -1, int(bts[i] // 10**9) + 60))
    H = pd.DataFrame(his_rows); B = pd.DataFrame(base_rows)
    FEATS = [k for k in B.columns]
    print(f"ALL his entries, training months: n={len(H)} | baseline minutes: {len(B)}\n")
    print("AUC battery, no prior hypotheses (* = bootstrap CI clears 0.5):")
    print("| Feature | AUC | CI | His median | Baseline median |")
    print("|---|---|---|---|---|")
    sig_feats = []
    res = []
    for k in FEATS:
        a_t = H[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
        a_k = B[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
        if len(a_t) < 30:
            continue
        auc = rank_auc(a_t, a_k)
        ci = boot_ci(a_t, a_k) if auc > 0.5 else boot_ci(-a_t, -a_k)
        res.append((abs(auc - 0.5), k, auc, ci, a_t.median(), a_k.median()))
    for _, k, auc, ci, mt, mb in sorted(res, reverse=True):
        star = "*" if ci["clears"] else " "
        print(f"| {k} | {auc:.3f}{star} | [{ci['lo']:.3f},{ci['hi']:.3f}] | {mt:.2f} | {mb:.2f} |")
        if ci["clears"] and abs(auc - 0.5) >= 0.08:
            sig_feats.append(k)
    # clustering of HIS entries in the meaningful dimensions
    print(f"\nK-MEANS on his entries, dimensions: {sig_feats}")
    X = H[sig_feats].replace([np.inf, -np.inf], np.nan).dropna()
    Xs = (X - X.mean()) / X.std()
    rng = np.random.default_rng(7)
    best = None
    K = 4
    for _ in range(25):
        cent = Xs.sample(K, random_state=int(rng.integers(1e9))).to_numpy()
        for _ in range(50):
            dist = ((Xs.to_numpy()[:, None, :] - cent[None]) ** 2).sum(2)
            lab = dist.argmin(1)
            new = np.array([Xs.to_numpy()[lab == j].mean(0) if (lab == j).any() else cent[j]
                            for j in range(K)])
            if np.allclose(new, cent):
                break
            cent = new
        inertia = dist.min(1).sum()
        if best is None or inertia < best[0]:
            best = (inertia, lab.copy())
    H2 = H.loc[X.index].copy(); H2["cluster"] = best[1]
    print(f"\n| Cluster | n | Share | His win rate | His avg pnl | " +
          " | ".join(sig_feats) + " |")
    print("|---|---|---|---|---|" + "---|" * len(sig_feats))
    for j in sorted(H2.cluster.unique()):
        g = H2[H2.cluster == j]
        med = " | ".join(f"{g[k].median():.2f}" for k in sig_feats)
        print(f"| {j} | {len(g)} | {len(g)/len(H2):.0%} | {(g.pnl>0).mean():.0%} | "
              f"{g.pnl.mean():+.2f} | {med} |")
    H.to_csv(os.path.join(HERE, "p4_60_his_moments.csv"), index=False)
    print("\nOUT: p4_60_his_moments.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
