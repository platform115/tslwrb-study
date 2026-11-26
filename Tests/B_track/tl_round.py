#!/usr/bin/env python3
"""
tl_round.py — T-EN108: two-lane entry (first-break + retest).
Spec: TL_SPEC.md (committed first). CONTROL cell must reproduce
G2-3 (+265.4 / 542 / 46 / +173.0) or the run aborts.
RUN: python3 Tests/B_track/tl_round.py > Tests/B_track/TL_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25
WSEQ = 600
CELLS = {"CONTROL": None, "TL-A": (2.0, 0.25), "TL-B": (1.0, 0.75)}

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

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

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")][["month", "sec",
                                                      "side"]]
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

# ---------- candidate generation (both lanes), per month ----------
cands = {c: [] for c in CELLS}        # (mo, sd, tf, d, key, lane, jf)
month_arrays = {}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    month_arrays[mo] = (secs, mids)
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])]
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
                                .astype("int64").to_numpy() // 10**9))
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
                ddir = 1 if (prev <= e < px) else \
                    (-1 if (prev >= e > px) else 0)
                if ddir == 0:
                    continue
                key = (round(e, 2), ddir)
                if t - last_fire.get(key, -10**9) <= DEDUP:
                    continue
                last_fire[key] = t
                lvl = e + DISP * ddir
                # LANE 1 (all cells): stop from t0, TTL 300
                j3 = int(np.searchsorted(secs, t + TTL, "right"))
                seg2 = mids[jj:j3]
                hit = np.flatnonzero((seg2 >= lvl) if ddir > 0
                                     else (seg2 <= lvl))
                if len(hit):
                    jf = jj + int(hit[0])
                    for c in CELLS:
                        cands[c].append((mo, sd0, int(secs[jf]), ddir,
                                         key, 1, jf))
                # LANE 2 (TL cells): gate -> pullback -> re-break
                j9 = int(np.searchsorted(secs, t + WSEQ, "right"))
                seg = (mids[jj:j9] - e) * ddir
                for c, pars in CELLS.items():
                    if pars is None:
                        continue
                    X, pb = pars
                    gate = np.flatnonzero(seg >= X)
                    if not len(gate):
                        continue
                    jg = int(gate[0])
                    back = np.flatnonzero(seg[jg:] <= pb)
                    if not len(back):
                        continue
                    jt = jj + jg + int(back[0])
                    tt_ = int(secs[jt])
                    j3b = int(np.searchsorted(secs, tt_ + TTL,
                                              "right"))
                    seg2b = mids[jt:j3b]
                    hitb = np.flatnonzero((seg2b >= lvl) if ddir > 0
                                          else (seg2b <= lvl))
                    if not len(hitb):
                        continue
                    jfb = jt + int(hitb[0])
                    cands[c].append((mo, sd0, int(secs[jfb]), ddir,
                                     key, 2, jfb))

# ---------- single-position simulation per cell ----------
print("# TL REPORT — TWO-LANE ENTRY: FIRST-BREAK + RETEST (T-EN108)")
print("STATUS: CLOSED | 2026-11-26 | Spec: TL_SPEC.md (committed "
      "first) | incumbent G2-3: +265.4 / 542 / catch 46 / extras "
      "+173.0 / per-trade +0.49 | his G2: +231.2 / 62 / +3.73")
print()
print("| cell | trades (L1/L2) | per-trade | net (22-02/25-10) | "
      "caught/62 | extras net | lane2 net | verdict |")
print("|---|---|---|---|---|---|---|---|")
results = {}
for c in CELLS:
    out = []
    for mo in MONTHS:
        secs, mids = month_arrays[mo]
        cl = sorted([x for x in cands[c] if x[0] == mo],
                    key=lambda x: x[2])
        seen = set()
        busy = -10**12
        for (mo_, sd0, tf, ddir, key, lane, jf) in cl:
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
            pnl, ix = m7(exc, ts_, ahead[0] if ahead else None)
            busy = int(secs[jf + ix])
            out.append((mo, tf, ddir, pnl, lane))
    tr = pd.DataFrame(out, columns=["month", "tf", "d", "pnl", "lane"])
    nets = tr.groupby("month").pnl.sum()
    caught = 0
    for _, h in HIS62.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in HIS62.iterrows():
        near |= ((tr.month == h.month).to_numpy()
                 & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = tr.pnl[~near].sum()
    pooled = tr.pnl.sum()
    pt = pooled / max(1, len(tr))
    both = (len(nets) == 2 and all(x > 0 for x in nets.to_numpy()))
    n1 = int((tr.lane == 1).sum()); n2 = int((tr.lane == 2).sum())
    l2net = tr.pnl[tr.lane == 2].sum()
    results[c] = dict(n=len(tr), pooled=pooled, caught=caught, exn=exn)
    if c == "CONTROL":
        ok = (abs(pooled - 265.4) < 1.0 and len(tr) == 542
              and caught == 46)
        v = "REPRODUCED" if ok else "MISMATCH - RUN INVALID"
    else:
        adopt = (pooled > 265.4 and caught >= 46 and exn >= 0
                 and both)
        alt = (pt >= 0.98 and pooled >= 150 and both and caught >= 30)
        v = "ADOPT" if adopt else ("QUALITY-ALT" if alt else "no")
    print(f"| {c} | {len(tr)} ({n1}/{n2}) | {pt:+.2f} | {pooled:+.1f} "
          f"({nets.get('2022-02', 0):+.1f}/"
          f"{nets.get('2025-10', 0):+.1f}) | {caught} | {exn:+.1f} | "
          f"{l2net:+.1f} | {v} |")
print()
print("Registry: T-EN108.")
