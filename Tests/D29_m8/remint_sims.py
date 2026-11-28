#!/usr/bin/env python3
"""
remint_sims.py — T-RH02: baseline re-mint under fixed stamps (F-36).
Every resolver-fed system re-simulated on parts_v2 candidates; OLD
registered numbers vs NEW, month-level, with catch. Engine verbatim
from the certified m8ab/m8g2/g3rwy lineage (no R-9 asserts here BY
DESIGN: this run MINTS the new baselines; the old asserts are stale
by the stamp fix - documented in BACKTEST_MATRIX).
RUN: python3 Tests/D29_m8/remint_sims.py > Tests/D29_m8/REMINT_REPORT.md
"""
# STALE-LINEAGE NOTE (2026-11-28, F-36/T-RH02): this CLOSED round
# ran on pre-stamp-fix baselines; its hardcoded R-9 asserts are
# stale by design. Re-running requires re-pointing them to the
# T-RH02 baselines. Its registered conclusions are annotated in
# BACKTEST_MATRIX.

import os, sys, time
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

T0 = time.time()
MONTHS = {"2021-09": "2021-10-01", "2022-02": "2022-03-01",
          "2023-05": "2023-06-01", "2024-05": "2024-06-01",
          "2024-11": "2024-12-01", "2025-10": "2025-11-01"}
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25
PARTS = "Tests/D11_unmatched/parts"
os.makedirs(PARTS, exist_ok=True)

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
pd_cl = rth_b.groupby("sd").close.last().reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

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

# WRB body edges per sd with completion times (knowable <= t)
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
for sd in wrb_day:
    wrb_day[sd].sort()

# levels machinery (shipped, for M7)
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

def m7(exc, ts, best):
    peak, tp, armed = 0.0, 0, False
    arm = max(best - 0.75, 0.5) if (best is not None and best <= 8.0) \
        else None
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

# ---------- resolver machinery for fill-time family edges ----------
RES = {}
for mo, nxt in MONTHS.items():
    bm_ = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
            ].reset_index(drop=True)
    RES[mo] = Resolver(bm_, zr)
memo_f = {}
def fam_edges_all(mo, sd0, t, di):
    key = (mo, sd0, t // 60)
    if key not in memo_f:
        out = []
        for fam in ("SQZ", "GAP", "SHD", "REA"):
            out += [float(e) for e in
                    edges_at(RES[mo], sd0, np.datetime64(t, "s"),
                             fam)]
        if sd0 in wrb_day:
            out += [p for c_, p in wrb_day[sd0] if c_ <= t]
        if di is not None and di >= 1 and np.isfinite(pd_hi[di - 1]):
            out += [float(pd_hi[di - 1]), float(pd_lo[di - 1]),
                    float(pd_cl[di - 1])]
        memo_f[key] = sorted(set(out))
    return memo_f[key]

def run_cell_m8(tag, dmin):
    """Certified T-EN115 sim; dmin None -> M7 baseline; else the
    capture-target union per M8_SPEC."""
    out = []
    for mo in MONTHS:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        C = pd.read_parquet(
            f"Tests/D11_unmatched/parts/cand_{tag}_{mo}.parquet")
        C = C.sort_values("tf", kind="stable")
        seen = set()
        busy = -10**12
        for r in C.itertuples():
            dk = (r.tf, r.e, r.d)
            if dk in seen:
                continue
            seen.add(dk)
            if r.tf < busy:
                continue
            lvl = r.e + DISP * r.d
            jf = int(r.jf)
            j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * r.d
            ts_ = (secs[jf:j4] - r.tf).astype(int)
            di = day_ix.get(r.sd)
            lv = lf(di) if di is not None else []
            ahead = [(p - lvl) * r.d for p in lv
                     if (p - lvl) * r.d > 0.25]
            if dmin is not None and di is not None:
                fe = fam_edges_all(mo, r.sd, int(r.tf), di)
                ahead += [(p - lvl) * r.d for p in fe
                          if (p - lvl) * r.d >= dmin]
            ahead = sorted(ahead)
            pnl, ix = m7(exc, ts_, ahead[0] if ahead else None)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl), fam=r.fam))
    return pd.DataFrame(out)

def m7_var(exc, ts, best, W=8.0, A=None, stall=60):
    """M7 with dials: arm window W (levels), or fixed-trail arm A
    (targets ignored), stall length."""
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

def run_cell_dial(tag, dmin=None, W=8.0, A=None, stall=60):
    out = []
    for mo in MONTHS:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        C = pd.read_parquet(
            f"Tests/D11_unmatched/parts/cand_{tag}_{mo}.parquet")
        C = C.sort_values("tf", kind="stable")
        seen = set()
        busy = -10**12
        for r in C.itertuples():
            dk = (r.tf, r.e, r.d)
            if dk in seen:
                continue
            seen.add(dk)
            if r.tf < busy:
                continue
            lvl = r.e + DISP * r.d
            jf = int(r.jf)
            j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * r.d
            ts_ = (secs[jf:j4] - r.tf).astype(int)
            di = day_ix.get(r.sd)
            lv = lf(di) if di is not None else []
            ahead = [(p - lvl) * r.d for p in lv
                     if (p - lvl) * r.d > 0.25]
            if dmin is not None and di is not None:
                fe = fam_edges_all(mo, r.sd, int(r.tf), di)
                ahead += [(p - lvl) * r.d for p in fe
                          if (p - lvl) * r.d >= dmin]
            ahead = sorted(ahead)
            pnl, ix = m7_var(exc, ts_,
                             ahead[0] if ahead else None,
                             W=W, A=A, stall=stall)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl)))
    return pd.DataFrame(out)

PDIR = {"ctrl": "Tests/D11_unmatched/parts_v2",
        "full": "Tests/D11_unmatched/parts_v2",
        "quiet": "Tests/D5_quiet/parts_v2"}

def run_cell2(tag, A=None, dmin=None, band=None):
    out = []
    for mo in MONTHS:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        C = pd.read_parquet(f"{PDIR[tag]}/cand_{tag}_{mo}.parquet")
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
            if band is not None:
                if di is None:
                    continue
                fe = fam_edges_all(mo, r.sd, int(r.tf), di)
                ah = [(p - lvl) * r.d for p in fe
                      if (p - lvl) * r.d > 0.5]
                R_ = min(ah) if ah else np.inf
                if not (band[0] <= R_ <= band[1]):
                    continue
            if r.tf < busy:
                continue
            jf = int(r.jf)
            j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * r.d
            ts_ = (secs[jf:j4] - r.tf).astype(int)
            lv = lf(di) if di is not None else []
            ahead = [(p - lvl) * r.d for p in lv
                     if (p - lvl) * r.d > 0.25]
            if dmin is not None and di is not None:
                fe = fam_edges_all(mo, r.sd, int(r.tf), di)
                ahead += [(p - lvl) * r.d for p in fe
                          if (p - lvl) * r.d >= dmin]
            ahead = sorted(ahead)
            pnl, ix = m7_var(exc, ts_,
                             ahead[0] if ahead else None, A=A)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl)))
    return pd.DataFrame(out)

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm_ = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm_) & (mm_ <= 5), "burst",
                    np.where(np.isfinite(mm_) & (mm_ <= 45),
                             "window", "none"))
def ctx_row(r):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f_}_interact"]:
            return "squeeze" if f_ == "SQZ" else "other"
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HISW = F[(F.ctx == "squeeze") & (F.np_ == "window")]
HISQ = F[(F.ctx == "squeeze") & (F.np_ == "none")]

def catch(tr, H):
    c = 0
    for _, h in H.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            c += 1
    return c

OLD = {
 "G2-4 (EN-01xWINxMP-7)": (2126, 565.9, "48/62"),
 "G2-6 (EN-02xWINxMP-7)": (6252, 1659.0, "59/62"),
 "G2-7 (EN-01xWINxMP-9)": (2370, 858.1, "-"),
 "G2-9 (EN-01xWINxMP-8)": (2400, 824.8, "-"),
 "G2-10 (EN-02xWINxMP-9)": (8153, 2644.0, "-"),
 "G2-8 (EN-02xWINxMP-8)": (8383, 2670.0, "-"),
 "G2-11 (G2-6+RWY)": (1212, 627.2, "-"),
 "G3-1 (EN-02xQTxMP-7)": (19008, 3689.4, "150/151"),
 "G3-2 (EN-02xQTxMP-9)": (23941, 5727.8, "150/151"),
 "G3-3 (G3-2+RWY)": (3843, 1944.4, "88/151"),
 "G3-4 (G3-1+RWY)": (3159, 1186.4, "82/151"),
}
CELLS = [
 ("G2-4 (EN-01xWINxMP-7)", "ctrl", dict(), HISW),
 ("G2-6 (EN-02xWINxMP-7)", "full", dict(), HISW),
 ("G2-7 (EN-01xWINxMP-9)", "ctrl", dict(A=1.5), None),
 ("G2-9 (EN-01xWINxMP-8)", "ctrl", dict(dmin=2.0), None),
 ("G2-10 (EN-02xWINxMP-9)", "full", dict(A=1.5), None),
 ("G2-8 (EN-02xWINxMP-8)", "full", dict(dmin=2.0), None),
 ("G2-11 (G2-6+RWY)", "full", dict(band=(2.0, 8.0)), None),
 ("G3-1 (EN-02xQTxMP-7)", "quiet", dict(), HISQ),
 ("G3-2 (EN-02xQTxMP-9)", "quiet", dict(A=1.5), HISQ),
 ("G3-3 (G3-2+RWY)", "quiet", dict(A=1.5, band=(2.0, 8.0)), HISQ),
 ("G3-4 (G3-1+RWY)", "quiet", dict(band=(2.0, 8.0)), HISQ),
]
print("# REMINT_REPORT — NEW BASELINES UNDER FIXED STAMPS (T-RH02)")
print("STATUS: CLOSED | 2026-11-28 | basis: F-36 stamp fix (harness-"
      "certified 0/240); candidates regenerated (parts_v2); engines "
      "verbatim from certified lineage; OLD asserts stale BY DESIGN "
      "- this run mints the new numbers. Months-spend: nothing new "
      "(R-11); same six months, training-side.")
print()
print("| system | OLD n/net | NEW n/net | NEW per-trade | NEW by "
      "month (21-09/22-02/23-05/24-05/24-11/25-10) | NEW catch | "
      "delta net |")
print("|---|---|---|---|---|---|---|")
news = {}
for name, tag, kw, H in CELLS:
    tr = run_cell2(tag, **kw)
    news[name] = tr
    on, op, oc = OLD[name]
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in MONTHS)
    c = f"{catch(tr, H)}/{len(H)}" if H is not None else "-"
    print(f"| {name} | {on}/{op:+.1f} | {len(tr)}/"
          f"{tr.pnl.sum():+.1f} | {tr.pnl.mean():+.2f} | {bym} | "
          f"{c} | {tr.pnl.sum()-op:+.1f} |")
print()
print("(5W-RWY and S5-MF re-mints run separately on the touch "
      "engine; reported alongside.)")
print()
print("Registry: T-RH02.")
