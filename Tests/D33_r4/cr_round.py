#!/usr/bin/env python3
"""
cr_round.py — T-SA02: S5-line + level-detector constants ranges.
Spec: CR_SPEC.md (frozen first). Builder, levels and sim derive
verbatim from the certified s5mf/rwy lineage, parameterized per
dial; the CENTER cell must reproduce the certified builder (1541
approaches / 1263 touches) and sim (750/+472.1) exactly before any
cell is read. Checkpointed per cell; rerun until REPORT.
RUN: python3 Tests/D33_r4/cr_round.py   (repeat until done)
"""
import os, sys, time
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p4_3_confluence_news import news_sets                   # noqa

T0 = time.time()
MONTHS = {"2022-02": "2022-03-01", "2025-10": "2025-11-01"}
GRID = 0.25
CK = "Tests/D33_r4/cells.parquet"

ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9
b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
zr = None

MIDS, OFI = {}, {}
for mo in MONTHS:
    f = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    MIDS[mo] = (f.sec.to_numpy(np.int64), f.mid.to_numpy(float))
    o = pd.read_parquet(f"Data/inputs/ofi10_per_sec_{mo}.parquet")
    OFI[mo] = (o.sec.to_numpy(np.int64),
               np.concatenate([[0.0], np.cumsum(
                   (o.ofi_b - o.ofi_a).to_numpy(float))]))

def ofi30(mo, t, sdn, win=30):
    osec, ocum = OFI[mo]
    i = int(np.searchsorted(osec, t - win))
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
def lf(di, tol=2.0, m=4, W=60, kill=5.0):
    key = (di, tol, m, W, kill)
    if key not in lv_cache:
        msk = (Vdi >= di - W) & (Vdi < di)
        out = []
        for p in density_levels(Vpx[msk], Vdi[msk], Vnb[msk], tol, m):
            sel = np.abs(Vpx[msk] - p) <= tol
            last_mem = int(Vdi[msk][sel].max())
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - p) > kill).all()):
                out.append(p)
        lv_cache[key] = out
    return lv_cache[key]


bnr = b[~b.is_roll_day]
bt_all = bnr.ts_event.dt.tz_convert(None).astype("int64"
                                                ).to_numpy() // 10**9
sd_all = bnr.sd.to_numpy()

def build_touches(az=2.0, td=0.5, sp=600, lvkw=None):
    """Certified builder A (s5mf lineage), parameterized."""
    lvkw = lvkw or {}
    rows = []
    napp = 0
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
            lv = lf(di, **lvkw)
            if not lv:
                continue
            msk_day = (sd1 == sd0) & rth
            if not msk_day.any():
                continue
            t0d = int(bt[msk_day].min())
            t1d = int(bt[msk_day].max()) + 60
            j0 = int(np.searchsorted(secs, t0d))
            j1 = int(np.searchsorted(secs, t1d, "right"))
            mseg = mids[j0:j1]; sseg = secs[j0:j1]
            if len(mseg) < 120:
                continue
            for L in lv:
                dist = np.abs(mseg - L)
                near = dist <= az
                enter = np.flatnonzero(near & ~np.roll(near, 1))
                last_t = -10**12
                for k in enter[enter > 30]:
                    t = int(sseg[k])
                    if t - last_t <= sp:
                        continue
                    last_t = t
                    d_app = 1 if mseg[k - 1] < L else -1
                    j2 = int(np.searchsorted(sseg, t + 600, "right"))
                    if j2 - k < 60:
                        continue
                    napp += 1
                    kf = int(np.searchsorted(secs, t))
                    j2f = int(np.searchsorted(secs, t + 600, "right"))
                    w_t = np.flatnonzero(
                        np.abs(mids[kf:j2f] - L) <= td)
                    if len(w_t):
                        rows.append(dict(month=mo,
                                         t=int(secs[kf + int(w_t[0])]),
                                         side=d_app, level=L))
    return pd.DataFrame(rows), napp

def sim(sub, off=0.75, stopd=1.25, ttl=120, armd=1.0, gb=0.75,
        fs=60, fstep=30, cap=900, lvkw=None):
    """Certified S5 sim (s1 lineage), parameterized."""
    lvkw = lvkw or {}
    out = []
    for mo in MONTHS:
        secs, mids = MIDS[mo]
        tt = sub[sub.month == mo].sort_values("t", kind="stable")
        busy = -10**12
        for r in tt.itertuples():
            t0 = int(r.t) + 3
            if t0 < busy:
                continue
            d = int(r.side); L = float(r.level)
            ent = L + off * d
            j0 = int(np.searchsorted(secs, t0))
            j1 = int(np.searchsorted(secs, t0 + ttl, "right"))
            seg = mids[j0:j1]
            hit = np.flatnonzero((seg >= ent) if d > 0
                                 else (seg <= ent))
            if not len(hit):
                continue
            jf = j0 + int(hit[0]); tf = int(secs[jf])
            if tf < busy:
                continue
            kb = int(np.searchsorted(bt_all, tf, "right")) - 1
            di = day_ix.get(sd_all[kb]) if kb >= 0 else None
            lv = lf(di, **lvkw) if di is not None else []
            ahead = sorted([(p - ent) * d for p in lv
                            if (p - ent) * d > 0.5])
            tgt = ahead[0] if ahead else None
            j4 = int(np.searchsorted(secs, tf + cap, "right"))
            exc = (mids[jf:j4] - ent) * d
            ts_ = (secs[jf:j4] - tf).astype(int)
            stop_exc = (L - stopd * d - ent) * d
            peak = 0.0
            pnl = exc[-1] if len(exc) else 0.0
            ix = len(exc) - 1
            next_chk = fs
            for i in range(len(exc)):
                if exc[i] > peak:
                    peak = exc[i]
                if exc[i] <= stop_exc:
                    pnl, ix = stop_exc, i
                    break
                if tgt is not None and peak >= tgt - armd \
                        and exc[i] <= peak - gb:
                    pnl, ix = peak - gb, i
                    break
                if ts_[i] >= next_chk:
                    v = ofi30(mo, tf + int(ts_[i]), d)
                    if v is not None and v < 0:
                        pnl, ix = exc[i], i
                        break
                    next_chk += fstep
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, pnl=float(pnl)))
    return pd.DataFrame(out)

CELLS = [("CENTER", {}, {}, {})]
for nm, kw in (("offset-0.50", dict(off=0.50)),
               ("offset-1.00", dict(off=1.00)),
               ("ttl-90", dict(ttl=90)), ("ttl-180", dict(ttl=180)),
               ("stop-1.00", dict(stopd=1.00)),
               ("stop-1.50", dict(stopd=1.50)),
               ("arm-0.75", dict(armd=0.75)),
               ("arm-1.50", dict(armd=1.50)),
               ("giveback-0.50", dict(gb=0.50)),
               ("giveback-1.00", dict(gb=1.00)),
               ("fadestart-45", dict(fs=45)),
               ("fadestart-90", dict(fs=90)),
               ("fadestep-15", dict(fstep=15)),
               ("fadestep-45", dict(fstep=45)),
               ("cap-600", dict(cap=600)),
               ("cap-1200", dict(cap=1200))):
    CELLS.append((nm, {}, kw, {}))
for nm, ukw in (("approach-1.5", dict(az=1.5)),
                ("approach-2.5", dict(az=2.5)),
                ("touch-0.25", dict(td=0.25)),
                ("touch-0.75", dict(td=0.75)),
                ("spacing-300", dict(sp=300)),
                ("spacing-900", dict(sp=900))):
    CELLS.append((nm, ukw, {}, {}))
for nm, lkw in (("lvl-tol-1.5", dict(tol=1.5)),
                ("lvl-tol-2.5", dict(tol=2.5)),
                ("lvl-score-3", dict(m=3)), ("lvl-score-5", dict(m=5)),
                ("lvl-window-45", dict(W=45)),
                ("lvl-window-75", dict(W=75)),
                ("lvl-kill-3.75", dict(kill=3.75)),
                ("lvl-kill-6.25", dict(kill=6.25))):
    CELLS.append((nm, {}, {}, lkw))

done = pd.read_parquet(CK) if os.path.exists(CK) else \
    pd.DataFrame(columns=["cell", "n_touch", "n", "net", "pt",
                          "m1", "m2"])
done_set = set(done.cell)
U_center = None
for name, ukw, skw, lkw in CELLS:
    if name in done_set:
        continue
    if time.time() - T0 > 480:
        print(f"CONTINUE ({len(done_set)}/{len(CELLS)} cells)")
        sys.exit(0)
    U, napp = build_touches(**ukw, lvkw=lkw)
    if name == "CENTER":
        if not (napp == 1541 and len(U) == 1264):
            # mb-rule: certified touches = 1264 full-series incl the
            # NO_TEST edge case; builder control is on these counts
            print(f"# ABORTED — center builder {napp}/{len(U)}")
            sys.exit(1)
    tr = sim(U, **skw, lvkw=lkw)
    if name == "CENTER":
        if not (len(tr) == 750 and abs(tr.pnl.sum() - 472.1) < 0.1):
            print(f"# ABORTED — center sim {len(tr)}/"
                  f"{tr.pnl.sum():+.1f}")
            sys.exit(1)
    m1 = tr[tr.month == "2022-02"].pnl.sum()
    m2 = tr[tr.month == "2025-10"].pnl.sum()
    done = pd.concat([done, pd.DataFrame([dict(
        cell=name, n_touch=len(U), n=len(tr),
        net=float(tr.pnl.sum()),
        pt=float(tr.pnl.mean() if len(tr) else 0),
        m1=float(m1), m2=float(m2))])], ignore_index=True)
    done.to_parquet(CK, index=False)
    done_set.add(name)
    print(f"{name}: {len(tr)}/{tr.pnl.sum():+.1f}", flush=True)

# ---- report ----
C = done.set_index("cell")
base = C.loc["CENTER"]
DIALS = {"offset": ["offset-0.50", "offset-1.00"],
         "ttl": ["ttl-90", "ttl-180"],
         "stop": ["stop-1.00", "stop-1.50"],
         "arm": ["arm-0.75", "arm-1.50"],
         "giveback": ["giveback-0.50", "giveback-1.00"],
         "fade-start": ["fadestart-45", "fadestart-90"],
         "fade-step": ["fadestep-15", "fadestep-45"],
         "cap": ["cap-600", "cap-1200"],
         "approach-zone": ["approach-1.5", "approach-2.5"],
         "touch-distance": ["touch-0.25", "touch-0.75"],
         "level-spacing": ["spacing-300", "spacing-900"],
         "lvl-tolerance": ["lvl-tol-1.5", "lvl-tol-2.5"],
         "lvl-score": ["lvl-score-3", "lvl-score-5"],
         "lvl-window": ["lvl-window-45", "lvl-window-75"],
         "lvl-kill": ["lvl-kill-3.75", "lvl-kill-6.25"]}
print("# CR REPORT — S5-LINE CONSTANTS RANGES (T-SA02, D-33 R4)")
print("STATUS: CLOSED | 2026-11-28 | Spec: CR_SPEC.md (frozen "
      "first) | center controls exact (1541/1264 builder; "
      "750/+472.1 sim) | NOTHING adopted (T-SA01 law)")
print()
print(f"Baseline: 750 trades, +472.1 (+195.3 / +276.8).")
print()
print("| cell | touches | trades | net | per-trade | 22-02 | "
      "25-10 |")
print("|---|---|---|---|---|---|---|")
for name, *_ in CELLS:
    r = C.loc[name]
    print(f"| {name} | {int(r.n_touch)} | {int(r.n)} | "
          f"{r.net:+.1f} | {r.pt:+.2f} | {r.m1:+.1f} | "
          f"{r.m2:+.1f} |")
print()
print("## LABELS (T-SA01 convention: ROBUST within +-15% pooled "
      "net AND months same-direction; SENSITIVE beyond; KNIFE-EDGE "
      "= sign flip)")
print("| dial | low cell | high cell | label |")
print("|---|---|---|---|")
flagged = []
for dial, (lo, hi) in DIALS.items():
    lab = "ROBUST"
    for c in (lo, hi):
        r = C.loc[c]
        if r.net <= 0 or r.m1 <= 0 or r.m2 <= 0:
            lab = "KNIFE-EDGE"
            break
        if abs(r.net - base.net) / base.net > 0.15:
            lab = "SENSITIVE"
    lo_r, hi_r = C.loc[lo], C.loc[hi]
    print(f"| {dial} | {lo_r.net:+.1f} | {hi_r.net:+.1f} | {lab} |")
    if lab != "ROBUST":
        flagged.append((dial, lab))
print()
print("## SUMMARY")
if flagged:
    for d_, l_ in flagged:
        print(f"- {d_}: {l_}")
else:
    print("- ALL DIALS ROBUST.")
print()
print("Registry: T-SA02.")
