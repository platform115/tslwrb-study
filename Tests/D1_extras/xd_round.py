#!/usr/bin/env python3
"""
xd_round.py — T-XD01: D-1 extras decomposition. Spec: XD_SPEC.md
(committed first). R-9: double control arm aborts on mismatch.
RUN: python3 Tests/D1_extras/xd_round.py > Tests/D1_extras/XD_REPORT.md
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2022-02": "2022-03-01", "2025-10": "2025-11-01",
          "2023-05": "2023-06-01", "2024-05": "2024-06-01"}
EXPECT = {("2022-02", "2025-10"): (757, 325.1),
          ("2023-05", "2024-05"): (760, 158.1)}
BOOKFILE = {"2022-02": "book_per_sec_2022-02.parquet",
            "2025-10": "book_per_sec_2025-10.parquet",
            "2023-05": "book_top_per_sec_2023-05.parquet",
            "2024-05": "book_top_per_sec_2024-05.parquet"}
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25

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
day_rng = pd_hi - pd_lo
NS = news_sets(".")
ev_all = np.asarray(NS["all"], dtype=np.int64) // 10**9
t20 = set((np.asarray(NS[">=20tk"], dtype=np.int64) // 10**9).tolist())
t45 = set((np.asarray(NS[">=45tk"], dtype=np.int64) // 10**9).tolist())
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

def m7tag(exc, ts, best):
    peak, tp, armed = 0.0, 0, False
    arm = max(best - 0.75, 0.5) if (best is not None and best <= 8.0) \
        else None
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i, "stop"
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i, "spike"
        if ts[i] - tp >= 60:
            return exc[i], i, "stall"
        if ts[i] >= 480:
            return exc[i], i, "timecap"
    return ((exc[-1], len(exc) - 1, "end") if len(exc)
            else (0.0, 0, "end"))

# ---------- candidate generation with feature context ----------
cands = []
month_arrays = {}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    secs = fl.sec.to_numpy(np.int64)
    mids = fl.mid.to_numpy(float)
    cnet = np.concatenate([[0.0], np.cumsum(
        (fl.buyv - fl.sellv).to_numpy(float))])
    cvol = np.concatenate([[0.0], np.cumsum(
        (fl.buyv + fl.sellv).to_numpy(float))])
    bk = pd.read_parquet(f"Data/inputs/{BOOKFILE[mo]}")
    bsec = bk.sec.to_numpy()
    bb0 = bk.bid0.to_numpy(float); ba0 = bk.ask0.to_numpy(float)
    month_arrays[mo] = dict(secs=secs, mids=mids, cnet=cnet,
                            cvol=cvol, bsec=bsec, bb0=bb0, ba0=ba0,
                            bm=bm)
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    ts_ct = bm.ts_event.dt.tz_convert("America/Chicago")
    hr_ct = ts_ct.dt.hour.to_numpy() + ts_ct.dt.minute.to_numpy() / 60
    dow_a = ts_ct.dt.dayofweek.to_numpy()
    evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
    band_cache = {}
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
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        jr = min(max(int(np.searchsorted(secs, es)), 0), len(mids) - 1)
        m_rel = mids[jr]
        j5 = int(np.searchsorted(secs, es + 300, "right"))
        seg5 = mids[jr:j5]
        w_react = float(abs(mids[min(j5, len(mids)) - 1] - m_rel))
        w_range = float(seg5.max() - seg5.min()) if len(seg5) else np.nan
        w_vol = float(cvol[j5] - cvol[jr])
        last_fire = {}
        sig_count = 0
        for jj in range(max(j0, 1), j1):
            t = int(secs[jj])
            t64 = np.datetime64(t, "s")
            E1 = list(edges_at(R, sd0, t64, "SQZ"))
            ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
            E2 = ([blo[ki], bhi[ki]]
                  if (ki >= 0 and np.isfinite(blo[ki])) else [])
            px, prev = mids[jj], mids[jj - 1]
            for src, e in ([(0, x) for x in E1] + [(1, x) for x in E2]):
                ddir = 1 if (prev <= e < px) else \
                    (-1 if (prev >= e > px) else 0)
                if ddir == 0:
                    continue
                key = (round(e, 2), ddir)
                if t - last_fire.get(key, -10**9) <= DEDUP:
                    continue
                last_fire[key] = t
                sig_count += 1
                bw = (bhi[ki] - blo[ki]) if E2 else np.nan
                ctx = dict(es=es, src=src, bw=bw, sig_idx=sig_count,
                           e_rel=(e - m_rel), w_react=w_react,
                           w_range=w_range, w_vol=w_vol,
                           hr=float(hr_ct[kb]), dw=float(dow_a[kb]),
                           t0=t)
                lvl = e + DISP * ddir
                j3 = int(np.searchsorted(secs, t + TTL, "right"))
                seg2 = mids[jj:j3]
                hit = np.flatnonzero((seg2 >= lvl) if ddir > 0
                                     else (seg2 <= lvl))
                if len(hit):
                    jf = jj + int(hit[0])
                    cands.append((mo, sd0, int(secs[jf]), ddir, key,
                                  jf, 1, 0.0, dict(ctx)))
                j9 = int(np.searchsorted(secs, t + 600, "right"))
                seg = (mids[jj:j9] - e) * ddir
                gate = np.flatnonzero(seg >= 1.0)
                if len(gate):
                    jg = int(gate[0])
                    back = np.flatnonzero(seg[jg:] <= 0.75)
                    if len(back):
                        jt = jj + jg + int(back[0])
                        tt_ = int(secs[jt])
                        j3b = int(np.searchsorted(secs, tt_ + TTL,
                                                  "right"))
                        seg2b = mids[jt:j3b]
                        hitb = np.flatnonzero(
                            (seg2b >= lvl) if ddir > 0
                            else (seg2b <= lvl))
                        if len(hitb):
                            jfb = jt + int(hitb[0])
                            cands.append((mo, sd0, int(secs[jfb]),
                                          ddir, key, jfb, 2,
                                          float(seg[:jg + 1].max()),
                                          dict(ctx)))

# ---------- simulate + features ----------
out = []
for mo in MONTHS:
    A = month_arrays[mo]
    secs, mids = A["secs"], A["mids"]
    cnet, cvol = A["cnet"], A["cvol"]
    bsec, bb0, ba0 = A["bsec"], A["bb0"], A["ba0"]
    cl = sorted([x for x in cands if x[0] == mo], key=lambda x: x[2])
    seen = set()
    busy = -10**12
    trades_today = {}
    for (mo_, sd0, tf, ddir, key, jf, lane, pre_exc, ctx) in cl:
        dk = (tf, key)
        if dk in seen:
            continue
        seen.add(dk)
        if tf < busy:
            continue
        lvl = key[0] + DISP * ddir
        j4 = int(np.searchsorted(secs, tf + 1800, "right"))
        exc = (mids[jf:j4] - lvl) * ddir
        ts_ = (secs[jf:j4] - tf).astype(int)
        di = day_ix.get(sd0)
        lv = lf(di) if di is not None else []
        ahead = sorted([(p - lvl) * ddir for p in lv
                        if (p - lvl) * ddir > 0.25])
        behind = sorted([(lvl - p) * ddir for p in lv
                         if (lvl - p) * ddir > 0.25])
        pnl, ix, reason = m7tag(exc, ts_, ahead[0] if ahead else None)
        busy = int(secs[jf + ix])
        ntd = trades_today.get(sd0, 0)
        trades_today[sd0] = ntd + 1
        # features at entry second tf
        def fsum(c, a, b_):
            i = int(np.searchsorted(secs, a))
            j = int(np.searchsorted(secs, b_, "right"))
            return float(c[j] - c[i])
        kbk = int(np.searchsorted(bsec, tf, "right")) - 1
        if kbk >= 0 and tf - bsec[kbk] <= 5:
            own0 = bb0[kbk] if ddir > 0 else ba0[kbk]
            opp0 = ba0[kbk] if ddir > 0 else bb0[kbk]
            timb = (own0 - opp0) / max(own0 + opp0, 1.0)
        else:
            own0 = opp0 = timb = np.nan
        j60 = int(np.searchsorted(secs, tf - 60))
        j300 = int(np.searchsorted(secs, tf - 300))
        jme = int(np.searchsorted(secs, tf, "right")) - 1
        di_ = day_ix.get(sd0, 0)
        med14 = float(np.nanmedian(day_rng[max(0, di_ - 14):di_])) \
            if di_ > 0 else np.nan
        bmd = A["bm"]
        gday = bmd[(bmd.sd == sd0)
                   & (bmd.ts_event.dt.tz_convert(None).astype("int64")
                      // 10**9 <= tf)]
        rng_sofar = float(gday.high.max() - gday.low.min()) \
            if len(gday) else np.nan
        g30 = gday.tail(30)
        rv30 = float(np.abs(g30.close.diff()).sum()) if len(g30) > 5 \
            else np.nan
        mfe = float(exc[:ix + 1].max()) if ix >= 0 else 0.0
        mae = float(-exc[:ix + 1].min()) if ix >= 0 else 0.0
        pdi = di_ - 1
        inpr = (float(pd_lo[pdi] <= mids[jme] <= pd_hi[pdi])
                if pdi >= 0 and np.isfinite(pd_lo[pdi]) else np.nan)
        dpe = (float(min(abs(mids[jme] - pd_hi[pdi]),
                         abs(mids[jme] - pd_lo[pdi])))
               if pdi >= 0 and np.isfinite(pd_lo[pdi]) else np.nan)
        out.append(dict(
            month=mo, sd=sd0, tf=tf, d=ddir, pnl=pnl, exit=reason,
            mfe=mfe, mae=mae,
            lane=lane, edge_src=ctx["src"], band_width=ctx["bw"],
            edge_dist_rel=ctx["e_rel"] * ddir, pre_exc=pre_exc,
            cross_to_fill=tf - ctx["t0"], sig_idx=ctx["sig_idx"],
            trades_today=ntd,
            tier20=float(ctx["es"] in t20),
            tier45=float(ctx["es"] in t45),
            mins_since_rel=(ctx["t0"] - ctx["es"]) / 60.0,
            react5=ctx["w_react"], range5=ctx["w_range"],
            vol5=ctx["w_vol"], hour=ctx["hr"], dow=ctx["dw"],
            room_ahead=min(ahead[0], 20.0) if ahead else 20.0,
            lvl_within8=float(bool(ahead) and ahead[0] <= 8.0),
            n_levels_10=float(sum(a_ <= 10 for a_ in ahead)
                              + sum(b_ <= 10 for b_ in behind)),
            room_behind=min(behind[0], 20.0) if behind else 20.0,
            flow30=fsum(cnet, tf - 30, tf) * ddir,
            flow120=fsum(cnet, tf - 120, tf) * ddir,
            vol30=fsum(cvol, tf - 30, tf),
            top_imb=timb, own0=own0, opp0=opp0,
            mom60=float((mids[jme] - mids[max(j60, 0)]) * ddir),
            mom300=float((mids[jme] - mids[max(j300, 0)]) * ddir),
            in_prior_range=inpr, dist_pd_edge=dpe,
            rng_ratio=rng_sofar / med14 if (med14 and med14 > 0)
            else np.nan,
            rv30=rv30))
T = pd.DataFrame(out)

# ---------- R-9 CONTROL ----------
fails = []
for pair, (n_e, p_e) in EXPECT.items():
    sub = T[T.month.isin(pair)]
    if not (len(sub) == n_e and abs(sub.pnl.sum() - p_e) < 0.1):
        fails.append(f"{pair}: {len(sub)} / {sub.pnl.sum():+.1f} "
                     f"(expected {n_e} / {p_e:+.1f})")
if fails:
    print("# XD RUN ABORTED — R-9 CONTROL FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

print("# XD REPORT — D-1 EXTRAS DECOMPOSITION (T-XD01)")
print("STATUS: CLOSED | 2026-11-27 | Spec: XD_SPEC.md (committed "
      "first) | R-9 double control: training 757/+325.1 and "
      "validation 760/+158.1 both reproduced exactly | study only")
print()
print(f"Population: {len(T)} G2-4 trades over 4 months "
      f"({T.groupby('month').size().to_dict()}).")
print()
print("## 1. CONCENTRATION — WHERE THE NET LIVES")
print("| month | net | top 10% share | top 25% share | % trades "
      "pnl>0 |")
print("|---|---|---|---|---|")
for mo in list(MONTHS) + ["POOLED"]:
    s = T if mo == "POOLED" else T[T.month == mo]
    srt = s.pnl.sort_values(ascending=False)
    n10 = max(1, int(0.10 * len(srt)))
    n25 = max(1, int(0.25 * len(srt)))
    net = srt.sum()
    print(f"| {mo} | {net:+.1f} | {srt.head(n10).sum() / net:.0%} | "
          f"{srt.head(n25).sum() / net:.0%} | "
          f"{(s.pnl > 0).mean():.0%} |")
print()
# earners
thr = T.pnl.quantile(0.75)
T["earner"] = (T.pnl >= thr).astype(int)
print(f"EARNERS = top quartile pooled (pnl >= {thr:+.2f}): "
      f"{int(T.earner.sum())} trades holding "
      f"{T.pnl[T.earner == 1].sum() / T.pnl.sum():.0%} of pooled net.")
print()
FAMS = {
 "F1 entry mechanics": ["lane", "edge_src", "band_width",
                        "edge_dist_rel", "pre_exc", "cross_to_fill",
                        "sig_idx", "trades_today"],
 "F2 news context": ["tier20", "tier45", "mins_since_rel", "react5",
                     "range5", "vol5", "hour", "dow"],
 "F3 levels": ["room_ahead", "lvl_within8", "n_levels_10",
               "room_behind"],
 "F4 flow/book": ["flow30", "flow120", "vol30", "top_imb", "own0",
                  "opp0"],
 "F5 path before": ["mom60", "mom300", "in_prior_range",
                    "dist_pd_edge"],
 "F6 regime": ["rng_ratio", "rv30"]}
print("## 2. ENTRY-TIME FEATURES — EARNERS vs REST")
print("(BH-FDR q=0.10 within family; FINDING also needs >=3/4 month "
      "direction consistency)")
# correlation prune note
num = T[[f for fs in FAMS.values() for f in fs]].select_dtypes("number")
corr = num.corr().abs()
dups = [(a, b_) for i, a in enumerate(corr.columns)
        for b_ in corr.columns[i + 1:] if corr.loc[a, b_] > 0.9]
if dups:
    print("Correlated >0.9 (reported as one signal): "
          + "; ".join(f"{a}~{b_}" for a, b_ in dups))
print()
print("| family | feature | earner med | rest med | p | BH | "
      "months same dir | verdict |")
print("|---|---|---|---|---|---|---|---|")
findings = []
for fam, feats in FAMS.items():
    ps = {}
    for f in feats:
        a = T[T.earner == 1][f].dropna()
        c = T[T.earner == 0][f].dropna()
        if len(a) < 20 or len(c) < 20:
            ps[f] = (np.nan, np.nan, np.nan)
            continue
        p = mannwhitneyu(a, c).pvalue
        ps[f] = (p, a.median(), c.median())
    valid = sorted([(p, f) for f, (p, _, _) in ps.items()
                    if np.isfinite(p)])
    mfam = len(valid)
    bh_pass = set()
    for rank, (p, f) in enumerate(valid, 1):
        if p <= 0.10 * rank / mfam:
            bh_pass = set(f2 for p2, f2 in valid[:rank])
    for f in feats:
        p, am, cm = ps[f]
        if not np.isfinite(p):
            print(f"| {fam} | {f} | - | - | - | - | - | insufficient |")
            continue
        sgn = np.sign(am - cm)
        nsame = 0
        for mo in MONTHS:
            a_ = T[(T.earner == 1) & (T.month == mo)][f].dropna()
            c_ = T[(T.earner == 0) & (T.month == mo)][f].dropna()
            if len(a_) >= 5 and len(c_) >= 5 and \
               np.sign(a_.median() - c_.median()) == sgn:
                nsame += 1
        bh = f in bh_pass
        v = ("FINDING" if (bh and nsame >= 3) else
             ("suggestive" if p <= 0.05 else "null"))
        if v == "FINDING":
            findings.append((fam, f, am, cm, p, nsame))
        print(f"| {fam} | {f} | {am:.2f} | {cm:.2f} | {p:.4f} | "
              f"{'Y' if bh else 'n'} | {nsame}/4 | {v} |")
print()
print("## 3. ANATOMY (path features - NOT usable for selection)")
print("| exit type | n | net | share of pooled net | earner n | "
      "earner net |")
print("|---|---|---|---|---|---|")
for r_ in ("spike", "stall", "timecap", "stop", "end"):
    s = T[T.exit == r_]
    se = s[s.earner == 1]
    print(f"| {r_} | {len(s)} | {s.pnl.sum():+.1f} | "
          f"{s.pnl.sum() / T.pnl.sum():.0%} | {len(se)} | "
          f"{se.pnl.sum():+.1f} |")
print(f"MFE med earners {T[T.earner == 1].mfe.median():.2f} vs rest "
      f"{T[T.earner == 0].mfe.median():.2f}; MAE med "
      f"{T[T.earner == 1].mae.median():.2f} vs "
      f"{T[T.earner == 0].mae.median():.2f}.")
print()
print(f"## FINDINGS ({len(findings)}) — candidate inputs for D-2/D-3 "
      "specs (J gates; nothing adopted here)")
for fam, f, am, cm, p, ns in findings:
    print(f"- {f} ({fam}): earners {am:.2f} vs rest {cm:.2f}, "
          f"p={p:.1e}, {ns}/4 months")
T.to_parquet("Data/inputs/xd_trades.parquet", index=False)
print()
print("Trade table saved: Data/inputs/xd_trades.parquet. "
      "Registry: T-XD01.")
