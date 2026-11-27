#!/usr/bin/env python3
"""
rwy_round.py — T-SR05: the runway selector as a strategy (D-32b).
Spec: RWY_SPEC.md (frozen first). Builder+sim verbatim from the
certified s5mf_round lineage; family-edge machinery from g26/ssel.
RUN: python3 Tests/D32_structsel/rwy_round.py > Tests/D32_structsel/RWY_REPORT.md
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

CELLS = {"RWY[2,8] (FROZEN)": (2.0, 8.0),
         "RWY[1.5,8]": (1.5, 8.0), "RWY[2,6]": (2.0, 6.0),
         "RWY[2,10]": (2.0, 10.0), "RWY[3,8]": (3.0, 8.0)}
print("# RWY REPORT — THE RUNWAY SELECTOR AS A STRATEGY "
      "(T-SR05, D-32b)")
print("STATUS: CLOSED | 2026-11-27 | Spec: RWY_SPEC.md (frozen "
      "first) | controls exact (builder 1541/1263; S1-ANY "
      "422/+216.5; 5W full-RTH 750/+472.1) | TRAINING-ONLY cap")
print()
print("| cell | touches | trades | win | per-trade | pooled | "
      "by month | worst | stop% | capture% |")
print("|---|---|---|---|---|---|---|---|---|---|")
nets0 = {mo: ctrl_full[ctrl_full.month == mo].pnl.sum()
         for mo in MONTHS}
print(f"| 5W full-RTH baseline | {len(LVLANY)} | 750 | "
      f"{(ctrl_full.pnl>0).mean():.0%} | +0.63 | +472.1 | "
      f"{'/'.join(f'{nets0[mo]:+.0f}' for mo in MONTHS)} | -2.00 | "
      f"{(ctrl_full.exit=='stop').mean():.0%} | "
      f"{(ctrl_full.exit=='capture').mean():.0%} |")
res = {}
for nm, (lo_, hi_) in CELLS.items():
    sub = LVLANY[(LVLANY.rwy >= lo_) & (LVLANY.rwy <= hi_)]
    tr = sim(sub)
    res[nm] = tr
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    pooled = tr.pnl.sum()
    pt = pooled / max(1, len(tr))
    print(f"| {nm} | {len(sub)} | {len(tr)} | "
          f"{(tr.pnl>0).mean():.0%} | {pt:+.2f} | {pooled:+.1f} | "
          f"{'/'.join(f'{nets[mo]:+.0f}' for mo in MONTHS)} | "
          f"{tr.pnl.min():+.2f} | {(tr.exit=='stop').mean():.0%} | "
          f"{(tr.exit=='capture').mean():.0%} |")
print()
tr = res["RWY[2,8] (FROZEN)"]
pooled = tr.pnl.sum(); pt = pooled / max(1, len(tr))
both = all(tr[tr.month == mo].pnl.sum() > 0 for mo in MONTHS)
worst = tr.pnl.min()
sr = (tr.exit == "stop").mean()
print("## VERDICT vs THE FROZEN LINES (RWY[2,8] only)")
print(f"- controls exact: PASS")
print(f"- n >= 100: {'PASS' if len(tr) >= 100 else 'FAIL'} "
      f"({len(tr)})")
print(f"- per-trade >= +1.00: {'PASS' if pt >= 1.0 else 'FAIL'} "
      f"({pt:+.2f})")
print(f"- both months positive: {'PASS' if both else 'FAIL'}")
print(f"- worst >= -2.1: {'PASS' if worst >= -2.1 else 'FAIL'} "
      f"({worst:+.2f})")
print(f"- stop-rate < 47%: {'PASS' if sr < 0.47 else 'FAIL'} "
      f"({sr:.0%})")
ok = (len(tr) >= 100 and pt >= 1.0 and both and worst >= -2.1
      and sr < 0.47)
print(f"OVERALL: {'REGISTER 5W-RWY TRAINING-ONLY' if ok else 'PARTIAL - facts to J'}")
tr.to_parquet("Tests/D32_structsel/trades_5w_rwy.parquet",
              index=False)
print()
print("Registry: T-SR05.")
