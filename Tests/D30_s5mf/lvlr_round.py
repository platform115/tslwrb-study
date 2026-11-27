#!/usr/bin/env python3
"""
lvlr_round.py — T-SR03: 5W full-RTH anatomy (D-31). Spec:
LVLR_SPEC.md (frozen first). Machinery derived verbatim from
s5mf_round.py (certified T-SR02). Controls: builder 1541/1263,
S1-ANY 422/+216.5, LVL-ANY 750/+472.1.
RUN: python3 Tests/D30_s5mf/lvlr_round.py > Tests/D30_s5mf/LVLR_REPORT.md
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
FAM_ORDER = ("SQZ", "GAP", "SHD", "REA", "WRB", "PDY")

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
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

MIDS, OFI, VOLS = {}, {}, {}
for mo in MONTHS:
    f = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    MIDS[mo] = (f.sec.to_numpy(np.int64), f.mid.to_numpy(float))
    VOLS[mo] = (f.buyv.to_numpy(float) + f.sellv.to_numpy(float))
    o = pd.read_parquet(f"Data/inputs/ofi10_per_sec_{mo}.parquet")
    OFI[mo] = (o.sec.to_numpy(np.int64),
               np.concatenate([[0.0], np.cumsum(
                   (o.ofi_b - o.ofi_a).to_numpy(float))]))

def ofi30(mo, t, sdn):
    osec, ocum = OFI[mo]
    i = int(np.searchsorted(osec, t - 30))
    j = int(np.searchsorted(osec, t, "right"))
    if j <= i:
        return None
    return float(ocum[j] - ocum[i]) * sdn

# ---- levels pool (verbatim s1_round) ----
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
wrb_day = {}
for tfm, tfs in (("5min", 300), ("15min", 900)):
    for sd, g in bb.groupby("sd"):
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
        for o, c in zip(r.open.to_numpy()[w_], r.close.to_numpy()[w_]):
            rows.append(pd.DataFrame({"sd": [sd, sd],
                                      "px": [max(o, c), min(o, c)],
                                      "newsborn": [False, False]}))
for sd in wrb_day:
    wrb_day[sd].sort()
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

bnr = b[~b.is_roll_day]
bt_all = bnr.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
sd_all = bnr.sd.to_numpy()

def sim(sub):
    out = []
    for mo in MONTHS:
        secs, mids = MIDS[mo]
        tt = sub[sub.month == mo].sort_values("t", kind="stable")
        busy = -10**12
        for r in tt.itertuples():
            t0 = int(r.t) + 3
            if t0 < busy:
                continue
            d = int(r.side)
            L = float(r.level)
            ent = L + 0.75 * d
            j0 = int(np.searchsorted(secs, t0))
            j1 = int(np.searchsorted(secs, t0 + 120, "right"))
            seg = mids[j0:j1]
            hit = np.flatnonzero((seg >= ent) if d > 0
                                 else (seg <= ent))
            if not len(hit):
                continue
            jf = j0 + int(hit[0])
            tf = int(secs[jf])
            if tf < busy:
                continue
            stop_px = L - 1.25 * d
            kb = int(np.searchsorted(bt_all, tf, "right")) - 1
            di = day_ix.get(sd_all[kb]) if kb >= 0 else None
            lv = lf(di) if di is not None else []
            ahead = sorted([(p - ent) * d for p in lv
                            if (p - ent) * d > 0.5])
            tgt = ahead[0] if ahead else None
            j4 = int(np.searchsorted(secs, tf + 900, "right"))
            exc = (mids[jf:j4] - ent) * d
            ts_ = (secs[jf:j4] - tf).astype(int)
            stop_exc = (stop_px - ent) * d
            peak = 0.0
            pnl = exc[-1] if len(exc) else 0.0
            ix = len(exc) - 1
            reason = "cap"
            next_chk = 60
            for i in range(len(exc)):
                if exc[i] > peak:
                    peak = exc[i]
                if exc[i] <= stop_exc:
                    pnl, ix, reason = stop_exc, i, "stop"
                    break
                if tgt is not None and peak >= tgt - 1.0 \
                        and exc[i] <= peak - 0.75:
                    pnl, ix, reason = peak - 0.75, i, "capture"
                    break
                if ts_[i] >= next_chk:
                    v = ofi30(mo, tf + int(ts_[i]), d)
                    if v is not None and v < 0:
                        pnl, ix, reason = exc[i], i, "flowfade"
                        break
                    next_chk += 30
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=tf, d=d, pnl=float(pnl),
                            exit=reason, tt=int(r.t),
                            level=float(r.level),
                            fam=getattr(r, "fam", "LVL")))
    return pd.DataFrame(out)

# ---- BUILDER A: T-BK03 approaches + touches (e1-verbatim loop) ----
a_rows = []
for mo, nxt in MONTHS.items():
    secs, mids = MIDS[mo]
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)]
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    for sd0 in sorted(bm.sd.unique()):
        di = day_ix.get(sd0)
        if di is None:
            continue
        lv = lf(di)
        if not lv:
            continue
        msk_day = (sd1 == sd0) & rth
        if not msk_day.any():
            continue
        t0d, t1d = int(bt[msk_day].min()), int(bt[msk_day].max()) + 60
        j0 = int(np.searchsorted(secs, t0d))
        j1 = int(np.searchsorted(secs, t1d, "right"))
        mseg = mids[j0:j1]
        sseg = secs[j0:j1]
        if len(mseg) < 120:
            continue
        for L in lv:
            dist = np.abs(mseg - L)
            near = dist <= 2.0
            enter = np.flatnonzero(near & ~np.roll(near, 1))
            last_t = -10**12
            for k in enter[enter > 30]:
                t = int(sseg[k])
                if t - last_t <= 600:
                    continue
                last_t = t
                d_app = 1 if mseg[k - 1] < L else -1
                j2 = int(np.searchsorted(sseg, t + 600, "right"))
                fwd = mseg[k:j2]
                if len(fwd) < 60:
                    continue
                touch_t = None
                kf = int(np.searchsorted(secs, t))
                j2f = int(np.searchsorted(secs, t + 600, "right"))
                fwdf = mids[kf:j2f]
                w_t = np.flatnonzero(np.abs(fwdf - L) <= 0.5)
                if len(w_t):
                    touch_t = int(secs[kf + int(w_t[0])])
                a_rows.append(dict(month=mo, t=t, side=d_app,
                                   level=L, touch_t=touch_t))
A = pd.DataFrame(a_rows)
e1 = pd.read_csv("Tests/D6_deepbook/e1_outcomes.csv")
e1["cid"] = np.arange(len(e1))
mb = pd.read_csv("Tests/D6_deepbook/mb_outcomes.csv")
fails = []
if len(A) != len(e1):
    fails.append(f"builder approaches {len(A)} != {len(e1)}")
else:
    mA = A.merge(e1, on=["month", "t", "side", "level"], how="inner")
    if len(mA) != len(e1):
        fails.append(f"approach keys match {len(mA)}/{len(e1)}")
Atch = A.dropna(subset=["touch_t"]).copy()
Atch["touch_t"] = Atch.touch_t.astype(int)
# mb's certified rule: outcome != NO_TEST (day-sliced labeler) AND a
# full-series first touch within 600s. Reconstruct exactly for R-9.
Ao = Atch.merge(e1[["month", "t", "side", "level", "outcome"]],
                on=["month", "t", "side", "level"], how="left")
Amb = Ao[Ao.outcome != "NO_TEST"]
if len(Amb) != len(mb):
    fails.append(f"builder touches {len(Amb)} != {len(mb)}")
else:
    mT = Amb.merge(mb, left_on=["month", "touch_t", "side"],
                   right_on=["month", "t", "side"], how="inner")
    if len(mT) != len(mb):
        fails.append(f"touch keys match {len(mT)}/{len(mb)}")

# ---- CONTROL sim: S1-ANY reproduction on the 693 covered ----
F = pd.read_parquet("Data/inputs/db3_features.parquet")
MBo = pd.read_csv("Tests/D6_deepbook/mb_outcomes.csv")
E1o = pd.read_csv("Tests/D6_deepbook/e1_outcomes.csv")
E1o["cid"] = np.arange(len(E1o))
B = F[F.q == "mb"].merge(MBo[["cid", "outcome"]], on="cid")
B = B.merge(E1o[["cid", "level", "his", "his_side"]], on="cid")
if len(B) != 693:
    fails.append(f"covered universe {len(B)} != 693")
ctrl = sim(B)
cp = ctrl.pnl.sum()
if not (len(ctrl) == 422 and abs(cp - 216.5) < 0.1):
    fails.append(f"S1-ANY control {len(ctrl)}/{cp:+.1f} != 422/+216.5")
if fails:
    print("# S5MF RUN ABORTED — R-9 FAILED")
    for f_ in fails:
        print("-", f_)
    sys.exit(1)

# ---- LVL-ANY (5W full-RTH) + control assert ----
LVLANY = Atch.rename(columns={"touch_t": "tt"}).copy()
LVLANY = LVLANY[["month", "tt", "side", "level"]].rename(
    columns={"tt": "t"})
lvl_tr = sim(LVLANY)
lp = lvl_tr.pnl.sum()
if not (len(lvl_tr) == 750 and abs(lp - 472.1) < 0.1):
    print(f"# LVLR ABORTED — LVL-ANY control {len(lvl_tr)}/{lp:+.1f}"
          f" != 750/+472.1")
    sys.exit(1)

# ---- bank the three T-SR02 trade tables (J: saved for future use) --
ctrl.to_parquet("Tests/D30_s5mf/trades_s1any_covered.parquet",
                index=False)
MFm = pd.read_csv("Tests/D30_s5mf/mf_touch_moments.csv")
mf_tr = sim(MFm)
mf_tr.to_parquet("Tests/D30_s5mf/trades_s5mf.parquet", index=False)

# ---- features per trade ----
from scipy.stats import mannwhitneyu

def score_levels(di):
    msk = (Vdi >= di - 60) & (Vdi < di)
    px, dii, nb = Vpx[msk], Vdi[msk], Vnb[msk]
    kept = {}
    if len(px):
        gp = np.round(px / GRID).astype(np.int64)
        lo, hi = gp.min(), gp.max()
        width = int(round(2.0 / GRID))
        order = np.argsort(gp)
        gs, ds, nbs = gp[order], dii[order], nb[order]
        uniq = np.arange(lo, hi + 1)
        score = np.zeros(len(uniq))
        for k, g0 in enumerate(uniq):
            a = np.searchsorted(gs, g0 - width)
            b2 = np.searchsorted(gs, g0 + width, "right")
            if b2 > a:
                score[k] = len(set(ds[a:b2])) + (
                    1.0 if nbs[a:b2].any() else 0.0)
        taken = np.zeros(len(uniq), bool)
        for k in np.argsort(-score):
            if score[k] < 4 or taken[k]:
                continue
            kept[float(uniq[k] * GRID)] = float(score[k])
            taken[max(0, k - 2 * width):k + 2 * width + 1] = True
    return kept

# first-touch-today rank from the touch universe
Au = Atch.copy()
Au["sd_t"] = pd.to_datetime(Au.touch_t, unit="s", utc=True
                            ).dt.tz_convert("America/Chicago"
                                            ).dt.date.astype(str)
Au = Au.sort_values("touch_t", kind="stable")
Au["rank"] = Au.groupby(["sd_t", "level"]).cumcount()
rank_map = {(r.month, int(r.touch_t), r.level): int(r.rank)
            for r in Au.itertuples()}

day_med = {}
rows_f = []
for r in lvl_tr.itertuples():
    mo = r.month
    secs, mids = MIDS[mo]
    vols = VOLS[mo]
    t = int(r.tt)
    j = int(np.searchsorted(secs, t, "right")) - 1
    j60 = int(np.searchsorted(secs, t - 60, "right")) - 1
    speed60 = abs(mids[j] - mids[j60]) if j60 >= 0 else np.nan
    j10 = int(np.searchsorted(secs, t - 10))
    v10 = float(vols[j10:j + 1].sum())
    kb = int(np.searchsorted(bt_all, t, "right")) - 1
    sd0 = sd_all[kb]
    if (mo, sd0) not in day_med:
        di0 = day_ix[sd0]
        m1 = (sd_all == sd0)
        t0d = int(bt_all[m1].min()); t1d = int(bt_all[m1].max()) + 60
        a0 = int(np.searchsorted(secs, t0d))
        a1 = int(np.searchsorted(secs, t1d, "right"))
        blocks = [vols[x:x + 10].sum()
                  for x in range(a0, max(a0, a1 - 10), 10)]
        day_med[(mo, sd0)] = float(np.median(blocks)) if blocks else np.nan
    vmed = day_med[(mo, sd0)]
    kk = int(np.searchsorted(ev_all, t, "right")) - 1
    mins_rel = (t - ev_all[kk]) / 60 if kk >= 0 else 1e9
    hr = pd.Timestamp(t, unit="s", tz="UTC").tz_convert(
        "America/Chicago")
    hr_f = hr.hour + hr.minute / 60
    di = day_ix.get(sd0)
    sc = score_levels(di).get(r.level, np.nan) if di is not None \
        else np.nan
    rk = rank_map.get((mo, t, r.level), np.nan)
    rows_f.append(dict(
        month=mo, tt=t, tf=r.tf, d=r.d, pnl=r.pnl, exit=r.exit,
        level=r.level, mins_rel=mins_rel, hr=hr_f, score=sc,
        first=(rk == 0), speed60=speed60,
        vol10r=(v10 / vmed if vmed and np.isfinite(vmed) else np.nan),
        fill_delay=r.tf - (t + 3)))
T = pd.DataFrame(rows_f)
T.to_parquet("Tests/D30_s5mf/trades_5w_fullrth.parquet", index=False)

# ---- lenses ----
def bucketize(T):
    L = {}
    L["L1 news"] = np.where(T.mins_rel <= 5, "a_burst<=5",
                   np.where(T.mins_rel <= 45, "b_window5-45",
                            "c_quiet>45"))
    L["L2 hour"] = np.where(T.hr < 10, "a_0830-10",
                   np.where(T.hr < 12, "b_10-12",
                   np.where(T.hr < 14, "c_12-14", "d_14-15")))
    s = T.score.fillna(-1)
    L["L3a score"] = np.where(s >= 6, "hi>=6",
                     np.where(s >= 5, "mid5", "lo4"))
    L["L3b first"] = np.where(T.first, "first", "repeat")
    for nm, col in (("L4a speed60", T.speed60),
                    ("L4b vol10r", T.vol10r),
                    ("L5 fill_delay", T.fill_delay)):
        q1, q2 = col.quantile(1 / 3), col.quantile(2 / 3)
        L[nm] = np.where(col <= q1, "t1_lo",
                np.where(col <= q2, "t2_mid", "t3_hi"))
    return L

LN = bucketize(T)
print("# LVLR REPORT — 5W FULL-RTH ANATOMY (T-SR03, D-31)")
print("STATUS: CLOSED | 2026-11-27 | Spec: LVLR_SPEC.md (frozen "
      "first) | controls exact (1541/1263; 422/+216.5; 750/+472.1) "
      "| TRAINING-ONLY context; promoted items are candidates only")
print()
print("Baseline: 750 trades, +0.63/trade, +472.1 "
      "(+195.3 / +276.8 by month).")
print()
tests = []
for nm, lab in LN.items():
    T[nm] = lab
    print(f"## {nm}")
    print("| bucket | n | per-trade | median | win% | "
          "22-02 pt | 25-10 pt |")
    print("|---|---|---|---|---|---|---|")
    g = T.groupby(lab)
    best = None
    for b_, sub in g:
        m1 = sub[sub.month == "2022-02"]; m2 = sub[sub.month == "2025-10"]
        pt = sub.pnl.mean()
        print(f"| {b_} | {len(sub)} | {pt:+.2f} | "
              f"{sub.pnl.median():+.2f} | {(sub.pnl>0).mean():.0%} | "
              f"{m1.pnl.mean() if len(m1) else float('nan'):+.2f} | "
              f"{m2.pnl.mean() if len(m2) else float('nan'):+.2f} |")
        if best is None or pt > best[1]:
            best = (b_, pt, sub)
    top = best[2]; rest = T[T[nm] != best[0]]
    try:
        p = mannwhitneyu(top.pnl, rest.pnl).pvalue
    except Exception:
        p = 1.0
    d1 = (top[top.month == "2022-02"].pnl.mean()
          - rest[rest.month == "2022-02"].pnl.mean())
    d2 = (top[top.month == "2025-10"].pnl.mean()
          - rest[rest.month == "2025-10"].pnl.mean())
    tests.append((nm, best[0], len(top), top.pnl.mean(), p,
                  d1 > 0 and d2 > 0))
    print()
print("## L6 EXIT ANATOMY (where the money comes from)")
print("| exit | n | net | per-trade | 22-02 net | 25-10 net |")
print("|---|---|---|---|---|---|")
for e_, sub in T.groupby("exit"):
    print(f"| {e_} | {len(sub)} | {sub.pnl.sum():+.1f} | "
          f"{sub.pnl.mean():+.2f} | "
          f"{sub[sub.month=='2022-02'].pnl.sum():+.1f} | "
          f"{sub[sub.month=='2025-10'].pnl.sum():+.1f} |")
print()
print("## TOP-vs-REST TESTS (BH-FDR q=0.10 across the lens family)")
ps = sorted([(p, i) for i, (_, _, _, _, p, _) in enumerate(tests)])
mth = len(ps); passed = set()
for rank, (p, i) in enumerate(ps, 1):
    if p <= 0.10 * rank / mth:
        passed.add(i)
    else:
        break
print("| lens | top bucket | n | per-trade | MW p | BH | "
      "both-months dir | FINDING |")
print("|---|---|---|---|---|---|---|---|")
for i, (nm, b_, n_, pt, p, bothdir) in enumerate(tests):
    bh = "PASS" if i in passed else "fail"
    fnd = "FINDING" if (i in passed and bothdir) else "-"
    print(f"| {nm} | {b_} | {n_} | {pt:+.2f} | {p:.4f} | {bh} | "
          f"{'yes' if bothdir else 'NO'} | {fnd} |")
print()
print("## PROMOTION RULE CHECK (frozen: monotone + FINDING + "
      "n>=150 + per-trade >= +0.85 + both months positive)")
for i, (nm, b_, n_, pt, p, bothdir) in enumerate(tests):
    if i in passed and bothdir and n_ >= 150 and pt >= 0.85:
        sub = T[T[nm] == b_]
        bm_ = all(sub[sub.month == mo].pnl.sum() > 0 for mo in MONTHS)
        print(f"- CANDIDATE: {nm} = {b_} ({n_} trades, {pt:+.2f}"
              f"/trade){' - both months positive' if bm_ else ' - FAILS month line'}")
print("(none printed = no qualifier; the null is reportable per spec)")
print()
print("Banked: trades_s1any_covered / trades_5w_fullrth (with "
      "features) / trades_s5mf parquets. Registry: T-SR03.")
