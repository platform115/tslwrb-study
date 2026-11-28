#!/usr/bin/env python3
"""
d4_vectors.py — D-4 / D-18: GOLDEN VECTORS for the G2-4 Pine port.
Sessions: 2025-10-15 (busy, 135 cands), 2025-10-13 (ordinary, 23),
2025-10-31 (sparse, 3).
DERIVES FROM (R-9 lineage): candidate machinery verbatim from
d8_prep.py (row-identical control passed), sim verbatim from
d8_round.py (T-VL05 control passed).
CONTROLS (abort on miss):
 C1: full-month candidate rebuild == certified
     Tests/D11_unmatched/parts/cand_ctrl_2025-10.parquet, bit-exact.
 C2: full-month G2-4 sim net on 2025-10 == +194.0 (T-RH02 by-month).
OUTPUTS (Tests/D4_handoff/vectors/):
 v_structure_<sd>.csv  per 1m bar: W20 band, sqz10/sqz30 edges
 v_signals_<sd>.csv    every cross + order (placed/filled/expired)
 v_trades_<sd>.csv     every trade: fill, arm, exit, reason, pnl
 V_SUMMARY.md          per-session roll-up + tolerance sheet
RUN: python3 Tests/D4_handoff/d4_vectors.py             (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MO, NXT = "2025-10", "2025-11-01"
TARGETS = ["2025-10-13", "2025-10-15", "2025-10-31"]
DISP, TTL, DEDUP, STOP, GRID = 1.25, 300, 300, 3.75, 0.25
OUTD = "Tests/D4_handoff/vectors"
os.makedirs(OUTD, exist_ok=True)

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


# WRB + levels machinery (verbatim)
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
for sd, lst in wrb_day.items():
    rows.append(pd.DataFrame({"sd": sd,
                              "px": [p for _, p in lst],
                              "newsborn": False}))
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
            return -STOP, i, "stop", armed
        if armed and exc[i] <= peak - 0.75:
            return peak - 0.75, i, "trail", armed
        if ts[i] - tp >= stall:
            return exc[i], i, "stall", armed
        if ts[i] >= 480:
            return exc[i], i, "cap", armed
    return ((exc[-1], len(exc) - 1, "end", armed) if len(exc)
            else (0.0, 0, "none", armed))


# ---------- candidate build with signal recording ----------
bm = b[(b.ts_event >= f"{MO}-01") & (b.ts_event < NXT)
       ].reset_index(drop=True)
R = Resolver(bm, zr)
fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{MO}_full.parquet")
secs = fl.sec.to_numpy(np.int64)
mids = fl.mid.to_numpy(float)
bt = bm.ts_event.dt.tz_convert(None).astype("int64").to_numpy() // 10**9
rth = bm.session.eq("RTH").to_numpy()
sd1 = bm.sd.to_numpy()
evm = np.unique(ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])])
band_cache = {}
memo = {}
def fam_edges(fam, sd0, t):
    key = (fam, sd0, t // 60)
    if key not in memo:
        memo[key] = [float(e) for e in
                     edges_at(R, sd0, np.datetime64(t, "s"), fam)]
    return memo[key]

cands, signals = [], []
for es in evm:
    es = int(es)
    j0 = int(np.searchsorted(secs, es + 300))
    j1 = int(np.searchsorted(secs, es + 2700, "right"))
    if j1 - j0 < 60:
        continue
    kb = int(np.searchsorted(bt, secs[j0], "right")) - 1
    if kb < 0 or not rth[kb]:
        continue
    sd0 = sd1[kb]
    di = day_ix.get(sd0)
    if sd0 not in band_cache:
        g = bm[bm.sd == sd0].reset_index(drop=True)
        band_cache[sd0] = (band_arrays(g, 20, 0.8),
                           (g.ts_event.dt.tz_convert(None)
                            .astype("int64").to_numpy() // 10**9))
    (blo, bhi), g_bt = band_cache[sd0]
    last_fire = {}
    for jj in range(max(j0, 1), j1):
        t = int(secs[jj])
        E = [("SQZ", e) for e in fam_edges("SQZ", sd0, t)]
        ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
        if ki >= 0 and np.isfinite(blo[ki]):
            E += [("W20", blo[ki]), ("W20", bhi[ki])]
        px, prev = mids[jj], mids[jj - 1]
        for fam, e in E:
            dd = 1 if (prev <= e < px) else \
                (-1 if (prev >= e > px) else 0)
            if dd == 0:
                continue
            key = (round(e, 2), dd)
            if t - last_fire.get(key, -10**9) <= DEDUP:
                continue
            last_fire[key] = t
            lvl = e + DISP * dd
            j3 = int(np.searchsorted(secs, t + TTL, "right"))
            seg2 = mids[jj:j3]
            hit = np.flatnonzero((seg2 >= lvl) if dd > 0
                                 else (seg2 <= lvl))
            rec = dict(sd=sd0, cross_t=t, fam=fam, edge=key[0],
                       dir=dd, tech="cross", order_lvl=round(lvl, 2),
                       filled=bool(len(hit)),
                       fill_t=int(secs[jj + int(hit[0])])
                       if len(hit) else None)
            if sd0 in TARGETS:
                signals.append(rec)
            if len(hit):
                jf = jj + int(hit[0])
                cands.append((sd0, int(secs[jf]), dd, key[0], jf,
                              fam))
            j9 = int(np.searchsorted(secs, t + 600, "right"))
            seg = (mids[jj:j9] - e) * dd
            gate = np.flatnonzero(seg >= 1.0)
            if len(gate):
                jg = int(gate[0])
                back = np.flatnonzero(seg[jg:] <= 0.75)
                if len(back):
                    jt = jj + jg + int(back[0])
                    tt_ = int(secs[jt])
                    j3b = int(np.searchsorted(secs, tt_ + TTL,
                                              "right"))
                    s2b = mids[jt:j3b]
                    hb = np.flatnonzero((s2b >= lvl) if dd > 0
                                        else (s2b <= lvl))
                    rec2 = dict(sd=sd0, cross_t=tt_, fam=fam,
                                edge=key[0], dir=dd, tech="retest",
                                order_lvl=round(lvl, 2),
                                filled=bool(len(hb)),
                                fill_t=int(secs[jt + int(hb[0])])
                                if len(hb) else None)
                    if sd0 in TARGETS:
                        signals.append(rec2)
                    if len(hb):
                        jfb = jt + int(hb[0])
                        cands.append((sd0, int(secs[jfb]), dd,
                                      key[0], jfb, fam))
C = pd.DataFrame(cands, columns=["sd", "tf", "d", "e", "jf", "fam"])

# C1: bit-exact vs certified part
cert = pd.read_parquet(
    "Tests/D11_unmatched/parts/cand_ctrl_2025-10.parquet")
if not C.reset_index(drop=True).equals(cert.reset_index(drop=True)):
    print("# D4 VECTORS ABORTED - C1 FAILED (candidates differ "
          f"{len(C)} vs {len(cert)})")
    sys.exit(1)
print("C1 PASS: month candidates bit-exact vs certified part "
      f"({len(C)})")

# ---------- sim with trade recording ----------
C = C.sort_values("tf", kind="stable")
seen = set(); busy = -10**12
trades = []
for r in C.itertuples():
    dk = (r.tf, r.e, r.d)
    if dk in seen:
        continue
    seen.add(dk)
    lvl = r.e + DISP * r.d
    di = day_ix.get(r.sd)
    if di is None:
        continue
    if r.tf < busy:
        continue
    jf = int(r.jf)
    j4 = int(np.searchsorted(secs, r.tf + 1800, "right"))
    exc = (mids[jf:j4] - lvl) * r.d
    ts_ = (secs[jf:j4] - r.tf).astype(int)
    lv = lf(di)
    ahead = sorted([(p - lvl) * r.d for p in lv
                    if (p - lvl) * r.d > 0.25])
    best = ahead[0] if ahead else None
    pnl, ix, reason, armed = m7_var(exc, ts_, best)
    busy = int(secs[jf + ix])
    trades.append(dict(sd=r.sd, month=MO, fill_t=int(r.tf),
                       d=int(r.d), edge=float(r.e),
                       entry=round(lvl, 2),
                       best_dist=round(best, 2) if best else None,
                       armed=armed, exit_t=busy, reason=reason,
                       pnl=round(float(pnl), 2)))
T = pd.DataFrame(trades)
net = T.pnl.sum()
if abs(net - 194.0) > 0.5:
    print(f"# D4 VECTORS ABORTED - C2 FAILED (month net {net:+.1f} "
          "!= +194.0)")
    sys.exit(1)
print(f"C2 PASS: month sim net {net:+.1f} == certified +194.0")

# ---------- per-session structure + outputs ----------
for sd in TARGETS:
    g = bm[bm.sd == sd].reset_index(drop=True)
    blo, bhi = band_arrays(g, 20, 0.8)
    rows_s = []
    gts = g.ts_event.dt.tz_convert("America/Chicago")
    for i in range(len(g)):
        t_know = int(g.ts_event.dt.tz_convert(None)
                     .astype("int64").iloc[i] // 10**9) + 120
        sq = {}
        for fam, w in (("sqz10", 10), ("sqz30", 30)):
            eps = [z for z in R._objs(sd, fam)
                   if z["comp"] <= np.datetime64(t_know, "s")]
            if eps:
                z = max(eps, key=lambda q: q["comp"])
                sq[f"{fam}_lo"], sq[f"{fam}_hi"] = z["lo"], z["hi"]
            else:
                sq[f"{fam}_lo"] = sq[f"{fam}_hi"] = None
        rows_s.append(dict(bar_ct=gts.iloc[i].strftime(
            "%Y-%m-%d %H:%M"), w20_lo=round(float(blo[i]), 2)
            if np.isfinite(blo[i]) else None,
            w20_hi=round(float(bhi[i]), 2)
            if np.isfinite(bhi[i]) else None, **sq))
    pd.DataFrame(rows_s).to_csv(f"{OUTD}/v_structure_{sd}.csv",
                                index=False)
    S = pd.DataFrame([s for s in signals if s["sd"] == sd])
    S.to_csv(f"{OUTD}/v_signals_{sd}.csv", index=False)
    T[T.sd == sd].to_csv(f"{OUTD}/v_trades_{sd}.csv", index=False)

with open(f"{OUTD}/V_SUMMARY.md", "w") as f:
    f.write("# D4 GOLDEN VECTORS — SUMMARY (certified engine "
            "output; controls C1/C2 PASS)\n")
    f.write("| session | signals | orders filled | trades | net |\n")
    f.write("|---|---|---|---|---|\n")
    for sd in TARGETS:
        S = [s for s in signals if s["sd"] == sd]
        Tt = T[T.sd == sd]
        f.write(f"| {sd} | {len(S)} | "
                f"{sum(1 for s in S if s['filled'])} | {len(Tt)} | "
                f"{Tt.pnl.sum():+.1f} |\n")
    f.write("""
## TOLERANCES (J-gated; stage gates in D4_HANDOFF_PROMPT.md)
- S2/S3 structure values: EXACT when TradingView 1m bars equal
  ours; where bars differ, each differing bar is listed and
  explained by the bar difference, nothing else.
- S4 signals: >= 90% of signals matched within +/- 60s, same edge
  (+/- 1 tick) and direction; every unmatched signal listed.
- S5 fills: same fill/expiry outcome on >= 90% of matched signals.
- S6 trades: per-trade exit reason matches on >= 85% of matched
  fills; per-trade P/L within 0.50 on matched same-reason trades.
- Any systematic one-direction bias in mismatches = STOP, report.
""")
print("VECTORS WRITTEN:", OUTD)
