#!/usr/bin/env python3
"""
v4_look.py — T-VL04: VALIDATION STEP 3 — tier20 direction + the four
parked suggestives on 2023-05/2024-05. REPORT-ONLY (frozen: direction
+ p, no thresholds, no adoption). Small n stated throughout.
RUN: python3 Tests/V_validation/v4_look.py > Tests/V_validation/V4_REPORT.md
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p6_24_s6_3_selectors import interact_edges              # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

RNG = np.random.default_rng(113)
MONTHS = {"2023-05": "2023-06-01", "2024-05": "2024-06-01"}
DEDUP = 300

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
NS = news_sets(".")
ev_all = np.asarray(NS["all"], dtype=np.int64) // 10**9
t20 = set((np.asarray(NS[">=20tk"], dtype=np.int64) // 10**9).tolist())
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
ep_all = pd.read_parquet("Data/inputs/tsl_episodes_clean.parquet"
                         ).dropna(subset=["first_entry_utc"])
ep_all["m"] = pd.to_datetime(ep_all.first_entry_utc, utc=True
                             ).dt.strftime("%Y-%m")

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

print("# V4 REPORT — VALIDATION STEP 3: TIER20 + THE FOUR SUGGESTIVES "
      "(T-VL04)")
print("STATUS: CLOSED | 2026-11-26 | REPORT-ONLY per the frozen plan "
      "(direction + p; nothing adopted from this step) | n is small "
      "everywhere - stated, not hidden")
print()

for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    secs = fl.sec.to_numpy(np.int64)
    mids = fl.mid.to_numpy(float)
    cvol = np.concatenate([[0.0], np.cumsum(
        (fl.buyv + fl.sellv).to_numpy(float))])
    cnet = np.concatenate([[0.0], np.cumsum(
        (fl.buyv - fl.sellv).to_numpy(float))])
    bk = pd.read_parquet(f"Data/inputs/book_top_per_sec_{mo}.parquet")
    bsec = bk.sec.to_numpy(); bb0 = bk.bid0.to_numpy(float)
    ba0 = bk.ask0.to_numpy(float)
    def top_at(t):
        k = int(np.searchsorted(bsec, t, "right")) - 1
        if k < 0 or t - bsec[k] > 5:
            return None
        return bb0[k], ba0[k]
    def fsum(c, a, b_):
        i = int(np.searchsorted(secs, a))
        j = int(np.searchsorted(secs, b_, "right"))
        return float(c[j] - c[i])
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
    # scanned windows
    W_rows = []
    for es in evm:
        es = int(es)
        j0 = int(np.searchsorted(secs, es + 300))
        j1 = int(np.searchsorted(secs, es + 2700, "right"))
        if j1 - j0 < 60:
            continue
        kb = int(np.searchsorted(bt, secs[j0], "right")) - 1
        if kb < 0 or not rth[kb]:
            continue
        W_rows.append(dict(es=es, tier20=float(es in t20),
                           vol5=fsum(cvol, es, es + 300), label=0))
    W = pd.DataFrame(W_rows)
    # his G2-like entries (B5 recipe)
    em = ep_all[ep_all.m == mo].copy()
    em["t_s"] = (pd.to_datetime(em.first_entry_utc, utc=True)
                 .dt.as_unit("ns").astype("int64") // 10**9)
    HIS = []
    for _, r_ in em.iterrows():
        side_ = 1 if r_.side == "long" else -1
        t_ = int(r_.t_s)
        kk_ = int(np.searchsorted(ev_all, t_, "right")) - 1
        mins_ = (t_ - ev_all[kk_]) / 60.0 if kk_ >= 0 else np.inf
        if not (5 < mins_ <= 45):
            continue
        kb_ = int(np.searchsorted(bt, t_, "right")) - 1
        if kb_ < 0:
            continue
        if interact_edges(R, sd1[kb_], np.datetime64(t_, "s"), "SQZ",
                          15, secs, mids, side_):
            HIS.append((t_, side_))
    sc = W.es.to_numpy()
    for t_, _s in HIS:
        elig = sc[(sc + 300 <= t_) & (t_ <= sc + 2700)]
        if len(elig):
            W.loc[W.es == int(elig.max()), "label"] = 1
    print(f"## {mo} — TIER20 DIRECTION (his G2-like: {len(HIS)})")
    for f, nm in (("tier20", "engagement"),):
        s1 = W[W.tier20 == 1]; s0 = W[W.tier20 == 0]
        print(f"- tier20 windows: he traded {int(s1.label.sum())}/"
              f"{len(s1)} ({s1.label.mean() if len(s1) else 0:.0%}); "
              f"minor windows: {int(s0.label.sum())}/{len(s0)} "
              f"({s0.label.mean() if len(s0) else 0:.0%}) -> direction "
              f"{'REPEATS' if (len(s1) and s1.label.mean() > s0.label.mean()) else 'does NOT repeat'}")
    a = W[W.label == 1].vol5; c = W[W.label == 0].vol5
    if len(a) >= 3:
        print(f"- flow_vol_5m: his med {a.median():,.0f} vs other "
              f"{c.median():,.0f} (p={mannwhitneyu(a, c).pvalue:.3f}) "
              f"-> {'same direction' if a.median() > c.median() else 'OPPOSITE'}")
    # which-signal paired: own0 + flow at taken vs passed crosses
    band_cache = {}
    ep_feats = []
    for t_, side_ in HIS:
        kb_ = int(np.searchsorted(bt, t_, "right")) - 1
        sd0 = sd1[kb_]
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        kk_ = int(np.searchsorted(ev_all, t_, "right")) - 1
        es0 = int(ev_all[kk_])
        j0 = int(np.searchsorted(secs, max(es0 + 300, t_ - 600)))
        j1 = int(np.searchsorted(secs, t_ + 60, "right"))
        crosses = []
        last_fire = {}
        for jj in range(max(j0, 1), j1):
            t2 = int(secs[jj])
            E = list(edges_at(R, sd0, np.datetime64(t2, "s"), "SQZ"))
            ki = int(np.searchsorted(g_bt + 60, t2, "right")) - 1
            if ki >= 0 and np.isfinite(blo[ki]):
                E += [blo[ki], bhi[ki]]
            px, prev = mids[jj], mids[jj - 1]
            for e in E:
                dd = 1 if (prev <= e < px) else \
                    (-1 if (prev >= e > px) else 0)
                if dd != side_:
                    continue
                key = (round(e, 2), dd)
                if t2 - last_fire.get(key, -10**9) <= DEDUP:
                    continue
                last_fire[key] = t2
                crosses.append(t2)
        if len(crosses) < 2:
            continue
        taken = max(crosses)
        rows = []
        for t2 in crosses:
            tp = top_at(t2)
            if tp is None:
                continue
            own0 = tp[0] if side_ > 0 else tp[1]
            rows.append(dict(t=t2, taken=int(t2 == taken), own0=own0,
                             flow30=fsum(cnet, t2 - 30, t2) * side_))
        if sum(r["taken"] for r in rows) == 1 and len(rows) >= 2:
            ep_feats.append(pd.DataFrame(rows))
    print(f"- which-signal episodes with >=2 covered crosses: "
          f"{len(ep_feats)}")
    for f in ("own0", "flow30"):
        if len(ep_feats) < 3:
            print(f"  - {f}: insufficient episodes")
            continue
        obs = 0.0
        nulls = np.zeros(2000)
        for g in ep_feats:
            v = g[f].to_numpy()
            r_ = pd.Series(v).rank(pct=True).to_numpy()
            obs += float(r_[g.taken.to_numpy() == 1][0])
            nulls += r_[RNG.integers(0, len(v), 2000)]
        obs /= len(ep_feats); nulls /= len(ep_feats)
        p = float(min((nulls >= obs).mean(), (nulls <= obs).mean()) * 2)
        print(f"  - {f}: taken med "
              f"{pd.concat(ep_feats).query('taken==1')[f].median():.1f}"
              f" vs passed "
              f"{pd.concat(ep_feats).query('taken==0')[f].median():.1f}"
              f" ({'taken HIGHER' if obs > 0.5 else 'taken LOWER'}, "
              f"p={min(p,1.0):.3f})")
    # sup0 at the 480s clock among his trades
    em2 = em.dropna(subset=["last_exit_utc"]).copy()
    em2["hold"] = (pd.to_datetime(em2.last_exit_utc, utc=True)
                   - pd.to_datetime(em2.first_entry_utc, utc=True)
                   ).dt.total_seconds()
    ce, hd = [], []
    for _, r_ in em2.iterrows():
        side_ = 1 if r_.side == "long" else -1
        t0 = int(r_.t_s)
        tp = top_at(t0 + 480)
        if tp is None:
            continue
        sup0 = tp[0] if side_ > 0 else tp[1]
        if 400 <= r_.hold <= 560:
            ce.append(sup0)
        elif r_.hold >= 700:
            hd.append(sup0)
    print(f"- sup0 at the 480s clock: clock-exiters n={len(ce)} (med "
          f"{np.median(ce) if ce else float('nan'):.0f}) vs holders "
          f"n={len(hd)} (med {np.median(hd) if hd else float('nan'):.0f})"
          + (f" -> holders {'THICKER (repeats)' if (ce and hd and np.median(hd) > np.median(ce)) else 'NOT thicker'}"
             if (ce and hd) else " -> insufficient"))
    print()
print("Nothing above is adopted; directions feed the standing "
      "directions queue only. Registry: T-VL04.")
