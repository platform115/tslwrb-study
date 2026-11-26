#!/usr/bin/env python3
"""
c2_audit.py — T-IM54: the sharpened coverage pass (C2). Spec:
C_AUDIT_SPEC.md C2 addendum (committed first).
RUN: python3 Tests/A2_measurement/c2_audit.py > Tests/A2_measurement/C2_AUDIT_REPORT.md
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
CELLS = ((20, 0.5), (20, 0.8))
DISP, TTL, DEDUP, STOP = 1.25, 300, 300, 3.75

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)

def band_arrays(g, W, q):
    """Per-bar most-recent-episode band (vectorized, completed bars)."""
    h = g.high.to_numpy(); l = g.low.to_numpy()
    n = len(h)
    hs = pd.Series(h).rolling(W).max().to_numpy()
    ls = pd.Series(l).rolling(W).min().to_numpy()
    rng_w = hs - ls
    med = pd.Series(rng_w).shift(1).rolling(60, min_periods=10
                                            ).median().to_numpy()
    active = np.isfinite(rng_w) & np.isfinite(med) & (rng_w <= q * med)
    blo = np.full(n, np.nan); bhi = np.full(n, np.nan)
    cur_lo = cur_hi = np.nan
    run_lo = run_hi = np.nan
    in_run = False
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

def m3a(exc, ts):
    peak, tp = 0.0, 0
    for i in range(len(exc)):
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if exc[i] <= -STOP:
            return -STOP, i
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i
    return (exc[-1], len(exc) - 1) if len(exc) else (0.0, 0)

# the 9 missed trades (from T-IM53; recompute identically)
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
G2H = F[(F.ctx == "squeeze") & (F.np_ == "window")]
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

absent = []
CTX = {}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    P = prep(".", mo)
    CTX[mo] = (bm, R, P["secs"], P["mids"])
    sub = D[(D.month == mo) & (D.disp == 1.25)]
    for _, h in G2H[G2H.month == mo].iterrows():
        if len(sub[(sub.d == h.side) & (abs(sub.tf - h.sec) <= 300)]):
            continue
        secs, mids = P["secs"], P["mids"]
        t64 = np.datetime64(int(h.sec), "s")
        E = edges_at(R, h.session_date, t64, "SQZ")
        j = int(np.searchsorted(secs, int(h.sec), "right")) - 1
        px = mids[j]
        if not [e for e in E if abs(px - e) <= 5.0]:
            absent.append(dict(month=mo, sd=h.session_date,
                               sec=int(h.sec), side=int(h.side), px=px,
                               mv15=h.mv15, dwell=h.dwell120))
AB = pd.DataFrame(absent)
print("# C2 AUDIT — TRIGGER-LEVEL COVERAGE (T-IM54)")
print("STATUS: CLOSED | 2026-11-26 | Spec: C2 addendum (committed first)")
print()
print(f"Missed trades: {len(AB)}.")
print()
caught_by = {c: set() for c in CELLS}
results = []
for (W, q) in CELLS:
    fires = 0; fill_pnls = []; nd = 0
    for mo, nxt in MONTHS.items():
        bm, R, secs, mids = CTX[mo]
        nd += bm.sd.nunique()
        bt = bm.ts_event.dt.tz_convert(None).astype("int64"
                                                    ).to_numpy() // 10**9
        rth = bm.session.eq("RTH").to_numpy()
        evm = ev_all[(ev_all >= secs[0]) & (ev_all <= secs[-1])]
        for sd0, g in bm.groupby("sd"):
            blo, bhi = band_arrays(g.reset_index(drop=True), W, q)
            g_bt = (g.ts_event.dt.tz_convert(None).astype("int64")
                    .to_numpy() // 10**9)
            for es in evm:
                w0, w1 = es + 300, es + 2700
                if w1 < g_bt[0] or w0 > g_bt[-1]:
                    continue
                kb = int(np.searchsorted(bt, w0, "right")) - 1
                if kb < 0 or not rth[kb]:
                    continue
                j0 = int(np.searchsorted(secs, w0))
                j1 = int(np.searchsorted(secs, w1, "right"))
                last_fire = {}
                for jj in range(max(j0, 1), j1):
                    t = int(secs[jj])
                    ki = int(np.searchsorted(g_bt + 60, t, "right")) - 1
                    if ki < 0 or not np.isfinite(blo[ki]):
                        continue
                    px, prev = mids[jj], mids[jj - 1]
                    for e in (blo[ki], bhi[ki]):
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
                        fires += 1
                        j3 = int(np.searchsorted(secs, tf + 1800,
                                                 "right"))
                        exc = (mids[jf:j3] - lvl) * ddir
                        ts_ = (secs[jf:j3] - tf).astype(int)
                        pnl, _ = m3a(exc, ts_)
                        near = AB[(AB.month == mo)
                                  & (AB.side == ddir)
                                  & (abs(AB.sec - tf) <= 300)]
                        if len(near):
                            for _, nr in near.iterrows():
                                caught_by[(W, q)].add((nr.month, nr.sec))
                        fill_pnls.append((pnl, bool(len(near))))
    FP = pd.DataFrame(fill_pnls, columns=["pnl", "near_miss_trade"])
    ex = FP[~FP.near_miss_trade]
    results.append((W, q, fires, nd, len(caught_by[(W, q)]),
                    ex.pnl.sum(), (ex.pnl > 0).mean() if len(ex)
                    else np.nan,
                    FP[FP.near_miss_trade].pnl.sum()))
print("## (a)+(b) TRIGGER SIMULATION + TRADED INCREMENTAL COST (M3A)")
print("| cell | incr. fills | fills/day | of the 9 caught | caught "
      "P&L | extra fills | extras net | extras win |")
print("|---|---|---|---|---|---|---|---|")
for W, q, fires, nd, cgt, exnet, exwin, cpnl in results:
    print(f"| W{W} q{q} | {fires} | {fires/nd:.1f} | {cgt} | "
          f"{cpnl:+.1f} | {fires - cgt} | {exnet:+.1f} | {exwin:.0%} |")
u = set().union(*caught_by.values())
print(f"\n## (c) UNION: {len(u)} of the {len(AB)} caught by at least "
      "one cell.")
print()
print("## (d) THE STILL-UNCOVERED, WITH CAUSES")
print("| month | time | side | nearest certified structure | fade "
      "anatomy (mv15<0 & dwell>0.45)? |")
print("|---|---|---|---|---|")
for _, r in AB.iterrows():
    if (r.month, r.sec) in u:
        continue
    bm, R, secs, mids = CTX[r.month]
    t64 = np.datetime64(int(r.sec), "s")
    best = ("none", np.inf)
    for fam in ("REA", "GAP", "SHD", "SQZ"):
        for e in edges_at(R, r.sd, t64, fam):
            if abs(r.px - e) < best[1]:
                best = (fam, abs(r.px - e))
    fade = bool((r.mv15 < 0) and (r.dwell > 0.45)) \
        if np.isfinite(r.mv15) and np.isfinite(r.dwell) else None
    tloc = pd.Timestamp(int(r.sec), unit="s", tz="UTC"
                        ).tz_convert("America/Chicago")
    print(f"| {r.month} | {tloc.strftime('%a %H:%M CT')} | "
          f"{'L' if r.side > 0 else 'S'} | {best[0]} at "
          f"{best[1]:.2f} pts | {fade} |")
print()
print("Adoption bar (pre-stated): >= 2 of 9 converted AND extras net "
      ">= 0. Registry: T-IM54.")
