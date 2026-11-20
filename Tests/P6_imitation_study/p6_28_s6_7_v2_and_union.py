#!/usr/bin/env python3
"""
p6_28_s6_7_v2_and_union.py — SELECTOR v2 (Key-KME-Zone system) + POST-HOC
UNION CELL + S6 WRAP NUMBERS. (T-IM35.)
===============================================================================
POST-HOC (flagged): U = REA-interaction & (KME-window OR signal) - the
union cell left out of the registered rounds.
SELECTOR v2 (pre-registered here, before running): targets his Key-KME-
Zone system. Structural proxy for "open WRB Zone": the UNFILLED/PARTIAL
5m hidden gap (G1: KME gaps live on 5m; his "open WRB Zones via unfilled
hidden gaps"). Cells:
  V2a: 5m-gap interaction (5-min window, direction-aligned) & KME-window
  V2b: V2a & Big gap (size >= 1.5x median of today's 5m gaps)
  V2c: V2a & C3 signal
Also: v1 (REA-interaction & C3) x v2 overlap on caught entries, and the
combined uncaught list - the S6 wrap accounting.

RUN: python3 Tests/P6_imitation_study/p6_28_s6_7_v2_and_union.py      (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p6_22_s6_1_presence import Resolver, MONTH
from p6_24_s6_3_selectors import interact_edges
from p6_12_g1_hidden_gap import fill_state
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p4_3_confluence_news import news_sets

GRID, DEDUP = 30, 300


def gap5_edges(R, sd, t, secs, mids, side, M=5, big=False, b1=None):
    """Most-recent unfilled/partial 5m gap per direction; interaction check."""
    objs = [z for z in R._objs(sd, "gap") if z["comp"] <= t and z["tf"] == 5]
    if not objs:
        return []
    if big:
        med = np.median([z["hi"] - z["lo"] for z in objs])
        objs = [z for z in objs if (z["hi"] - z["lo"]) >= 1.5 * med]
    want = "up" if side > 0 else "down"
    best = {}
    for z in objs:
        if z["dir"] != want:
            continue
        k = z["dir"]
        if k not in best or z["comp"] > best[k]["comp"]:
            best[k] = z
    ts1, h1, l1 = b1
    sel = []
    for z in best.values():
        if fill_state(z, h1, l1, ts1, np.datetime64(t)) != "FILLED":
            sel += [z["lo"], z["hi"]]
    if not sel:
        return []
    t_s = t.astype("datetime64[s]").astype(np.int64)
    j1 = int(np.searchsorted(secs, t_s - M * 60))
    j2 = int(np.searchsorted(secs, t_s, "right")) - 1
    if j2 - j1 < 5:
        return []
    w = mids[j1:j2 + 1]; px_t = mids[j2]
    out = []
    for e in sel:
        if not (w.min() - 1 <= e <= w.max() + 1):
            continue
        crossed = ((w < e).any() and (w > e).any())
        if crossed and (px_t - e) * side > 0:
            out.append(e); continue
        if np.min(np.abs(w - e)) <= 1.0 and (px_t - e) * side >= 2.0:
            out.append(e)
    return out


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{MONTH}-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    P = prep(repo, MONTH)
    secs, mids = P["secs"], P["mids"]
    cx = P["cx"]
    ts1b = bm.ts_event.dt.tz_convert(None).to_numpy()
    b1 = (ts1b, bm.high.to_numpy(), bm.low.to_numpy())
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    sg = cx.sig[cx.sig.score >= 6]
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

    sd1 = bm.sd.to_numpy()

    def sec_sd(t):
        j = np.searchsorted(ts1b, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    CELLS = ["U rea&(KME|sig)", "V1 rea&sig", "V2a gap5&KME", "V2b +Big", "V2c gap5&KME&sig"]

    def flags(sd0, t, side):
        rea = bool(interact_edges(R, sd0, t, "REA", 15, secs, mids, side))
        c1, c3 = c1_at(t), c3_at(t, side)
        g5 = bool(gap5_edges(R, sd0, t, secs, mids, side, big=False, b1=b1))
        g5b = bool(gap5_edges(R, sd0, t, secs, mids, side, big=True, b1=b1))
        return {"U rea&(KME|sig)": rea and (c1 or c3), "V1 rea&sig": rea and c3,
                "V2a gap5&KME": g5 and c1, "V2b +Big": g5b and c1,
                "V2c gap5&KME&sig": g5 and c1 and c3}

    catch = {c: [] for c in CELLS}; rows = []
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        side = 1 if r.side == "long" else -1
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        f = flags(sd0, t, side)
        for c in CELLS:
            catch[c].append(f[c])
        rows.append(dict(t=r.first_entry_utc, side=r.side, pnl=r.realized_pnl, **f))
    D = pd.DataFrame(rows)
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
            for d in (1, -1):
                need = [c for c in CELLS if ts_ - last[(c, d)] > DEDUP]
                if need:
                    f = flags(sd0, tt, d)
                    for c in need:
                        if f[c]:
                            fires[c] += 1; last[(c, d)] = ts_
            tt = tt + np.timedelta64(GRID, "s")
        print(".", end="", flush=True)
    nd = len(sds); n = len(D)
    print(f"\n\n===== SELECTOR v2 + UNION ({MONTH}, {nd} sessions, {n} entries) =====")
    print("| cell | catch | catch % | fires/day | fires/catch |")
    for c in CELLS:
        k = D[c].sum()
        print(f"| {c} | {k}/{n} | {k/n:.0%} | {fires[c]/nd:.1f} | {fires[c]/max(1,k):.0f} |")
    both = (D["V1 rea&sig"] | D["V2c gap5&KME&sig"])
    print(f"| V1 or V2c | {both.sum()}/{n} | {both.mean():.0%} | ~{(fires['V1 rea&sig']+fires['V2c gap5&KME&sig'])/nd:.1f} | - |")
    print(f"\nV1-only {int((D['V1 rea&sig'] & ~D['V2c gap5&KME&sig']).sum())} | "
          f"V2c-only {int((D['V2c gap5&KME&sig'] & ~D['V1 rea&sig']).sum())} | "
          f"both {int((D['V1 rea&sig'] & D['V2c gap5&KME&sig']).sum())}")
    print("\n## UNCAUGHT by V1|V2c (the wrap list)")
    for _, r in D[~both].iterrows():
        print(f"  {str(pd.Timestamp(r.t))[:19]} {r.side} pnl {r.pnl}")
    D.to_parquet(os.path.join(repo, "Data/inputs/s6_selectors_final.parquet"))


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
