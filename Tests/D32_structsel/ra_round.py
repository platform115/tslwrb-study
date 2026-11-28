#!/usr/bin/env python3
"""
ra_round.py — T-SR08: reclaim anatomy + flow-conditioned reclaim
exit (D-33 round 2). Spec: RA_SPEC.md (frozen first). Machinery
verbatim from the certified fb_round lineage.
RUN: python3 Tests/D32_structsel/ra_round.py > Tests/D32_structsel/RA_REPORT.md
"""
# STALE-LINEAGE NOTE (2026-11-28, F-36/T-RH02): this CLOSED round
# ran on pre-stamp-fix baselines; its hardcoded R-9 asserts are
# stale by design. Re-running requires re-pointing them to the
# T-RH02 baselines. Its registered conclusions are annotated in
# BACKTEST_MATRIX.

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

MIDS, OFI = {}, {}
for mo in MONTHS:
    f = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    MIDS[mo] = (f.sec.to_numpy(np.int64), f.mid.to_numpy(float))
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
                            exit=reason,
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

# ---- family-edge machinery (per month resolver; per-minute memo) ---
RES = {}
for mo, nxt in MONTHS.items():
    bm_ = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
            ].reset_index(drop=True)
    RES[mo] = Resolver(bm_, zr)
memo_f = {}
def fam_edges_all(mo, sd0, t, di):
    key = (mo, sd0, t // 60)
    if key not in memo_f:
        out = []
        for fam in ("SQZ", "GAP", "SHD", "REA"):
            out += [float(e) for e in
                    edges_at(RES[mo], sd0, np.datetime64(t, "s"),
                             fam)]
        if sd0 in wrb_day:
            out += [p for c_, p in wrb_day[sd0] if c_ <= t]
        if di is not None and di >= 1 and np.isfinite(pd_hi[di - 1]):
            out += [float(pd_hi[di - 1]), float(pd_lo[di - 1]),
                    float(pd_cl[di - 1])]
        memo_f[key] = sorted(set(out))
    return memo_f[key]

def runway(mo, t, side, L):
    kb = int(np.searchsorted(bt_all, t, "right")) - 1
    sd0 = sd_all[kb]
    di = day_ix.get(sd0)
    E = L + 0.75 * side
    fe = fam_edges_all(mo, sd0, t, di)
    ah = [(p - E) * side for p in fe if (p - E) * side > 0.5]
    return min(ah) if ah else np.inf

# ---- touch table with runway ----
LVLANY = Atch.rename(columns={"touch_t": "tt"}).copy()
LVLANY = LVLANY[["month", "tt", "side", "level"]].rename(
    columns={"tt": "t"})
LVLANY["rwy"] = [runway(r.month, int(r.t), int(r.side),
                        float(r.level))
                 for r in LVLANY.itertuples()]

# ---- cells ----
ctrl_full = sim(LVLANY)
cp = ctrl_full.pnl.sum()
if not (len(ctrl_full) == 750 and abs(cp - 472.1) < 0.1):
    print(f"# RWY ABORTED — control {len(ctrl_full)}/{cp:+.1f}")
    sys.exit(1)

# RWY baseline control
RWYT = LVLANY[(LVLANY.rwy >= 2.0) & (LVLANY.rwy <= 8.0)]
rwy_base = sim(RWYT)
if not (len(rwy_base) == 102 and abs(rwy_base.pnl.sum() - 157.1) < 0.1):
    print(f"# FB ABORTED — RWY control {len(rwy_base)}/"
          f"{rwy_base.pnl.sum():+.1f}")
    sys.exit(1)

from scipy.stats import mannwhitneyu

def ofi30s(mo, t, sdn):
    return ofi30(mo, t, sdn)   # certified helper from head

def sim_var(sub, mode):
    """mode: 'fcr' flow-conditioned reclaim; 'fb25' unconditional
    x=0.25 (degenerate control). Reclaim threshold exc <= -1.00."""
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
                if exc[i] <= -1.00:
                    fire = True
                    if mode == "fcr":
                        v = ofi30s(mo, tf + int(ts_[i]), d)
                        fire = (v is not None and v < 0)
                    if fire:
                        pnl, ix, reason = -1.00, i, "failbrk"
                        break
                if tgt is not None and peak >= tgt - 1.0 \
                        and exc[i] <= peak - 0.75:
                    pnl, ix, reason = peak - 0.75, i, "capture"
                    break
                if ts_[i] >= next_chk:
                    v = ofi30s(mo, tf + int(ts_[i]), d)
                    if v is not None and v < 0:
                        pnl, ix, reason = exc[i], i, "flowfade"
                        break
                    next_chk += 30
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=tf, d=d, pnl=float(pnl),
                            exit=reason))
    return pd.DataFrame(out)

# degenerate-case control: fb25 must reproduce T-SR07's 104/+125.6
dg = sim_var(RWYT, "fb25")
if not (len(dg) == 104 and abs(dg.pnl.sum() - 125.6) < 0.1):
    print(f"# RA ABORTED — degenerate control {len(dg)}/"
          f"{dg.pnl.sum():+.1f} != 104/+125.6")
    sys.exit(1)

# ---- reclaim anatomy on certified baseline trades ----
def anatomy(base, uni):
    rows = []
    for r in base.itertuples():
        mo = r.month
        secs, mids = MIDS[mo]
        jf = int(np.searchsorted(secs, r.tf))
        j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
        # reconstruct exc path to its certified exit
        key = uni[(uni.month == mo)]
        # exc from fill to +900 (cap horizon)
        j9 = int(np.searchsorted(secs, r.tf + 900, "right"))
        # entry price: level +0.75d — level not in trade row for
        # fb-head sims; recover from pnl path start
        rows.append((r, jf, j9))
    return rows

ana = []
for uname, base, uni in (("5W-full", ctrl_full, LVLANY),
                         ("RWY[2,8]", rwy_base, RWYT)):
    um = uni.set_index(["month"])  # unused; levels come from uni rows
    # map fill->touch row for level
    lv_map = {}
    for rr in uni.itertuples():
        lv_map.setdefault((rr.month, int(rr.t)), (float(rr.level),
                                                  int(rr.side)))
    for r in base.itertuples():
        mo = r.month
        secs, mids = MIDS[mo]
        # find source touch: the touch with t <= tf <= t+123 matching d
        cand = [(abs(r.tf - t_), lvl, sd_) for (m_, t_), (lvl, sd_)
                in lv_map.items()
                if m_ == mo and 0 <= r.tf - t_ <= 125 and sd_ == r.d]
        if not cand:
            continue
        cand.sort()
        L = cand[0][1]
        d = int(r.d)
        ent = L + 0.75 * d
        jf = int(np.searchsorted(secs, r.tf))
        j9 = int(np.searchsorted(secs, r.tf + 900, "right"))
        exc = (mids[jf:j9] - ent) * d
        ts_ = (secs[jf:j9] - r.tf).astype(int)
        rec = np.flatnonzero(exc <= -1.00)
        if not len(rec):
            continue
        i0 = int(rec[0])
        trec = int(ts_[i0])
        mfe = float(exc[:i0].max()) if i0 > 0 else 0.0
        i10 = int(np.searchsorted(ts_, trec - 10))
        vel = float(exc[i10] - exc[i0]) if i10 < i0 else 0.0
        v = ofi30s(mo, r.tf + trec, d)
        ana.append(dict(uni=uname, month=mo, tf=r.tf,
                        final=r.pnl, stopped=(r.pnl <= -1.99),
                        t_rec=trec, mfe=mfe, vel=vel,
                        ofi=(np.nan if v is None else v)))
A = pd.DataFrame(ana)

print("# RA REPORT — RECLAIM ANATOMY + FLOW-CONDITIONED EXIT "
      "(T-SR08, D-33 R2)")
print("STATUS: CLOSED | 2026-11-27 | Spec: RA_SPEC.md (frozen "
      "first) | controls exact (incl. T-SR07 degenerate 104/+125.6)"
      " | TRAINING-ONLY context")
print()
for uname in ("5W-full", "RWY[2,8]"):
    S = A[A.uni == uname]
    print(f"## RECLAIM ANATOMY — {uname} "
          f"({len(S)} reclaimed trades; "
          f"{int(S.stopped.sum())} ended stopped)")
    tests = []
    S = S.copy()
    S["L_ofi_sign"] = np.where(S.ofi.isna(), "no-book",
                      np.where(S.ofi < 0, "against", "with/flat"))
    q1, q2 = S.t_rec.quantile(1/3), S.t_rec.quantile(2/3)
    S["L_time"] = np.where(S.t_rec <= q1, "t1_fast",
                  np.where(S.t_rec <= q2, "t2_mid", "t3_slow"))
    S["L_mfe"] = np.where(S.mfe >= 1.0, "mfe>=1.0",
                 np.where(S.mfe >= 0.5, "mfe0.5-1", "mfe<0.5"))
    q1v, q2v = S.vel.quantile(1/3), S.vel.quantile(2/3)
    S["L_vel"] = np.where(S.vel <= q1v, "v1_slow",
                 np.where(S.vel <= q2v, "v2_mid", "v3_fast"))
    for nm in ("L_ofi_sign", "L_time", "L_mfe", "L_vel"):
        print(f"### {nm}")
        print("| bucket | n | stop-rate | mean final | "
              "22-02 stop% | 25-10 stop% |")
        print("|---|---|---|---|---|---|")
        best = None
        for b_, sub in S.groupby(nm):
            m1 = sub[sub.month == "2022-02"]
            m2 = sub[sub.month == "2025-10"]
            print(f"| {b_} | {len(sub)} | {sub.stopped.mean():.0%} |"
                  f" {sub.final.mean():+.2f} | "
                  f"{m1.stopped.mean() if len(m1) else float('nan'):.0%} | "
                  f"{m2.stopped.mean() if len(m2) else float('nan'):.0%} |")
            if best is None or sub.final.mean() > best[1]:
                best = (b_, sub.final.mean(), sub)
        top = best[2]; rest = S[S[nm] != best[0]]
        try:
            p = mannwhitneyu(top.final, rest.final).pvalue
        except Exception:
            p = 1.0
        d1 = (top[top.month == "2022-02"].final.mean()
              - rest[rest.month == "2022-02"].final.mean())
        d2 = (top[top.month == "2025-10"].final.mean()
              - rest[rest.month == "2025-10"].final.mean())
        tests.append((nm, best[0], len(top), best[1], p,
                      d1 > 0 and d2 > 0))
        print()
    ps = sorted([(p, i) for i, (_,_,_,_,p,_) in enumerate(tests)])
    passed = set()
    for rank, (p, i) in enumerate(ps, 1):
        if p <= 0.10 * rank / len(ps):
            passed.add(i)
        else:
            break
    print(f"### BH (q=0.10, {uname})")
    print("| lens | top | n | mean final | p | BH | both-dir | "
          "FINDING |")
    print("|---|---|---|---|---|---|---|---|")
    for i, (nm, b_, n_, m_, p, bd) in enumerate(tests):
        print(f"| {nm} | {b_} | {n_} | {m_:+.2f} | {p:.4f} | "
              f"{'PASS' if i in passed else 'fail'} | "
              f"{'yes' if bd else 'NO'} | "
              f"{'FINDING' if (i in passed and bd) else '-'} |")
    print()

# ---- constructive rule cells ----
print("## FLOW-CONDITIONED RECLAIM EXIT (the one frozen rule)")
print("| universe | cell | trades | per-trade | pooled | by month |"
      " stops | failbrk | worst |")
print("|---|---|---|---|---|---|---|---|---|")
res = {}
for uname, uni, base in (("5W-full", LVLANY, ctrl_full),
                         ("RWY[2,8]", RWYT, rwy_base)):
    nets = {mo: base[base.month == mo].pnl.sum() for mo in MONTHS}
    ex = base.exit.value_counts()
    print(f"| {uname} | baseline | {len(base)} | "
          f"{base.pnl.mean():+.2f} | {base.pnl.sum():+.1f} | "
          f"{'/'.join(f'{nets[mo]:+.0f}' for mo in MONTHS)} | "
          f"{ex.get('stop',0)} | - | {base.pnl.min():+.2f} |")
    tr = sim_var(uni, "fcr")
    res[uname] = tr
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    ex = tr.exit.value_counts()
    print(f"| {uname} | FCR | {len(tr)} | {tr.pnl.mean():+.2f} | "
          f"{tr.pnl.sum():+.1f} | "
          f"{'/'.join(f'{nets[mo]:+.0f}' for mo in MONTHS)} | "
          f"{ex.get('stop',0)} | {ex.get('failbrk',0)} | "
          f"{tr.pnl.min():+.2f} |")
print()
print("## MECHANISM (twin-matched; busy-freed separate)")
print("| universe | changed | delta (22-02/25-10/pooled) | rescued "
      "| killed | busy add/drop (net) |")
print("|---|---|---|---|---|---|")
vb = {}
for uname, base in (("5W-full", ctrl_full), ("RWY[2,8]", rwy_base)):
    bk = base.drop_duplicates(["month","tf"]).set_index(["month","tf"])
    tk = res[uname].drop_duplicates(["month","tf"]).set_index(["month","tf"])
    shared = bk.index.intersection(tk.index)
    d_ = (tk.loc[shared].pnl - bk.loc[shared].pnl)
    ch = d_[d_.abs() > 1e-9]
    chm = {mo: ch[[i for i in ch.index if i[0] == mo]].sum()
           for mo in MONTHS}
    resc = int(((bk.loc[shared].pnl <= -1.99) & (d_ > 1e-9)).sum())
    kill = int(((bk.loc[shared].pnl > 0) & (d_ < -1e-9)).sum())
    add = tk.index.difference(bk.index)
    drop = bk.index.difference(tk.index)
    addp = tk.loc[add].pnl.sum() if len(add) else 0.0
    dropp = bk.loc[drop].pnl.sum() if len(drop) else 0.0
    print(f"| {uname} | {len(ch)} | {chm['2022-02']:+.1f}/"
          f"{chm['2025-10']:+.1f}/{ch.sum():+.1f} | {resc} | {kill} "
          f"| {len(add)}/{len(drop)} ({addp-dropp:+.1f}) |")
    if uname == "RWY[2,8]":
        vb = dict(ch=ch.sum(), chm=chm, tr=res[uname])
print()
tr = vb["tr"]; chm = vb["chm"]
pooled = tr.pnl.sum()
both_ok = all(v >= 0 for v in chm.values())
print("## VERDICT vs THE FROZEN LINES (RWY-FCR)")
print(f"- controls exact: PASS")
print(f"- mechanism delta > 0 pooled, >= 0 both months: "
      f"{'PASS' if (vb['ch'] > 0 and both_ok) else 'FAIL'} "
      f"({vb['ch']:+.1f}; {chm['2022-02']:+.1f}/"
      f"{chm['2025-10']:+.1f})")
print(f"- full-cell pooled > +157.1: "
      f"{'PASS' if pooled > 157.1 else 'FAIL'} ({pooled:+.1f})")
print(f"- worst >= -2.1: "
      f"{'PASS' if tr.pnl.min() >= -2.1 else 'FAIL'} "
      f"({tr.pnl.min():+.2f})")
ok = (vb["ch"] > 0 and both_ok and pooled > 157.1
      and tr.pnl.min() >= -2.1)
print(f"OVERALL: "
      f"{'ADOPT-AS-CANDIDATE - J gates' if ok else 'facts to J'}")
print()
print("Registry: T-SR08.")
