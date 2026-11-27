#!/usr/bin/env python3
"""
d27_audit.py — T-SA01 Parts A+B: sensitivity audit engine. Derived
from the certified m15/cd lineage. One-at-a-time perturbations;
resume via Tests/D6_deepbook/d27_results.csv.
RUN: python3 Tests/D6_deepbook/d27_audit.py
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

MONTHS = {"2022-02": "2022-03-01", "2025-10": "2025-11-01"}
EXPECT = {("2022-02", "2025-10"): (757, 325.1)}
BOOKFILE = {"2022-02": "book_per_sec_2022-02.parquet",
            "2025-10": "book_per_sec_2025-10.parquet",
            "2023-05": "book_top_per_sec_2023-05.parquet",
            "2024-05": "book_top_per_sec_2024-05.parquet"}
DISP, GRID = 1.25, 0.25

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


def m7p(exc, ts, best, gb, fl, stop, cap):
    peak, tp, armed = 0.0, 0, False
    arm = max(best - gb, fl) if (best is not None and best <= 8.0) \
        else None
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -stop:
            return -stop, i
        if armed and exc[i] <= peak - gb:
            return peak - gb, i
        if ts[i] - tp >= 60:
            return exc[i], i
        if ts[i] >= cap:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

def generate(TTL, DEDUP, WSEQ):
    cands = []
    arrays = {}
    for mo, nxt in MONTHS.items():
        bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
               ].reset_index(drop=True)
        R = Resolver(bm, zr)
        _f = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = _f.sec.to_numpy(np.int64)
        mids = _f.mid.to_numpy(float)
        arrays[mo] = (secs, mids)
        bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                    ).to_numpy() // 10**9
        rth = bm.session.eq("RTH").to_numpy()
        sd1 = bm.sd.to_numpy()
        evm = np.unique(ev_all[(ev_all >= secs[0])
                               & (ev_all <= secs[-1])])
        band_cache = {}
        for es in evm:
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
                                    .astype("int64").to_numpy()
                                    // 10**9))
            (blo, bhi), g_bt = band_cache[sd0]
            last_fire = {}
            for jj in range(max(j0, 1), j1):
                t = int(secs[jj])
                t64 = np.datetime64(t, "s")
                E = list(edges_at(R, sd0, t64, "SQZ"))
                ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
                if ki >= 0 and np.isfinite(blo[ki]):
                    E += [blo[ki], bhi[ki]]
                px, prev = mids[jj], mids[jj - 1]
                for e in E:
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
                        cands.append((mo, sd0, int(secs[jf]), dd,
                                      key, jf))
                    j9 = int(np.searchsorted(secs, t + WSEQ, "right"))
                    seg = (mids[jj:j9] - e) * dd
                    gate = np.flatnonzero(seg >= 1.0)
                    if len(gate):
                        jg = int(gate[0])
                        back = np.flatnonzero(seg[jg:] <= 0.75)
                        if len(back):
                            jt = jj + jg + int(back[0])
                            tt_ = int(secs[jt])
                            j3b = int(np.searchsorted(
                                secs, tt_ + 300, "right"))
                            s2b = mids[jt:j3b]
                            hb = np.flatnonzero(
                                (s2b >= lvl) if dd > 0
                                else (s2b <= lvl))
                            if len(hb):
                                jfb = jt + int(hb[0])
                                cands.append((mo, sd0,
                                              int(secs[jfb]), dd,
                                              key, jfb))
    return cands, arrays

def simulate(cands, arrays, gb, fl, stop, cap):
    nets = {mo: 0.0 for mo in MONTHS}
    n = 0
    for mo in MONTHS:
        secs, mids = arrays[mo]
        cl = sorted([x for x in cands if x[0] == mo],
                    key=lambda x: x[2])
        seen = set()
        busy = -10**12
        for (mo_, sd0, tf, dd, key, jf) in cl:
            dk = (tf, key)
            if dk in seen:
                continue
            seen.add(dk)
            if tf < busy:
                continue
            lvl = key[0] + DISP * dd
            j4 = int(np.searchsorted(secs, tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * dd
            ts_ = (secs[jf:j4] - tf).astype(int)
            di = day_ix.get(sd0)
            lv = lf(di) if di is not None else []
            ahead = sorted([(p - lvl) * dd for p in lv
                            if (p - lvl) * dd > 0.25])
            pnl, ix = m7p(exc, ts_, ahead[0] if ahead else None,
                          gb, fl, stop, cap)
            busy = int(secs[jf + ix])
            nets[mo] += pnl
            n += 1
    return n, nets

import os, time
RESF = "Tests/D6_deepbook/d27_results.csv"
done = (pd.read_csv(RESF).variant.tolist()
        if os.path.exists(RESF) else [])
BASE = dict(gb=0.75, fl=0.5, stop=3.75, cap=480,
            TTL=300, DEDUP=300, WSEQ=600)
VARIANTS = [("BASELINE", {})]
for k, vals in [("gb", [0.5, 1.0]), ("fl", [0.25, 0.75]),
                ("stop", [3.0, 4.5, 5.25]), ("cap", [360, 720])]:
    VARIANTS += [(f"{k}={v}", {k: v}) for v in vals]
for k, vals in [("TTL", [150, 450]), ("DEDUP", [150, 450]),
                ("WSEQ", [300, 900])]:
    VARIANTS += [(f"{k}={v}", {k: v}) for v in vals]
T0 = time.time()
base_cands = None
base_arrays = None
rows = []
for name, over in VARIANTS:
    if name in done:
        continue
    p = dict(BASE); p.update(over)
    if base_cands is None or any(k in over for k in
                                 ("TTL", "DEDUP", "WSEQ")):
        cands, arrays = generate(p["TTL"], p["DEDUP"], p["WSEQ"])
        if not any(k in over for k in ("TTL", "DEDUP", "WSEQ")):
            base_cands, base_arrays = cands, arrays
    else:
        cands, arrays = base_cands, base_arrays
    n, nets = simulate(cands, arrays, p["gb"], p["fl"], p["stop"],
                       p["cap"])
    row = dict(variant=name, trades=n,
               pooled=round(sum(nets.values()), 1),
               m1=round(nets["2022-02"], 1),
               m2=round(nets["2025-10"], 1))
    rows.append(row)
    print(row)
    df = pd.DataFrame(rows)
    if os.path.exists(RESF):
        df = pd.concat([pd.read_csv(RESF), df]).drop_duplicates(
            "variant", keep="last")
    df.to_csv(RESF, index=False)
    rows = []
    if time.time() - T0 > 480:
        print("TIME BUDGET - rerun to continue")
        break
print("PASS COMPLETE" if time.time() - T0 <= 480 else "")
