#!/usr/bin/env python3
"""
g26_round.py — T-EN115: G2-6 (multi-family edges) vs control, six
months. Spec: G26_SPEC.md (frozen first). Per-minute edge memoization;
per-month candidate checkpoints (resume-safe).
RUN: python3 Tests/D11_unmatched/g26_round.py   (repeat until REPORT)
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

# ---------- per-month candidate generation, one pass per cell ----------
# ctrl: families exactly as certified engine (SQZ then W20, shared
# dedupe within that set only). full: SQZ, W20 first (same order),
# then GAP/SHD/REA/WRB/PDY. Generating per cell keeps the control
# free of cross-family dedupe suppression (cause of first R-9 abort).
JOBS = [(mo, nxt, tag) for mo, nxt in MONTHS.items()
        for tag in ("ctrl", "full")]
for mo, nxt, tag in JOBS:
    part = f"{PARTS}/cand_{tag}_{mo}.parquet"
    if os.path.exists(part):
        continue
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    secs = fl.sec.to_numpy(np.int64)
    mids = fl.mid.to_numpy(float)
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
    band_cache = {}
    memo = {}
    def fam_edges(fam, sd0, t):
        # comps verified minute-aligned -> per-minute memo is exact
        key = (fam, sd0, t // 60)
        if key not in memo:
            memo[key] = [float(e) for e in
                         edges_at(R, sd0, np.datetime64(t, "s"), fam)]
        return memo[key]
    def tail_edges(sd0, t, di):
        out = []
        for fam in ("GAP", "SHD", "REA"):
            out += [(fam, e) for e in fam_edges(fam, sd0, t)]
        if sd0 in wrb_day:
            out += [("WRB", p) for c_, p in wrb_day[sd0] if c_ <= t]
        if di is not None and di >= 1 and np.isfinite(pd_hi[di - 1]):
            out += [("PDY", float(p)) for p in
                    (pd_hi[di - 1], pd_lo[di - 1], pd_cl[di - 1])]
        return out
    cands = []
    for es in evm:
        es = int(es)
        j0 = int(np.searchsorted(secs, es + 300))
        j1 = int(np.searchsorted(secs, es + 2700, "right"))
        if j1 - j0 < 60:
            continue
        kb = int(np.searchsorted(bt, secs[j0], "right")) - 1
        if kb < 0 or not rth[kb]:
            continue
        sd0 = sd1[kb]
        di = day_ix.get(sd0)
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        last_fire = {}
        for jj in range(max(j0, 1), j1):
            t = int(secs[jj])
            E = [("SQZ", e) for e in fam_edges("SQZ", sd0, t)]
            ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
            if ki >= 0 and np.isfinite(blo[ki]):
                E += [("W20", blo[ki]), ("W20", bhi[ki])]
            if tag == "full":
                E += tail_edges(sd0, t, di)
            px, prev = mids[jj], mids[jj - 1]
            for fam, e in E:
                dd = 1 if (prev <= e < px) else \
                    (-1 if (prev >= e > px) else 0)
                if dd == 0:
                    continue
                key = (round(e, 2), dd)
                if t - last_fire.get(key, -10**9) <= DEDUP:
                    continue
                last_fire[key] = t
                lvl = e + DISP * dd
                j3 = int(np.searchsorted(secs, t + TTL, "right"))
                seg2 = mids[jj:j3]
                hit = np.flatnonzero((seg2 >= lvl) if dd > 0
                                     else (seg2 <= lvl))
                if len(hit):
                    jf = jj + int(hit[0])
                    cands.append((sd0, int(secs[jf]), dd, key[0],
                                  jf, fam))
                j9 = int(np.searchsorted(secs, t + 600, "right"))
                seg = (mids[jj:j9] - e) * dd
                gate = np.flatnonzero(seg >= 1.0)
                if len(gate):
                    jg = int(gate[0])
                    back = np.flatnonzero(seg[jg:] <= 0.75)
                    if len(back):
                        jt = jj + jg + int(back[0])
                        tt_ = int(secs[jt])
                        j3b = int(np.searchsorted(secs, tt_ + TTL,
                                                  "right"))
                        s2b = mids[jt:j3b]
                        hb = np.flatnonzero((s2b >= lvl) if dd > 0
                                            else (s2b <= lvl))
                        if len(hb):
                            jfb = jt + int(hb[0])
                            cands.append((sd0, int(secs[jfb]), dd,
                                          key[0], jfb, fam))
    pd.DataFrame(cands, columns=["sd", "tf", "d", "e", "jf", "fam"]
                 ).to_parquet(part, index=False)
    print(f"{tag} {mo}: {len(cands)} candidates", flush=True)
    if time.time() - T0 > 480:
        print("CONTINUE (rerun to finish remaining months)")
        sys.exit(0)

# ---------- simulate both cells ----------
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
HISG2 = F[(F.ctx == "squeeze") & (F.np_ == "window")]

def run_cell(tag):
    out = []
    for mo in MONTHS:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        C = pd.read_parquet(f"{PARTS}/cand_{tag}_{mo}.parquet")
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
            ahead = sorted([(p - lvl) * r.d for p in lv
                            if (p - lvl) * r.d > 0.25])
            pnl, ix = m7(exc, ts_, ahead[0] if ahead else None)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl), fam=r.fam))
    return pd.DataFrame(out)

CTRL = run_cell("ctrl")
G26 = run_cell("full")
CTRL.to_parquet(f"{PARTS}/trades_ctrl.parquet", index=False)
G26.to_parquet(f"{PARTS}/trades_full.parquet", index=False)

# R-9 control
fails = []
for pair, (n_e, p_e) in {("2022-02", "2025-10"): (757, 325.1),
                         ("2023-05", "2024-05"): (760, 158.1)}.items():
    sub = CTRL[CTRL.month.isin(pair)]
    if not (len(sub) == n_e and abs(sub.pnl.sum() - p_e) < 0.1):
        fails.append(f"CONTROL {pair}: {len(sub)}/"
                     f"{sub.pnl.sum():+.1f} != {n_e}/{p_e:+.1f}")
if fails:
    print("# G26 RUN ABORTED — R-9 FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

def catchline(tr):
    tot = c62 = cAll = nAll = 0
    for mo in ("2021-09", "2022-02", "2024-11", "2025-10"):
        H = HISG2[HISG2.month == mo]
        nAll += len(H)
        for _, h in H.iterrows():
            hit = len(tr[(tr.month == mo) & (tr.d == h.side)
                         & (abs(tr.tf - h.sec) <= 300)]) > 0
            cAll += hit
            if mo in ("2022-02", "2025-10"):
                tot += 1
                c62 += hit
    return c62, tot, cAll, nAll

rep = open("Tests/D11_unmatched/G26_REPORT.md", "w")
def P(s=""):
    print(s, file=rep)
P("# G26 REPORT — G2-6 MULTI-FAMILY vs CONTROL, SIX MONTHS (T-EN115)")
P("STATUS: CLOSED | 2026-11-27 | Spec: G26_SPEC.md (frozen first) | "
  "R-9 CONTROL exact on both certified pairs")
P()
P("| cell | trades | per-trade | pooled | by month "
  "(21-09/22-02/23-05/24-05/24-11/25-10) | catch62 | catch-all-4mo | "
  "extras net |")
P("|---|---|---|---|---|---|---|---|")
for name, tr in (("CONTROL (G2-4)", CTRL), ("G2-6", G26)):
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    pooled = tr.pnl.sum()
    c62, t62, cA, nA = catchline(tr)
    near = np.zeros(len(tr), bool)
    for mo in ("2021-09", "2022-02", "2024-11", "2025-10"):
        for _, h in HISG2[HISG2.month == mo].iterrows():
            near |= ((tr.month == mo).to_numpy()
                     & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = tr.pnl[~near].sum()
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in MONTHS)
    P(f"| {name} | {len(tr)} | {pooled/max(1,len(tr)):+.2f} | "
      f"{pooled:+.1f} | {bym} | {c62}/{t62} | {cA}/{nA} | {exn:+.1f} |")
P()
P("## PER-FAMILY ATTRIBUTION (G2-6 cell; toxicity screen)")
P("| family | trades | net | per-trade | months net<0 |")
P("|---|---|---|---|---|")
for fam, g in G26.groupby("fam"):
    mn = sum(1 for mo in MONTHS
             if g[g.month == mo].pnl.sum() < 0)
    tox = " TOXIC-FLAG" if mn >= 4 else ""
    P(f"| {fam} | {len(g)} | {g.pnl.sum():+.1f} | "
      f"{g.pnl.sum()/max(1,len(g)):+.2f} | {mn}/6{tox} |")
P()
P("Registry: T-EN115.")
rep.close()
print("REPORT WRITTEN")
