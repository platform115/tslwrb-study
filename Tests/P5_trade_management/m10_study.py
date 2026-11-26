#!/usr/bin/env python3
"""
m10_study.py — T-MG17: his-exit imminence study. Spec: M10_SPEC.md
(committed first).
RUN: python3 Tests/P5_trade_management/m10_study.py > Tests/P5_trade_management/M10_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination",
          "Tests/P5_trade_management"):
    sys.path.insert(0, d)
from p6_0_feature_battery import build_ctx                   # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
GRID = 0.25
RNG = np.random.default_rng(113)

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

# shipped multi-day levels
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

G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
G = G[G.entry_verified & G.exit_verified
      & G.exit_msg_s.notna()].copy()
G["sd_n"] = G.side.map({"long": 1, "short": -1})

states = []
for mo in MONTHS:
    C = build_ctx(".", mo)
    secs, mids = C["secs"], C["mids"]
    csv_, ctv = C["csv"], C["ctv"]
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < MONTHS[mo])]
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    bsd = bm.sd.to_numpy()
    for _, r in G[G.month == mo].iterrows():
        t0, t1 = int(r.entry_msg_s), int(r.exit_msg_s)
        if t1 - t0 < 40 or not np.isfinite(r.entry_price):
            continue
        j0 = int(np.searchsorted(secs, t0))
        j1 = int(np.searchsorted(secs, t1, "right")) - 1
        if j1 - j0 < 20:
            continue
        k = int(np.searchsorted(bt, t0, "right")) - 1
        di = day_ix.get(bsd[k]) if k >= 0 else None
        lv = lf(di) if di else []
        kk3 = int(np.searchsorted(ev_all, t0, "right")) - 1
        mse0 = (t0 - ev_all[kk3]) / 60.0 if kk3 >= 0 else 99.0
        d = int(r.sd_n)
        exc = (mids[j0:j1 + 1] - r.entry_price) * d
        ts_ = (secs[j0:j1 + 1] - t0).astype(int)
        peak = 0.0
        vol_at_peak = np.nan
        for i in range(10, len(exc), 2):
            jj = j0 + i
            t_now = int(secs[jj])
            to_exit = t1 - t_now
            if 30 < to_exit < 120:
                continue          # excluded ambiguous band
            lab = 1 if to_exit <= 30 else 0
            v30 = ctv[jj + 1] - ctv[max(jj - 30, 0) + 1]
            f30 = (csv_[jj + 1] - csv_[max(jj - 30, 0) + 1]) * d
            f10 = (csv_[jj + 1] - csv_[max(jj - 10, 0) + 1]) * d
            if exc[i] > peak:
                peak = exc[i]
                vol_at_peak = v30
            px_now = r.entry_price + exc[i] * d
            ahead = [(p - px_now) * d for p in lv
                     if (p - px_now) * d > 0.25]
            behind = [(px_now - p) * d for p in lv
                      if (px_now - p) * d > 0.25]
            states.append(dict(
                sd=r.session_date, trade=f"{mo}_{t0}", lab=lab,
                t=ts_[i], exc=exc[i], peak=peak,
                give_back=peak - exc[i],
                slope10=exc[i] - exc[max(i - 10, 0)],
                slope30=exc[i] - exc[max(i - 30, 0)],
                room_ahead=min(ahead) if ahead else 99.0,
                lvl_behind=min(behind) if behind else 99.0,
                mins_since_ev=mse0 + ts_[i] / 60.0,
                flow10=f10, flow30=f30, vol30=v30,
                vol_fade=v30 / vol_at_peak if (np.isfinite(vol_at_peak)
                                               and vol_at_peak > 0)
                else np.nan))
S = pd.DataFrame(states)
S.to_parquet("Data/inputs/m10_states.parquet", index=False)
print("# M10 REPORT — HIS-EXIT IMMINENCE (T-MG17)")
print("STATUS: CLOSED | 2026-11-26 | Spec: M10_SPEC.md (committed "
      "first)")
print()
print(f"States: {len(S):,} from {S.trade.nunique()} of his audited "
      f"trades; exit-imminent (<=30s): {S.lab.mean():.0%} base rate.")
print()
FEATS = ["t", "exc", "peak", "give_back", "slope10", "slope30",
         "room_ahead", "lvl_behind", "mins_since_ev", "flow10",
         "flow30", "vol30", "vol_fade"]
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
X = S[FEATS].astype(float)
for c in FEATS:
    X[c] = X[c].fillna(X[c].median())
y = S.lab.to_numpy()
oof = np.full(len(S), np.nan)
imps = []
for tr, te in GroupKFold(4).split(X, y, groups=S.sd):
    rf = RandomForestClassifier(n_estimators=300, random_state=113,
                                n_jobs=-1, min_samples_leaf=40)
    rf.fit(X.iloc[tr], y[tr])
    oof[te] = rf.predict_proba(X.iloc[te])[:, 1]
    pi = permutation_importance(rf, X.iloc[te], y[te], n_repeats=3,
                                random_state=113, n_jobs=-1,
                                scoring="roc_auc")
    imps.append(pd.Series(pi.importances_mean, index=FEATS))
auc = roc_auc_score(y, oof)
print(f"## HELD-OUT AUC: {auc:.3f} (verdict lines: >=0.65 predictable "
      "| 0.55-0.65 weak | <0.55 in-data exhaustion earned)")
print()
IM = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
print("Importance (held-out):")
for c, v in IM.head(7).items():
    print(f"- {c}: {v:.4f}")
print()
print("## PLAIN CELLS (share of states that are exit-imminent | "
      "base rate = overall)")
def cell(name, msk):
    sub = S[msk]
    if len(sub) < 200:
        return
    pt = sub.groupby("trade").lab.mean().mean()
    print(f"- {name}: n={len(sub):,} | imminent {sub.lab.mean():.0%} | "
          f"per-trade {pt:.0%}")
base = S.lab.mean()
print(f"(base rate {base:.0%})")
cell("vol_fade < 0.5 (volume died from peak)", S.vol_fade < 0.5)
cell("vol_fade > 1.5 (volume building)", S.vol_fade > 1.5)
cell("flow30 < -50 (flow against)", S.flow30 < -50)
cell("flow30 > +50 (flow with)", S.flow30 > 50)
cell("at a level ahead < 1", S.room_ahead < 1)
cell("give_back < 0.5 & exc >= 2 (winning at peak)",
     (S.give_back < 0.5) & (S.exc >= 2))
cell("slope30 < -1 (fading)", S.slope30 < -1)
print()
print("Registry: T-MG17. m10_states.parquet saved.")
