#!/usr/bin/env python3
"""
m11_study.py — T-MG18: where his exits land. Spec: M11_SPEC.md
(committed first).
RUN: python3 Tests/P5_trade_management/m11_study.py > Tests/P5_trade_management/M11_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
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

# shipped levels
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

wb = pd.read_parquet("Data/inputs/wrb_1m.parquet")
wb = wb[wb.body_size > wb.prior_body_max].copy()
wb["comp_s"] = (wb.ts_event.dt.tz_convert(None).astype("int64")
                // 10**9 + 60)
wb = wb.sort_values("comp_s")
wcs = wb.comp_s.to_numpy()
wbody = wb.body_size.to_numpy()

G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
G = G[G.entry_verified & G.exit_verified & G.exit_msg_s.notna()
      & np.isfinite(G.entry_price) & np.isfinite(G.exit_price)].copy()
G["sd_n"] = G.side.map({"long": 1, "short": -1})
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

PROJ = (0.5, 1.0, 1.618, 2.0)
fams = ("wrb_proj", "mdl_level", "intraday_edge", "round")
hits = {f: {0.5: 0, 1.0: 0} for f in fams}
nulls = {f: {0.5: [], 1.0: []} for f in fams}
n_tr = 0
fast_hits = {f: 0 for f in fams}
n_fast = 0
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < MONTHS[mo])
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    bsd = bm.sd.to_numpy()
    for _, r in G[G.month == mo].iterrows():
        t0, t1 = int(r.entry_msg_s), int(r.exit_msg_s)
        if t1 - t0 < 30:
            continue
        d = int(r.sd_n)
        # trigger WRB within 5 min before entry
        kw = int(np.searchsorted(wcs, t0, "right")) - 1
        B = None
        if kw >= 0 and t0 - wcs[kw] <= 300:
            B = float(wbody[kw])
        targets = {}
        targets["wrb_proj"] = ([r.entry_price + d * m_ * B
                                for m_ in PROJ] if B else [])
        k = int(np.searchsorted(bt, t0, "right")) - 1
        di = day_ix.get(bsd[k]) if k >= 0 else None
        targets["mdl_level"] = lf(di) if di else []
        t64 = np.datetime64(t0, "s")
        ied = []
        for fam in ("REA", "SQZ", "GAP", "SHD"):
            ied += list(edges_at(R, bsd[k], t64, fam))
        targets["intraday_edge"] = ied
        lo5 = np.floor(min(r.entry_price, r.exit_price) / 5) * 5 - 10
        targets["round"] = list(np.arange(lo5, lo5 + 40, 5.0)) + \
            list(np.arange(lo5 + 2.5, lo5 + 40, 5.0))
        # path range for the null
        j0 = int(np.searchsorted(secs, t0))
        j1 = int(np.searchsorted(secs, t1, "right"))
        if j1 - j0 < 10:
            continue
        path = mids[j0:j1]
        rnd = RNG.uniform(path.min(), path.max(), size=100)
        n_tr += 1
        fast = (t1 - t0) <= 150 and r.pnl_stated is not None and \
            np.isfinite(r.pnl_stated) and r.pnl_stated > 1
        if fast:
            n_fast += 1
        for f in fams:
            tg = np.array(targets[f], dtype=float)
            if not len(tg):
                continue
            dd_ = np.min(np.abs(tg - r.exit_price))
            for tol in (0.5, 1.0):
                if dd_ <= tol:
                    hits[f][tol] += 1
            if fast and dd_ <= 0.5:
                fast_hits[f] += 1
            nd = np.min(np.abs(tg[None, :] - rnd[:, None]), axis=1)
            for tol in (0.5, 1.0):
                nulls[f][tol].append((nd <= tol).mean())
print("# M11 REPORT — WHERE HIS EXITS LAND (T-MG18)")
print("STATUS: CLOSED | 2026-11-26 | Spec: M11_SPEC.md (committed "
      "first)")
print()
print(f"Audited exits analyzed: {n_tr} (fast-take subset, <=150s & "
      f">1pt: {n_fast}).")
print()
print("| target family | exits within 2 ticks | null | ratio | within "
      "1 pt | null | ratio |")
print("|---|---|---|---|---|---|---|")
for f in fams:
    e05 = hits[f][0.5] / n_tr
    n05 = np.mean(nulls[f][0.5]) if nulls[f][0.5] else np.nan
    e10 = hits[f][1.0] / n_tr
    n10 = np.mean(nulls[f][1.0]) if nulls[f][1.0] else np.nan
    print(f"| {f} | {e05:.0%} | {n05:.0%} | "
          f"{e05/max(n05,1e-9):.2f}x | {e10:.0%} | {n10:.0%} | "
          f"{e10/max(n10,1e-9):.2f}x |")
print()
print("## FAST-TAKE SUBSET (the pre-placed-limit suspects; within 2 "
      "ticks)")
for f in fams:
    print(f"- {f}: {fast_hits[f]}/{n_fast}")
print()
print("Verdict line: >= 1.5x null = destination evidence. "
      "Registry: T-MG18.")
