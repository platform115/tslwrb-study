#!/usr/bin/env python3
"""
p6_25_s6_4_accounting.py — S6.4: DAILY ACCOUNTING + ACTED-vs-IGNORED EDGE
PROPERTIES + DAY MAP v2. (T-IM32.)
===============================================================================
1. Daily table: his entries caught by >=1 / >=2 selectors / uncaught.
2. WHY THOSE STRUCTURES (user): for each caught entry, the trigger edge's
   properties; versus IGNORED interactions - detector fires (30s grid,
   5-min dedupe) with no entry of his within +/-10 min. Properties:
   family | TF | KME-window (45 min) | edge age (min since knowable) |
   object size (band width; 0 for levels) | CONFLUENCE (edges of other
   families within 1 pt) | round-number (multiple of 10 / 25 pts) |
   TESTED count (prior touches of the edge today within 1 pt, >=5 min apart).
3. Day map v2: 3 busiest sessions - each trade with its identified trigger
   object (family, TF, edge price, age, KME tag, confluence).

RUN: python3 Tests/P6_imitation_study/p6_25_s6_4_accounting.py        (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_22_s6_1_presence import Resolver, MONTH            # noqa: E402
from p6_23_s6_2_interaction import edges_at                # noqa: E402
from p6_24_s6_3_selectors import interact_edges, SELS      # noqa: E402
from p4_66_context_ablation import prep                    # noqa: E402
from p4_2_entry_context import month_bounds                # noqa: E402
from p4_3_confluence_news import news_sets                 # noqa: E402

RNG = np.random.default_rng(113)
FAMS = ("REA", "SQZ", "GAP", "SHD")
WIN = {"REA": 15, "SQZ": 15, "GAP": 5, "SHD": 5}


def edge_props(R, sd, t, fam, e, secs, mids, ev):
    """Property dict for one edge price e of family fam at time t."""
    # age + size from the selected object owning this edge
    age = np.nan; size = np.nan; tf = np.nan
    if fam in ("GAP", "SHD"):
        objs = R._objs(sd, "gap" if fam == "GAP" else "shd")
        best = {}
        for z in objs:
            if z["comp"] <= t:
                k = (z["tf"], z["dir"])
                if k not in best or z["comp"] > best[k]["comp"]:
                    best[k] = z
        for z in best.values():
            if abs(z["lo"] - e) <= 0.26 or abs(z["hi"] - e) <= 0.26:
                age = float((t - z["comp"]) / np.timedelta64(1, "m"))
                size = z["hi"] - z["lo"]; tf = z["tf"]; break
    elif fam == "REA":
        for f2 in ("rea_sw", "rea_zz"):
            best = {}
            for z in R._objs(sd, f2):
                if z["comp"] <= t:
                    k = z["side"]
                    if k not in best or z["comp"] > best[k]["comp"]:
                        best[k] = z
            for z in best.values():
                if abs(z["px"] - e) <= 0.26:
                    age = float((t - z["comp"]) / np.timedelta64(1, "m"))
                    size = 0.0; tf = 5 if f2 == "rea_sw" else 1
    else:
        for f2 in ("sqz10", "sqz30"):
            eps = [z for z in R._objs(sd, f2) if z["comp"] <= t]
            if eps:
                z = max(eps, key=lambda q: q["comp"])
                if abs(z["lo"] - e) <= 0.26 or abs(z["hi"] - e) <= 0.26:
                    age = float((t - z["comp"]) / np.timedelta64(1, "m"))
                    size = z["hi"] - z["lo"]; tf = 1
    # KME window
    t_ns = int(t.astype("datetime64[ns]").astype(np.int64))
    kk = np.searchsorted(ev, t_ns, "right") - 1
    kme = bool(kk >= 0 and (t_ns - ev[kk]) <= 45 * 60 * 10**9)
    # confluence: edges of OTHER families within 1 pt
    conf = 0
    for f2 in FAMS:
        if f2 == fam:
            continue
        conf += sum(1 for e2 in edges_at(R, sd, t, f2) if abs(e2 - e) <= 1.0)
    # round number
    rnd = (abs(e % 10) < 0.26 or abs(e % 10 - 10) < 0.26)
    rnd25 = (abs(e % 25) < 0.26 or abs(e % 25 - 25) < 0.26)
    # tested count today: prior touches within 1 pt, >= 5 min apart
    t_s = t.astype("datetime64[s]").astype(np.int64)
    j0 = int(np.searchsorted(secs, t_s - 12 * 3600))
    j2 = int(np.searchsorted(secs, t_s, "right")) - 1
    w = mids[j0:j2 + 1]; ws = secs[j0:j2 + 1]
    near = np.abs(w - e) <= 1.0
    touches = 0; last = -10**12
    for i in np.flatnonzero(near):
        if ws[i] - last >= 300:
            touches += 1; last = ws[i]
    return dict(fam=fam, tf=tf, kme=kme, age_min=age, size=size,
                confluence=conf, round10=rnd, round25=rnd25, tested=touches)


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
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, t, "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].copy()
    em["t"] = [np.datetime64(pd.Timestamp(x).tz_convert(None)) for x in em.first_entry_utc]
    em["sd"] = [sec_sd(t) for t in em.t]
    his_times = em.t.to_numpy()

    # ---- 1. daily accounting ----
    caught_any = {}; caught_2 = {}
    acted_props = []
    for _, r in em.iterrows():
        side = 1 if r.side == "long" else -1
        nsel = 0; first_edge = None; first_fam = None
        for name, fam, M in SELS:
            E = interact_edges(R, r.sd, r.t, fam, M, secs, mids, side)
            if E:
                nsel += 1
                if first_edge is None:
                    fills = np.atleast_1d(r.entry_prices)
                    fill = float(fills[0]) if len(fills) and np.isfinite(fills[0]) else np.nan
                    first_edge = min(E, key=lambda q: abs((fill if np.isfinite(fill) else 0) - q))
                    first_fam = fam
        caught_any[r.name] = nsel >= 1; caught_2[r.name] = nsel >= 2
        if first_edge is not None:
            acted_props.append(edge_props(R, r.sd, r.t, first_fam, first_edge, secs, mids, ev))
    em["c1"] = em.index.map(caught_any); em["c2"] = em.index.map(caught_2)
    print("## 1. DAILY ACCOUNTING")
    print("| session | entries | caught >=1 | >=2 | uncaught |")
    for sd0, g in em.groupby("sd"):
        print(f"| {sd0} | {len(g)} | {g.c1.sum()} | {g.c2.sum()} | {(~g.c1).sum()} |")
    print(f"| TOTAL | {len(em)} | {em.c1.sum()} | {em.c2.sum()} | {(~em.c1).sum()} |")

    # ---- 2. ignored interactions sample ----
    ignored_props = []
    sds = sorted(set(em.sd.dropna()))
    for sd0 in sds:
        g = bm[bm.sd == sd0]
        t0 = np.datetime64(g.ts_event.iloc[0].tz_convert(None))
        t1 = np.datetime64(g.ts_event.iloc[-1].tz_convert(None))
        last = {}
        tt = t0
        while tt < t1 and len(ignored_props) < 600:
            for fam in FAMS:
                for d in (1, -1):
                    key = (fam, d)
                    ts_ = tt.astype("datetime64[s]").astype(np.int64)
                    if ts_ - last.get(key, -10**12) <= 300:
                        continue
                    E = interact_edges(R, sd0, tt, fam, WIN[fam], secs, mids, d)
                    if E:
                        last[key] = ts_
                        near_entry = np.any(np.abs((his_times - tt) / np.timedelta64(1, "m")) <= 10)
                        if not near_entry and RNG.random() < 0.15:
                            ignored_props.append(edge_props(R, sd0, tt, fam, E[0], secs, mids, ev))
            tt = tt + np.timedelta64(60, "s")
    A, I = pd.DataFrame(acted_props), pd.DataFrame(ignored_props)
    print(f"\n## 2. ACTED-ON ({len(A)}) vs IGNORED ({len(I)}) interacted edges")
    print("| property | acted | ignored |")
    print(f"| KME-window | {A.kme.mean():.0%} | {I.kme.mean():.0%} |")
    print(f"| edge age min (q50) | {A.age_min.median():.0f} | {I.age_min.median():.0f} |")
    print(f"| object size pts (q50) | {A['size'].median():.2f} | {I['size'].median():.2f} |")
    print(f"| confluence >=1 other family | {(A.confluence>=1).mean():.0%} | {(I.confluence>=1).mean():.0%} |")
    print(f"| confluence >=2 | {(A.confluence>=2).mean():.0%} | {(I.confluence>=2).mean():.0%} |")
    print(f"| round-10 edge | {A.round10.mean():.0%} | {I.round10.mean():.0%} |")
    print(f"| round-25 edge | {A.round25.mean():.0%} | {I.round25.mean():.0%} |")
    print(f"| tested >=2 today | {(A.tested>=2).mean():.0%} | {(I.tested>=2).mean():.0%} |")
    print(f"| tested >=3 today | {(A.tested>=3).mean():.0%} | {(I.tested>=3).mean():.0%} |")
    print("| family mix | " + str(dict(A.fam.value_counts())) + " | " + str(dict(I.fam.value_counts())) + " |")

    # ---- 3. day map v2 ----
    busy = em.sd.value_counts().head(3).index
    print("\n## 3. DAY MAP v2 (trigger objects identified)")
    for sd0 in busy:
        print(f"\n=== {sd0} ===")
        for _, r in em[em.sd == sd0].sort_values("t").iterrows():
            side = 1 if r.side == "long" else -1
            tag = "-"
            for name, fam, M in SELS:
                E = interact_edges(R, sd0, r.t, fam, M, secs, mids, side)
                if E:
                    fills = np.atleast_1d(r.entry_prices)
                    fill = float(fills[0]) if len(fills) and np.isfinite(fills[0]) else np.nan
                    e = min(E, key=lambda q: abs((fill if np.isfinite(fill) else 0) - q))
                    pr = edge_props(R, sd0, r.t, fam, e, secs, mids, ev)
                    tag = (f"{fam} edge {e:.2f} (tf {pr['tf']}, age {pr['age_min']:.0f}m, "
                           f"{'KME' if pr['kme'] else 'no-KME'}, confl {pr['confluence']}, "
                           f"tested {pr['tested']}x)")
                    break
            print(f"  {str(pd.Timestamp(r.first_entry_utc))[11:19]} {r.side:5s} "
                  f"fill {np.atleast_1d(r.entry_prices)[:1]} pnl {r.realized_pnl} | {tag}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
