#!/usr/bin/env python3
"""
d8_levels.py — D-8 STEP 1b: BLIND LEVEL PREDICTION (report only).
The MDL level lists for the quarantined months were generated from
market structure alone and COMMITTED (d8_prep.py, 0a) BEFORE this
comparison. Question: do our computed levels land on the prices HE
stated as zones in those months?
MEASUREMENT (frozen here, before any number is read):
- A zone reference = his_zone_refs row, instrument ES, price_1
  present, stated in the month; its session = the session of ts_utc.
- HIT = that session's blind list has a level within TOL of
  price_1. TOL = 2.0 points (the lf lineage's own tolerance);
  1.0 and 0.5 shown as tighter context rows.
- NULL (chance line): the share of the session's traded range
  covered by the +/-TOL bands of its levels - the hit rate a
  random price in range would get. A real effect needs hit >> null.
- REFERENCE: the same measurement on the six training months
  (levels from the same lf machinery, zones from the same archive).
DERIVES FROM (R-9 lineage): lf machinery verbatim from
g26_remint_gen.py (same copy as d8_prep.py, which passed the
row-identical rebuild control this sitting).
RUN: python3 Tests/D8_judgment/d8_levels.py             (repo root)
"""
import numpy as np
import pandas as pd

MONTHS_TRAIN = ["2021-09", "2022-02", "2023-05", "2024-05",
                "2024-11", "2025-10"]
MONTHS_NEW = ["2022-05", "2026-03"]
GRID = 0.25
TOLS = (2.0, 1.0, 0.5)

import sys
for d in ("Tests/P4_entry_determination",):
    sys.path.insert(0, d)
from p4_3_confluence_news import news_sets                   # noqa: E402

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk2 = np.searchsorted(ev_all, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_all[np.maximum(kk2, 0)]) <= 2700
wrb_day = {}
for tfm, tfs in (("5min", 300), ("15min", 900)):
    for sd, g in b[~b.is_roll_day].groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w_ = body > pm
        comp = (r.index.astype("int64").to_numpy() // 10**9 + tfs)[w_]
        for c_, o, cl_ in zip(comp, r.open.to_numpy()[w_],
                              r.close.to_numpy()[w_]):
            wrb_day.setdefault(sd, []).append(
                (int(c_), float(max(o, cl_))))
            wrb_day.setdefault(sd, []).append(
                (int(c_), float(min(o, cl_))))
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
for sd, lst in wrb_day.items():
    rows.append(pd.DataFrame({"sd": sd,
                              "px": [p for _, p in lst],
                              "newsborn": False}))
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


# session ranges for the null
rng = b[~b.is_roll_day].groupby("sd").agg(hi=("high", "max"),
                                          lo=("low", "min"))

# CONTROL: the committed blind lists must equal lf() recomputed
for mo in MONTHS_NEW:
    blind = pd.read_csv(f"Tests/D8_judgment/blind_levels_{mo}.csv")
    for sd, g in blind.groupby("session_date"):
        want = sorted(lf(day_ix[sd]))
        got = sorted(g.level.tolist())
        assert want == got, f"blind list mismatch {sd}"
print("CONTROL PASS: committed blind lists == lf() recomputation")

zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
zq = zr[(zr.instrument == "ES") & zr.price_1.notna()].copy()
zt = pd.to_datetime(zq.ts_utc, utc=True).dt.tz_convert(None)
# session of the reference = session of its minute bar
bt = b.ts_event.dt.tz_convert(None).to_numpy()
bsd = b.sd.to_numpy()
jj = np.searchsorted(bt, zt.to_numpy(), "right") - 1
zq["sd"] = np.where(jj >= 0, bsd[np.maximum(jj, 0)], None)
zq["mo"] = zq.sd.astype(str).str[:7]


def month_table(mo):
    out = {}
    refs = zq[zq.mo == mo]
    refs = refs[refs.sd.isin(day_ix)]
    for tol in TOLS:
        hits = 0; n = 0; cov_w = []
        for sd, g in refs.groupby("sd"):
            lv = np.array(lf(day_ix[sd]), float)
            for p in g.price_1.astype(float):
                n += 1
                if len(lv) and np.abs(lv - p).min() <= tol:
                    hits += 1
        for sd in refs.sd.unique():
            lv = np.array(lf(day_ix[sd]), float)
            r = rng.loc[sd]
            span = r.hi - r.lo
            if span <= 0 or not len(lv):
                continue
            iv = [(max(p - tol, r.lo), min(p + tol, r.hi))
                  for p in lv if p + tol > r.lo and p - tol < r.hi]
            iv.sort()
            cov = 0.0; cur = None
            for a, b2 in iv:
                if cur is None or a > cur[1]:
                    if cur:
                        cov += cur[1] - cur[0]
                    cur = [a, b2]
                else:
                    cur[1] = max(cur[1], b2)
            if cur:
                cov += cur[1] - cur[0]
            cov_w.append(cov / span)
        out[tol] = (hits, n, float(np.mean(cov_w)) if cov_w else 0.0)
    return out


print()
print("# D8 STEP 1b — BLIND LEVEL PREDICTION (REPORT ONLY)")
print("hit = his stated zone price within TOL of a committed blind "
      "level, same session. null = share of session range covered "
      "by the level bands (chance line).")
print()
print("| month | refs | TOL 2.0 hit | null | TOL 1.0 hit | null | "
      "TOL 0.5 hit | null |")
print("|---|---|---|---|---|---|---|---|")
for mo in MONTHS_TRAIN + MONTHS_NEW:
    t = month_table(mo)
    h2, n2, c2 = t[2.0]; h1, n1, c1 = t[1.0]; h5, n5, c5 = t[0.5]
    if n2 == 0:
        print(f"| {mo} | 0 | - | - | - | - | - | - |")
        continue
    tag = " (NEW)" if mo in MONTHS_NEW else ""
    print(f"| {mo}{tag} | {n2} | {h2/n2:.0%} | {c2:.0%} | "
          f"{h1/n1:.0%} | {c1:.0%} | {h5/n5:.0%} | {c5:.0%} |")
