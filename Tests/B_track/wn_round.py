#!/usr/bin/env python3
"""
wn_round.py — T-EN112: window-selection study. Spec: WN_SPEC.md
(committed first). Study only.
RUN: python3 Tests/B_track/wn_round.py > Tests/B_track/WN_REPORT.md
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p4_66_context_ablation import prep                      # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

RNG = np.random.default_rng(113)
MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
GRID = 0.25

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
rth_b = b[b.session.eq("RTH") & ~b.is_roll_day]
pd_hi = rth_b.groupby("sd").high.max().reindex(days_all).to_numpy()
pd_lo = rth_b.groupby("sd").low.min().reindex(days_all).to_numpy()
NS = news_sets(".")
ev_all = np.asarray(NS["all"], dtype=np.int64) // 10**9
t20 = set((np.asarray(NS[">=20tk"], dtype=np.int64) // 10**9).tolist())
t45 = set((np.asarray(NS[">=45tk"], dtype=np.int64) // 10**9).tolist())

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

# levels (shipped config) — same construction as all prior rounds
rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk2 = np.searchsorted(ev_all, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_all[np.maximum(kk2, 0)]) <= 2700
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
bb = b[~b.is_roll_day]
for tfm in ("5min", "15min"):
    for sd, g in bb.groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w_ = body > pm
        for o, c in zip(r.open.to_numpy()[w_], r.close.to_numpy()[w_]):
            rows.append(pd.DataFrame({"sd": [sd, sd],
                                      "px": [max(o, c), min(o, c)],
                                      "newsborn": [False, False]}))
EV = pd.concat(rows, ignore_index=True)
EV["px"] = (EV.px * 4).round() / 4
EV = EV.drop_duplicates(["sd", "px"])
EV["di"] = EV.sd.map(day_ix); EV = EV.dropna(subset=["di"])
EV["di"] = EV.di.astype(int)
Vpx, Vdi, Vnb = EV.px.to_numpy(), EV.di.to_numpy(), EV.newsborn.to_numpy()

def density_levels(px, di, nb, tol, m):
    if not len(px):
        return []
    gp = np.round(px / GRID).astype(np.int64)
    lo, hi = gp.min(), gp.max()
    width = int(round(tol / GRID))
    order = np.argsort(gp)
    gs, ds, nbs = gp[order], di[order], nb[order]
    uniq = np.arange(lo, hi + 1); score = np.zeros(len(uniq))
    for k, g0 in enumerate(uniq):
        a = np.searchsorted(gs, g0 - width)
        b2 = np.searchsorted(gs, g0 + width, "right")
        if b2 > a:
            score[k] = len(set(ds[a:b2])) + (1.0 if nbs[a:b2].any()
                                             else 0.0)
    out, taken = [], np.zeros(len(uniq), bool)
    for k in np.argsort(-score):
        if score[k] < m or taken[k]:
            continue
        out.append(float(uniq[k] * GRID))
        taken[max(0, k - 2 * width):k + 2 * width + 1] = True
    return out

lv_cache = {}
def lf(di):
    if di not in lv_cache:
        msk = (Vdi >= di - 60) & (Vdi < di)
        out = []
        for p in density_levels(Vpx[msk], Vdi[msk], Vnb[msk], 2.0, 4):
            sel = np.abs(Vpx[msk] - p) <= 2.0
            last_mem = int(Vdi[msk][sel].max())
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - p) > 5.0).all()):
                out.append(p)
        lv_cache[di] = out
    return lv_cache[di]

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                      "side"]]

W_rows = []
unassigned = 0
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    fsec = fl.sec.to_numpy()
    cnet = np.concatenate([[0.0],
                           np.cumsum((fl.buyv - fl.sellv).to_numpy()
                                     .astype(float))])
    cvol = np.concatenate([[0.0],
                           np.cumsum((fl.buyv + fl.sellv).to_numpy()
                                     .astype(float))])
    def fsum(c, a, b_):
        i = int(np.searchsorted(fsec, a)); j = int(np.searchsorted(
            fsec, b_, "right"))
        return float(c[j] - c[i])
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    ts_ct = bm.ts_event.dt.tz_convert("America/Chicago")
    hour_ct = ts_ct.dt.hour.to_numpy() + ts_ct.dt.minute.to_numpy()/60
    dow = ts_ct.dt.dayofweek.to_numpy()
    evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
    band_cache = {}
    # his entries per day, sorted, for self-state
    his_mo = HIS62[HIS62.month == mo].sort_values("sec")
    scanned = []
    for es in evm:
        es = int(es)
        j0 = int(np.searchsorted(secs, es + 300))
        j1 = int(np.searchsorted(secs, es + 2700, "right"))
        if j1 - j0 < 60:
            continue
        kb = int(np.searchsorted(bt, secs[j0], "right")) - 1
        if kb < 0 or not rth[kb]:
            continue
        sd0 = sd1[kb]
        scanned.append(es)
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        jr = int(np.searchsorted(secs, es))
        jr = min(max(jr, 0), len(mids) - 1)
        j5 = int(np.searchsorted(secs, es + 300, "right"))
        m_rel = mids[jr]
        seg5 = mids[jr:j5]
        di = day_ix.get(sd0)
        lv = lf(di) if di is not None else []
        dists = [abs(p - m_rel) for p in lv]
        ki = int(np.searchsorted(g_bt + 60, es, "right")) - 1
        bw = (bhi[ki] - blo[ki]) if (ki >= 0 and
                                     np.isfinite(blo[ki])) else np.nan
        pdi = di - 1 if (di is not None and di >= 1) else None
        inpr = (float(pd_lo[pdi] <= m_rel <= pd_hi[pdi])
                if pdi is not None and np.isfinite(pd_lo[pdi])
                else np.nan)
        dpe = (float(min(abs(m_rel - pd_hi[pdi]),
                         abs(m_rel - pd_lo[pdi])))
               if pdi is not None and np.isfinite(pd_lo[pdi])
               else np.nan)
        # RTH open sec for that day: first RTH bar of sd0
        kb0 = np.flatnonzero((sd1 == sd0) & rth)
        open_s = int(bt[kb0[0]]) if len(kb0) else es
        W_rows.append(dict(
            month=mo, es=es, sd=sd0,
            tier20=float(es in t20), tier45=float(es in t45),
            hour_ct=float(hour_ct[kb]), dow=float(dow[kb]),
            mins_since_open=(es - open_s) / 60.0,
            react_abs_5m=float(abs(mids[min(j5, len(mids)) - 1]
                                   - m_rel)) if j5 > jr else np.nan,
            react_range_5m=float(seg5.max() - seg5.min())
            if len(seg5) else np.nan,
            flow_net_abs_5m=abs(fsum(cnet, es, es + 300)),
            flow_vol_5m=fsum(cvol, es, es + 300),
            dist_level=float(min(dists)) if dists else 20.0,
            n_levels_10=float(sum(d_ <= 10 for d_ in dists)),
            has_band=float(np.isfinite(bw)), band_width=bw,
            in_prior_range=inpr, dist_pd_edge=dpe,
            n_his_today=float((his_mo.sec < es).pipe(
                lambda s_: ((his_mo.sec.map(
                    lambda x: True)) & s_)).sum()
                if len(his_mo) else 0.0),
            label=0))
    # label via es assignment
    sc_arr = np.array(sorted(scanned))
    for _, h in his_mo.iterrows():
        sec = int(h.sec)
        elig = sc_arr[(sc_arr + 300 <= sec) & (sec <= sc_arr + 2700)]
        if not len(elig):
            unassigned += 1
            continue
        es_a = int(elig.max())
        for r_ in W_rows:
            if r_["month"] == mo and r_["es"] == es_a:
                r_["label"] = 1

D = pd.DataFrame(W_rows)
# fix n_his_today (count of his entries that day before es)
D["n_his_today"] = 0.0
for mo in MONTHS:
    his_mo = HIS62[HIS62.month == mo]
    for i, r_ in D[D.month == mo].iterrows():
        day_secs = his_mo.sec.to_numpy()
        # same session date: use sd via es day — approximate by same sd rows
        D.at[i, "n_his_today"] = float(
            ((day_secs < r_.es) & (np.abs(day_secs - r_.es) < 86400)
             ).sum())

print("# WN REPORT — WHICH NEWS WINDOWS DOES HE TRADE (T-EN112)")
print("STATUS: CLOSED | 2026-11-26 | Spec: WN_SPEC.md (committed "
      "first) | study only")
print()
npos = int(D.label.sum())
print(f"Population: {len(D)} scanned windows "
      f"({(D.month == '2022-02').sum()} / "
      f"{(D.month == '2025-10').sum()} per month); he traded "
      f"{npos} ({D[D.label == 1].groupby('month').size().to_dict()}); "
      f"{unassigned} of his entries assigned to no scanned window "
      f"(reported, not dropped). Base rate {npos / len(D):.0%}.")
print()
# leak/missingness sweep
print("## LEAK SWEEP")
flags = []
for f in ["react_abs_5m", "react_range_5m", "band_width",
          "in_prior_range", "dist_pd_edge"]:
    mp = D[D.label == 1][f].isna().mean()
    mn = D[D.label == 0][f].isna().mean()
    if abs(mp - mn) > 0.25:
        flags.append(f"{f}: missing {mp:.0%} pos vs {mn:.0%} neg")
print("missingness parity: " + ("; ".join(flags) if flags
                                else "clean (no gap > 25pp)")
      + ". All features end at es+300 by construction.")
print()
UNIV = ["tier20", "tier45", "hour_ct", "dow", "mins_since_open",
        "react_abs_5m", "react_range_5m", "flow_net_abs_5m",
        "flow_vol_5m", "dist_level", "n_levels_10", "has_band",
        "band_width", "in_prior_range", "dist_pd_edge"]
print("## UNIVARIATE (Mann-Whitney; Bonferroni alpha .0036, "
      "suggestive .05; FINDING also needs same direction both months)")
print("| feature | his med | other med | p | both-months same dir | "
      "verdict |")
print("|---|---|---|---|---|---|")
for f in UNIV:
    a = D[D.label == 1][f].dropna()
    c = D[D.label == 0][f].dropna()
    if len(a) < 5 or len(c) < 5:
        print(f"| {f} | - | - | - | - | insufficient |")
        continue
    p = mannwhitneyu(a, c).pvalue
    same = True
    for mo in MONTHS:
        am = D[(D.label == 1) & (D.month == mo)][f].dropna()
        cm = D[(D.label == 0) & (D.month == mo)][f].dropna()
        if len(am) and len(cm) and \
           np.sign(am.median() - cm.median()) != \
           np.sign(a.median() - c.median()):
            same = False
    v = ("FINDING" if (p <= 0.0036 and same) else
         ("suggestive" if p <= 0.05 else "null"))
    print(f"| {f} | {a.median():.2f} | {c.median():.2f} | {p:.4f} | "
          f"{'yes' if same else 'NO'} | {v} |")
print()
print("## SELF-STATE (flagged class, excluded from model)")
a = D[D.label == 1].n_his_today; c = D[D.label == 0].n_his_today
print(f"n_his_today: his-window med {a.median():.0f} vs other "
      f"{c.median():.0f} (p={mannwhitneyu(a, c).pvalue:.4f}) — in "
      "replication this becomes OUR trade count; context, not a "
      "market feature.")
print()
# model lane: LODO CV
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import roc_auc_score
feats = UNIV
X = D[feats].copy()
for f in feats:
    X[f] = X[f].fillna(X[f].median())
X = ((X - X.mean()) / X.std(ddof=0).replace(0, 1)).to_numpy()
y = D.label.to_numpy()
days_arr = D.sd.to_numpy()
def lodo_auc(model_fn, Xm, ym):
    oof = np.full(len(ym), np.nan)
    for d_ in np.unique(days_arr):
        tr = days_arr != d_
        te = ~tr
        if ym[tr].sum() == 0 or te.sum() == 0:
            continue
        m_ = model_fn()
        m_.fit(Xm[tr], ym[tr])
        oof[te] = m_.predict_proba(Xm[te])[:, 1]
    ok = ~np.isnan(oof)
    if ym[ok].sum() == 0 or ym[ok].sum() == ok.sum():
        return np.nan, oof
    return roc_auc_score(ym[ok], oof[ok]), oof
auc_lr, _ = lodo_auc(lambda: LogisticRegression(max_iter=2000, C=1.0),
                     X, y)
auc_dt, _ = lodo_auc(lambda: DecisionTreeClassifier(
    max_depth=2, min_samples_leaf=8, random_state=113), X, y)
null_lr = []
null_dt = []
mo_arr = D.month.to_numpy()
for it in range(1000):
    yp = y.copy()
    for mo in MONTHS:
        mmask = mo_arr == mo
        yp[mmask] = RNG.permutation(yp[mmask])
    a1, _ = lodo_auc(lambda: LogisticRegression(max_iter=2000, C=1.0),
                     X, yp)
    a2, _ = lodo_auc(lambda: DecisionTreeClassifier(
        max_depth=2, min_samples_leaf=8, random_state=113), X, yp)
    null_lr.append(a1); null_dt.append(a2)
null_lr = np.array([x for x in null_lr if np.isfinite(x)])
null_dt = np.array([x for x in null_dt if np.isfinite(x)])
p_lr = float((null_lr >= auc_lr).mean())
p_dt = float((null_dt >= auc_dt).mean())
print("## MODEL LANE (leave-one-day-out CV; 1000 within-month label "
      "permutations)")
print(f"- logistic: out-of-fold AUC {auc_lr:.3f} (null median "
      f"{np.median(null_lr):.3f}, perm p={p_lr:.3f})")
print(f"- depth-2 tree: out-of-fold AUC {auc_dt:.3f} (null median "
      f"{np.median(null_dt):.3f}, perm p={p_dt:.3f})")
print(("- FINDING threshold: p < 0.01. Tree readout only if the "
       "tree clears; otherwise withheld (overfit bait)."))
if p_dt < 0.01:
    m_ = DecisionTreeClassifier(max_depth=2, min_samples_leaf=8,
                                random_state=113).fit(X, y)
    from sklearn.tree import export_text
    print("```")
    print(export_text(m_, feature_names=feats))
    print("```")
print()
print("Registry: T-EN112.")
