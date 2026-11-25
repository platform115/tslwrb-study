#!/usr/bin/env python3
"""
mdl_v2.py — T-IM51: detector v2 + revealed-preference teaching set.
Spec: MDL_SPEC.md + V2 addendum (committed first).
RUN: python3 Tests/P5_trade_management/mdl_v2.py > Tests/P5_trade_management/MDL_V2_REPORT.md
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(113)
TOL_REC, KILL = 3.0, 5.0

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b[~b.is_roll_day].sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days = sorted(b.sd.unique())
day_ix = {d: i for i, d in enumerate(days)}
dcl = b.groupby("sd").close.last()
closes = np.array([dcl[d] for d in days])

# ---------------- market evidence v2 ----------------
import sys, os
sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets                   # noqa: E402
ev_t = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
so["ks"] = (so.knowable_ts.astype("datetime64[ns]").astype("int64")
            // 10**9)
kk = np.searchsorted(ev_t, so.ks.to_numpy(), "right") - 1
so["newsborn"] = (so.ks.to_numpy() - ev_t[np.maximum(kk, 0)]) <= 2700
for col in ("band_lo", "band_hi"):
    g = so[["sd", col, "newsborn"]].dropna().rename(columns={col: "px"})
    rows.append(g)
# 5m/15m WRB bodies (certified definition on resampled bars)
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
E = E.dropna(subset=["di"]); E["di"] = E.di.astype(int)
E = E.sort_values("px").reset_index(drop=True)
print("# MDL V2 REPORT — DETECTOR v2 + REVEALED-PREFERENCE TARGET "
      "(T-IM51)")
print("STATUS: CLOSED | 2026-11-25 | Spec: MDL_SPEC.md + V2 addendum")
print()
print(f"Market evidence v2: {len(E):,} deduped (sd,px) records "
      f"(shadows/gaps/swings corpus-wide + 5m/15m WRB bodies; news-born "
      f"{E.newsborn.mean():.0%}).")

# ---------------- revealed-preference teaching set ----------------
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
                      columns=["object_id", "band_lo", "band_hi"])
sl2 = sl2.merge(so2.drop_duplicates("object_id"), on="object_id")
for _, r in sl2.iterrows():
    if r.sd in day_ix and np.isfinite(r.band_lo):
        act.append((r.sd, float(r.band_lo)))
        act.append((r.sd, float(r.band_hi)))
A = pd.DataFrame(act, columns=["sd", "px"])
A["px"] = (A.px * 4).round() / 4
A = A.drop_duplicates(["sd", "px"])
A["di"] = A.sd.map(day_ix).astype(int)
A = A.sort_values("px").reset_index(drop=True)
# cluster actions into revealed regions (>=3 distinct days within 2.5)
regions = []
arr = A[["px", "di"]].to_numpy()
i, n = 0, len(arr)
while i < n:
    j = i
    while j + 1 < n and arr[j + 1, 0] - arr[j, 0] <= 2.5:
        j += 1
    seg = arr[i:j + 1]
    dset = np.unique(seg[:, 1].astype(int))
    if len(dset) >= 3:
        regions.append(dict(px=float(np.median(seg[:, 0])),
                            d_first=int(np.sort(dset)[2]),
                            d_last=int(dset.max()),
                            ndays=len(dset)))
    i = j + 1
REG = pd.DataFrame(regions)
REG["d_end"] = np.minimum(REG.d_last + 60, len(days) - 1)
print(f"Revealed teaching set: {len(A):,} action records -> "
      f"{len(REG)} revealed key regions (median member-days "
      f"{REG.ndays.median():.0f}, median span "
      f"{(REG.d_last-REG.d_first).median():.0f} sessions).")
pk = zr[(zr.price_1.notna()) & (zr.tier == "key")]
inreg = 0
for _, r in pk.iterrows():
    if r.sd not in day_ix:
        continue
    di = day_ix[r.sd]
    if ((REG.px - r.price_1).abs() <= TOL_REC).any():
        m = REG[(REG.px - r.price_1).abs() <= TOL_REC]
        if ((m.d_first <= di) & (di <= m.d_end)).any():
            inreg += 1
print(f"Sanity: {inreg}/{len(pk)} of his priced KEY mentions fall "
      f"inside an active revealed region.")
print()

# ---------------- detector clustering ----------------
def levels_for_day(di, W, tol, m):
    sub = E[(E.di >= di - W) & (E.di < di)]
    if not len(sub):
        return []
    arr = sub[["px", "di", "newsborn"]].to_numpy()
    out, i, n = [], 0, len(arr)
    while i < n:
        j = i
        while j + 1 < n and arr[j + 1, 0] - arr[i, 0] <= tol:
            j += 1
        seg = arr[i:j + 1]
        score = len(np.unique(seg[:, 1].astype(int)))
        if seg[:, 2].any():
            score += 1                      # news-born bonus (spec)
        if score >= m:
            lvl = float(np.median(seg[:, 0]))
            last_mem = int(seg[:, 1].max())
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - lvl) > KILL).all()):
                out.append(lvl)
        i = j + 1
    return out

print("## V2 RECOVERY (primary = revealed regions; secondary = 55 "
      "priced keys)")
print("| window | tol | min score | revealed regions recovered | "
      "priced keys recovered | levels/day |")
print("|---|---|---|---|---|---|")
best = None
for W in (40, 60):
    for tol in (2.0, 3.0):
        for m in (4, 5):
            cache = {}
            def lf(di, W=W, tol=tol, m=m, cache=cache):
                if di not in cache:
                    cache[di] = levels_for_day(di, W, tol, m)
                return cache[di]
            hit = tot = 0
            for _, r in REG.iterrows():
                tot += 1
                sample = np.linspace(r.d_first, r.d_end, 8).astype(int)
                if any(any(abs(l - r.px) <= TOL_REC for l in lf(di))
                       for di in np.unique(sample)):
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
                      RNG.choice(np.arange(70, len(days)), 30,
                                 replace=False)]))
            print(f"| {W} | {tol} | {m} | {hit}/{tot} "
                  f"({hit/max(1,tot):.0%}) | {hk}/{tk} "
                  f"({hk/max(1,tk):.0%}) | {med} |")
            if best is None or hit / max(1, tot) > best[0]:
                best = (hit / max(1, tot), W, tol, m)
print()
sc, W, tol, m = best
print(f"Best cell: W{W} tol{tol} score>={m} -> revealed recovery "
      f"{sc:.0%}. Verdict bands: >=50% fit / 25-50% partial / <25% "
      "unfit (frozen).")
print("Registry: T-IM51.")
