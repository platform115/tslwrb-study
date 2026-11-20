#!/usr/bin/env python3
"""
p6_24_s6_3_selectors.py — S6.3: EVENT-BASED SELECTORS SCORED. (T-IM31.)
===============================================================================
Selectors (S6.2-amended, plan-locked):
  SEL-A' REA interaction, 15-min window   SEL-C' SQZ interaction, 15-min
  SEL-B' GAP interaction, 5-min window    SEL-E' SHD interaction, 5-min
Interaction = price crossed a selected edge (direction on the break side)
or rejected it (touch within 1 pt, now >= 2 pts away on that side) —
identical logic to p6_23. Direction for fires/day: either direction counts
(a fire is "an interaction event occurred"); his entries are caught when
the selector was true AT the entry second WITH his direction.

Scored per selector:
  catch: n of his 92 entries where true at the entry second
  fires/day: interaction events on a 30-second grid over the month,
     deduped with a 5-minute gap clock per selector per direction
  union catch + pairwise overlap
  DISPLACEMENT (the entry-price rule for replication): for each caught
     entry, the trigger edge = the interacted edge nearest to the fill;
     displacement = signed (fill - edge) * side; distribution reported.
Anchors: per-second mids (1-second mandate). Structures harness-certified.

RUN: python3 Tests/P6_imitation_study/p6_24_s6_3_selectors.py         (repo root)
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
from p4_66_context_ablation import prep                    # noqa: E402
from p4_2_entry_context import month_bounds                # noqa: E402

SELS = [("SEL-A' REA/15m", "REA", 15), ("SEL-C' SQZ/15m", "SQZ", 15),
        ("SEL-B' GAP/5m", "GAP", 5), ("SEL-E' SHD/5m", "SHD", 5)]
GRID = 30          # seconds between fire evaluations
DEDUP = 300        # 5-minute gap clock per (selector, direction)


def interact_edges(R, sd, t, fam, M, secs, mids, side):
    """Returns the list of interacted edges for (fam, window, side) at t."""
    t_s = t.astype("datetime64[s]").astype(np.int64)
    j1 = int(np.searchsorted(secs, t_s - M * 60))
    j2 = int(np.searchsorted(secs, t_s, "right")) - 1
    if j2 - j1 < 5:
        return []
    w = mids[j1:j2 + 1]
    px_t = mids[j2]
    out = []
    # minute-cached edges (knowable_ts has 1-minute resolution)
    for e in edges_at(R, sd, t, fam):
        if not (w.min() - 1 <= e <= w.max() + 1):
            continue
        crossed = ((w < e).any() and (w > e).any()) or (w[0] - e) * (px_t - e) < 0
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
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, t, "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(MONTH)
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    print(f"{len(em)} entries", flush=True)

    # ---- catches + displacement ----
    catches = {name: [] for name, _, _ in SELS}
    disp = {name: [] for name, _, _ in SELS}
    for _, r in em.iterrows():
        t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
        side = 1 if r.side == "long" else -1
        sd0 = sec_sd(t)
        if sd0 is None:
            continue
        fills = np.atleast_1d(r.entry_prices)
        fill = float(fills[0]) if len(fills) and np.isfinite(fills[0]) else np.nan
        for name, fam, M in SELS:
            E = interact_edges(R, sd0, t, fam, M, secs, mids, side)
            caught = bool(E)
            catches[name].append(caught)
            if caught and np.isfinite(fill):
                e = min(E, key=lambda q: abs(fill - q))
                disp[name].append((fill - e) * side)

    # ---- fires/day ----
    fires = {name: 0 for name, _, _ in SELS}
    sds = sorted(set(sd1))
    for sd0 in sds:
        g = bm[bm.sd == sd0]
        t0 = np.datetime64(g.ts_event.iloc[0].tz_convert(None))
        t1 = np.datetime64(g.ts_event.iloc[-1].tz_convert(None))
        last = {(nm, d): -10**12 for nm, _, _ in SELS for d in (1, -1)}
        tt = t0
        while tt < t1:
            for name, fam, M in SELS:
                for d in (1, -1):
                    ts_ = tt.astype("datetime64[s]").astype(np.int64)
                    if ts_ - last[(name, d)] <= DEDUP:
                        continue
                    if interact_edges(R, sd0, tt, fam, M, secs, mids, d):
                        fires[name] += 1
                        last[(name, d)] = ts_
            tt = tt + np.timedelta64(GRID, "s")
        print(".", end="", flush=True)
    ndays = len(sds)

    print(f"\n\n===== S6.3 SELECTOR SCOREBOARD ({MONTH}, {ndays} sessions) =====")
    print("| selector | catch | catch % | fires/day | disp q25/50/75 (pts past edge) |")
    print("|---|---|---|---|---|")
    C = pd.DataFrame(catches)
    for name, _, _ in SELS:
        c = C[name]
        dq = np.percentile(disp[name], [25, 50, 75]) if disp[name] else [np.nan]*3
        print(f"| {name} | {c.sum()}/{len(c)} | {c.mean():.0%} | {fires[name]/ndays:.1f} "
              f"| {dq[0]:+.2f} / {dq[1]:+.2f} / {dq[2]:+.2f} |")
    u = C.any(axis=1)
    n2 = (C.sum(axis=1) >= 2)
    print(f"| UNION | {u.sum()}/{len(u)} | {u.mean():.0%} | - | - |")
    print(f"| >=2 selectors | {n2.sum()}/{len(n2)} | {n2.mean():.0%} | - | - |")
    print("\n## overlap matrix (joint catch counts)")
    names = [n for n, _, _ in SELS]
    print("        " + "  ".join(f"{n[:10]:>10s}" for n in names))
    for a in names:
        rowx = [f"{(C[a] & C[bn]).sum():>10d}" for bn in names]
        print(f"{a[:8]:8s}" + "  ".join(rowx))
    print("\n## UNCAUGHT entries (listed verbatim for the next cycle)")
    k = 0
    for (_, r), caught in zip(em.iterrows(), u):
        if not caught:
            k += 1
            print(f"  {str(pd.Timestamp(r.first_entry_utc))[:19]} {r.side} "
                  f"entries {np.atleast_1d(r.entry_prices)[:2]} pnl {r.realized_pnl}")
    if k == 0:
        print("  none")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
