#!/usr/bin/env python3
"""
p6_26_s6_5_conjunction.py — CONJUNCTION GRID (pre-registered, T-IM33).
===============================================================================
Base: REA interaction, 15-min window, direction-aligned (S6.3: 86% catch,
299 fires/day). Conditions (from measured evidence, fixed before this run):
  C1  inside a KME window (45 min after a scheduled event)  [S6.4: 42 vs 10]
  C2  volatility spike NOW: |mv120| >= 18 ticks OR comp5 >= 1.39
      (his own grounded "volatility spike"; comp5 = current 5-min range /
      median of the prior hour's same-width windows)
Cells: base | base&C1 | base&C2 | base&C1&C2 | base&(C1|C2). Each scored:
catch of his 92 entries (at the entry second, his direction) and fires/day
(30 s grid, both directions, 5-min dedupe). No cell added after results.

RUN: python3 Tests/P6_imitation_study/p6_26_s6_5_conjunction.py       (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_22_s6_1_presence import Resolver, MONTH            # noqa: E402
from p6_24_s6_3_selectors import interact_edges            # noqa: E402
from p4_66_context_ablation import prep                    # noqa: E402
from p4_2_entry_context import month_bounds                # noqa: E402
from p4_3_confluence_news import news_sets                 # noqa: E402

TICK = 0.25
MV_T, COMP_T = 18.0, 1.39
GRID, DEDUP = 30, 300


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{MONTH}-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    P = prep(repo, MONTH)
    secs, mids = P["secs"], P["mids"]
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64)

    # ---- per-second condition arrays (vectorized, <=t by construction) ----
    i120 = np.searchsorted(secs, secs - 120)
    mv120 = np.abs(mids - mids[np.maximum(i120, 0)]) / TICK
    S = pd.Series(mids)
    r300 = (S.rolling(300, min_periods=60).max()
            - S.rolling(300, min_periods=60).min()).to_numpy()
    base = pd.Series(r300).shift(300).rolling(3600, min_periods=900).median().to_numpy()
    comp5 = np.where((base > 0) & np.isfinite(base), r300 / base, np.nan)
    c2_arr = (mv120 >= MV_T) | (comp5 >= COMP_T)

    def c1_at(t):
        t_ns = int(t.astype("datetime64[ns]").astype(np.int64))
        kk = np.searchsorted(ev, t_ns, "right") - 1
        return bool(kk >= 0 and (t_ns - ev[kk]) <= 45 * 60 * 10**9)

    def c2_at(t):
        j = int(np.searchsorted(secs, t.astype("datetime64[s]").astype(np.int64), "right")) - 1
        return bool(c2_arr[j]) if j >= 0 else False

    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]

    CELLS = ["base", "base&C1", "base&C2", "base&C1&C2", "base&(C1|C2)"]

    def cell_ok(name, c1, c2):
        return {"base": True, "base&C1": c1, "base&C2": c2,
                "base&C1&C2": c1 and c2, "base&(C1|C2)": c1 or c2}[name]

    # ---- catches ----
    catch = {c: 0 for c in CELLS}
    n = 0
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        side = 1 if r.side == "long" else -1
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        n += 1
        if not interact_edges(R, sd0, t, "REA", 15, secs, mids, side):
            continue
        c1, c2 = c1_at(t), c2_at(t)
        for c in CELLS:
            catch[c] += cell_ok(c, c1, c2)

    # ---- fires/day ----
    fires = {c: 0 for c in CELLS}
    sds = sorted(set(sd1))
    for sd0 in sds:
        g = bm[bm.sd == sd0]
        t0 = np.datetime64(g.ts_event.iloc[0].tz_convert(None))
        t1 = np.datetime64(g.ts_event.iloc[-1].tz_convert(None))
        last = {(c, d): -10**12 for c in CELLS for d in (1, -1)}
        tt = t0
        while tt < t1:
            ts_ = tt.astype("datetime64[s]").astype(np.int64)
            need = [(c, d) for c in CELLS for d in (1, -1)
                    if ts_ - last[(c, d)] > DEDUP]
            if need:
                c1 = c1_at(tt); c2 = c2_at(tt)
                for d in set(d for _, d in need):
                    hit = bool(interact_edges(R, sd0, tt, "REA", 15, secs, mids, d))
                    if hit:
                        for c in CELLS:
                            if (c, d) in dict.fromkeys(need) and cell_ok(c, c1, c2) \
                               and ts_ - last[(c, d)] > DEDUP:
                                fires[c] += 1; last[(c, d)] = ts_
            tt = tt + np.timedelta64(GRID, "s")
        print(".", end="", flush=True)
    nd = len(sds)
    print(f"\n\n===== CONJUNCTION GRID ({MONTH}, {nd} sessions, {n} entries) =====")
    print("| cell | catch | catch % | fires/day | fires per catch |")
    print("|---|---|---|---|---|")
    for c in CELLS:
        fpd = fires[c] / nd
        fpc = fires[c] / max(1, catch[c])
        print(f"| {c} | {catch[c]}/{n} | {catch[c]/n:.0%} | {fpd:.1f} | {fpc:.0f} |")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
