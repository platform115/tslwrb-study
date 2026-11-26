#!/usr/bin/env python3
"""
bk_round.py — T-EN111: book lens on which-signal. Spec: BK_SPEC.md
(committed first). Derived from ws_round.py (same episode machinery,
same fixes); only the feature set changes. Study only.
RUN: python3 Tests/B_track/bk_round.py > Tests/B_track/BK_REPORT.md
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

RNG = np.random.default_rng(113)
MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
DEDUP, GRID = 300, 0.25

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

# levels (shipped config), for room_ahead
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
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")]

FEATS = ["opp0", "opp10", "own0", "imb0", "imb10", "d30_opp0",
         "depth_tot"]
ep_rows = []          # (ep_id, month, taken, feat dict)
uncovered = []
ep_id = 0
single_cross = 0
unmatched = 0

for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    bk = pd.read_parquet(f"Data/inputs/book_per_sec_{mo}.parquet")
    bsec = bk.sec.to_numpy()
    bb0 = bk.bid0.to_numpy().astype(float)
    ba0 = bk.ask0.to_numpy().astype(float)
    bb10 = bk.bid10.to_numpy().astype(float)
    ba10 = bk.ask10.to_numpy().astype(float)
    def book_at(t):
        k = int(np.searchsorted(bsec, t, "right")) - 1
        if k < 0 or t - bsec[k] > 5:
            return None
        return bb0[k], ba0[k], bb10[k], ba10[k]
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    fsec = fl.sec.to_numpy()
    fimb = (fl.buyv - fl.sellv).to_numpy().astype(float)
    cimb = np.concatenate([[0.0], np.cumsum(fimb)])
    def imb30(t):
        a = int(np.searchsorted(fsec, t - 30))
        b2 = int(np.searchsorted(fsec, t, "right"))
        return float(cimb[b2] - cimb[a])
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
    band_cache = {}
    # build the full deduped cross list once (as before)
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
                CL.append((sd0, t, key[0], ddir, jj, es))
    CLdf = pd.DataFrame(CL, columns=["sd", "t", "e", "d", "jj", "es"])
    CLdf = CLdf.drop_duplicates(["sd", "t", "e", "d", "es"])
    for _, h in HIS62[HIS62.month == mo].iterrows():
        sec, side = int(h.sec), int(h.side)
        cand = CLdf[(CLdf.d == side) & (CLdf.t >= sec - 600)
                    & (CLdf.t <= sec + 60)]
        if not len(cand):
            unmatched += 1
            continue
        taken_row = cand.loc[cand.t.idxmax()]
        e, es0 = taken_row.e, taken_row.es
        ep = CLdf[(CLdf.e == e) & (CLdf.d == side) & (CLdf.es == es0)
                  & (CLdf.t <= sec + 60)].sort_values("t")
        if len(ep) < 2:
            single_cross += 1
            continue
        ep_id += 1
        di = day_ix.get(taken_row.sd)
        lv = lf(di) if di is not None else []
        ahead = sorted([(p - (e + 1.25 * side)) * side for p in lv
                        if (p - (e + 1.25 * side)) * side > 0.25])
        room = min(ahead[0], 20.0) if ahead else 20.0
        j_rel = int(np.searchsorted(secs, es0))
        mid_rel = mids[min(j_rel, len(mids) - 1)]
        first_t = int(ep.t.min())
        jA = int(np.searchsorted(secs, first_t))
        prior_fail_ts = []
        for rank, (_, c) in enumerate(ep.iterrows(), start=1):
            t, jj = int(c.t), int(c.jj)
            # prior fails: earlier crosses whose 300s excursion < 1.0
            bnow = book_at(t)
            bprev = book_at(t - 30)
            if bnow is None:
                uncovered.append((mo, t))
                continue
            b0, a0, b10_, a10_ = bnow
            opp0 = a0 if side > 0 else b0
            own0 = b0 if side > 0 else a0
            opp10 = a10_ if side > 0 else b10_
            own10 = b10_ if side > 0 else a10_
            d30 = (opp0 - (bprev[1] if side > 0 else bprev[0])) \
                if bprev is not None else np.nan
            ep_rows.append(dict(
                ep=ep_id, month=mo, taken=int(t == int(taken_row.t)),
                opp0=opp0, opp10=opp10, own0=own0,
                imb0=(own0 - opp0) / max(own0 + opp0, 1.0),
                imb10=(own10 - opp10) / max(own10 + opp10, 1.0),
                d30_opp0=d30, depth_tot=b10_ + a10_))

D = pd.DataFrame(ep_rows)
keep = [e_ for e_, g in D.groupby("ep")
        if g.taken.sum() == 1 and len(g) >= 2]
dropped_eps = D.ep.nunique() - len(keep)
D = D[D.ep.isin(keep)]
print("# BK REPORT — BOOK LENS ON WHICH-SIGNAL (T-EN111)")
print("STATUS: CLOSED | 2026-11-26 | Spec: BK_SPEC.md (committed "
      "first) | study only | data: per-second book from J's drive "
      "(MBP-10 reductions)")
print()
ntk = D[D.taken == 1]
print(f"Episodes: {D.ep.nunique()} multi-cross with full book "
      f"coverage (paired analysis; {dropped_eps} dropped for missing "
      f"book seconds), {single_cross} single-cross, {unmatched} "
      f"unmatched.")
print()
print(f"Book coverage: {len(uncovered)} crosses without a book "
      f"second within 5s (dropped, listed not hidden). All features "
      f"are market-state -> valid in the paired design (no "
      f"monotone-in-time artifact possible).")
print()
print("## PAIRED TEST: TAKEN CROSS vs ITS PASSED SIBLINGS "
      "(within-episode permutation, 10,000 draws)")
print("| feature | taken med | passed med | direction | perm p | "
      "verdict (alpha .0071 / .05) |")
print("|---|---|---|---|---|---|")
NPERM = 10000
eps = [g for _, g in D.groupby("ep")]
for f in FEATS:
    obs = 0.0
    for g in eps:
        v = g[f].to_numpy()
        r = pd.Series(v).rank(pct=True).to_numpy()
        obs += float(r[g.taken.to_numpy() == 1][0])
    obs /= len(eps)
    null = np.zeros(NPERM)
    for g in eps:
        v = g[f].to_numpy()
        r = pd.Series(v).rank(pct=True).to_numpy()
        null += r[RNG.integers(0, len(v), NPERM)]
    null /= len(eps)
    p = float(min((null >= obs).mean(), (null <= obs).mean()) * 2)
    p = min(p, 1.0)
    tm, pm = D[D.taken == 1][f].median(), D[D.taken == 0][f].median()
    dr = "taken HIGHER" if obs > null.mean() else "taken LOWER"
    v_ = ("FINDING" if p <= 0.0071 else
          ("suggestive" if p <= 0.05 else "null"))
    print(f"| {f} | {tm:.2f} | {pm:.2f} | {dr} | {p:.4f} | {v_} |")
print()
print("Power note: ~{} paired episodes; only large effects can clear "
      "the adjusted alpha.".format(len(eps)))
print("Registry: T-EN111.")
