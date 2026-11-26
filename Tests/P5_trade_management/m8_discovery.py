#!/usr/bin/env python3
"""
m8_discovery.py — T-MG15: hold-or-sell discovery (steps 1-3).
Spec: M8_SPEC.md (committed first).
RUN: python3 Tests/P5_trade_management/m8_discovery.py > Tests/P5_trade_management/M8_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p4_66_context_ablation import prep                      # noqa: E402
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

# multi-day levels (shipped config)
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

# ---- trades to replay ----
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
D = D[D.disp == 1.25]
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
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
HIS = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                    "side"]]
GT = HIS.merge(G, left_on=["month", "sec"],
               right_on=["month", "entry_msg_s"], suffixes=("_f", ""))
GT["sd_n"] = GT.side.map({"long": 1, "short": -1})

states = []
for mo, nxt in MONTHS.items():
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)]
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    bsd = bm.sd.to_numpy()
    trades = []
    for _, r in D[D.month == mo].iterrows():
        trades.append((int(r.tf), float(r.edge + 1.25 * r.d), int(r.d),
                       "ours"))
    for _, r in GT[GT.month == mo].iterrows():
        if np.isfinite(r.entry_price):
            trades.append((int(r.sec), float(r.entry_price),
                           int(r.sd_n), "his"))
    for tf, lvl, dd, who in trades:
        k = int(np.searchsorted(bt, tf, "right")) - 1
        di = day_ix.get(bsd[k]) if k >= 0 else None
        lv = lf(di) if di else []
        j1 = int(np.searchsorted(secs, tf))
        j2 = int(np.searchsorted(secs, tf + 1800, "right"))
        if j2 - j1 < 180:
            continue
        exc = (mids[j1:j2] - lvl) * dd
        ts_ = (secs[j1:j2] - tf).astype(int)
        kk3 = int(np.searchsorted(ev_all, tf, "right")) - 1
        mse0 = (tf - ev_all[kk3]) / 60.0 if kk3 >= 0 else np.nan
        peak = 0.0
        # sample every 5th second to control autocorrelation volume
        for i in range(10, len(exc) - 300, 5):
            if exc[i] > peak:
                peak = exc[i]
            px_now = lvl + exc[i] * dd
            ahead = [(p - px_now) * dd for p in lv
                     if (p - px_now) * dd > 0.25]
            behind = [(px_now - p) * dd for p in lv
                      if (px_now - p) * dd > 0.25]
            states.append(dict(
                month=mo, sd=bsd[k], who=who, trade_id=f"{mo}_{tf}",
                t=ts_[i], exc=exc[i], peak=peak,
                give_back=peak - exc[i],
                slope10=exc[i] - exc[max(i - 10, 0)],
                slope30=exc[i] - exc[max(i - 30, 0)],
                room_ahead=min(ahead) if ahead else 99.0,
                lvl_behind=min(behind) if behind else 99.0,
                mins_since_ev=mse0 + ts_[i] / 60.0,
                fut120=exc[min(i + 120, len(exc) - 1)] - exc[i],
                fut300=exc[min(i + 300, len(exc) - 1)] - exc[i]))
S = pd.DataFrame(states)
S.to_parquet("Data/inputs/m8_states.parquet", index=False)
print("# M8 DISCOVERY — HOLD-OR-SELL STATES (T-MG15)")
print("STATUS: CLOSED | 2026-11-26 | Spec: M8_SPEC.md (committed first)")
print()
print(f"State-seconds: {len(S):,} (every 5th second) from "
      f"{S.trade_id.nunique()} trades ({(S.who=='his').sum():,} from "
      f"his {S[S.who=='his'].trade_id.nunique()} trades).")
print(f"Base rates: mean fut120 = {S.fut120.mean():+.3f}, mean fut300 "
      f"= {S.fut300.mean():+.3f} (the drift a policy must beat).")
print()
FEATS = ["t", "exc", "peak", "give_back", "slope10", "slope30",
         "room_ahead", "lvl_behind", "mins_since_ev"]
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold
X = S[FEATS].astype(float)
for lbl in ("fut120", "fut300"):
    y = S[lbl].to_numpy()
    imps = []
    for tr, te in GroupKFold(4).split(X, y, groups=S.sd):
        rf = RandomForestRegressor(n_estimators=250, random_state=113,
                                   n_jobs=-1, min_samples_leaf=50)
        rf.fit(X.iloc[tr], y[tr])
        pi = permutation_importance(rf, X.iloc[te], y[te], n_repeats=3,
                                    random_state=113, n_jobs=-1)
        imps.append(pd.Series(pi.importances_mean, index=FEATS))
    IM = pd.concat(imps, axis=1).mean(axis=1).sort_values(
        ascending=False)
    print(f"## RANKING for {lbl} (held-out, session-grouped)")
    for c, v in IM.head(5).items():
        print(f"- {c}: {v:.4f}")
    print()
# distributions on the top feature splits (plain evidence)
print("## PLAIN EVIDENCE — continuation by state (per-second mean "
      "fut120, with per-trade-averaged check)")
def show(name, msk):
    sub = S[msk]
    pt = sub.groupby("trade_id").fut120.mean()
    print(f"- {name}: n={len(sub):,} | fut120 per-sec "
          f"{sub.fut120.mean():+.3f} | per-trade {pt.mean():+.3f}")
show("give_back < 0.5 (at/near peak)", S.give_back < 0.5)
show("give_back 0.5-1.5", (S.give_back >= 0.5) & (S.give_back < 1.5))
show("give_back >= 1.5 (deep off peak)", S.give_back >= 1.5)
show("slope30 > +1 (accelerating)", S.slope30 > 1)
show("slope30 < -1 (fading)", S.slope30 < -1)
show("room_ahead < 1 (at a level)", S.room_ahead < 1)
show("room_ahead 1-4", (S.room_ahead >= 1) & (S.room_ahead < 4))
show("room_ahead >= 4 (open air)", S.room_ahead >= 4)
show("exc >= 2 & give_back < 0.5 (winning, at peak)",
     (S.exc >= 2) & (S.give_back < 0.5))
show("exc >= 2 & give_back >= 1.5 (winning, fading)",
     (S.exc >= 2) & (S.give_back >= 1.5))
print()
print("REVIEW GATE: J sees this before any policy extraction (step 4).")
print("Registry: T-MG15. m8_states.parquet saved.")
