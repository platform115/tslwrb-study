#!/usr/bin/env python3
"""
g3rwy_round.py — T-EN117: the frozen RWY selector on the volume
lines. Spec: RWYV_SPEC.md (frozen first). Engine verbatim from the
certified m8ab/m8g2 lineage; quiet candidates from T-EN116 parts.
RUN: python3 Tests/D5_quiet/g3rwy_round.py > Tests/D5_quiet/RWYV_REPORT.md
"""
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

PDIR = {"ctrl": "Tests/D11_unmatched/parts",
        "full": "Tests/D11_unmatched/parts",
        "quiet": "Tests/D5_quiet/parts"}

def run_cell2(tag, A=None, band=None):
    """m8ab's certified sim; A=None -> M7, else M9 arm A; band ->
    runway admit gate (lo, hi) measured at fill vs entry price."""
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
            ahead = sorted([(p - lvl) * r.d for p in lv
                            if (p - lvl) * r.d > 0.25])
            pnl, ix = m7_var(exc, ts_,
                             ahead[0] if ahead else None, A=A)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl), fam=r.fam))
    return pd.DataFrame(out)

fails = []
B32 = run_cell2("quiet", A=1.5)
if not (len(B32) == 24017 and abs(B32.pnl.sum() - 5973.1) < 0.1):
    fails.append(f"G3-2 base {len(B32)}/{B32.pnl.sum():+.1f}")
B31 = run_cell2("quiet")
if not (len(B31) == 19015 and abs(B31.pnl.sum() - 3767.8) < 0.1):
    fails.append(f"G3-1 base {len(B31)}/{B31.pnl.sum():+.1f}")
B26 = run_cell2("full")
if not (len(B26) == 6267 and abs(B26.pnl.sum() - 1667.1) < 0.1):
    fails.append(f"G2-6 base {len(B26)}/{B26.pnl.sum():+.1f}")
if fails:
    print("# RWYV ABORTED — R-9 FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f_}_interact"]:
            return "squeeze" if f_ == "SQZ" else "other"
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HISG3 = F[(F.ctx == "squeeze") & (F.np_ == "none")]

def row(name, tr):
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    caught = 0
    for _, h in HISG3.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            caught += 1
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in MONTHS)
    print(f"| {name} | {len(tr)} | "
          f"{tr.pnl.sum()/max(1,len(tr)):+.2f} | {tr.pnl.sum():+.1f}"
          f" | {bym} | {caught}/{len(HISG3)} |")
    return nets

print("# RWYV REPORT — THE RWY SELECTOR ON THE VOLUME LINES "
      "(T-EN117)")
print("STATUS: CLOSED | 2026-11-27 | Spec: RWYV_SPEC.md (frozen "
      "first) | controls exact (all three baselines) | band [2,8] "
      "carried frozen from T-SR05 | TRAINING-ONLY")
print()
print("| cell | trades | per-trade | pooled | by month | catch-G3 |")
print("|---|---|---|---|---|---|")
row("G3-2 baseline", B32)
V = run_cell2("quiet", A=1.5, band=(2.0, 8.0))
nets_v = row("G3-2-RWY[2,8] VERDICT", V)
row("G3-2-RWY[1.5,8]", run_cell2("quiet", A=1.5, band=(1.5, 8.0)))
row("G3-2-RWY[2,10]", run_cell2("quiet", A=1.5, band=(2.0, 10.0)))
row("G3-1 baseline", B31)
row("G3-1-RWY[2,8]", run_cell2("quiet", band=(2.0, 8.0)))
row("G2-6 baseline", B26)
row("G2-6-RWY[2,8]", run_cell2("full", band=(2.0, 8.0)))
print()
print("## PER-FAMILY (G3-2-RWY)")
print("| family | trades | net | per-trade | months net<0 |")
print("|---|---|---|---|---|")
toxbad = False
for fam, g in V.groupby("fam"):
    mn = sum(1 for mo in MONTHS if g[g.month == mo].pnl.sum() < 0)
    if mn >= 4:
        toxbad = True
    print(f"| {fam} | {len(g)} | {g.pnl.sum():+.1f} | "
          f"{g.pnl.sum()/max(1,len(g)):+.2f} | {mn}/6"
          f"{' TOXIC-FLAG' if mn >= 4 else ''} |")
print()
pt = V.pnl.sum() / max(1, len(V))
allpos = all(v > 0 for v in nets_v.values())
print("## VERDICT vs THE FROZEN LINES (G3-2-RWY[2,8])")
print(f"- controls exact: PASS")
print(f"- per-trade >= +0.45: {'PASS' if pt >= 0.45 else 'FAIL'} "
      f"({pt:+.2f})")
print(f"- n >= 500: {'PASS' if len(V) >= 500 else 'FAIL'} "
      f"({len(V)})")
print(f"- all six months > 0: {'PASS' if allpos else 'FAIL'}")
print(f"- no unflagged toxic family: "
      f"{'FLAGGED' if toxbad else 'PASS'}")
ok = (pt >= 0.45 and len(V) >= 500 and allpos and not toxbad)
print(f"OVERALL: "
      f"{'REGISTER QUALITY-VARIANT - J gates' if ok else 'PARTIAL - facts to J'}")
print()
print("Registry: T-EN117.")
