#!/usr/bin/env python3
"""
mdl_v3.py — T-IM51 (v3): chaining defect fixed with density-peak
clustering (0.25-pt grid; score = distinct member-days in +/-tol
around the gridpoint; levels = local maxima with suppression). No
single-linkage anywhere. Spec: MDL_SPEC.md + V2 addendum; the v2 run's
numbers are VOID (chaining artifact caught by the 3/55 sanity check).
RUN: python3 Tests/P5_trade_management/mdl_v3.py > Tests/P5_trade_management/MDL_V3_REPORT.md
"""
import sys

import numpy as np
import pandas as pd

RNG = np.random.default_rng(113)
TOL_REC, KILL = 3.0, 5.0
GRID = 0.25

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b[~b.is_roll_day].sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days = sorted(b.sd.unique())
day_ix = {d: i for i, d in enumerate(days)}
closes = b.groupby("sd").close.last().reindex(days).to_numpy()

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets                   # noqa: E402
ev_t = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9


def density_levels(px, di, newsborn, tol, m):
    """Density-peak levels: gridpoints whose +/-tol neighborhood holds
    >= m distinct member-days (+1 if any news-born); local maxima with
    2*tol suppression. No chaining possible."""
    if not len(px):
        return []
    gp = np.round(px / GRID).astype(np.int64)
    lo, hi = gp.min(), gp.max()
    width = int(round(tol / GRID))
    # for each gridpoint, set of days via sorted (gp, di) sweep
    order = np.argsort(gp)
    gs, ds, nb = gp[order], di[order], newsborn[order]
    uniq = np.arange(lo, hi + 1)
    score = np.zeros(len(uniq), float)
    for k, g0 in enumerate(uniq):
        a = np.searchsorted(gs, g0 - width)
        b2 = np.searchsorted(gs, g0 + width, "right")
        if b2 > a:
            score[k] = len(set(ds[a:b2])) + (1.0 if nb[a:b2].any()
                                             else 0.0)
    out = []
    taken = np.zeros(len(uniq), bool)
    for k in np.argsort(-score):
        if score[k] < m or taken[k]:
            continue
        out.append((float(uniq[k] * GRID), score[k]))
        s0 = max(0, k - 2 * width)
        taken[s0:k + 2 * width + 1] = True
    return out


# ---------------- market evidence (same v2 sources) ----------------
rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk = np.searchsorted(ev_t, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_t[np.maximum(kk, 0)]) <= 2700
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
for tfm in ("5min", "15min"):
    for sd, g in b.groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w = body > pm
        for o, c in zip(r.open.to_numpy()[w], r.close.to_numpy()[w]):
            rows.append(pd.DataFrame({"sd": [sd, sd],
                                      "px": [max(o, c), min(o, c)],
                                      "newsborn": [False, False]}))
E = pd.concat(rows, ignore_index=True)
E["px"] = (E.px * 4).round() / 4
E = E.drop_duplicates(["sd", "px"])
E["di"] = E.sd.map(day_ix)
E = E.dropna(subset=["di"])
E["di"] = E.di.astype(int)
Epx, Edi, Enb = E.px.to_numpy(), E.di.to_numpy(), E.newsborn.to_numpy()

print("# MDL V3 REPORT — CHAINING FIXED, EVERYTHING RERUN (T-IM51)")
print("STATUS: CLOSED | 2026-11-25 | v2 numbers VOID (chaining caught "
      "by the 3/55 sanity check); v3 = density-peak clustering")
print()
print(f"Market evidence: {len(E):,} records. ")

# ---------------- revealed teaching set (actions) ----------------
ep = pd.read_parquet("Data/inputs/tsl_episodes_clean.parquet")
act = []
for _, r in ep.iterrows():
    sd = str(r.trading_date) if pd.notna(r.trading_date) else None
    if sd is None or sd not in day_ix:
        continue
    for arr in (r.entry_prices, r.exit_prices):
        if arr is None:
            continue
        for p in np.atleast_1d(arr):
            if np.isfinite(p):
                act.append((sd, float(p)))
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet").reset_index()
zr["sd"] = pd.to_datetime(zr.ts_utc, utc=True).dt.strftime("%Y-%m-%d")
for _, r in zr[zr.price_1.notna()].iterrows():
    if r.sd in day_ix:
        act.append((r.sd, float(r.price_1)))
sl = pd.read_parquet("Data/inputs/s4_ref_links.parquet")
sl2 = sl.merge(zr[["index", "sd"]], left_on="ref_idx", right_on="index")
so2 = pd.read_parquet("Data/inputs/s4_objects.parquet",
                      columns=["object_id", "band_lo", "band_hi"]
                      ).drop_duplicates("object_id")
sl2 = sl2.merge(so2, on="object_id")
for _, r in sl2.iterrows():
    if r.sd in day_ix and np.isfinite(r.band_lo):
        act.append((r.sd, float(r.band_lo)))
        act.append((r.sd, float(r.band_hi)))
A = pd.DataFrame(act, columns=["sd", "px"])
A["px"] = (A.px * 4).round() / 4
A = A.drop_duplicates(["sd", "px"])
A["di"] = A.sd.map(day_ix).astype(int)
Apx, Adi = A.px.to_numpy(), A.di.to_numpy()
Anb = np.zeros(len(A), bool)

# revealed levels per sampled day -> persistent episodes
TRAIL = 60
rev_by_day = {}
for di in range(70, len(days)):
    msk = (Adi >= di - TRAIL) & (Adi < di + 1)   # teaching may see day di
    rev_by_day[di] = [p for p, s in
                      density_levels(Apx[msk], Adi[msk], Anb[msk],
                                     2.5, 3)]
# episodes: link same-price (within 2 pts) across consecutive days
episodes = []
open_eps = []
for di in range(70, len(days)):
    today = rev_by_day[di]
    matched = set()
    for e in open_eps:
        hit = [p for p in today if abs(p - e["px"]) <= 2.0]
        if hit:
            e["last"] = di
            e["px"] = 0.8 * e["px"] + 0.2 * hit[0]
            matched.update(hit)
        elif di - e["last"] > 10:
            episodes.append(e)
    open_eps = [e for e in open_eps if di - e["last"] <= 10]
    for p in today:
        if p not in matched:
            open_eps.append(dict(px=p, first=di, last=di))
episodes += open_eps
REG = pd.DataFrame([e for e in episodes if e["last"] - e["first"] >= 5])
print(f"Teaching set: {len(A):,} action records -> {len(REG)} revealed "
      f"level-episodes lasting >= 5 sessions (median life "
      f"{(REG.last - REG.first).median():.0f} sessions).")
pk = zr[(zr.price_1.notna()) & (zr.tier == "key")]
inreg = tot_k = 0
for _, r in pk.iterrows():
    if r.sd not in day_ix or day_ix[r.sd] < 70:
        continue
    tot_k += 1
    di = day_ix[r.sd]
    m = REG[(abs(REG.px - r.price_1) <= TOL_REC)
            & (REG.first <= di) & (di <= REG.last + 10)]
    inreg += bool(len(m))
print(f"SANITY: {inreg}/{tot_k} of his priced KEY mentions fall inside "
      f"an active revealed episode (v2 was 3/55 - the defect detector).")
print()

# ---------------- detector recovery ----------------
print("## RECOVERY (primary = revealed episodes; secondary = priced "
      "keys)")
print("| window | tol | min score | revealed recovered | priced keys "
      "| levels/day |")
print("|---|---|---|---|---|---|")
best = None
for W in (40, 60):
    for tol in (2.0, 3.0):
        for m in (4, 5):
            cache = {}
            def lf(di, W=W, tol=tol, m=m, cache=cache):
                if di not in cache:
                    msk = (Edi >= di - W) & (Edi < di)
                    lv = density_levels(Epx[msk], Edi[msk], Enb[msk],
                                        tol, m)
                    out = []
                    for p, s in lv:
                        last_mem = int(Edi[msk][np.abs(Epx[msk] - p)
                                                <= tol].max())
                        cseg = closes[last_mem + 1:di]
                        if not (len(cseg)
                                and (np.abs(cseg - p) > KILL).all()):
                            out.append(p)
                    cache[di] = out
                return cache[di]
            hit = tot = 0
            for _, r in REG.iterrows():
                tot += 1
                sample = np.unique(np.linspace(r.first, min(r.last,
                                   len(days) - 1), 6).astype(int))
                if any(any(abs(l - r.px) <= TOL_REC for l in lf(di))
                       for di in sample):
                    hit += 1
            hk = tk = 0
            for _, r in pk.iterrows():
                if r.sd not in day_ix or day_ix[r.sd] < 70:
                    continue
                tk += 1
                if any(abs(l - r.price_1) <= TOL_REC
                       for l in lf(day_ix[r.sd])):
                    hk += 1
            med = int(np.median([len(lf(di)) for di in
                      RNG.choice(np.arange(70, len(days)), 25,
                                 replace=False)]))
            print(f"| {W} | {tol} | {m} | {hit}/{tot} "
                  f"({hit/max(1,tot):.0%}) | {hk}/{tk} "
                  f"({hk/max(1,tk):.0%}) | {med} |")
            if best is None or hit / max(1, tot) > best[0]:
                best = (hit / max(1, tot), W, tol, m)
print()
print(f"Best: W{best[1]} tol{best[2]} score>={best[3]} -> revealed "
      f"recovery {best[0]:.0%}. Bands (frozen): >=50% fit / 25-50% "
      "partial / <25% unfit.")
print("Registry: T-IM51.")
