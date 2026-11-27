#!/usr/bin/env python3
"""
g31_round.py — T-EN116: G3-1 quiet-market cycle (D-5). Spec:
G31_SPEC.md (frozen first). Generation loop verbatim from the
certified g26_round (T-EN115); the ONLY change is the time windows
(quiet RTH spans instead of news windows). Resume-safe parts.
RUN: python3 Tests/D5_quiet/g31_round.py   (repeat until REPORT)
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
PARTS = "Tests/D5_quiet/parts"
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
        for tag in ("quiet",)]
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
    evm = np.unique(ev_all[(ev_all >= secs[0] - 86400)
                           & (ev_all <= secs[-1])])
    # quiet spans: per RTH day, seconds with (t - last release) > 2700
    day_spans = []
    for sd0 in sorted(bm[bm.session.eq("RTH")].sd.unique()):
        msk_day = (sd1 == sd0) & rth
        if not msk_day.any():
            continue
        t0d, t1d = int(bt[msk_day].min()), int(bt[msk_day].max()) + 60
        cuts = [t0d]
        for es in evm[(evm >= t0d - 2700) & (evm <= t1d)]:
            lo, hi = max(int(es), t0d), min(int(es) + 2700, t1d)
            day_spans.append(None)  # placeholder (built below)
        # build quiet spans = [t0d,t1d] minus union of [es, es+2700]
        iv = sorted((max(int(es), t0d), min(int(es) + 2700, t1d))
                    for es in evm[(evm >= t0d - 2700) & (evm <= t1d)]
                    if int(es) + 2700 > t0d and int(es) < t1d)
        day_spans = [s for s in day_spans if s is not None]
        cur = t0d
        for lo, hi in iv:
            if lo > cur:
                day_spans.append((sd0, cur, lo))
            cur = max(cur, hi)
        if cur < t1d:
            day_spans.append((sd0, cur, t1d))
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
    day_fire = {}
    for sd0, w0, w1 in day_spans:
        j0 = int(np.searchsorted(secs, w0))
        j1 = int(np.searchsorted(secs, w1, "right"))
        if j1 - j0 < 60:
            continue
        di = day_ix.get(sd0)
        if sd0 not in band_cache:
            g = bm[bm.sd == sd0].reset_index(drop=True)
            band_cache[sd0] = (band_arrays(g, 20, 0.8),
                               (g.ts_event.dt.tz_convert(None)
                                .astype("int64").to_numpy() // 10**9))
        (blo, bhi), g_bt = band_cache[sd0]
        last_fire = day_fire.setdefault(sd0, {})
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

# ---------- R-9 CONTROL 1: engine reproduces banked T-EN115 cands --
mo_c = "2022-02"
B_ = pd.read_parquet(
    f"Tests/D11_unmatched/parts/cand_full_{mo_c}.parquet")
# regenerate with the news-window logic restored, same machinery
bm = b[(b.ts_event >= f"{mo_c}-01") & (b.ts_event < "2022-03-01")
       ].reset_index(drop=True)
R = Resolver(bm, zr)
fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo_c}_full.parquet")
secs = fl.sec.to_numpy(np.int64)
mids = fl.mid.to_numpy(float)
bt = bm.ts_event.dt.tz_convert(None).astype("int64").to_numpy() // 10**9
rth = bm.session.eq("RTH").to_numpy()
sd1 = bm.sd.to_numpy()
evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
band_cache = {}
memo = {}
def fam_edges(fam, sd0, t):
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
                cands.append((sd0, int(secs[jf]), dd, key[0], jf,
                              fam))
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
A_ = pd.DataFrame(cands, columns=["sd", "tf", "d", "e", "jf", "fam"])
sa = set(map(tuple, A_[["tf", "d", "e", "jf"]].itertuples(False)))
sb = set(map(tuple, B_[["tf", "d", "e", "jf"]].itertuples(False)))
if sa != sb:
    print(f"# G31 ABORTED — ENGINE CONTROL: regen {len(sa)} vs "
          f"banked {len(sb)}, symdiff {len(sa ^ sb)}")
    sys.exit(1)

# ---------- sims ----------
def run_cell(tag, A=None):
    out = []
    for mo in MONTHS:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        pdir = ("Tests/D11_unmatched/parts" if tag != "quiet"
                else PARTS)
        C = pd.read_parquet(f"{pdir}/cand_{tag}_{mo}.parquet")
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
            best = ahead[0] if ahead else None
            if A is None:
                pnl, ix = m7(exc, ts_, best)
            else:
                peak, tp, armed = 0.0, 0, False
                pnl, ix = ((exc[-1], len(exc) - 1) if len(exc)
                           else (0.0, 0))
                for i in range(len(exc)):
                    if exc[i] > peak:
                        peak, tp = exc[i], ts_[i]
                    if exc[i] >= A:
                        armed = True
                    if exc[i] <= -STOP:
                        pnl, ix = -STOP, i
                        break
                    if armed and exc[i] <= peak - 0.75:
                        pnl, ix = peak - 0.75, i
                        break
                    if ts_[i] - tp >= 60 or ts_[i] >= 480:
                        pnl, ix = exc[i], i
                        break
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl), fam=r.fam))
    return pd.DataFrame(out)

G26 = run_cell("full")
if not (len(G26) == 6252 and abs(G26.pnl.sum() - 1659.0) < 0.1):
    print(f"# G31 ABORTED — SIM CONTROL {len(G26)}/"
          f"{G26.pnl.sum():+.1f}")
    sys.exit(1)

G31 = run_cell("quiet")
G31M9 = run_cell("quiet", A=1.5)

# his G3 set
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

def report_cell(name, tr):
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    caught = 0
    near = np.zeros(len(tr), bool)
    for _, h in HISG3.iterrows():
        hitm = ((tr.month == h.month).to_numpy()
                & (tr.d == h.side).to_numpy()
                & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
        caught += int(hitm.any())
        near |= hitm
    exn = tr.pnl[~near].sum()
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in MONTHS)
    print(f"| {name} | {len(tr)} | "
          f"{tr.pnl.sum()/max(1,len(tr)):+.2f} | {tr.pnl.sum():+.1f}"
          f" | {bym} | {caught}/{len(HISG3)} | {exn:+.1f} |")
    return caught, nets

print("# G31 REPORT — G3-1: THE QUIET-MARKET CYCLE (T-EN116)")
print("STATUS: CLOSED | 2026-11-27 | Spec: G31_SPEC.md (frozen "
      "first) | R-9 dual controls exact (engine set-equal on "
      f"{mo_c}; G2-6 sim 6252/+1659.0) | six months | TRAINING-ONLY")
print()
print("| cell | trades | per-trade | pooled | by month "
      "(21-09/22-02/23-05/24-05/24-11/25-10) | catch-G3 | extras |")
print("|---|---|---|---|---|---|---|")
c26, _ = report_cell("G2-6 (news windows, ref)", G26)
c31, nets31 = report_cell("G3-1 x M7", G31)
c31b, _ = report_cell("G3-1 x M9 (secondary)", G31M9)
print()
print("## PER-FAMILY (G3-1 x M7; first-family tag, shared busy)")
print("| family | trades | net | per-trade | months net<0 |")
print("|---|---|---|---|---|")
toxbad = False
for fam, g in G31.groupby("fam"):
    mn = sum(1 for mo in MONTHS if g[g.month == mo].pnl.sum() < 0)
    tox = " TOXIC-FLAG" if mn >= 4 else ""
    if mn >= 4:
        toxbad = True
    print(f"| {fam} | {len(g)} | {g.pnl.sum():+.1f} | "
          f"{g.pnl.sum()/max(1,len(g)):+.2f} | {mn}/6{tox} |")
print()
pooled = G31.pnl.sum()
pt = pooled / max(1, len(G31))
wm = min(nets31.values())
near31 = np.zeros(len(G31), bool)
for _, h in HISG3.iterrows():
    near31 |= ((G31.month == h.month).to_numpy()
               & (G31.d == h.side).to_numpy()
               & (np.abs(G31.tf - h.sec) <= 300).to_numpy())
exn = G31.pnl[~near31].sum()
nH = len(HISG3)
print("## VERDICT vs THE FROZEN LINES (G3-1 x M7)")
print(f"- controls exact: PASS")
print(f"- catch >= 60% of his G3 set: "
      f"{'PASS' if c31 >= 0.6*nH else 'FAIL'} ({c31}/{nH})")
print(f"- pooled > 0, no month < -10: "
      f"{'PASS' if (pooled > 0 and wm > -10) else 'FAIL'} "
      f"({pooled:+.1f}; worst {wm:+.1f})")
print(f"- extras >= 0: {'PASS' if exn >= 0 else 'FAIL'} ({exn:+.1f})")
print(f"- per-trade >= +0.20: {'PASS' if pt >= 0.20 else 'FAIL'} "
      f"({pt:+.2f})")
print(f"- no unflagged toxic family: "
      f"{'FLAGGED' if toxbad else 'PASS'}")
ok = (c31 >= 0.6*nH and pooled > 0 and wm > -10 and exn >= 0
      and pt >= 0.20 and not toxbad)
print(f"OVERALL: "
      f"{'REGISTER G3-1 TRAINING-ONLY' if ok else 'PARTIAL - facts to J'}")
print()
print("Registry: T-EN116.")
