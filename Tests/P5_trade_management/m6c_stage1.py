#!/usr/bin/env python3
"""
m6c_stage1.py — T-MG14: M6C stage 1 - snap/limit at COMPUTED multi-day
levels (MDL v3 best cell). Live-computable end to end; his words
nowhere in the rule. Spec: M6C_SPEC.md stage 1 + MDL_SPEC.md.
RUN: python3 Tests/P5_trade_management/m6c_stage1.py > Tests/P5_trade_management/M6C_S1_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets
from p4_66_context_ablation import prep

RNG = np.random.default_rng(113)
GRID, W, TOL, MSC, KILL = 0.25, 60, 2.0, 4, 5.0
MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
STOP = 3.75

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b[~b.is_roll_day].sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days = sorted(b.sd.unique()); day_ix = {d: i for i, d in enumerate(days)}
closes = b.groupby("sd").close.last().reindex(days).to_numpy()
ev_t = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

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
            score[k] = len(set(ds[a:b2])) + (1.0 if nbs[a:b2].any() else 0.0)
    out, taken = [], np.zeros(len(uniq), bool)
    for k in np.argsort(-score):
        if score[k] < m or taken[k]:
            continue
        out.append(float(uniq[k] * GRID))
        taken[max(0, k - 2 * width):k + 2 * width + 1] = True
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
cache = {}
def lf(di):
    if di not in cache:
        msk = (Edi >= di - W) & (Edi < di)
        out = []
        for p in density_levels(Epx[msk], Edi[msk], Enb[msk], TOL, MSC):
            last_mem = int(Edi[msk][np.abs(Epx[msk] - p) <= TOL].max())
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - p) > KILL).all()):
                out.append(p)
        cache[di] = out
    return cache[di]

def m3a(exc, ts):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if exc[i] <= -STOP:
            return -STOP, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

def snap(exc, ts, arm):
    peak, tp, armed = 0.0, 0, False
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

def limitx(exc, ts, tgt):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if tgt is not None and exc[i] >= tgt:
            return tgt, i
        if exc[i] <= -STOP:
            return -STOP, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

# his 62
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window", "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec", "side"]]
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = HIS62.merge(G, left_on=["month", "sec"],
                 right_on=["month", "entry_msg_s"], suffixes=("_f", ""))
GT["sd_n"] = GT.side.map({"long": 1, "short": -1})

print("# M6C STAGE 1 — COMPUTED-LEVEL SNAP (LIVE-COMPUTABLE) (T-MG14)")
print("STATUS: CLOSED | 2026-11-26 | detector = MDL v3 best cell; his "
      "words nowhere in the rule")
print()
REACH = (3.0, 5.0, 8.0)
res = {f"{k} reach{a}": [] for k in ("snap", "limit") for a in REACH}
res["M3A baseline"] = []
nlev = []
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not np.isfinite(r.entry_price):
            continue
        di = day_ix.get(r.session_date)
        lv = lf(di) if di else []
        ahead = sorted([(p - r.entry_price) * r.sd_n for p in lv
                        if (p - r.entry_price) * r.sd_n > 0.25])
        best = ahead[0] if ahead else None
        nlev.append(best is not None)
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.sd_n
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        for a in REACH:
            arm = max(best - 0.75, 0.5) if (best is not None and best <= a) else None
            tgt = max(best - 0.25, 0.5) if (best is not None and best <= a) else None
            res[f"snap reach{a}"].append(snap(exc, ts, arm)[0])
            res[f"limit reach{a}"].append(limitx(exc, ts, tgt)[0])
        res["M3A baseline"].append(m3a(exc, ts)[0])
print(f"Trades with a computed level ahead: {int(np.sum(nlev))}/62.")
print()
print("## STAGE 1 — HIS 62 FILLS (qualify: net > +123.9; his-labels "
      "stage 0 scored +127.8/+129.0)")
print("| candidate | net | win | avg win/loss | worst | share of his |")
print("|---|---|---|---|---|---|")
quals = []
for n in res:
    a = np.array(res[n])
    w = a > 0
    al = a[~w].mean() if (~w).any() else 0.0
    print(f"| {n} | {a.sum():+.1f} | {w.mean():.0%} | +{a[w].mean():.2f}"
          f" / {al:.2f} | {a.min():+.2f} | {a.sum()/231.2:.0%} |")
    if a.sum() > 123.9 and n != "M3A baseline":
        quals.append((a.sum(), n))
print()
print(f"Qualifiers: {sorted(quals, reverse=True) if quals else 'NONE'}")
print("Registry: T-MG14. (Joint stage follows only on a qualifier, "
      "per the frozen two-stage bars.)")
