#!/usr/bin/env python3
"""
p6_3_t1_separators.py — IMITATION STUDY step 3: within-T1 separator battery.
His momentum-join entries vs the ~4,400 lookalike moments, 2025-10.
(Preserved from the inline run, T-IM03.) Features from data <= moment; AUC
folded to >=0.5. Revived selectors included per user directive (old score
signals, flow speed/exhaustion, KME windows, clock).
RESULT: samesig (same-direction score>=6 signal in prior 5 min) AUC 0.727 -
the RETIRED signal machinery is the best within-T1 separator; mins-from-open
0.670 (his median 53 vs 158); KME window 0.667; fl15 0.610. n(his)=14 after
45s dedupe + 15s matching - small-sample AUCs, wide uncertainty.
RUN: python3 Tests/P6_imitation_study/p6_3_t1_separators.py               (repo root)
"""
# (verbatim logic of the registered inline run - see T-IM03; rerun reproduces)

import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "P4_entry_determination"))
from p4_2_entry_context import month_bounds
from p4_66_context_ablation import prep
from p4_3_confluence_news import news_sets
TICK = 0.25
def run(repo=".", m="2025-10"):
    P = prep(repo, m); cx = P["cx"]; secs, mids = P["secs"], P["mids"]
    def mv(back):
        k = np.searchsorted(secs, secs - back)
        return (mids - mids[np.maximum(k, 0)]) / TICK
    mv8, mv10, mv30, mv120, mv300 = mv(8), mv(10), mv(30), mv(120), mv(300)
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{m}_full.parquet"))
    sv = (f.buyv - f.sellv).to_numpy(float); tv = (f.buyv + f.sellv).to_numpy(float)
    csv_ = np.concatenate([[0.0], np.cumsum(sv)]); ctv = np.concatenate([[0.0], np.cumsum(tv)])
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    sg = cx.sig[cx.sig.score >= 6]
    sig_s = sg.comp_ns.to_numpy(np.int64) // 10**9
    sig_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    oo = np.argsort(sig_s); sig_s, sig_d = sig_s[oo], sig_d[oo]
    bar_i = np.clip(np.searchsorted(cx.bts, secs * 10**9, "right") - 1, 0, len(cx.c) - 1)
    rth = np.asarray(cx.rth)[bar_i]; keep = P["keep"]; mins = P["mins_rth"]
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(m); em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    his_s = {int(pd.Timestamp(r.first_entry_utc).value // 10**9): (1 if r.side == "long" else -1)
             for _, r in em.iterrows()}
    def T1(j, d):
        return abs(mv8[j]) >= 4 and np.sign(mv8[j]) == d and d * mv120[j] >= 8
    his_set = set()
    for s0, side in his_s.items():
        j = int(np.searchsorted(secs, s0, "right")) - 1
        if j > 10 and T1(j, side):
            his_set.add(int(secs[j]))
    rows = []; last = -10**18
    for j in np.flatnonzero(keep & rth):
        d = int(np.sign(mv8[j]))
        if d == 0 or not T1(j, d): continue
        if secs[j] - last <= 45: continue
        last = int(secs[j]); s0 = last
        a1 = int(np.searchsorted(secs, s0 - 300)); a9 = int(np.searchsorted(secs, s0 - 900))
        kk = np.searchsorted(ev, s0 * 10**9, "right") - 1
        kme = 1.0 if (kk >= 0 and (s0 * 10**9 - ev[kk]) <= 45 * 60 * 10**9) else 0.0
        b2 = np.searchsorted(sig_s, s0, "right"); a2 = np.searchsorted(sig_s, s0 - 300)
        samesig = 1.0 if (sig_d[a2:b2] == d).any() else 0.0
        rows.append(dict(y=any(abs(s0 - hs) <= 15 for hs in his_set),
            mv8=abs(mv8[j]), mv10=d*mv10[j], mv30=d*mv30[j], mv120=d*mv120[j],
            mv300=d*mv300[j], fl5=d*(csv_[j+1]-csv_[a1])/300.0,
            fl15=d*(csv_[j+1]-csv_[a9])/900.0, vol5=(ctv[j+1]-ctv[a1])/300.0,
            mins=float(mins[bar_i[j]]), kme=kme, samesig=samesig))
    df = pd.DataFrame(rows)
    nh = int(df.y.sum()); print(f"T1 moments: {len(df)}, his among them: {nh}")
    for c in [c for c in df.columns if c != "y"]:
        x = df[c].to_numpy(float); y = df.y.to_numpy(bool)
        r = pd.Series(x).rank().to_numpy()
        auc = (r[y].sum() - nh*(nh+1)/2) / (nh*(len(df)-nh)); auc = max(auc, 1-auc)
        print(f"  {c}: AUC {auc:.3f} | his med {np.median(x[y]):+.2f} | rest {np.median(x[~y]):+.2f}")
if __name__ == "__main__":
    run()
