#!/usr/bin/env python3
"""db2_moments.py — T-BK03 moment lists (container side).
E1: level-approach events with frozen outcomes + his tags.
E2: his quiet-squeeze (G3) entries in the depth months.
OUT: Tests/D6_deepbook/moments_e1.csv (+outcomes), moments_e2.csv
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2022-02": "2022-03-01", "2025-10": "2025-11-01"}
GRID = 0.25
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()

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

# his audited entries (all, for tagging) + G3 subset
gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
gt = gt[gt.month.isin(MONTHS)].copy()
lag = gt.posting_lag_s.where(np.isfinite(gt.posting_lag_s), 0.0)
gt["t_entry"] = (gt.entry_msg_s - lag).astype(int)
gt["sd_n"] = gt.side.map({"long": 1, "short": -1})
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
G3 = F[(F.ctx == "squeeze") & (F.np_ == "none")
       & F.month.isin(MONTHS)]

e1_rows, e2_rows = [], []
for mo, nxt in MONTHS.items():
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    secs = fl.sec.to_numpy(np.int64)
    mids = fl.mid.to_numpy(float)
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)]
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    his_mo = gt[gt.month == mo]
    for sd0 in sorted(bm.sd.unique()):
        di = day_ix.get(sd0)
        if di is None:
            continue
        lv = lf(di)
        if not lv:
            continue
        msk_day = (sd1 == sd0) & rth
        if not msk_day.any():
            continue
        t0d, t1d = int(bt[msk_day].min()), int(bt[msk_day].max()) + 60
        j0 = int(np.searchsorted(secs, t0d))
        j1 = int(np.searchsorted(secs, t1d, "right"))
        mseg = mids[j0:j1]
        sseg = secs[j0:j1]
        if len(mseg) < 120:
            continue
        for L in lv:
            dist = np.abs(mseg - L)
            near = dist <= 2.0
            enter = np.flatnonzero(near & ~np.roll(near, 1))
            last_t = -10**12
            for k in enter[enter > 30]:
                t = int(sseg[k])
                if t - last_t <= 600:
                    continue
                last_t = t
                d_app = 1 if mseg[k - 1] < L else -1  # price below -> testing from below
                # outcome over next 600s
                j2 = int(np.searchsorted(sseg, t + 600, "right"))
                fwd = mseg[k:j2]
                if len(fwd) < 60:
                    continue
                beyond = (fwd - L) * d_app       # >0 = through the level
                outcome = "CHOP"
                ext = 0.0
                touched = False
                for i2 in range(len(fwd)):
                    ext = max(ext, beyond[i2])
                    if abs(fwd[i2] - L) <= 0.5:
                        touched = True
                    if beyond[i2] >= 1.5:
                        outcome = "BREAK"
                        break
                    if touched and (L - fwd[i2]) * d_app >= 1.5 \
                            and ext < 1.0:
                        outcome = "HOLD"
                        break
                if not touched and outcome != "BREAK":
                    outcome = "NO_TEST"
                his_tag = 0; his_side = 0
                hh = his_mo[(np.abs(his_mo.t_entry - t) <= 300)
                            & (np.abs(his_mo.entry_price - L) <= 2.5)]
                if len(hh):
                    his_tag = 1
                    his_side = int(hh.iloc[0].sd_n)
                e1_rows.append(dict(month=mo, t=t, side=d_app,
                                    level=L, outcome=outcome,
                                    his=his_tag, his_side=his_side))
    for _, h in G3[G3.month == mo].iterrows():
        e2_rows.append(dict(month=mo, t=int(h.sec),
                            side=int(h.side)))
E1 = pd.DataFrame(e1_rows)
E2 = pd.DataFrame(e2_rows)
# device moment format: month,t,side,cid,role,q
E1out = E1.rename(columns={}).copy()
E1out["cid"] = np.arange(len(E1out))
E1out["role"] = (E1out.outcome == "HOLD").astype(int)
E1out[["month", "t", "side", "cid", "role"]].to_csv(
    "Tests/D6_deepbook/moments_e1.csv", index=False)
E1.to_csv("Tests/D6_deepbook/e1_outcomes.csv", index=False)
E2["cid"] = np.arange(len(E2)); E2["role"] = 1
E2[["month", "t", "side", "cid", "role"]].to_csv(
    "Tests/D6_deepbook/moments_e2.csv", index=False)
print(f"E1: {len(E1)} approaches "
      f"({E1.outcome.value_counts().to_dict()}; his-tagged "
      f"{int(E1.his.sum())}); E2: {len(E2)} G3 entries")
