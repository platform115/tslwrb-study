#!/usr/bin/env python3
"""db_moments.py — build the moment lists for T-BK02 (container side).
Q1: his exit moments + duration-AND-excursion-matched hold moments
(the certified T-MG20 matching). Q2: taken/passed crosses (T-EN109
episode machinery, dedupe fixes included).
OUT: Tests/D6_deepbook/moments_q1.csv, moments_q2.csv
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = ("2022-02", "2025-10")
NXT = {"2022-02": "2022-03-01", "2025-10": "2025-11-01"}
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

# ---------- Q1: EX2-style matched moments ----------
gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
gt = gt[gt.month.isin(MONTHS)].copy()
lag = gt.posting_lag_s.where(np.isfinite(gt.posting_lag_s), 0.0)
gt["t_entry"] = gt.entry_msg_s - lag
gt["sd_n"] = gt.side.map({"long": 1, "short": -1})
gt = gt[np.isfinite(gt.hold_s) & (gt.hold_s >= 30) & gt.sd_n.notna()
        & np.isfinite(gt.entry_price)].copy()
gt["t_exit"] = gt.t_entry + gt.hold_s

MIDS = {}
for mo in MONTHS:
    f = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    MIDS[mo] = (f.sec.to_numpy(np.int64), f.mid.to_numpy(float))

def mid_at(mo, t):
    secs, mids = MIDS[mo]
    k = int(np.searchsorted(secs, t, "right")) - 1
    if k < 0 or t - secs[k] > 5:
        return None
    return float(mids[k])

rows1 = []
cid = 0
dropped = 0
for _, r in gt.iterrows():
    mo = r.month
    m_case = mid_at(mo, r.t_exit)
    if m_case is None:
        dropped += 1
        continue
    exc_case = (m_case - r.entry_price) * r.sd_n
    tol = max(0.5, 0.25 * abs(exc_case))
    dur = r.hold_s
    pool = gt[(gt.month == mo) & (gt.index != r.name)
              & (gt.hold_s >= 1.2 * dur)]
    ctr = []
    for _, c in pool.iterrows():
        tm = c.t_entry + dur
        mc = mid_at(mo, tm)
        if mc is None:
            continue
        if abs((mc - c.entry_price) * c.sd_n - exc_case) > tol:
            continue
        ctr.append((int(tm), int(c.sd_n)))
        if len(ctr) >= 3:
            break
    if not ctr:
        dropped += 1
        continue
    cid += 1
    rows1.append(dict(month=mo, t=int(r.t_exit), side=int(r.sd_n),
                      cid=cid, role=1))
    for tm, sdn in ctr:
        rows1.append(dict(month=mo, t=tm, side=sdn, cid=cid, role=0))
Q1 = pd.DataFrame(rows1)
Q1.to_csv("Tests/D6_deepbook/moments_q1.csv", index=False)
print(f"Q1: {Q1[Q1.role == 1].cid.nunique()} cases, {len(Q1)} moments "
      f"({dropped} dropped)")

# ---------- Q2: episode crosses (T-EN109 machinery) ----------
b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f_}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f_,
                                                             "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")]

def band_arrays(g, W, q):
    h = g.high.to_numpy(); l = g.low.to_numpy(); n = len(h)
    hs = pd.Series(h).rolling(W).max().to_numpy()
    ls = pd.Series(l).rolling(W).min().to_numpy()
    rng_w = hs - ls
    med = pd.Series(rng_w).shift(1).rolling(60, min_periods=10
                                            ).median().to_numpy()
    active = np.isfinite(rng_w) & np.isfinite(med) & (rng_w <= q * med)
    blo = np.full(n, np.nan); bhi = np.full(n, np.nan)
    run_lo = run_hi = np.nan; in_run = False
    cur_lo = cur_hi = np.nan
    for i in range(n):
        if active[i]:
            s0 = max(0, i - W + 1)
            if not in_run:
                run_lo, run_hi = l[s0:i + 1].min(), h[s0:i + 1].max()
                in_run = True
            else:
                run_lo = min(run_lo, l[i]); run_hi = max(run_hi, h[i])
            cur_lo, cur_hi = run_lo, run_hi
        else:
            in_run = False
        blo[i], bhi[i] = cur_lo, cur_hi
    return blo, bhi

rows2 = []
ep_id = 0
for mo in MONTHS:
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < NXT[mo])
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    secs, mids = MIDS[mo]
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
    band_cache = {}
    CL = []
    for es in evm:
        j0 = int(np.searchsorted(secs, es + 300))
        j1 = int(np.searchsorted(secs, es + 2700, "right"))
        if j1 - j0 < 60:
            continue
        kb = int(np.searchsorted(bt, secs[j0], "right")) - 1
        if kb < 0 or not rth[kb]:
            continue
        sd0 = sd1[kb]
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        last_fire = {}
        for jj in range(max(j0, 1), j1):
            t = int(secs[jj])
            E = list(edges_at(R, sd0, np.datetime64(t, "s"), "SQZ"))
            ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
            if ki >= 0 and np.isfinite(blo[ki]):
                E += [blo[ki], bhi[ki]]
            px, prev = mids[jj], mids[jj - 1]
            for e in E:
                dd = 1 if (prev <= e < px) else \
                    (-1 if (prev >= e > px) else 0)
                if dd == 0:
                    continue
                key = (round(e, 2), dd)
                if t - last_fire.get(key, -10**9) <= 300:
                    continue
                last_fire[key] = t
                CL.append((sd0, t, key[0], dd, int(es)))
    CLdf = pd.DataFrame(CL, columns=["sd", "t", "e", "d", "es"])
    CLdf = CLdf.drop_duplicates(["sd", "t", "e", "d", "es"])
    for _, h in HIS62[HIS62.month == mo].iterrows():
        sec, side = int(h.sec), int(h.side)
        cand = CLdf[(CLdf.d == side) & (CLdf.t >= sec - 600)
                    & (CLdf.t <= sec + 60)]
        if not len(cand):
            continue
        tk = cand.loc[cand.t.idxmax()]
        ep = CLdf[(CLdf.e == tk.e) & (CLdf.d == side)
                  & (CLdf.es == tk.es) & (CLdf.t <= sec + 60)
                  ].sort_values("t")
        if len(ep) < 2:
            continue
        ep_id += 1
        for _, c in ep.iterrows():
            rows2.append(dict(month=mo, t=int(c.t), side=side,
                              ep=ep_id,
                              taken=int(int(c.t) == int(tk.t))))
Q2 = pd.DataFrame(rows2)
Q2.to_csv("Tests/D6_deepbook/moments_q2.csv", index=False)
print(f"Q2: {Q2.ep.nunique()} episodes, {len(Q2)} crosses "
      f"({int(Q2.taken.sum())} taken)")
