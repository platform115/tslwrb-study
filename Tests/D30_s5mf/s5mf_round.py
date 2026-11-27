#!/usr/bin/env python3
"""
s5mf_round.py — T-SR02 Part A: S5-MF (family-edge touch universe),
ANY arm. Spec: S5MF_SPEC.md (frozen first). Sim copied verbatim from
s1_round.py (certified); builder controls reproduce T-BK03 (1541/1263)
and S1-ANY (422/+216.5) before any look.
RUN: python3 Tests/D30_s5mf/s5mf_round.py > Tests/D30_s5mf/S5MF_REPORT.md
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

# ---- LVL-ANY: incumbent universe, full RTH ----
LVLANY = Atch.rename(columns={"touch_t": "tt"}).copy()
LVLANY = LVLANY[["month", "tt", "side", "level"]].rename(
    columns={"tt": "t"})
lvl_tr = sim(LVLANY)

# ---- BUILDER B: family-edge touches ----
mf_rows = []
for mo, nxt in MONTHS.items():
    secs, mids = MIDS[mo]
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    sd1 = bm.sd.to_numpy()
    memo = {}
    def fam_edges(fam, sd0, t):
        key = (fam, sd0, t // 60)
        if key not in memo:
            memo[key] = [float(e) for e in
                         edges_at(R, sd0, np.datetime64(t, "s"), fam)]
        return memo[key]
    for sd0 in sorted(bm.sd.unique()):
        di = day_ix.get(sd0)
        if di is None:
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
        state = {}     # key -> dict(prev_near, last_fire)
        pend = {}      # key -> dict(ta, side, E, fam, deadline)
        for k in range(len(mseg)):
            t = int(sseg[k])
            px = mseg[k]
            cur = []
            for fam in ("SQZ", "GAP", "SHD", "REA"):
                for e in fam_edges(fam, sd0, t):
                    cur.append((fam, e))
            if sd0 in wrb_day:
                for c_, p in wrb_day[sd0]:
                    if c_ <= t:
                        cur.append(("WRB", p))
            if di >= 1 and np.isfinite(pd_hi[di - 1]):
                for p in (pd_hi[di - 1], pd_lo[di - 1],
                          pd_cl[di - 1]):
                    cur.append(("PDY", float(p)))
            # resolve pendings against frozen E
            done = []
            for key, pdg in pend.items():
                if t > pdg["deadline"]:
                    done.append(key)
                elif abs(px - pdg["E"]) <= 0.5:
                    mf_rows.append(dict(month=mo, t=t,
                                        side=pdg["side"],
                                        level=pdg["E"],
                                        fam=pdg["fam"]))
                    done.append(key)
            for key in done:
                del pend[key]
            for fam, e in cur:
                key = (fam, round(e, 2))
                near = abs(px - e) <= 2.0
                st = state.get(key)
                if st is None:
                    state[key] = {"prev_near": near,
                                  "last_fire": -10**12}
                    continue
                if (near and not st["prev_near"] and k > 30
                        and t - st["last_fire"] > 600
                        and len(mseg) - k >= 60
                        and key not in pend):
                    st["last_fire"] = t
                    d_app = 1 if mseg[k - 1] < e else -1
                    pend[key] = dict(ta=t, side=d_app, E=e,
                                     fam=fam, deadline=t + 600)
                st["prev_near"] = near
        for key, pdg in pend.items():
            kf = int(np.searchsorted(secs, int(sseg[-1]) + 1))
            j2f = int(np.searchsorted(secs, pdg["deadline"], "right"))
            if j2f > kf:
                w_t = np.flatnonzero(
                    np.abs(mids[kf:j2f] - pdg["E"]) <= 0.5)
                if len(w_t):
                    mf_rows.append(dict(
                        month=mo, t=int(secs[kf + int(w_t[0])]),
                        side=pdg["side"], level=pdg["E"],
                        fam=pdg["fam"]))
    print(f"MF {mo}: built", file=sys.stderr)
MF = pd.DataFrame(mf_rows)
MF.to_csv("Tests/D30_s5mf/mf_touch_moments.csv", index=False)
mf_tr = sim(MF)

# ---- REPORT ----
print("# S5MF REPORT — S5-MF PART A: FAMILY-EDGE TOUCHES, ANY ARM "
      "(T-SR02)")
print("STATUS: CLOSED | 2026-11-27 | Spec: S5MF_SPEC.md (frozen "
      "first) | R-9 dual controls exact (builder 1541/1263; S1-ANY "
      "422/+216.5) | Tier-R | TRAINING-ONLY cap per R-11")
print()
print("NOTE: the certified mb list excludes day-slice NO_TEST rows "
      "(an artifact of the T-BK03 labeler); the LVL-ANY and MF-ANY "
      "cells use the spec's clean definition (full-series touch "
      "within 600s, no outcome machinery) - for the incumbent "
      "universe that differs from mb by exactly 1 touch in 1264.")
print()
print("| cell | touches | trades | win | per-trade | pooled | "
      "by month (22-02/25-10) | worst | exits (stop/fade/capture/cap) |")
print("|---|---|---|---|---|---|---|---|---|")
for name, uni_n, tr in (("S1-ANY control (693 covered)", 693, ctrl),
                        ("LVL-ANY (full RTH)", len(LVLANY), lvl_tr),
                        ("MF-ANY (family edges)", len(MF), mf_tr)):
    nets = {mo: tr[tr.month == mo].pnl.sum() for mo in MONTHS}
    pooled = tr.pnl.sum()
    pt = pooled / max(1, len(tr))
    w = (tr.pnl > 0).mean() if len(tr) else 0
    ex = tr.exit.value_counts()
    exs = (f"{ex.get('stop', 0)}/{ex.get('flowfade', 0)}/"
           f"{ex.get('capture', 0)}/{ex.get('cap', 0)}")
    bym = "/".join(f"{nets[mo]:+.0f}" for mo in MONTHS)
    print(f"| {name} | {uni_n} | {len(tr)} | {w:.0%} | {pt:+.2f} | "
          f"{pooled:+.1f} | {bym} | {tr.pnl.min():+.2f} | {exs} |")
print()
print("## PER-FAMILY (MF-ANY; first-family tag, shared busy — "
      "NOT additive)")
print("| family | trades | net | per-trade | months net<0 |")
print("|---|---|---|---|---|")
for fam, g in mf_tr.groupby("fam"):
    mn = sum(1 for mo in MONTHS if g[g.month == mo].pnl.sum() < 0)
    tox = " TOXIC-FLAG" if mn >= 2 else ""
    print(f"| {fam} | {len(g)} | {g.pnl.sum():+.1f} | "
          f"{g.pnl.sum()/max(1,len(g)):+.2f} | {mn}/2{tox} |")
print()
lp = lvl_tr.pnl.sum(); mp_ = mf_tr.pnl.sum()
mpt = mp_ / max(1, len(mf_tr))
both = all(mf_tr[mf_tr.month == mo].pnl.sum() > 0 for mo in MONTHS)
worst = mf_tr.pnl.min()
toxbad = any(sum(1 for mo in MONTHS
                 if g[g.month == mo].pnl.sum() < 0) >= 2
             for _, g in mf_tr.groupby("fam"))
print("## VERDICT vs THE FROZEN LINES")
print(f"- controls exact: PASS")
print(f"- MF-ANY pooled > LVL-ANY pooled: "
      f"{'PASS' if mp_ > lp else 'FAIL'} ({mp_:+.1f} vs {lp:+.1f})")
print(f"- MF-ANY per-trade >= +0.40: "
      f"{'PASS' if mpt >= 0.40 else 'FAIL'} ({mpt:+.2f})")
print(f"- both months > 0: {'PASS' if both else 'FAIL'}")
print(f"- worst trade >= -2.1: "
      f"{'PASS' if worst >= -2.1 else 'FAIL'} ({worst:+.2f})")
print(f"- no unflagged toxic family: "
      f"{'FLAGGED - see table' if toxbad else 'PASS'}")
ok = (mp_ > lp and mpt >= 0.40 and both and worst >= -2.1
      and not toxbad)
print(f"OVERALL: "
      f"{'REGISTER S5-MF TRAINING-ONLY' if ok else 'PARTIAL - facts to J'}")
print()
print("Part B deliverable: mf_touch_moments.csv "
      f"({len(MF)} touch moments) for device-side 3s extraction.")
print()
print("Registry: T-SR02.")
