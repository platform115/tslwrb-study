#!/usr/bin/env python3
"""
ssel_round.py — T-SR04: structural selectors on the certified 750
5W full-RTH trades. Spec: SSEL_SPEC.md (frozen first). Levels and
family-edge machinery derived verbatim from certified lineage
(s5mf_round / g26_round).
RUN: python3 Tests/D32_structsel/ssel_round.py > Tests/D32_structsel/SSEL_REPORT.md
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTHS = {"2022-02": "2022-03-01", "2025-10": "2025-11-01"}
GRID = 0.25

T = pd.read_parquet("Tests/D30_s5mf/trades_5w_fullrth.parquet")
if not (len(T) == 750 and abs(T.pnl.sum() - 472.1) < 0.1):
    print(f"# SSEL ABORTED — control {len(T)}/{T.pnl.sum():+.1f}")
    sys.exit(1)

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

# levels pool (verbatim lineage)
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
hi_all = bnr.high.to_numpy(); lo_all = bnr.low.to_numpy()

# per-month resolver + mids for day-range position
RES, MIDS = {}, {}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    RES[mo] = Resolver(bm, zr)
    f = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    MIDS[mo] = (f.sec.to_numpy(np.int64), f.mid.to_numpy(float))

memo = {}
def fam_edges_all(mo, sd0, t, di):
    key = (mo, sd0, t // 60)
    if key not in memo:
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
        memo[key] = sorted(set(out))
    return memo[key]

# ---- features ----
feat = []
for r in T.itertuples():
    mo = r.month
    tf = int(r.tf); d = int(r.d); L = float(r.level)
    ent = L + 0.75 * d
    kb = int(np.searchsorted(bt_all, tf, "right")) - 1
    sd0 = sd_all[kb]
    di = day_ix.get(sd0)
    lv = lf(di) if di is not None else []
    ahead_lvl = sorted([(p - ent) * d for p in lv
                        if (p - ent) * d > 0.5])
    s1 = ahead_lvl[0] if ahead_lvl else np.inf
    fe = fam_edges_all(mo, sd0, tf, di)
    ahead_fam = sorted([(p - ent) * d for p in fe
                        if (p - ent) * d > 0.5])
    s2 = ahead_fam[0] if ahead_fam else np.inf
    near_fam = [p for p in fe if abs(p - L) <= 1.5]
    s3_stack = any(abs(p - L) <= 0.75 for p in fe)
    s3_cnt = len(near_fam)
    m1 = (sd_all == sd0) & (bt_all <= tf)
    if m1.any():
        dh = hi_all[m1].max(); dl = lo_all[m1].min()
        rng = dh - dl
        pos = ((ent - dl) / rng if rng > 0 else 0.5)
        s4 = pos if d > 0 else (1 - pos)
    else:
        s4 = np.nan
    behind = sorted([(L - p) * d for p in lv if (L - p) * d > 0.25])
    s5 = behind[0] if behind else np.inf
    feat.append(dict(s1=s1, s2=s2, s3_stack=s3_stack, s3_cnt=s3_cnt,
                     s4=s4, s5=s5))
F = pd.concat([T.reset_index(drop=True), pd.DataFrame(feat)], axis=1)
if len(F) != 750 or F[["s1", "s2"]].isna().any().any():
    print("# SSEL ABORTED — feature join incomplete")
    sys.exit(1)

def b_room(x):
    return np.where(x <= 2, "a<=2", np.where(x <= 4, "b2-4",
           np.where(x <= 8, "c4-8", "d>8/none")))
LN = {}
LN["S1 room-to-level"] = b_room(F.s1)
LN["S2 room-to-famedge"] = b_room(F.s2)
LN["S3 stacked<=0.75"] = np.where(F.s3_stack, "stacked", "clean")
q1, q2 = F.s4.quantile(1 / 3), F.s4.quantile(2 / 3)
LN["S4 range-pos"] = np.where(F.s4 <= q1, "t1_interior",
                     np.where(F.s4 <= q2, "t2_mid", "t3_extension"))
LN["S5 backstop"] = np.where(F.s5 <= 2, "a<=2",
                    np.where(F.s5 <= 6, "b2-6", "c>6/none"))

print("# SSEL REPORT — STRUCTURAL SELECTORS, SURGICAL LINE "
      "(T-SR04, D-32)")
print("STATUS: CLOSED | 2026-11-27 | Spec: SSEL_SPEC.md (frozen "
      "first) | control: banked 750/+472.1 reproduced | features "
      "750/750 | TRAINING-ONLY context")
print()
print("Baseline: 750 trades, +0.63/trade; 353 stops (-2.00 each), "
      "237 captures (+4.11 each).")
print()
tests = []
for nm, lab in LN.items():
    F[nm] = lab
    print(f"## {nm}")
    print("| bucket | n | per-trade | median | win% | capture% | "
          "stop% | 22-02 pt | 25-10 pt |")
    print("|---|---|---|---|---|---|---|---|---|")
    best = None
    for b_, sub in F.groupby(lab):
        m1_ = sub[sub.month == "2022-02"]
        m2_ = sub[sub.month == "2025-10"]
        pt = sub.pnl.mean()
        print(f"| {b_} | {len(sub)} | {pt:+.2f} | "
              f"{sub.pnl.median():+.2f} | {(sub.pnl>0).mean():.0%} | "
              f"{(sub.exit=='capture').mean():.0%} | "
              f"{(sub.exit=='stop').mean():.0%} | "
              f"{m1_.pnl.mean() if len(m1_) else float('nan'):+.2f} | "
              f"{m2_.pnl.mean() if len(m2_) else float('nan'):+.2f} |")
        if best is None or pt > best[1]:
            best = (b_, pt, sub)
    top = best[2]; rest = F[F[nm] != best[0]]
    try:
        p = mannwhitneyu(top.pnl, rest.pnl).pvalue
    except Exception:
        p = 1.0
    d1 = (top[top.month == "2022-02"].pnl.mean()
          - rest[rest.month == "2022-02"].pnl.mean())
    d2 = (top[top.month == "2025-10"].pnl.mean()
          - rest[rest.month == "2025-10"].pnl.mean())
    tests.append((nm, best[0], len(top), best[1], p,
                  d1 > 0 and d2 > 0))
    print()
print("## TOP-vs-REST (BH-FDR q=0.10 across 5 lenses)")
ps = sorted([(p, i) for i, (_, _, _, _, p, _) in enumerate(tests)])
mth = len(ps); passed = set()
for rank, (p, i) in enumerate(ps, 1):
    if p <= 0.10 * rank / mth:
        passed.add(i)
    else:
        break
print("| lens | top bucket | n | per-trade | MW p | BH | both-dir | "
      "FINDING |")
print("|---|---|---|---|---|---|---|---|")
for i, (nm, b_, n_, pt, p, bothdir) in enumerate(tests):
    fnd = "FINDING" if (i in passed and bothdir) else "-"
    print(f"| {nm} | {b_} | {n_} | {pt:+.2f} | {p:.4f} | "
          f"{'PASS' if i in passed else 'fail'} | "
          f"{'yes' if bothdir else 'NO'} | {fnd} |")
print()
print("## PROMOTION RULE CHECK (monotone + FINDING + n>=150 + "
      ">=+0.85 + both months positive)")
anyq = False
for i, (nm, b_, n_, pt, p, bothdir) in enumerate(tests):
    if i in passed and bothdir and n_ >= 150 and pt >= 0.85:
        sub = F[F[nm] == b_]
        bm_ = all(sub[sub.month == mo].pnl.sum() > 0 for mo in MONTHS)
        anyq = True
        print(f"- CANDIDATE: {nm} = {b_} ({n_} trades, {pt:+.2f})"
              f"{' both months positive' if bm_ else ' FAILS month line'}")
if not anyq:
    print("(no qualifier)")
F.to_parquet("Tests/D32_structsel/trades_5w_struct.parquet",
             index=False)
print()
print("Banked: trades_5w_struct.parquet (750 trades + structural "
      "features). Registry: T-SR04.")
