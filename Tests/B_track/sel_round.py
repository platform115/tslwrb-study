#!/usr/bin/env python3
"""
sel_round.py — T-EN105: the selection round. Spec: SEL_SPEC.md
(committed first). Rebuilds the G2-3 fill set WITH trigger features,
decomposes the gap, ranks filters, tests deterministic rules.
RUN: python3 Tests/B_track/sel_round.py > Tests/B_track/SEL_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination",
          "Tests/P5_trade_management"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p6_0_feature_battery import build_ctx, battery          # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25
RNG = np.random.default_rng(113)

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9
cal = pd.read_parquet("Data/inputs/kme_calendar.parquet").dropna(
    subset=["ts_utc"]).sort_values("ts_utc")
cts = (pd.to_datetime(cal.ts_utc, utc=True).dt.as_unit("ns")
       .astype("int64").to_numpy() // 10**9)
cev = cal.event.astype(str).to_numpy()

def ev_name(es):
    j = int(np.searchsorted(cts, es, "right")) - 1
    return cev[j] if j >= 0 and abs(int(cts[j]) - int(es)) <= 1 else "?"

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

# ---- multi-day levels (shipped config; v3 recipe) ----
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

# ---- scan with features ----
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
fills = []
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    C = build_ctx(".", mo)
    secs, mids = C["secs"], C["mids"]
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    evm = ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])]
    band_cache = {}
    busy = -10**12
    for es in evm:
        w0, w1 = es + 300, es + 2700
        j0 = int(np.searchsorted(secs, w0))
        j1 = int(np.searchsorted(secs, w1, "right"))
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
            bwidth = np.nan
            ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
            if ki >= 0 and np.isfinite(blo[ki]):
                E += [blo[ki], bhi[ki]]
                bwidth = bhi[ki] - blo[ki]
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
                j2 = int(np.searchsorted(secs, t + TTL, "right"))
                seg = mids[jj:j2]
                hit = np.flatnonzero((seg >= lvl) if ddir > 0
                                     else (seg <= lvl))
                if not len(hit):
                    continue
                jf = jj + int(hit[0])
                tf = int(secs[jf])
                if tf < busy:
                    continue
                di = day_ix.get(sd0)
                lv = lf(di) if di else []
                ahead = sorted([(p - lvl) * ddir for p in lv
                                if (p - lvl) * ddir > 0.25])
                behind = sorted([(lvl - p) * ddir for p in lv
                                 if (lvl - p) * ddir > 0.25])
                j3 = int(np.searchsorted(secs, tf + 1800, "right"))
                exc = (mids[jf:j3] - lvl) * ddir
                ts_ = (secs[jf:j3] - tf).astype(int)
                pnl, ix = m7(exc, ts_, ahead[0] if ahead else None)
                busy = int(secs[jf + ix])
                f = battery(C, t, ddir) or {}
                fills.append(dict(
                    month=mo, sd=sd0, tf=tf, d=ddir, pnl=pnl,
                    mv15=f.get("mv15", np.nan),
                    mv60=f.get("mv60", np.nan),
                    mv300=f.get("mv300", np.nan),
                    flow1=f.get("flow1", np.nan),
                    vrate900=f.get("vrate900", np.nan),
                    rng120=f.get("rng120", np.nan),
                    mins_since_ev=(t - es) / 60.0,
                    event=ev_name(es), band_width=bwidth,
                    room_ahead=ahead[0] if ahead else 99.0,
                    lvl_behind=behind[0] if behind else 99.0,
                    tod_min=f.get("mins_open", np.nan)))
FL = pd.DataFrame(fills)
FL.to_parquet("Data/inputs/sel_fills.parquet", index=False)
near = np.zeros(len(FL), bool)
for _, h in HIS62.iterrows():
    near |= ((FL.month == h.month).to_numpy()
             & (FL.d == h.side).to_numpy()
             & (np.abs(FL.tf - h.sec) <= 300).to_numpy())
FL["near_his"] = near
print("# SEL REPORT — THE SELECTION ROUND (T-EN105)")
print("STATUS: CLOSED | 2026-11-26 | Spec: SEL_SPEC.md (committed "
      "first)")
print()
print("## STEP 1 — GAP DECOMPOSITION (G2-3 fills, M7 exits)")
nh, ex = FL[FL.near_his], FL[~FL.near_his]
print(f"- all fills: {len(FL)}, net {FL.pnl.sum():+.1f}, per-trade "
      f"{FL.pnl.mean():+.2f}")
print(f"- near-his fills: {len(nh)}, net {nh.pnl.sum():+.1f}, per-trade"
      f" {nh.pnl.mean():+.2f}")
print(f"- extras: {len(ex)}, net {ex.pnl.sum():+.1f}, per-trade "
      f"{ex.pnl.mean():+.2f}")
srt = FL.pnl.sort_values(ascending=False)
print(f"- concentration: top 10% of fills hold "
      f"{srt.head(int(len(srt)*0.1)).sum()/max(FL.pnl.sum(),1e-9):.0%} "
      f"of net; losers {int((FL.pnl<0).sum())} fills, "
      f"{FL.pnl[FL.pnl<0].sum():+.1f}")
print()
# ---- step 3: rank ----
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupKFold
FEATS = ["mv15", "mv60", "mv300", "flow1", "vrate900", "rng120",
         "mins_since_ev", "band_width", "room_ahead", "lvl_behind",
         "tod_min"]
X = FL[FEATS].astype(float)
for c in FEATS:
    X[c] = X[c].fillna(X[c].median())
for lbl_name, y in (("PROFIT (pnl>0)", (FL.pnl > 0).astype(int)),
                    ("HIS-LIKENESS", FL.near_his.astype(int))):
    imps = []
    for tr, te in GroupKFold(4).split(X, y, groups=FL.sd):
        rf = RandomForestClassifier(n_estimators=400, random_state=113,
                                    n_jobs=-1)
        rf.fit(X.iloc[tr], y.iloc[tr])
        pi = permutation_importance(rf, X.iloc[te], y.iloc[te],
                                    n_repeats=5, random_state=113,
                                    n_jobs=-1, scoring="roc_auc")
        imps.append(pd.Series(pi.importances_mean, index=FEATS))
    IM = pd.concat(imps, axis=1).mean(axis=1).sort_values(
        ascending=False)
    print(f"## RANKING — {lbl_name} (held-out permutation importance)")
    for c, v in IM.head(5).items():
        print(f"- {c}: {v:.3f}")
    print()
# ---- deterministic rule grid on top features ----
print("## DETERMINISTIC RULES (grids; traded results; bars: per-trade "
      ">= +1.00, catch >= 40, net >= +199, both months > 0)")
def caught_count(sub):
    c = 0
    for _, h in HIS62.iterrows():
        if len(sub[(sub.month == h.month) & (sub.d == h.side)
                   & (abs(sub.tf - h.sec) <= 300)]):
            c += 1
    return c
null_drops = []
for _ in range(20):
    k = RNG.choice(len(FL), size=len(FL) // 2, replace=False)
    null_drops.append(FL.iloc[k].pnl.mean())
print(f"(null control: random half-drops give per-trade "
      f"{np.mean(null_drops):+.2f} - any rule must beat this trivially)")
print()
print("| rule | fills | per-trade | net (22-02/25-10) | caught | "
      "extras net | ADOPT? |")
print("|---|---|---|---|---|---|---|")
RULES = []
for ra in (3.0, 4.5, 6.0, 99.0):
    RULES.append((f"room_ahead>= {ra}" if ra < 99 else "room any",
                  FL.room_ahead >= ra if ra < 99
                  else np.ones(len(FL), bool)))
for mv in (2.0, 4.0):
    RULES.append((f"mv15>={mv}", FL.mv15 >= mv))
for me in (20.0,):
    RULES.append((f"mins_since_ev<={me}", FL.mins_since_ev <= me))
RULES.append(("room>=4.5 & mv15>=2",
              (FL.room_ahead >= 4.5) & (FL.mv15 >= 2.0)))
RULES.append(("room>=3 & mins<=20",
              (FL.room_ahead >= 3.0) & (FL.mins_since_ev <= 20.0)))
for name, msk in RULES:
    sub = FL[msk]
    if not len(sub):
        continue
    nets = sub.groupby("month").pnl.sum()
    cgt = caught_count(sub)
    exn = sub[~sub.near_his].pnl.sum()
    ok = (sub.pnl.mean() >= 1.0 and cgt >= 40
          and sub.pnl.sum() >= 199
          and all(v > 0 for v in nets.to_numpy())
          and len(nets) == 2)
    print(f"| {name} | {len(sub)} | {sub.pnl.mean():+.2f} | "
          f"{sub.pnl.sum():+.1f} ({nets.get('2022-02',0):+.1f}/"
          f"{nets.get('2025-10',0):+.1f}) | {cgt} | {exn:+.1f} | "
          f"{'YES' if ok else 'no'} |")
print()
print("Registry: T-EN105. sel_fills.parquet saved (checksummed).")
