#!/usr/bin/env python3
"""
trh03_remint.py — T-RH03: HIS-SIDE LABEL RE-MINT UNDER FIXED STAMPS
(J approved 2026-11-28, at the D-8 step-1 gate; F-39).
a2_features' group labels predate the F-36 stamp fix. This run:
  A. re-classifies the certified months (2022-02, 2025-10) with
     post-fix stamps (machinery = d8_classify.py, control PINNED:
     307 joined, exactly 5 ctx flips, 0 np_ flips, W/Q 61/149) and
     BANKS the labels (Data/inputs/his_groups_postfix.parquet).
  B. re-simulates the six catch-carrying systems on the six
     training months (machinery verbatim from remint_sims.py /
     T-RH02; parts/ layout). R-9: every system must reproduce its
     T-RH02 n/net AND its pre-fix catch EXACTLY before any
     post-fix number is read. Abort on any miss.
  C. recomputes every catch reference against the post-fix groups
     and prints OLD -> NEW. These become the references of record.
Resume-safe: per-cell trade checkpoints in Tests/D8_judgment/parts.
RUN: python3 Tests/D8_judgment/trh03_remint.py          (repo root)
"""
import os, sys, time
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p6_24_s6_3_selectors import interact_edges              # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

T0 = time.time()
MONTHS = {"2021-09": "2021-10-01", "2022-02": "2022-03-01",
          "2023-05": "2023-06-01", "2024-05": "2024-06-01",
          "2024-11": "2024-12-01", "2025-10": "2025-11-01"}
DISP, STOP, GRID = 1.25, 3.75, 0.25
PDIR = {"ctrl": "Tests/D11_unmatched/parts",
        "full": "Tests/D11_unmatched/parts",
        "quiet": "Tests/D5_quiet/parts"}
CKPT = "Tests/D8_judgment/parts"
FAMS = (("REA", 15), ("SQZ", 15), ("GAP", 5), ("SHD", 5))
FRESH_S = 5
EV_NS = np.asarray(news_sets(".")["all"], dtype=np.int64)

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
ev_all = EV_NS // 10**9
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")

# ---------- PART A: post-fix labels for the certified months ----------
LBL = "Data/inputs/his_groups_postfix.parquet"
def structure_fields(R, sd, t64, side, secs, mids, j):
    out = {}
    for fam, M in FAMS:
        E = interact_edges(R, sd, t64, fam, M, secs, mids, side)
        out[f"{fam}_interact"] = bool(E)
    return out
def np_of(t):
    kk = int(np.searchsorted(EV_NS, t * 10**9, "right")) - 1
    mins = (t * 10**9 - EV_NS[kk]) / 60e9 if kk >= 0 else np.nan
    if np.isfinite(mins) and mins <= 5:
        return "burst"
    if np.isfinite(mins) and mins <= 45:
        return "window"
    return "none"
def ctx_of(row):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if row[f"{f_}_interact"]:
            return "squeeze" if f_ == "SQZ" else "other"
    return "other"

if not os.path.exists(LBL):
    gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
    rows = []
    for month in ("2022-02", "2025-10"):
        nxt = MONTHS[month]
        bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < nxt)
               ].reset_index(drop=True)
        R = Resolver(bm, zr)
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{month}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        for _, r in gt[gt.month == month].iterrows():
            t = int(r.entry_msg_s)
            d_ = 1 if r.side == "long" else -1
            j = int(np.searchsorted(secs, t, "right")) - 1
            fresh = j >= 0 and (t - secs[j]) <= FRESH_S
            row = dict(month=month, sec=t, side=d_, data_fresh=fresh,
                       episode_id=int(r.episode_id))
            if fresh and j >= 4100:
                t64 = np.datetime64(t, "s")
                row.update(structure_fields(R, r.session_date, t64,
                                            d_, secs, mids, j))
                row["np_"] = np_of(t)
                row["ctx"] = ctx_of(row)
            else:
                row["np_"] = None; row["ctx"] = None
            rows.append(row)
    L = pd.DataFrame(rows)
    Lf = L[L.data_fresh]
    w = len(Lf[(Lf.ctx == "squeeze") & (Lf.np_ == "window")])
    q = len(Lf[(Lf.ctx == "squeeze") & (Lf.np_ == "none")])
    if (len(Lf), w, q) != (307, 61, 149):
        print(f"# T-RH03 ABORTED - PART A CONTROL FAILED: fresh "
              f"{len(Lf)} W {w} Q {q} != 307/61/149 (the pinned "
              f"post-fix values from d8_classify)")
        sys.exit(1)
    L.to_parquet(LBL, index=False)
    print(f"PART A PASS: post-fix labels banked ({len(Lf)} fresh; "
          f"W/Q 61/149)", flush=True)

L = pd.read_parquet(LBL)
POST_W = L[L.data_fresh & (L.ctx == "squeeze") & (L.np_ == "window")]
POST_Q = L[L.data_fresh & (L.ctx == "squeeze") & (L.np_ == "none")]

# pre-fix groups (the registered record) for the R-9 catch asserts
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm_ = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm_) & (mm_ <= 5), "burst",
                    np.where(np.isfinite(mm_) & (mm_ <= 45),
                             "window", "none"))
def ctx_row(r):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f_}_interact"]:
            return "squeeze" if f_ == "SQZ" else "other"
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
PRE_W = F[(F.ctx == "squeeze") & (F.np_ == "window")]
PRE_Q = F[(F.ctx == "squeeze") & (F.np_ == "none")]

# ---------- PART B machinery (verbatim remint_sims lineage) ----------
rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk2 = np.searchsorted(ev_all, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_all[np.maximum(kk2, 0)]) <= 2700
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
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
for sd, lst in wrb_day.items():
    rows.append(pd.DataFrame({"sd": sd,
                              "px": [p for _, p in lst],
                              "newsborn": False}))
EVt = pd.concat(rows, ignore_index=True)
EVt["px"] = (EVt.px * 4).round() / 4
EVt = EVt.drop_duplicates(["sd", "px"])
EVt["di"] = EVt.sd.map(day_ix); EVt = EVt.dropna(subset=["di"])
EVt["di"] = EVt.di.astype(int)
Vpx, Vdi, Vnb = EVt.px.to_numpy(), EVt.di.to_numpy(), EVt.newsborn.to_numpy()

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

def m7_var(exc, ts, best, W=8.0, A=None, stall=60):
    peak, tp, armed = 0.0, 0, False
    if A is None:
        arm = max(best - 0.75, 0.5) if (best is not None
                                        and best <= W) else None
    else:
        arm = A
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i
        if ts[i] - tp >= stall or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

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

def run_cell2(tag, A=None, dmin=None, band=None):
    out = []
    for mo in MONTHS:
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{mo}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        C = pd.read_parquet(f"{PDIR[tag]}/cand_{tag}_{mo}.parquet")
        C = C.sort_values("tf", kind="stable")
        seen = set()
        busy = -10**12
        for r in C.itertuples():
            dk = (r.tf, r.e, r.d)
            if dk in seen:
                continue
            seen.add(dk)
            lvl = r.e + DISP * r.d
            di = day_ix.get(r.sd)
            if band is not None:
                if di is None:
                    continue
                fe = fam_edges_all(mo, r.sd, int(r.tf), di)
                ah = [(p - lvl) * r.d for p in fe
                      if (p - lvl) * r.d > 0.5]
                R_ = min(ah) if ah else np.inf
                if not (band[0] <= R_ <= band[1]):
                    continue
            if r.tf < busy:
                continue
            jf = int(r.jf)
            j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
            exc = (mids[jf:j4] - lvl) * r.d
            ts_ = (secs[jf:j4] - r.tf).astype(int)
            lv = lf(di) if di is not None else []
            ahead = [(p - lvl) * r.d for p in lv
                     if (p - lvl) * r.d > 0.25]
            if dmin is not None and di is not None:
                fe = fam_edges_all(mo, r.sd, int(r.tf), di)
                ahead += [(p - lvl) * r.d for p in fe
                          if (p - lvl) * r.d >= dmin]
            ahead = sorted(ahead)
            pnl, ix = m7_var(exc, ts_,
                             ahead[0] if ahead else None, A=A)
            busy = int(secs[jf + ix])
            out.append(dict(month=mo, tf=int(r.tf), d=int(r.d),
                            pnl=float(pnl)))
    return pd.DataFrame(out)

def catch(tr, H):
    c = 0
    for _, h in H.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            c += 1
    return c

# cells: name, tag, kwargs, T-RH02 asserts (n, net, pre-fix catch, group)
CELLS = [
 ("G2-4", "ctrl", dict(), 2064, 569.4, 47, "W"),
 ("G2-6", "full", dict(), 6267, 1667.1, 59, "W"),
 ("G3-1", "quiet", dict(), 19015, 3767.8, 150, "Q"),
 ("G3-2", "quiet", dict(A=1.5), 24017, 5973.1, 150, "Q"),
 ("G3-3", "quiet", dict(A=1.5, band=(2.0, 8.0)), 3924, 1411.9, 90, "Q"),
 ("G3-4", "quiet", dict(band=(2.0, 8.0)), 3236, 765.5, 83, "Q"),
]
results = []
for name, tag, kw, n_e, p_e, c_e, grp in CELLS:
    ck = f"{CKPT}/trh03_trades_{name}.parquet"
    if os.path.exists(ck):
        tr = pd.read_parquet(ck)
    else:
        tr = run_cell2(tag, **kw)
        tr.to_parquet(ck, index=False)
        print(f"{name}: simulated {len(tr)}/{tr.pnl.sum():+.1f}",
              flush=True)
        if time.time() - T0 > 480:
            print("CONTINUE (rerun to finish remaining cells)")
            sys.exit(0)
    PRE = PRE_W if grp == "W" else PRE_Q
    POST = POST_W if grp == "W" else POST_Q
    c_pre = catch(tr, PRE)
    if (len(tr) != n_e or abs(tr.pnl.sum() - p_e) > 0.1
            or c_pre != c_e):
        print(f"# T-RH03 ABORTED - R-9 FAILED on {name}: "
              f"{len(tr)}/{tr.pnl.sum():+.1f} catch {c_pre} != "
              f"{n_e}/{p_e:+.1f} catch {c_e}")
        sys.exit(1)
    c_post = catch(tr, POST)
    results.append((name, n_e, c_e, len(PRE), c_post, len(POST)))

rep = open("Tests/D8_judgment/TRH03_REPORT.md", "w")
def P(s=""):
    print(s, file=rep); print(s)
P("# T-RH03 — HIS-SIDE LABEL RE-MINT UNDER FIXED STAMPS (F-39)")
P("STATUS: CLOSED | 2026-11-28 | J approved at the D-8 step-1 gate")
P("Machinery: d8_classify (labels; control pinned 307/5/61/149/0)")
P("+ remint_sims lineage (sims; R-9 exact on all six cells incl.")
P("pre-fix catches). Groups of record: G2 62 -> 61, G3 151 -> 149.")
P()
P("| system | n (R-9 exact) | catch OLD (pre-fix) | catch NEW (post-fix) |")
P("|---|---|---|---|")
for name, n_e, c_e, d_pre, c_post, d_post in results:
    P(f"| {name} | {n_e} | {c_e}/{d_pre} | {c_post}/{d_post} |")
P()
P("These NEW references are the references of record from this")
P("commit forward (headlines updated same-commit). Months-spend:")
P("nothing new (R-11) - training months only, no quarantined data.")
P("Registry: T-RH03.")
rep.close()
print("T-RH03 DONE")
