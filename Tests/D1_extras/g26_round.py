#!/usr/bin/env python3
"""
g26_round.py — T-EN113: gated G2-4 (G2-6 candidate). Spec:
G26_SPEC.md (committed first). Derived from the certified xd_round
generation; gates applied at fill time; R-9 control aborts on
mismatch.
RUN: python3 Tests/D1_extras/g26_round.py > Tests/D1_extras/G26_REPORT.md
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
# ---------- gated simulation (gates computed at fill time) ----------
RV_TH, ROOM_TH = 36.0, 8.0
CELLS = ["CONTROL", "E", "P", "E+P"]
cell_tr = {c: [] for c in CELLS}
declined = {c: 0 for c in CELLS}
for cname in CELLS:
    for mo in MONTHS:
        A = month_arrays[mo]
        secs, mids = A["secs"], A["mids"]
        bmd = A["bm"]
        bts = bmd.ts_event.dt.tz_convert(None).astype("int64"
                                                      ).to_numpy() // 10**9
        cl = sorted([x for x in cands if x[0] == mo],
                    key=lambda x: x[2])
        seen = set()
        busy = -10**12
        for (mo_, sd0, tf, ddir, key, jf, lane, pre_exc, ctx) in cl:
            dk = (tf, key)
            if dk in seen:
                continue
            seen.add(dk)
            if tf < busy:
                continue
            lvl = key[0] + DISP * ddir
            di = day_ix.get(sd0)
            lv = lf(di) if di is not None else []
            ahead = sorted([(p - lvl) * ddir for p in lv
                            if (p - lvl) * ddir > 0.25])
            room = min(ahead[0], 20.0) if ahead else 20.0
            if cname in ("E", "E+P"):
                k0 = int(np.searchsorted(bts, tf, "right"))
                g30 = bmd.close.to_numpy()[max(0, k0 - 30):k0]
                rv30 = float(np.abs(np.diff(g30)).sum()) \
                    if len(g30) > 5 else np.nan
                if not (np.isfinite(rv30) and rv30 >= RV_TH):
                    declined[cname] += 1
                    continue
            if cname in ("P", "E+P"):
                if room > ROOM_TH:
                    declined[cname] += 1
                    continue
            j4 = int(np.searchsorted(secs, tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * ddir
            ts_ = (secs[jf:j4] - tf).astype(int)
            pnl, ix, reason = m7tag(exc, ts_,
                                    ahead[0] if ahead else None)
            busy = int(secs[jf + ix])
            cell_tr[cname].append(dict(month=mo, tf=tf, d=ddir,
                                       pnl=pnl, key=str(key)))
T = {c: pd.DataFrame(v) for c, v in cell_tr.items()}

fails = []
for pair, (n_e, p_e) in EXPECT.items():
    sub = T["CONTROL"][T["CONTROL"].month.isin(pair)]
    if not (len(sub) == n_e and abs(sub.pnl.sum() - p_e) < 0.1):
        fails.append(f"CONTROL {pair}: {len(sub)}/"
                     f"{sub.pnl.sum():+.1f} != {n_e}/{p_e:+.1f}")
for c in CELLS:
    for mo in MONTHS:
        if not len(T[c][T[c].month == mo]):
            fails.append(f"{c} empty in {mo}")
if fails:
    print("# G26 RUN ABORTED — R-9 CHECKS FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

print("# G26 REPORT — GATED G2-4 (G2-6 CANDIDATE) (T-EN113)")
print("STATUS: CLOSED | 2026-11-27 | Spec: G26_SPEC.md (committed "
      "first) | R-9 CONTROL reproduced exactly | circularity "
      "declared: gates derive from this corpus - passing is "
      "necessary, not sufficient; final judge = D-8 months")
print()
print("| cell | trades | declined | per-trade | pooled net | by "
      "month (22-02/25-10/23-05/24-05) | months pos | removed vs "
      "CONTROL: n / net | verdict |")
print("|---|---|---|---|---|---|---|---|---|")
ctrl_keys = set(map(tuple, T["CONTROL"][["month", "tf"]
                                        ].itertuples(index=False)))
ctrl_ix = T["CONTROL"].set_index(["month", "tf"]).pnl
for c in CELLS:
    tr = T[c]
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    pooled = tr.pnl.sum()
    pt = pooled / max(1, len(tr))
    pos = sum(1 for v in nets.values() if v > 0)
    ck = set(map(tuple, tr[["month", "tf"]].itertuples(index=False)))
    removed = ctrl_keys - ck
    rem_net = float(ctrl_ix.loc[list(removed)].sum()) if removed \
        else 0.0
    if c == "CONTROL":
        v = "(reproduced)"
    else:
        ok = (pt >= 0.48 and pooled >= 193 and pos == 4
              and rem_net <= 0)
        v = "REGISTER G2-6 CANDIDATE" if ok else "fails line"
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in
                   ["2022-02", "2025-10", "2023-05", "2024-05"])
    print(f"| {c} | {len(tr)} | {declined[c]} | {pt:+.2f} | "
          f"{pooled:+.1f} | {bym} | {pos}/4 | {len(removed)} / "
          f"{rem_net:+.1f} | {v} |")
print()
print("Thresholds frozen in spec: rv30 >= 36.0 (corpus median), "
      "room_ahead <= 8.0 (M7 arm). Registry: T-EN113.")
