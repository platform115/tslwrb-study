#!/usr/bin/env python3
"""
cd_round.py — T-EN110: cadence cap per news window. Spec: CD_SPEC.md
(committed first). Mandatory checks abort the run on failure.
RUN: python3 Tests/B_track/cd_round.py > Tests/B_track/CD_REPORT.md
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
CAPS = {"CONTROL": 10**9, "N=3": 3, "N=2": 2, "N=1": 1}
EXPECT = dict(n=607, pooled=276.1, caught=47, extras=185.6)

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
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

# ---------- lane-1 candidate generation (identical to tl_round) ----
cands = []                     # (mo, sd, tf, ddir, key, jf, es)
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
                j3 = int(np.searchsorted(secs, t + TTL, "right"))
                seg2 = mids[jj:j3]
                hit = np.flatnonzero((seg2 >= lvl) if ddir > 0
                                     else (seg2 <= lvl))
                if len(hit):
                    jf = jj + int(hit[0])
                    cands.append((mo, sd0, int(secs[jf]), ddir, key,
                                  jf, int(es)))

# ---------- simulate each cell ----------
cell_tr = {}
for cname, cap in CAPS.items():
    out = []
    for mo in MONTHS:
        secs, mids = month_arrays[mo]
        cl = sorted([x for x in cands if x[0] == mo],
                    key=lambda x: x[2])
        seen = set()
        busy = -10**12
        wcount = {}
        for (mo_, sd0, tf, ddir, key, jf, es) in cl:
            dk = (tf, key)
            if dk in seen:
                continue
            seen.add(dk)
            if tf < busy:
                continue
            if wcount.get(es, 0) >= cap:
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
            wcount[es] = wcount.get(es, 0) + 1
            out.append((mo, tf, ddir, pnl, key, es))
    cell_tr[cname] = pd.DataFrame(
        out, columns=["month", "tf", "d", "pnl", "key", "es"])

def score(tr):
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
    exn = float(tr.pnl[~near].sum())
    return nets, caught, exn, float(tr.pnl.sum())

# ---------- MANDATORY CHECKS (abort on fail) ----------
fails = []
cn, cc, ce, cp = score(cell_tr["CONTROL"])
if not (len(cell_tr["CONTROL"]) == EXPECT["n"]
        and abs(cp - EXPECT["pooled"]) < 0.1
        and cc == EXPECT["caught"]
        and abs(ce - EXPECT["extras"]) < 0.1):
    fails.append(f"check1 CONTROL mismatch: n={len(cell_tr['CONTROL'])}"
                 f" pooled={cp:+.1f} caught={cc} extras={ce:+.1f}")
order = ["N=1", "N=2", "N=3", "CONTROL"]
for a, b_ in zip(order, order[1:]):
    for mo in list(MONTHS) + ["pooled"]:
        na = len(cell_tr[a] if mo == "pooled"
                 else cell_tr[a][cell_tr[a].month == mo])
        nb = len(cell_tr[b_] if mo == "pooled"
                 else cell_tr[b_][cell_tr[b_].month == mo])
        if na > nb:
            fails.append(f"check2 monotonicity: {a}({mo})={na} > "
                         f"{b_}({mo})={nb}")
cand_set = set((mo, tf, key) for (mo, sd0, tf, ddir, key, jf, es)
               in cands)
# CONTROL busy intervals per month: [fill, exit] of each trade.
# Rebuild exits by replay (same order, same m7) to get busy spans.
ctrl_busy = {mo: [] for mo in MONTHS}
for mo in MONTHS:
    secs, mids = month_arrays[mo]
    cl = sorted([x for x in cands if x[0] == mo], key=lambda x: x[2])
    seen = set(); busy = -10**12
    for (mo_, sd0, tf, ddir, key, jf, es) in cl:
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
        ctrl_busy[mo].append((tf, busy))
ctrl_set = set(map(tuple, cell_tr["CONTROL"][["month", "tf", "key"]
                                             ].itertuples(index=False)))
for cname in ("N=1", "N=2", "N=3"):
    for mo_, tf, key in cell_tr[cname][["month", "tf", "key"]
                                       ].itertuples(index=False):
        if (mo_, tf, key) not in cand_set:
            fails.append(f"check3a alien-to-candidates fill in "
                         f"{cname}: {mo_} {tf}")
        elif (mo_, tf, key) not in ctrl_set:
            if not any(a < tf <= b_ for a, b_ in ctrl_busy[mo_]):
                fails.append(f"check3b unexplained non-control fill "
                             f"in {cname}: {mo_} {tf} (control not "
                             f"busy then)")
for cname, tr in cell_tr.items():
    if tr.duplicated(["tf", "key"]).any():
        fails.append(f"check4 duplicates in {cname}")
    for mo in MONTHS:
        if not len(tr[tr.month == mo]):
            fails.append(f"check4 empty month {mo} in {cname}")
if fails:
    print("# CD RUN ABORTED — MANDATORY CHECKS FAILED (per CD_SPEC)")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

# ---------- report ----------
print("# CD REPORT — CADENCE CAP PER NEWS WINDOW (T-EN110)")
print("STATUS: CLOSED | 2026-11-26 | Spec: CD_SPEC.md (committed "
      "first) | engine: fill-time (standard) | corrected incumbent "
      "G2-3: +276.1 / 607 / catch 47 / extras +185.6 | his G2: "
      "+231.2 / 62 / +3.73")
print()
print("MANDATORY CHECKS: all passed (control reproduced exactly; "
      "monotonicity, subset, no-duplicate, no-empty-month).")
print()
# his cadence anchor
print("## HIS CADENCE (descriptive anchor)")
hw = []
for _, h in HIS62.iterrows():
    prior = ev_all[(ev_all <= h.sec - 300) & (ev_all >= h.sec - 2700)]
    hw.append((h.month, int(prior.max()) if len(prior) else -1))
hwc = pd.Series([w for _, w in hw if w > 0]).value_counts(
    ).value_counts().sort_index()
print("| his entries per window | windows |")
print("|---|---|")
for k, v in hwc.items():
    print(f"| {int(k)} | {v} |")
print()
print("## GRID (cap on filled trades per news window)")
print("| cell | trades | per-trade | net (22-02/25-10) | caught/62 | "
      "extras net | verdict |")
print("|---|---|---|---|---|---|---|")
for cname in ["CONTROL", "N=3", "N=2", "N=1"]:
    tr = cell_tr[cname]
    nets, caught, exn, pooled = score(tr)
    pt = pooled / max(1, len(tr))
    both = (len(nets) == 2 and all(x > 0 for x in nets.to_numpy()))
    if cname == "CONTROL":
        v = "(incumbent reproduced)"
    else:
        adopt = (pooled > 276.1 and caught >= 47 and exn >= 0
                 and both)
        alt = (pt >= 0.98 and pooled >= 150 and both and caught >= 30)
        v = "ADOPT" if adopt else ("QUALITY-ALT" if alt else "no")
    print(f"| {cname} | {len(tr)} | {pt:+.2f} | {pooled:+.1f} "
          f"({nets.get('2022-02', 0):+.1f}/"
          f"{nets.get('2025-10', 0):+.1f}) | {caught} | {exn:+.1f} "
          f"| {v} |")
print()
print("Registry: T-EN110.")
