#!/usr/bin/env python3
"""
p6_2_precision_check.py — IMITATION STUDY step 2: do the type definitions
SELECT, or only DESCRIBE? 2025-10. (Preserved from the inline run, T-IM02.)
For each type definition: how many of HIS 92 first entries it catches vs how
many market-wide moments qualify (45 s deduped, RTH, direction from the
tape state itself). All features from data <= the moment tested.
RESULT 2025-10: T1 catches 20/92 but ~4,404 moments qualify (~176/day,
his share 0.5%); T1+flow: 15/92 vs 2,689; fade: 5/92 vs 4,291. The types
describe his entries; they do not select them.
RUN: python3 Tests/P6_imitation_study/p6_2_precision_check.py             (repo root)
"""
import sys, os
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "P4_entry_determination"))
from p4_2_entry_context import month_bounds
from p4_66_context_ablation import prep
TICK = 0.25
def run(repo=".", m="2025-10"):
    P = prep(repo, m); cx = P["cx"]; secs, mids = P["secs"], P["mids"]
    iw = np.searchsorted(secs, secs-8); mv8 = (mids-mids[np.maximum(iw,0)])/TICK
    i120 = np.searchsorted(secs, secs-120); mv120 = (mids-mids[np.maximum(i120,0)])/TICK
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{m}_full.parquet"))
    csv_ = np.concatenate([[0.0], np.cumsum((f.buyv-f.sellv).to_numpy(float))])
    def fl5(j, sgn):
        a1 = int(np.searchsorted(secs, secs[j]-300)); return sgn*(csv_[j+1]-csv_[a1])/300.0
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(m); em = ep[(ep.first_entry_utc>=lo)&(ep.first_entry_utc<hi)]
    his = [(int(pd.Timestamp(r.first_entry_utc).value//10**9), 1 if r.side=="long" else -1) for _, r in em.iterrows()]
    bar_i = np.clip(np.searchsorted(cx.bts, secs*10**9, "right")-1, 0, len(cx.c)-1)
    rth = np.asarray(cx.rth)[bar_i]; keep = P["keep"]
    defs = {
      "T1": lambda j,d: abs(mv8[j])>=4 and np.sign(mv8[j])==d and d*mv120[j]>=8,
      "T1+flow": lambda j,d: abs(mv8[j])>=4 and np.sign(mv8[j])==d and d*mv120[j]>=8 and fl5(j,d)>1.0,
      "T3 fade": lambda j,d: d*mv120[j]<=-8 and fl5(j,d)<-1.0,
    }
    sess = len(set(P["sd"][k] for k in np.flatnonzero(np.asarray(cx.rth))))
    for name, fn in defs.items():
        cov = sum(1 for s0, side in his
                  if (j:=int(np.searchsorted(secs,s0,"right"))-1) > 10 and fn(j, side))
        cnt = 0; last = -10**18
        for j in np.flatnonzero(keep & rth):
            d = int(np.sign(mv8[j])) if "T1" in name else -int(np.sign(mv120[j]))
            if d == 0 or not fn(j, d): continue
            if secs[j]-last <= 45: continue
            last = int(secs[j]); cnt += 1
        print(f"{name}: catches {cov}/{len(his)} | market-wide {cnt} (~{cnt/sess:.0f}/day) | his share {cov/max(cnt,1):.1%}")
if __name__ == "__main__":
    run()
