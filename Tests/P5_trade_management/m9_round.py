#!/usr/bin/env python3
"""
m9_round.py — T-MG16: the state-machine exit policy. Spec: M9_SPEC.md
(committed first).
RUN: python3 Tests/P5_trade_management/m9_round.py > Tests/P5_trade_management/M9_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p4_66_context_ablation import prep                      # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
GRID, STOP = 0.25, 3.75
RNG = np.random.default_rng(113)

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

# levels (shipped config, same as M7)
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

def m9(exc, ts, best, mse0, Se, Sl, rb):
    """Clock-tiered patience + fade-aware stall + level arm."""
    peak, tp, armed = 0.0, 0, False
    arm = max(best - 0.75, 0.5) if (best is not None and best <= 8.0) \
        else None
    bounce_from = None; bounce_t0 = 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
            bounce_from = None
        if arm is not None and exc[i] >= arm:
            armed = True
        if exc[i] <= -STOP:
            return -STOP, i
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i
        budget = Se if (mse0 + ts[i] / 60.0) <= 15.0 else Sl
        if bounce_from is not None:
            if exc[i] >= bounce_from + rb or ts[i] - bounce_t0 >= 120:
                return exc[i], i
            bounce_from = min(bounce_from, exc[i])
            continue
        if ts[i] - tp >= budget or ts[i] >= 900:
            if peak - exc[i] >= 1.5 and ts[i] < 900:
                bounce_from = exc[i]; bounce_t0 = ts[i]
                continue
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

def oracle(exc, ts):
    a, _ = m7(exc, ts, None)
    j = int(np.searchsorted(ts, 120, "right"))
    bmax = exc[:j].max() if j > 0 else 0
    bl = (bmax - 0.75) if bmax >= 0.75 else a
    return max(a, bl), 0

# trades
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
D = D[D.disp == 1.25]
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
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = HIS62.merge(G, left_on=["month", "sec"],
                 right_on=["month", "entry_msg_s"], suffixes=("_f", ""))
GT["sd_n"] = GT.side.map({"long": 1, "short": -1})

CELLS = [(Se, Sl, rb) for Se in (90, 120) for Sl in (45, 60)
         for rb in (0.5, 0.75)]
print("# M9 REPORT — THE STATE-MACHINE POLICY (T-MG16)")
print("STATUS: CLOSED | 2026-11-26 | Spec: M9_SPEC.md (committed first)")
print()
# finding-4 distribution (extra care, per J)
print("## FINDING-4 DISTRIBUTION (why the stop stays): outcomes after "
      "first touch of -1.5 (raw paths, 300s on)")
vals = []
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in D[D.month == mo].iterrows():
        lvl = r.edge + 1.25 * r.d
        j1 = int(np.searchsorted(secs, int(r.tf)))
        j2 = int(np.searchsorted(secs, int(r.tf) + 1800, "right"))
        exc = (mids[j1:j2] - lvl) * r.d
        k = np.flatnonzero(exc <= -1.5)
        if len(k):
            i0 = k[0]
            i1 = min(i0 + 300, len(exc) - 1)
            vals.append(exc[i1] - exc[i0])
v = np.array(vals)
q = np.percentile(v, [5, 25, 50, 75, 95])
print(f"n={len(v)} | mean {v.mean():+.2f} | q5/q25/q50/q75/q95 = "
      f"{q[0]:+.2f}/{q[1]:+.2f}/{q[2]:+.2f}/{q[3]:+.2f}/{q[4]:+.2f}")
print("Reading: the mean recovery is real BUT q5 shows the tail that "
      "a stop exists to cut. Stop unchanged this round, as specified.")
print()
# stage 1
res = {f"M9 Se{Se} Sl{Sl} r{rb}": [] for Se, Sl, rb in CELLS}
res["M7 baseline"] = []; res["DUAL ORACLE (ceiling)"] = []
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not np.isfinite(r.entry_price):
            continue
        di = day_ix.get(r.session_date)
        lv = lf(di) if di else []
        ahead = sorted([(p - r.entry_price) * r.sd_n for p in lv
                        if (p - r.entry_price) * r.sd_n > 0.25])
        best = ahead[0] if ahead else None
        kk3 = int(np.searchsorted(ev_all, int(r.sec), "right")) - 1
        mse0 = (int(r.sec) - ev_all[kk3]) / 60.0 if kk3 >= 0 else 99.0
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.sd_n
        ts_ = (secs[j1:j2] - int(r.sec)).astype(int)
        for Se, Sl, rb in CELLS:
            res[f"M9 Se{Se} Sl{Sl} r{rb}"].append(
                m9(exc, ts_, best, mse0, Se, Sl, rb)[0])
        res["M7 baseline"].append(m7(exc, ts_, best)[0])
        res["DUAL ORACLE (ceiling)"].append(oracle(exc, ts_)[0])
print("## STAGE 1 — HIS 62 FILLS (qualify: net > M7's +146.0)")
print("| candidate | net | win | worst | share of his |")
print("|---|---|---|---|---|")
quals = []
for n in res:
    a = np.array(res[n])
    print(f"| {n} | {a.sum():+.1f} | {(a>0).mean():.0%} | "
          f"{a.min():+.2f} | {a.sum()/231.2:.0%} |")
    if a.sum() > 146.0 and "baseline" not in n and "ORACLE" not in n:
        quals.append((a.sum(), n))
quals = [n for _, n in sorted(quals, reverse=True)][:3]
print()
print(f"Stage-1 qualifiers (top 3 to joint): {quals if quals else 'NONE'}")
print()
# stage 2
print("## STAGE 2 — JOINT (incumbent on this universe: M7 +186.0 / "
      "caught 40 / extras +88.4)")
print("| candidate | trades | net (22-02/25-10) | caught/62 | extras "
      "net | ADOPT? |")
print("|---|---|---|---|---|---|")
for n in quals + ["M7 baseline"]:
    allt = []
    for mo in MONTHS:
        P = prep(".", mo)
        secs, mids = P["secs"], P["mids"]
        bm = b[(b.ts_event >= f"{mo}-01")
               & (b.ts_event < MONTHS[mo])]
        bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                    ).to_numpy() // 10**9
        bsd = bm.sd.to_numpy()
        sub = D[D.month == mo].sort_values("tf")
        busy = -10**12
        for _, r in sub.iterrows():
            if r.tf < busy:
                continue
            lvl = r.edge + 1.25 * r.d
            j1 = int(np.searchsorted(secs, int(r.tf)))
            j2 = int(np.searchsorted(secs, int(r.tf) + 1800, "right"))
            if j2 - j1 < 5:
                continue
            exc = (mids[j1:j2] - lvl) * r.d
            ts_ = (secs[j1:j2] - int(r.tf)).astype(int)
            k = int(np.searchsorted(bt, int(r.tf), "right")) - 1
            di = day_ix.get(bsd[k]) if k >= 0 else None
            lv = lf(di) if di else []
            ahead = sorted([(p - lvl) * r.d for p in lv
                            if (p - lvl) * r.d > 0.25])
            best = ahead[0] if ahead else None
            if n == "M7 baseline":
                pnl, ix = m7(exc, ts_, best)
            else:
                parts = n.split()
                Se = int(parts[1][2:]); Sl = int(parts[2][2:])
                rb = float(parts[3][1:])
                kk3 = int(np.searchsorted(ev_all, int(r.tf),
                                          "right")) - 1
                mse0 = (int(r.tf) - ev_all[kk3]) / 60.0 if kk3 >= 0 \
                    else 99.0
                pnl, ix = m9(exc, ts_, best, mse0, Se, Sl, rb)
            busy = int(secs[j1 + ix])
            allt.append((mo, int(r.tf), int(r.d), pnl))
    tr = pd.DataFrame(allt, columns=["month", "tf", "d", "pnl"])
    nets = tr.groupby("month").pnl.sum()
    caught = 0
    for _, h in HIS62.iterrows():
        if len(tr[(tr.month == h.month) & (tr.d == h.side)
                  & (abs(tr.tf - h.sec) <= 300)]):
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in HIS62.iterrows():
        near |= ((tr.month == h.month).to_numpy()
                 & (np.abs(tr.tf - h.sec) <= 300).to_numpy())
    exn = tr.pnl[~near].sum()
    pooled = tr.pnl.sum()
    ok = (pooled > 186.0 and all(x > 0 for x in nets.to_numpy())
          and exn >= 0 and caught >= 40)
    print(f"| {n} | {len(tr)} | {pooled:+.1f} "
          f"({nets.get('2022-02',0):+.1f}/{nets.get('2025-10',0):+.1f})"
          f" | {caught} | {exn:+.1f} | {'YES' if ok else 'no'} |")
print()
print("Registry: T-MG16.")
