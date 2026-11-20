#!/usr/bin/env python3
"""
p6_29_selector_validation.py — SELECTOR OUT-OF-SAMPLE VALIDATION. (T-IM36.)
===============================================================================
V1 and U FROZEN exactly as trained on 2025-10 (T-IM34/35); ZERO refitting:
  V1: REA-interaction (15 min, direction-aligned) AND same-direction
      score>=6 signal completed within 5 min
  U:  REA-interaction AND (KME-window 45 min OR that signal)
Signals recomputed with the frozen scoring rules (insample=False path).
Reported per month: catch of his entries, fires/day (30 s grid, 5-min
dedupe), displacement of caught fills vs trigger edge.
Training reference: V1 38% / 18.6 f/d; U 49% / 48.4 f/d.

RUN: python3 Tests/P6_imitation_study/p6_29_selector_validation.py --month 2022-02
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
import p6_22_s6_1_presence as PR
from p6_24_s6_3_selectors import interact_edges
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p4_3_confluence_news import news_sets

GRID, DEDUP = 30, 300


def run(repo, month):
    nxt = (pd.Timestamp(month + "-01") + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d")
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < nxt)].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = PR.Resolver(bm, zr)
    P = prep(repo, month, insample=False)
    secs, mids = P["secs"], P["mids"]
    cx = P["cx"]
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    sg = cx.sig
    ss = sg.comp_ns.to_numpy(np.int64) // 10**9
    sdir = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    oo = np.argsort(ss); ss, sdir = ss[oo], sdir[oo]

    def c1_at(t):
        t_ns = int(t.astype("datetime64[ns]").astype(np.int64))
        kk = np.searchsorted(ev, t_ns, "right") - 1
        return bool(kk >= 0 and (t_ns - ev[kk]) <= 45 * 60 * 10**9)

    def c3_at(t, d):
        t_s = int(t.astype("datetime64[s]").astype(np.int64))
        a, bb = np.searchsorted(ss, t_s - 300), np.searchsorted(ss, t_s, "right")
        return bool((sdir[a:bb] == d).any())

    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(month)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    print(f"{month}: his entries {len(em)}", flush=True)

    catchV = catchU = n = 0
    disp = []
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        side = 1 if r.side == "long" else -1
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        n += 1
        E = interact_edges(R, sd0, t, "REA", 15, secs, mids, side)
        if not E:
            continue
        c1, c3 = c1_at(t), c3_at(t, side)
        if c3:
            catchV += 1
            fills = np.atleast_1d(r.entry_prices)
            if len(fills) and np.isfinite(fills[0]):
                e = min(E, key=lambda q: abs(float(fills[0]) - q))
                disp.append((float(fills[0]) - e) * side)
        if c1 or c3:
            catchU += 1
    firesV = firesU = 0
    sds = sorted(set(sd1))
    for sd0 in sds:
        g = bm[bm.sd == sd0]
        t0 = np.datetime64(g.ts_event.iloc[0].tz_convert(None))
        t1 = np.datetime64(g.ts_event.iloc[-1].tz_convert(None))
        lastV = {d: -10**12 for d in (1, -1)}
        lastU = {d: -10**12 for d in (1, -1)}
        tt = t0
        while tt < t1:
            ts_ = tt.astype("datetime64[s]").astype(np.int64)
            for d in (1, -1):
                needV = ts_ - lastV[d] > DEDUP
                needU = ts_ - lastU[d] > DEDUP
                if not (needV or needU):
                    continue
                c1 = c1_at(tt); c3 = c3_at(tt, d)
                v_ok = c3; u_ok = c1 or c3
                if (needV and v_ok) or (needU and u_ok):
                    if interact_edges(R, sd0, tt, "REA", 15, secs, mids, d):
                        if needV and v_ok:
                            firesV += 1; lastV[d] = ts_
                        if needU and u_ok:
                            firesU += 1; lastU[d] = ts_
            tt = tt + np.timedelta64(GRID, "s")
        print(".", end="", flush=True)
    nd = len(sds)
    dq = np.percentile(disp, [25, 50, 75]) if disp else [np.nan]*3
    print(f"\n\n===== VALIDATION {month} ({nd} sessions, {n} entries) =====")
    print(f"| selector | catch | catch % | fires/day | training ref |")
    print(f"| V1 | {catchV}/{n} | {catchV/max(1,n):.0%} | {firesV/nd:.1f} | 38% / 18.6 |")
    print(f"| U  | {catchU}/{n} | {catchU/max(1,n):.0%} | {firesU/nd:.1f} | 49% / 48.4 |")
    print(f"displacement (caught V1 fills): q25/50/75 = {dq[0]:+.2f}/{dq[1]:+.2f}/{dq[2]:+.2f}  (training +0.5/+3.0/+4.6)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--month", required=True)
    a = ap.parse_args()
    run(a.repo, a.month)
