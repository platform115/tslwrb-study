#!/usr/bin/env python3
"""
um_round.py — T-EN114: anatomy of the 12 unmatched entries.
Spec: UM_SPEC.md (committed first).
RUN: python3 Tests/D11_unmatched/um_round.py > Tests/D11_unmatched/UM_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2022-02": "2022-03-01", "2025-10": "2025-11-01"}
GRID = 0.25
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

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
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet"
                     ).reset_index()
zr["ts_s"] = (pd.to_datetime(zr.ts_utc, utc=True)
              .astype("int64") // 10**9)

# levels machinery (shipped)
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
wrb_edges = {}
for tfm in ("5min", "15min"):
    for sd, g in bb.groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w_ = body > pm
        ee = []
        for o, c in zip(r.open.to_numpy()[w_], r.close.to_numpy()[w_]):
            rows.append(pd.DataFrame({"sd": [sd, sd],
                                      "px": [max(o, c), min(o, c)],
                                      "newsborn": [False, False]}))
            ee += [max(o, c), min(o, c)]
        wrb_edges.setdefault(sd, []).extend(ee)
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

# HIS62 + find the unmatched 12 (same construction as T-EN107 Part A)
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f_}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f_,
                                                             "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")]
gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
gt2 = gt.groupby(["month", "entry_msg_s"], as_index=False).agg(
    entry_price=("entry_price", "first"),
    pnl=("pnl_calc", "sum"))

anat = []
for mo, nxt in MONTHS.items():
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
    CL = []
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
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        last_fire = {}
        for jj in range(max(j0, 1), j1):
            t = int(secs[jj])
            E = list(edges_at(R, sd0, np.datetime64(t, "s"), "SQZ"))
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
                if t - last_fire.get(key, -10**9) <= 300:
                    continue
                last_fire[key] = t
                CL.append((t, dd))
    CLt = np.array([c[0] for c in CL])
    CLd = np.array([c[1] for c in CL])
    for _, h in HIS62[HIS62.month == mo].iterrows():
        sec, side = int(h.sec), int(h.side)
        if ((CLd == side) & (CLt >= sec - 600)
                & (CLt <= sec + 60)).any():
            continue                      # matched -> not our quarry
        # --- anatomy ---
        kb = int(np.searchsorted(bt, sec, "right")) - 1
        sd0 = sd1[kb]
        di = day_ix.get(sd0)
        gp = gt2[(gt2.month == mo)
                 & (gt2.entry_msg_s == h.sec)]
        epx = float(gp.entry_price.iloc[0]) if len(gp) and \
            np.isfinite(gp.entry_price.iloc[0]) else np.nan
        jme = int(np.searchsorted(secs, sec, "right")) - 1
        px_now = mids[jme] if not np.isfinite(epx) else epx
        cands = {}
        for fam in ("SQZ", "REA", "GAP", "SHD"):
            E = list(edges_at(R, sd0, np.datetime64(sec, "s"), fam))
            if E:
                dmin = min(abs(e - px_now) for e in E)
                cands[f"edge_{fam}"] = dmin
        if sd0 in band_cache:
            (blo, bhi), g_bt = band_cache[sd0]
            ki = int(np.searchsorted(g_bt + 60, sec, "right")) - 1
            if ki >= 0 and np.isfinite(blo[ki]):
                cands["W20band"] = min(abs(blo[ki] - px_now),
                                       abs(bhi[ki] - px_now))
        lv = lf(di) if di is not None else []
        if lv:
            cands["mdlevel"] = min(abs(p - px_now) for p in lv)
        if di and di >= 1 and np.isfinite(pd_hi[di - 1]):
            cands["prior_day_HLC"] = min(
                abs(pd_hi[di - 1] - px_now),
                abs(pd_lo[di - 1] - px_now),
                abs(pd_cl[di - 1] - px_now))
        # overnight H/L (globex of same session date)
        gses = bm[(bm.sd == sd0)]
        gon = gses[~gses.session.eq("RTH")]
        if len(gon):
            cands["overnight_HL"] = min(
                abs(gon.high.max() - px_now),
                abs(gon.low.min() - px_now))
        gr = gses[gses.session.eq("RTH")]
        gbt = (gr.ts_event.dt.tz_convert(None).astype("int64")
               .to_numpy() // 10**9)
        or30 = gr[gbt < gbt[0] + 1800] if len(gr) else gr
        if len(or30):
            cands["opening_range"] = min(
                abs(or30.high.max() - px_now),
                abs(or30.low.min() - px_now))
        cands["round50"] = min(px_now % 50, 50 - px_now % 50)
        # 5m swings last 2h
        g2h = bm[(bt >= sec - 7200) & (bt <= sec)]
        if len(g2h) > 10:
            r5 = g2h.set_index("ts_event").resample("5min").agg(
                {"high": "max", "low": "min"}).dropna()
            hh, ll = r5.high.to_numpy(), r5.low.to_numpy()
            sw = []
            for i2 in range(2, len(r5) - 2):
                if hh[i2] == max(hh[i2 - 2:i2 + 3]):
                    sw.append(hh[i2])
                if ll[i2] == min(ll[i2 - 2:i2 + 3]):
                    sw.append(ll[i2])
            if sw:
                cands["swing_5m"] = min(abs(s - px_now) for s in sw)
        if sd0 in wrb_edges and wrb_edges[sd0]:
            cands["wrb_body"] = min(abs(e - px_now)
                                    for e in wrb_edges[sd0])
        # price action
        j5 = int(np.searchsorted(secs, sec - 300))
        mom5 = (mids[jme] - mids[max(j5, 0)]) * side
        kk_ = int(np.searchsorted(ev_all, sec, "right")) - 1
        mins_ = (sec - ev_all[kk_]) / 60.0
        # his words
        zz = zr[(np.abs(zr.ts_s - sec) <= 600)]
        words = int(len(zz))
        near3 = sorted(cands.items(), key=lambda kv: kv[1])[:3]
        attributed = [k for k, v in near3 if v <= 1.5]
        anat.append(dict(
            month=mo, sec=sec, side=side, px=round(px_now, 2),
            pnl=float(gp.pnl.iloc[0]) if len(gp) else np.nan,
            mins_since=round(mins_, 1), mom5=round(float(mom5), 2),
            n1=f"{near3[0][0]}={near3[0][1]:.2f}" if near3 else "-",
            n2=f"{near3[1][0]}={near3[1][1]:.2f}" if len(near3) > 1
            else "-",
            n3=f"{near3[2][0]}={near3[2][1]:.2f}" if len(near3) > 2
            else "-",
            attributed=(attributed[0] if attributed
                        else "NO STRUCTURE <=1.5"),
            his_msgs_10min=words))

A = pd.DataFrame(anat)
print("# UM REPORT — ANATOMY OF THE UNMATCHED ENTRIES (T-EN114)")
print("STATUS: CLOSED | 2026-11-27 | Spec: UM_SPEC.md (frozen first)")
print()
print(f"Unmatched found: {len(A)} (expected 12 per T-EN107).")
print()
print("## PER-ENTRY ANATOMY")
print(A.to_markdown(index=False))
print()
print("## ATTRIBUTION BUCKETS (nearest structure <= 1.5 pts)")
for k, v in A.attributed.value_counts().items():
    print(f"- {k}: {v}")
print()
print("## PRICE-ACTION CLASS")
print(f"- continuation (entered WITH prior 5-min move): "
      f"{int((A.mom5 > 0.5).sum())}; fade (AGAINST): "
      f"{int((A.mom5 < -0.5).sum())}; flat: "
      f"{int((A.mom5.abs() <= 0.5).sum())}")
print()
print("Registry: T-EN114.")
