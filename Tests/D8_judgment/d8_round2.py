#!/usr/bin/env python3
"""
d8_round2.py — D-8 STEP 2: G2-6 (EN-02 x FL-WIN x MP-7) on the
quarantined months. FROZEN SPEC: D8_SPEC.md (+ J reporting
amendments). REPORT ONLY - J gives the verdict.
DERIVES FROM (R-9 lineage): Tests/D8_judgment/d8_round.py (T-VL05
machinery, control-passed) with tag "full"; reporting via
d8_report.py.
R-9 CONTROL (first, abort on miss): six training months from the
certified parts must reproduce the T-RH02 G2-6 baseline EXACTLY:
6267 trades, +1667.1 net, months +179/+311/+375/+232/+237/+333,
catch 58/61 vs the post-fix groups of record (T-RH03).
RUN: python3 Tests/D8_judgment/d8_round2.py             (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS_TRAIN = {"2021-09": "2021-10-01", "2022-02": "2022-03-01",
                "2023-05": "2023-06-01", "2024-05": "2024-06-01",
                "2024-11": "2024-12-01", "2025-10": "2025-11-01"}
MONTHS_NEW = {"2022-05": "2022-06-01", "2026-03": "2026-04-01"}
DISP, STOP, GRID = 1.25, 3.75, 0.25
CERT_PARTS = "Tests/D11_unmatched/parts"
NEW_PARTS = "Tests/D8_judgment/parts"

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
# ROLL SESSIONS (session-level: any flagged bar marks the session;
# the per-bar flag is mixed on roll days - F-40). Used to exclude
# TRADES; day indexing stays as certified.
ROLL_SDS = set(b.groupby("sd").is_roll_day.max()
                .loc[lambda s: s].index)
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

# ---- levels machinery (verbatim lf lineage) ----
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


def m7_var(exc, ts, best, W=8.0, A=None, stall=60):
    peak, tp, armed = 0.0, 0, False
    if A is None:
        arm = max(best - 0.75, 0.5) if (best is not None
                                        and best <= W) else None
    else:
        arm = A
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i
        if ts[i] - tp >= stall or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)


def run_ctrl(months, parts_dir):
    out = []
    for mo in months:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        C = pd.read_parquet(f"{parts_dir}/cand_full_{mo}.parquet")
        C = C.sort_values("tf", kind="stable")
        seen = set()
        busy = -10**12
        for r in C.itertuples():
            dk = (r.tf, r.e, r.d)
            if dk in seen:
                continue
            seen.add(dk)
            lvl = r.e + DISP * r.d
            di = day_ix.get(r.sd)
            # F-40: trades on roll SESSIONS are KEPT here - the
            # certified convention (bar-level structure exclusion
            # only; 2021-09's roll trades are inside every certified
            # baseline). Ex-roll subtotals are REPORTED; J decides
            # the convention question post-look.
            if di is None:
                continue
            if r.tf < busy:
                continue
            jf = int(r.jf)
            j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * r.d
            ts_ = (secs[jf:j4] - r.tf).astype(int)
            lv = lf(di) if di is not None else []
            ahead = sorted([(p - lvl) * r.d for p in lv
                            if (p - lvl) * r.d > 0.25])
            pnl, ix = m7_var(exc, ts_, ahead[0] if ahead else None)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, sd=r.sd, tf=int(r.tf),
                            d=int(r.d), pnl=float(pnl)))
    return pd.DataFrame(out)


# ---- R-9 CONTROL ----
tr = run_ctrl(MONTHS_TRAIN, CERT_PARTS)
exp_m = {"2021-09": 179, "2022-02": 311, "2023-05": 375,
         "2024-05": 232, "2024-11": 237, "2025-10": 333}
fails = []
if len(tr) != 6267 or abs(tr.pnl.sum() - 1667.1) > 0.1:
    fails.append(f"pooled {len(tr)}/{tr.pnl.sum():+.1f} != 6267/+1667.1")
for mo, e in exp_m.items():
    v = tr[tr.month == mo].pnl.sum()
    if abs(v - e) > 0.5:
        fails.append(f"{mo}: {v:+.1f} != {e:+d}")
L = pd.read_parquet("Data/inputs/his_groups_postfix.parquet")
POST_W = L[L.data_fresh & (L.ctx == "squeeze") & (L.np_ == "window")]
import importlib.util as _il
_sp = _il.spec_from_file_location("d8_report",
                                 "Tests/D8_judgment/d8_report.py")
rep = _il.module_from_spec(_sp); _sp.loader.exec_module(rep)
c_ = rep.catch_count(tr, POST_W)
if (c_, len(POST_W)) != (58, 61):
    fails.append(f"catch {c_}/{len(POST_W)} != 58/61 (T-RH03 record)")
if fails:
    print("# D8 ROUND2 ABORTED - R-9 CONTROL FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)
print("R-9 CONTROL PASS: G2-6 training baseline reproduced exactly "
      "(6267/+1667.1; months match; catch 58/61 post-fix)")

# ---- NEW MONTHS ----
HG = pd.read_parquet("Tests/D8_judgment/d8_his_groups.parquet")
HG2 = HG[HG.data_fresh & (HG.ctx == "squeeze") & (HG.np_ == "window")]
tn = run_ctrl(MONTHS_NEW, NEW_PARTS)
tn.to_parquet("Tests/D8_judgment/trades_g26_new.parquet", index=False)

out = open("Tests/D8_judgment/D8_STEP2_G26_REPORT.md", "w")
def P(s=""):
    print(s, file=out); print(s)
P("# D8 STEP 2 — G2-6 REPORT (REPORT ONLY; J's verdict)")
rep.card_table(P, tn, MONTHS_NEW, HG2,
               "reference (training, 6 months): 6267 trades, "
               "+1667.1, +0.27/trade, catch 58/61 (T-RH03)")
rep.his_rows(P, list(MONTHS_NEW), "G2 squeeze+news", HG2)
rep.daily_breakdown(P, tn, list(MONTHS_NEW))
P("catch denominators: 2022-05 G2=39, 2026-03 G2=21 (post-fix).")
out.close()
