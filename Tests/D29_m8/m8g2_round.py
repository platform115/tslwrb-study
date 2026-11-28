#!/usr/bin/env python3
"""
m8g2_round.py — T-MG28, G2 line: M8 family-edge capture targets on
G2-4 and G2-6 (six months). Spec: Tests/D29_m8/M8_SPEC.md (frozen
first). Machinery verbatim from the certified g26_round (T-EN115);
cand parquets reused.
RUN: python3 Tests/D29_m8/m8g2_round.py > Tests/D29_m8/M8G2_REPORT.md
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

CTRL4 = run_cell_m8("ctrl", None)
fails = []
if not (len(CTRL4) == 2126 and abs(CTRL4.pnl.sum() - 565.9) < 0.1):
    fails.append(f"G2-4 control {len(CTRL4)}/{CTRL4.pnl.sum():+.1f}")
CTRL6 = run_cell_m8("full", None)
if not (len(CTRL6) == 6252 and abs(CTRL6.pnl.sum() - 1659.0) < 0.1):
    fails.append(f"G2-6 control {len(CTRL6)}/{CTRL6.pnl.sum():+.1f}")
if fails:
    print("# M8G2 ABORTED — R-9 FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

print("# M8G2 REPORT — M8 ON THE G2 LINE (T-MG28)")
print("STATUS: CLOSED | 2026-11-27 | Spec: Tests/D29_m8/M8_SPEC.md "
      "(frozen first) | controls exact (2126/+565.9; 6252/+1659.0) "
      "| mechanism-primary | six months")
print()
print("| strategy | cell | trades | per-trade | pooled | by month "
      "(21-09/22-02/23-05/24-05/24-11/25-10) |")
print("|---|---|---|---|---|---|")
cells = {}
for sname, tag, base in (("G2-4", "ctrl", CTRL4),
                         ("G2-6", "full", CTRL6)):
    nets = {mo: base[base.month == mo].pnl.sum() for mo in MONTHS}
    print(f"| {sname} | M7 baseline | {len(base)} | "
          f"{base.pnl.mean():+.2f} | {base.pnl.sum():+.1f} | "
          f"{'/'.join(f'{nets[mo]:+.0f}' for mo in MONTHS)} |")
    dmins = (2.0, 1.0, 3.0, 0.25) if sname == "G2-4" else (2.0,)
    for dmin in dmins:
        tr = run_cell_m8(tag, dmin)
        cells[(sname, dmin)] = tr
        nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
        tagc = " FROZEN" if dmin == 2.0 else ""
        print(f"| {sname} | M8 D={dmin}{tagc} | {len(tr)} | "
              f"{tr.pnl.mean():+.2f} | {tr.pnl.sum():+.1f} | "
              f"{'/'.join(f'{nets[mo]:+.0f}' for mo in MONTHS)} |")
print()
print("## MECHANISM (twin-matched; busy-freed separate)")
print("| strategy | D_min | changed | twin delta pooled | months "
      "delta>=0 | busy add/drop (net) |")
print("|---|---|---|---|---|---|")
vb = None
for sname, base in (("G2-4", CTRL4), ("G2-6", CTRL6)):
    bk = base.drop_duplicates(["month", "tf"]).set_index(
        ["month", "tf"])
    dmins = (2.0, 1.0, 3.0, 0.25) if sname == "G2-4" else (2.0,)
    for dmin in dmins:
        tr = cells[(sname, dmin)]
        tk = tr.drop_duplicates(["month", "tf"]).set_index(
            ["month", "tf"])
        shared = bk.index.intersection(tk.index)
        d_ = (tk.loc[shared].pnl - bk.loc[shared].pnl)
        ch = d_[d_.abs() > 1e-9]
        chm = {mo: ch[[i for i in ch.index if i[0] == mo]].sum()
               for mo in MONTHS}
        okm = sum(1 for v in chm.values() if v >= 0)
        add = tk.index.difference(bk.index)
        drop = bk.index.difference(tk.index)
        addp = tk.loc[add].pnl.sum() if len(add) else 0.0
        dropp = bk.loc[drop].pnl.sum() if len(drop) else 0.0
        print(f"| {sname} | {dmin} | {len(ch)} | {ch.sum():+.1f} | "
              f"{okm}/6 | {len(add)}/{len(drop)} "
              f"({addp - dropp:+.1f}) |")
        if sname == "G2-4" and dmin == 2.0:
            vb = dict(ch=ch.sum(), okm=okm, tr=tr, chm=chm)
print()
tr = vb["tr"]
pooled = tr.pnl.sum()
wm = min(tr[tr.month == mo].pnl.sum() for mo in MONTHS)
print("## VERDICT vs THE FROZEN LINES (G2 line: G2-4xM8, D=2.0)")
print(f"- controls exact: PASS")
print(f"- twin delta > 0 pooled AND >= 0 in >= 4/6 months: "
      f"{'PASS' if (vb['ch'] > 0 and vb['okm'] >= 4) else 'FAIL'} "
      f"({vb['ch']:+.1f}; {vb['okm']}/6)")
print(f"- full cell > +565.9: "
      f"{'PASS' if pooled > 565.9 else 'FAIL'} ({pooled:+.1f})")
print(f"- worst month > -10: "
      f"{'PASS' if wm > -10 else 'FAIL'} ({wm:+.1f})")
ok = (vb["ch"] > 0 and vb["okm"] >= 4 and pooled > 565.9
      and wm > -10)
print(f"G2-LINE VERDICT: "
      f"{'ADOPT-AS-CANDIDATE - J gates' if ok else 'facts to J'}")
print()
print("Registry: T-MG28 (G2 arm).")
