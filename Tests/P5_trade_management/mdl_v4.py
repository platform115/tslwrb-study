#!/usr/bin/env python3
"""
mdl_v4.py — T-IM52: v4 grid = tolerance scaling x break handling.
Spec: MDL_SPEC.md v4 addendum (committed first).
RUN: python3 Tests/P5_trade_management/mdl_v4.py > Tests/P5_trade_management/MDL_V4_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets

RNG = np.random.default_rng(113)
GRID = 0.25

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b[~b.is_roll_day].sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days = sorted(b.sd.unique()); day_ix = {d: i for i, d in enumerate(days)}
closes = b.groupby("sd").close.last().reindex(days).to_numpy()
ev_t = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

def density_levels(px, di, nb, tol_fun, m):
    if not len(px):
        return []
    gp = np.round(px / GRID).astype(np.int64)
    lo, hi = gp.min(), gp.max()
    order = np.argsort(gp)
    gs, ds, nbs = gp[order], di[order], nb[order]
    uniq = np.arange(lo, hi + 1); score = np.zeros(len(uniq))
    widths = np.array([int(round(tol_fun(g0 * GRID) / GRID))
                       for g0 in uniq])
    for k, g0 in enumerate(uniq):
        a = np.searchsorted(gs, g0 - widths[k])
        b2 = np.searchsorted(gs, g0 + widths[k], "right")
        if b2 > a:
            score[k] = len(set(ds[a:b2])) + (1.0 if nbs[a:b2].any()
                                             else 0.0)
    out, taken = [], np.zeros(len(uniq), bool)
    for k in np.argsort(-score):
        if score[k] < m or taken[k]:
            continue
        out.append(float(uniq[k] * GRID))
        taken[max(0, k - 2 * widths[k]):k + 2 * widths[k] + 1] = True
    return out

# evidence (v3 recipe)
rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk = np.searchsorted(ev_t, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_t[np.maximum(kk, 0)]) <= 2700
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
for tfm in ("5min", "15min"):
    for sd, g in b.groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w_ = body > pm
        for o, c in zip(r.open.to_numpy()[w_], r.close.to_numpy()[w_]):
            rows.append(pd.DataFrame({"sd": [sd, sd],
                                      "px": [max(o, c), min(o, c)],
                                      "newsborn": [False, False]}))
E = pd.concat(rows, ignore_index=True)
E["px"] = (E.px * 4).round() / 4
E = E.drop_duplicates(["sd", "px"])
E["di"] = E.sd.map(day_ix); E = E.dropna(subset=["di"])
E["di"] = E.di.astype(int)
Epx, Edi, Enb = E.px.to_numpy(), E.di.to_numpy(), E.newsborn.to_numpy()

# actions-only teaching set (certified construction)
ep = pd.read_parquet("Data/inputs/tsl_episodes_clean.parquet")
act = []
for _, r in ep.iterrows():
    sd = str(r.trading_date) if pd.notna(r.trading_date) else None
    if sd is None or sd not in day_ix:
        continue
    for arr in (r.entry_prices, r.exit_prices):
        if arr is None:
            continue
        for p in np.atleast_1d(arr):
            if np.isfinite(p):
                act.append((sd, float(p)))
A = pd.DataFrame(act, columns=["sd", "px"])
A["px"] = (A.px * 4).round() / 4
A = A.drop_duplicates(["sd", "px"])
A["di"] = A.sd.map(day_ix).astype(int)
Apx, Adi = A.px.to_numpy(), A.di.to_numpy()
Anb = np.zeros(len(A), bool)
rev = {}
for di in range(70, len(days)):
    msk = (Adi >= di - 60) & (Adi < di + 1)
    rev[di] = density_levels(Apx[msk], Adi[msk], Anb[msk],
                             lambda p: 2.5, 3)
episodes, open_eps = [], []
for di in range(70, len(days)):
    today = rev[di]; matched = set()
    for e in open_eps:
        hit = [p for p in today if abs(p - e["px"]) <= 2.0]
        if hit:
            e["last"] = di; e["px"] = 0.8 * e["px"] + 0.2 * hit[0]
            matched.update(hit)
    episodes += [e for e in open_eps if di - e["last"] > 10]
    open_eps = [e for e in open_eps if di - e["last"] <= 10]
    for p in today:
        if p not in matched:
            open_eps.append(dict(px=p, first=di, last=di))
episodes += open_eps
REG = pd.DataFrame([e for e in episodes if e["last"] - e["first"] >= 5])

# the 62 for coverage
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
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = HIS62.merge(G, left_on=["month", "sec"],
                 right_on=["month", "entry_msg_s"], suffixes=("_f", ""))
GT["sd_n"] = GT.side.map({"long": 1, "short": -1})

TOLS = {"fixed2.0": lambda p: 2.0,
        "0.04%": lambda p: max(1.0, 0.0004 * p),
        "0.06%": lambda p: max(1.0, 0.0006 * p)}
print("# MDL V4 REPORT — SCALING x BREAK-HANDLING GRID (T-IM52)")
print("STATUS: CLOSED | 2026-11-26 | Spec: MDL v4 addendum (committed "
      "first)")
print()
print("| tolerance | break rule | recovery (actions-only) | levels/day "
      "| G2 coverage (level ahead) |")
print("|---|---|---|---|---|")
for tname, tf in TOLS.items():
    for brk in ("kill", "persist"):
        cache = {}
        def lf(di, tf=tf, brk=brk, cache=cache):
            if di not in cache:
                msk = (Edi >= di - 60) & (Edi < di)
                out = []
                for p in density_levels(Epx[msk], Edi[msk], Enb[msk],
                                        tf, 4):
                    if brk == "kill":
                        tol = tf(p)
                        sel = np.abs(Epx[msk] - p) <= tol
                        last_mem = int(Edi[msk][sel].max())
                        cseg = closes[last_mem + 1:di]
                        if (len(cseg)
                                and (np.abs(cseg - p) > 2.5 * tol).all()):
                            continue
                    out.append(p)
                cache[di] = out
            return cache[di]
        hit = tot = 0
        for _, r in REG.iterrows():
            tot += 1
            sample = np.unique(np.linspace(r["first"],
                               min(r["last"], len(days) - 1),
                               6).astype(int))
            if any(any(abs(l - r["px"]) <= 3.0 for l in lf(di))
                   for di in sample):
                hit += 1
        cov = 0
        for _, r in GT.iterrows():
            if not np.isfinite(r.entry_price):
                continue
            di = day_ix.get(r.session_date)
            lv = lf(di) if di else []
            if any((p - r.entry_price) * r.sd_n > 0.25 for p in lv):
                cov += 1
        med = int(np.median([len(lf(di)) for di in
                  RNG.choice(np.arange(70, len(days)), 20,
                             replace=False)]))
        print(f"| {tname} | {brk} | {hit}/{tot} ({hit/max(1,tot):.0%}) "
              f"| {med} | {cov}/62 |")
print()
print("Registry: T-IM52. Winner goes to the M7-scaled stage-1/joint "
      "rerun under the frozen bars.")
