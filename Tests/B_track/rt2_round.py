#!/usr/bin/env python3
"""
rt2_round.py — T-EN107: Part A (his first-vs-retest study) + Part B
(excursion-gated retest grid). Spec: RT2_SPEC.md (committed first).
RUN: python3 Tests/B_track/rt2_round.py > Tests/B_track/RT2_REPORT.md
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

# ---------- levels + M7 (identical to shipped) ----------
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

# ---------- HIS62 + audited per-trade P&L ----------
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
HIS62 = F[(F.ctx == "squeeze") & (F.np_ == "window")].copy()
gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
gt["pnl"] = gt.pnl_calc.where(gt.pnl_calc.notna(), gt.pnl_stated)
gt = gt[["month", "entry_msg_s", "pnl"]].rename(
    columns={"entry_msg_s": "sec", "pnl": "pnl_pts"})
HIS62 = HIS62.merge(gt.groupby(["month", "sec"], as_index=False
                               ).pnl_pts.sum(), on=["month", "sec"],
                    how="left")
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

print("# RT2 REPORT — EXCURSION-GATED RETEST + HIS ENTRY STYLE "
      "(T-EN107)")
print("STATUS: CLOSED | 2026-11-26 | Spec: RT2_SPEC.md (committed "
      "first) | incumbent G2-3: +265.4 / catch 46 / extras +173.0 / "
      "per-trade +0.49 | his G2: +231.2 / 62 trades / +3.73")
print()

# =========== shared per-month scan: cross stream + grid cells ======
cells = [(X, pb) for X in (1.0, 2.0) for pb in (0.25, 0.75)]
trades = {c: [] for c in cells}
cross_log = []          # (month, sd, t, e, dir) for Part A
h_rows = []

for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    busy_c = {c: -10**12 for c in cells}
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
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
                cross_log.append((mo, sd0, t, round(e, 2), ddir))
                # ---- Part B: excursion gate -> pullback -> re-break
                j9 = int(np.searchsorted(secs, t + WSEQ, "right"))
                seg = (mids[jj:j9] - e) * ddir
                for c in cells:
                    X, pb = c
                    gate = np.flatnonzero(seg >= X)
                    if not len(gate):
                        continue
                    jg = int(gate[0])
                    back = np.flatnonzero(seg[jg:] <= pb)
                    if not len(back):
                        continue
                    jt = jj + jg + int(back[0])
                    tt_ = int(secs[jt])
                    lvl = e + DISP * ddir
                    j3 = int(np.searchsorted(secs, tt_ + TTL, "right"))
                    seg2 = mids[jt:j3]
                    hit = np.flatnonzero((seg2 >= lvl) if ddir > 0
                                         else (seg2 <= lvl))
                    if not len(hit):
                        continue
                    jf = jt + int(hit[0])
                    tf = int(secs[jf])
                    if tf < busy_c[c]:
                        continue
                    j4 = int(np.searchsorted(secs, tf + 1800, "right"))
                    exc = (mids[jf:j4] - lvl) * ddir
                    ts_ = (secs[jf:j4] - tf).astype(int)
                    di = day_ix.get(sd0)
                    lv = lf(di) if di else []
                    ahead = sorted([(p - lvl) * ddir for p in lv
                                    if (p - lvl) * ddir > 0.25])
                    pnl, ix = m7(exc, ts_, ahead[0] if ahead else None)
                    busy_c[c] = int(secs[jf + ix])
                    trades[c].append((mo, tf, ddir, pnl))
    # ---- Part A for this month ----
    CL = [c for c in cross_log if c[0] == mo]
    for _, h in HIS62[HIS62.month == mo].iterrows():
        sec, sd_h, side = int(h.sec), None, int(h.side)
        cand = [c for c in CL if c[4] == side
                and sec - 600 <= c[2] <= sec + 60]
        if not cand:
            h_rows.append((mo, sec, side, "UNMATCHED", np.nan, np.nan,
                           np.nan, h.pnl_pts, h.kme_mins_since))
            continue
        cm = max(cand, key=lambda c: c[2])      # latest cross <= entry
        e, key_t = cm[3], cm[2]
        same = sorted(c[2] for c in CL if c[3] == e and c[4] == side
                      and sec - 600 <= c[2] <= sec + 60)
        n_prior = sum(1 for x in same if x < key_t)
        t_first = same[0]
        jA = int(np.searchsorted(secs, t_first))
        jB = int(np.searchsorted(secs, sec, "right"))
        segh = (mids[jA:jB] - e) * side
        max_exc = float(segh.max()) if len(segh) else np.nan
        pulled = False
        if len(segh):
            gate = np.flatnonzero(segh >= 1.0)
            if len(gate):
                pulled = bool((segh[int(gate[0]):] <= 0.75).any())
        cls = "RETEST-TAKE" if pulled else (
            "FIRST-TAKE" if n_prior == 0 else "OTHER")
        h_rows.append((mo, sec, side, cls, n_prior, max_exc, pulled,
                       h.pnl_pts, h.kme_mins_since))

h_rows_df = pd.DataFrame(h_rows, columns=[
    "month", "sec", "side", "cls", "n_prior", "max_exc", "pulled",
    "pnl", "mins_since"])
print("## PART A — HOW HE ENTERS, RELATIVE TO THE CROSS STREAM "
      "(62 ground-truth G2 entries)")
print("| class | n | 22-02/25-10 | his per-trade P&L med (mean) | "
      "max excursion before entry (med) | mins since release (med) |")
print("|---|---|---|---|---|---|")
for cls in ("FIRST-TAKE", "RETEST-TAKE", "OTHER", "UNMATCHED"):
    s = h_rows_df[h_rows_df.cls == cls]
    if not len(s):
        continue
    mo_split = "/".join(str((s.month == m).sum())
                        for m in ("2022-02", "2025-10"))
    print(f"| {cls} | {len(s)} | {mo_split} | "
          f"{s.pnl.median():+.2f} ({s.pnl.mean():+.2f}) | "
          f"{s.max_exc.median():.2f} | "
          f"{s.mins_since.median():.0f} |")
print()
print("## PART B — EXCURSION-GATED RETEST GRID (everything else = "
      "exact G2-3)")
print("| cell | trades | per-trade | net (22-02/25-10) | caught/62 | "
      "extras net | verdict |")
print("|---|---|---|---|---|---|---|")
for c in cells:
    X, pb = c
    tr = pd.DataFrame(trades[c], columns=["month", "tf", "d", "pnl"])
    nets = tr.groupby("month").pnl.sum() if len(tr) else pd.Series()
    caught = 0
    for _, h in HIS62.iterrows():
        if len(tr) and len(tr[(tr.month == h.month) & (tr.d == h.side)
                              & (abs(tr.tf - h.sec) <= 300)]):
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in HIS62.iterrows():
        if len(tr):
            near |= ((tr.month == h.month).to_numpy()
                     & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = tr.pnl[~near].sum() if len(tr) else 0.0
    pooled = tr.pnl.sum() if len(tr) else 0.0
    pt = pooled / max(1, len(tr))
    both = (len(nets) == 2 and all(x > 0 for x in nets.to_numpy()))
    adopt = (pooled > 265.4 and caught >= 46 and exn >= 0 and both)
    alt = (pt >= 0.98 and pooled >= 150 and both and caught >= 30)
    v = "ADOPT" if adopt else ("QUALITY-ALT" if alt else "no")
    print(f"| X{X} pb{pb} | {len(tr)} | {pt:+.2f} | {pooled:+.1f} "
          f"({nets.get('2022-02', 0):+.1f}/"
          f"{nets.get('2025-10', 0):+.1f}) | {caught} | {exn:+.1f} "
          f"| {v} |")
print()
print("Registry: T-EN107.")
