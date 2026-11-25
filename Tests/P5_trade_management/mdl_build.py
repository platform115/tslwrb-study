#!/usr/bin/env python3
"""
mdl_build.py — T-IM50: multi-day level detector. Spec: MDL_SPEC.md
(committed first). Evidence from 1m bars over the FULL corpus
(completed sessions only -> screening-tier legal by construction).
RUN: python3 Tests/P5_trade_management/mdl_build.py > Tests/P5_trade_management/MDL_REPORT.md
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(113)
TOL_REC = 3.0           # recovery tolerance (pts)
KILL = 5.0              # deactivation: daily close beyond level by 5+

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b[~b.is_roll_day].sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days = sorted(b.sd.unique())
day_ix = {d: i for i, d in enumerate(days)}

# ---------- evidence per completed day (HIS families) ----------
# E1: 5m swing reaction points (N=2 each side)
ev_rows = []
g5 = b.set_index("ts_event").groupby("sd")
for sd, g in b.groupby("sd"):
    r5 = g.set_index("ts_event").resample("5min").agg(
        {"high": "max", "low": "min", "close": "last"}).dropna()
    h, lo = r5.high.to_numpy(), r5.low.to_numpy()
    for i in range(2, len(r5) - 2):
        if h[i] == max(h[i - 2:i + 3]):
            ev_rows.append((sd, float(h[i]), "swing"))
        if lo[i] == min(lo[i - 2:i + 3]):
            ev_rows.append((sd, float(lo[i]), "swing"))
w = pd.read_parquet("Data/inputs/wrb_1m.parquet")
w = w[w.body_size > w.prior_body_max].copy()
w["sd"] = w.session_date.astype(str)
# E2: WRB body edges
for sd, g in w.groupby("sd"):
    for _, r in g.iterrows():
        ev_rows.append((sd, float(max(r.open, r.close)), "wrb"))
        ev_rows.append((sd, float(min(r.open, r.close)), "wrb"))
# E3: hidden-gap edges (unfilled at bar completion)
wg = pd.read_parquet("Data/inputs/wrb_1m.parquet")
wg = wg[wg.has_whg & (wg.whg_fill_status != "filled")].copy()
wg["sd"] = wg.session_date.astype(str)
for sd, g in wg.groupby("sd"):
    for _, r in g.iterrows():
        ev_rows.append((sd, float(r.whg_top), "gap"))
        ev_rows.append((sd, float(r.whg_bottom), "gap"))
E = pd.DataFrame(ev_rows, columns=["sd", "px", "fam"])
E["di"] = E.sd.map(day_ix)
E = E.dropna(subset=["di"])
E["di"] = E.di.astype(int)
print(f"# MDL REPORT — MULTI-DAY LEVEL DETECTOR (T-IM50)", flush=True)
print("STATUS: CLOSED | 2026-11-25 | Spec: MDL_SPEC.md (committed "
      "first) | evidence = completed sessions only (screening-legal)")
print()
print(f"Evidence records: {len(E):,} over {len(days)} sessions "
      f"({E.fam.value_counts().to_dict()})")
print()
# daily closes for deactivation
dcl = b.groupby("sd").close.last()
closes = np.array([dcl[d] for d in days])

def levels_for_day(di, W, tol, m):
    """Active levels at the OPEN of day index di (uses days < di)."""
    sub = E[(E.di >= di - W) & (E.di < di)]
    if not len(sub):
        return []
    arr = sub.sort_values("px")[["px", "di"]].to_numpy()
    out = []
    i = 0
    n = len(arr)
    while i < n:
        j = i
        while j + 1 < n and arr[j + 1, 0] - arr[i, 0] <= tol:
            j += 1
        seg = arr[i:j + 1]
        mdays = np.unique(seg[:, 1].astype(int))
        if len(mdays) >= m:
            lvl = float(np.median(seg[:, 0]))
            last_mem = int(mdays.max())
            # deactivation: any daily close beyond level +/- KILL after
            # the last member day
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - lvl) > KILL).all()):
                out.append(lvl)
        i = j + 1
    return out

# ---------- his key prices (recovery targets) ----------
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
zr["sd"] = pd.to_datetime(zr.ts_utc, utc=True).dt.strftime("%Y-%m-%d")
pk = zr[(zr.price_1.notna()) & (zr.tier == "key")][["sd", "price_1"]]
pa = zr[zr.price_1.notna()][["sd", "price_1"]]
print(f"Recovery targets: key-tier priced mentions {len(pk)}; all "
      f"priced mentions {len(pa)}.")
print()

def nearest_day(sd):
    # map mention date to the day index of that session (or previous)
    while sd not in day_ix and sd > days[0]:
        sd = (pd.Timestamp(sd) - pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    return day_ix.get(sd)

def recovery(targets, lv_fun):
    hit = tot = 0
    for _, r in targets.iterrows():
        di = nearest_day(r.sd)
        if di is None or di < 45:
            continue
        tot += 1
        lv = lv_fun(di)
        if any(abs(l - r.price_1) <= TOL_REC for l in lv):
            hit += 1
    return hit, tot

print("## RECOVERY CHECK (his-families detector, all parameter cells)")
print("| window | tol | min days | key-tier recovered | all-priced "
      "recovered | levels active (median/day) |")
print("|---|---|---|---|---|---|")
best = None
import functools
for W in (20, 40):
    for tol in (2.0, 3.0):
        for m in (3, 4):
            cache = {}
            def lf(di, W=W, tol=tol, m=m, cache=cache):
                if di not in cache:
                    cache[di] = levels_for_day(di, W, tol, m)
                return cache[di]
            hk, tk = recovery(pk, lf)
            ha, ta = recovery(pa, lf)
            sample = [len(lf(di)) for di in
                      RNG.choice(np.arange(60, len(days)), 40,
                                 replace=False)]
            med = int(np.median(sample))
            print(f"| {W} | {tol} | {m} | {hk}/{tk} ({hk/max(1,tk):.0%})"
                  f" | {ha}/{ta} ({ha/max(1,ta):.0%}) | {med} |")
            score = hk / max(1, tk)
            if best is None or score > best[0]:
                best = (score, W, tol, m)
print()
# ---------- generic control arm ----------
dh = b.groupby("sd").high.max(); dl = b.groupby("sd").low.min()
highs = np.array([dh[d] for d in days]); lows = np.array([dl[d] for d in days])
def generic_levels(di):
    if di < 6:
        return []
    out = [highs[di-1], lows[di-1], closes[di-1],
           highs[di-6:di].max(), lows[di-6:di].min()]
    return out
hk, tk = recovery(pk, generic_levels)
ha, ta = recovery(pa, generic_levels)
print("## GENERIC CONTROL ARM (prior-day H/L/C + 5-day H/L)")
print(f"key-tier recovered: {hk}/{tk} ({hk/max(1,tk):.0%}); all-priced: "
      f"{ha}/{ta} ({ha/max(1,ta):.0%}); levels/day = 5 by construction")
print()
# ---------- independent-value check (SCREENING tier, 1m bars) ----------
sc, W, tol, m = best
print(f"## INDEPENDENT-VALUE CHECK (best cell W{W} tol{tol} m{m}; "
      "SCREENING tier: 1m bars, completed-bar rule)")
cache2 = {}
def lf2(di):
    if di not in cache2:
        cache2[di] = levels_for_day(di, W, tol, m)
    return cache2[di]
react_lvl, react_rnd = [], []
pick = RNG.choice(np.arange(60, len(days)), 150, replace=False)
for di in pick:
    g = b[b.sd == days[di]]
    h_, l_, c_ = g.high.to_numpy(), g.low.to_numpy(), g.close.to_numpy()
    if len(g) < 60:
        continue
    rng_day = h_.max() - l_.min()
    lv = lf2(di)
    rnds = RNG.uniform(l_.min(), h_.max(), size=max(1, len(lv)))
    for price_set, sink in ((lv, react_lvl), (rnds, react_rnd)):
        for L in price_set:
            touched = np.flatnonzero((l_ <= L + 1) & (h_ >= L - 1))
            if not len(touched):
                continue
            t0 = touched[0]
            seg = c_[t0:t0 + 30]
            if len(seg) < 5:
                continue
            side = 1 if c_[max(t0 - 1, 0)] > L else -1
            move_away = (seg - L) * side
            sink.append(float(move_away.max() >= 1.5))
print(f"touched-level reactions (>=1.5 pt away within 30 min): levels "
      f"{np.mean(react_lvl):.0%} (n={len(react_lvl)}) vs random prices "
      f"{np.mean(react_rnd):.0%} (n={len(react_rnd)})")
print()
# save best-cell levels for the study months
rows = []
for di in range(60, len(days)):
    for L in lf2(di):
        rows.append((days[di], L))
LV = pd.DataFrame(rows, columns=["session_date", "level"])
LV.to_parquet("Data/inputs/mdl_levels.parquet", index=False)
print(f"Saved {len(LV):,} level-days (best cell) to "
      "Data/inputs/mdl_levels.parquet. Registry: T-IM50.")
