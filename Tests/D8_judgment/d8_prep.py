#!/usr/bin/env python3
"""
d8_prep.py — D-8 STEP 0a: feature prep for the quarantined months
(2022-05, 2026-03). OUTCOME-BLIND: reads market data and structural
objects only; no system result is computed here.
DERIVES FROM (R-9 lineage): Tests/D11_unmatched/g26_remint_gen.py —
candidate machinery copied VERBATIM (band_arrays, wrb_day, EV/
density_levels/lf, per-event candidate loop, tags ctrl/full).
R-9 CONTROL: before building any new-month part, this script
rebuilds cand_ctrl_2023-05 and asserts frame-equality with the
certified part in Tests/D11_unmatched/parts (the T-RH02 basis).
Abort on any mismatch.
PHASES (resume-safe):
  1. BLIND LEVEL LISTS: lf(di) per new-month session -> committed
     BEFORE his zone references for these months are compared (1b).
     lf reads s4_objects + WRB bodies + prior-day marks only.
  2. CONTROL: cand_ctrl_2023-05 rebuild == certified part.
  3. NEW PARTS: cand_ctrl_{2022-05,2026-03} into
     Tests/D8_judgment/parts.
RUN: python3 Tests/D8_judgment/d8_prep.py   (repo root; rerun to
resume)
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
MONTHS_NEW = {"2022-05": "2022-06-01", "2026-03": "2026-04-01"}
CTRL_MONTH = ("2023-05", "2023-06-01")
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25
PARTS = "Tests/D8_judgment/parts"
CERT = "Tests/D11_unmatched/parts"
os.makedirs(PARTS, exist_ok=True)
BUDGET = 1800

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

# levels machinery (lf: s4 objects + WRB bodies + prior-day marks;
# NO his-zone input -> blind by construction)
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


# ---------- PHASE 1: blind level lists ----------
for mo in MONTHS_NEW:
    out = f"Tests/D8_judgment/blind_levels_{mo}.csv"
    if os.path.exists(out):
        continue
    sds = sorted(b[b.sd.str.startswith(mo) & ~b.is_roll_day
                   ].sd.unique())
    recs = []
    for sd in sds:
        di = day_ix[sd]
        for p in lf(di):
            recs.append((sd, p))
    pd.DataFrame(recs, columns=["session_date", "level"]
                 ).to_csv(out, index=False)
    print(f"BLIND LEVELS {mo}: {len(recs)} level-days -> {out}",
          flush=True)

# ---------- candidate builder (verbatim machinery) ----------
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

def build_month(mo, nxt, tag, parts_dir):
    part = f"{parts_dir}/cand_{tag}_{mo}.parquet"
    if os.path.exists(part):
        return False
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
    return True


# ---------- PHASE 2: R-9 controls (rebuild 2023-05, must match) ----------
# (extended 2026-11-28 at J's G2-6 go: the "full" tag joins with the
# same row-identical control before its new-month parts are built)
for tag in ("ctrl", "full"):
    part = f"{PARTS}/cand_{tag}_{CTRL_MONTH[0]}.parquet"
    if os.path.exists(part + ".ok"):
        continue
    build_month(CTRL_MONTH[0], CTRL_MONTH[1], tag, PARTS)
    new = pd.read_parquet(part)
    cert = pd.read_parquet(f"{CERT}/cand_{tag}_{CTRL_MONTH[0]}.parquet")
    if not new.reset_index(drop=True).equals(
            cert.reset_index(drop=True)):
        print("# D8 PREP ABORTED — R-9 CONTROL FAILED: rebuilt "
              f"cand_{tag}_{CTRL_MONTH[0]} != certified part "
              f"({len(new)} vs {len(cert)} rows)")
        sys.exit(1)
    open(part + ".ok", "w").write("match\n")
    print(f"R-9 CONTROL PASS: cand_{tag}_{CTRL_MONTH[0]} rebuilt "
          f"identical ({len(new)} rows)", flush=True)

# ---------- PHASE 3: new-month parts ----------
for tag in ("ctrl", "full"):
    for mo, nxt in MONTHS_NEW.items():
        if build_month(mo, nxt, tag, PARTS):
            if time.time() - T0 > BUDGET:
                print("CONTINUE (rerun to finish)")
                sys.exit(0)
print("D8 PREP 0a DONE")
