#!/usr/bin/env python3
"""
p6_16_g4_contraction.py — S3 GENERATOR 4: CONTRACTION RANGES. (T-IM23.)
===============================================================================
HIS OBJECT: the price band of a volatility-contraction period, carrying S/R
("S area broken of the most recent contracting volatility intervals").

DEFINITION CANDIDATES (documented families):
  C1 (Crabel 1990, NR-k): a bar whose range is the narrowest of the last k
     bars marks contraction; band = high/low span of those k bars.
     Tested: NR7 on 5m and 15m.
  C2 (rolling compression, same family as the p6_0 battery measure):
     on 1m bars, W-bar rolling range <= q x median of the prior same-width
     windows (1-hour history) marks an ACTIVE bar; a contraction EPISODE =
     a maximal run of active bars; band = [min low, max high] of the
     episode so far. Tested: W in {15, 30, 60}, q in {0.5, 0.67}.
  Both <=t: episode/NR bands use only completed bars; an episode's band at
  t covers its bars up to t only.

SELECTION: most recent episode (active or ended) at t — single object.
MATCHING: role-aware (his S area = band low, R area = band high),
relation-aware (broken = beyond the edge), tol 3. Fair permutation null.
MERGE TEST (S2 left open): the same generator scored against his
tight-range / trading-range references — if one family explains both
vocabularies, that is merge evidence; if not, they stay separate.

RUN: python3 Tests/P6_imitation_study/p6_16_g4_contraction.py         (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p6_12_g1_hidden_gap import resample_tf                # noqa: E402
from p6_13_g1_identification import RELATIONAL             # noqa: E402

TOL = 3.0
RNG = np.random.default_rng(71)


def episodes_c2(g, W, q):
    """1m bars one session -> list of episodes dicts (band grows through time).
    Returns per-bar: (active_run_id or -1). Episode bands resolved at query."""
    h = g.high.to_numpy(); l = g.low.to_numpy()
    n = len(g)
    rng_w = np.full(n, np.nan)
    for i in range(W, n):
        rng_w[i] = h[i-W+1:i+1].max() - l[i-W+1:i+1].min()
    med = np.full(n, np.nan)
    for i in range(W, n):
        prior = rng_w[max(W, i-60):i]
        prior = prior[np.isfinite(prior)]
        if len(prior) >= 10:
            med[i] = np.median(prior)
    active = np.isfinite(rng_w) & np.isfinite(med) & (rng_w <= q * med)
    eps = []
    i = 0
    while i < n:
        if active[i]:
            j0 = i
            while i < n and active[i]:
                i += 1
            eps.append((j0, i - 1))       # inclusive bar span of the episode
        else:
            i += 1
    return eps, h, l


def band_c2(eps, h, l, jbar, W):
    """Most recent episode at/before bar jbar; band over its bars <= jbar."""
    best = None
    for (a, bnd) in eps:
        if a <= jbar:
            best = (a, min(bnd, jbar))
    if best is None:
        return None
    a, bnd = best
    a0 = max(0, a - W + 1)                # the W-window that triggered spans back
    return float(l[a0:bnd+1].min()), float(h[a0:bnd+1].max())


def nr_band(rb, k, jbar):
    """Most recent NR-k bar at/before jbar on resampled bars; band = k-bar span."""
    h = rb.high.to_numpy(); l = rb.low.to_numpy()
    r = h - l
    best = None
    for i in range(k, jbar + 1):
        if r[i] <= r[i-k:i].min():
            best = i
    if best is None:
        return None
    return float(l[best-k+1:best+1].min()), float(h[best-k+1:best+1].max())


def hit(band, px, role, relation, tol=TOL):
    if band is None:
        return None
    lo, hi = band
    if role == "S":
        return (lo - 2*tol) <= px <= (lo + tol) if relation == "broken" else abs(px - lo) <= tol
    if role == "R":
        return (hi - tol) <= px <= (hi + 2*tol) if relation == "broken" else abs(px - hi) <= tol
    ex = 2*tol if relation == "broken" else tol
    return (lo - ex) <= px <= (hi + ex)


def load_refs(zr, kinds, b, ts1, c1, sd_arr):
    from p6_11_parser_v3 import SIDE  # not needed; role already parsed
    out = []
    sub = zr[(zr.kind.isin(kinds)) & (zr.relation.isin(RELATIONAL))
             & (zr.instrument == "ES")]
    for _, r in sub.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None))
        j = np.searchsorted(ts1, t, "right") - 1
        if j < 0:
            continue
        out.append(dict(t=t, px=c1[max(0, np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1)],
                        sd=sd_arr[j], role=(r.role if isinstance(r.role, str) else None),
                        relation=r.relation, ts=pd.Timestamp(r.ts_utc)))
    return out


def run(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    c1 = b.close.to_numpy()
    sd_arr = b.sd.to_numpy()
    refs = load_refs(zr, ("contraction",), b, ts1, c1, sd_arr)
    refs_tr = load_refs(zr, ("tight_range", "trading_range"), b, ts1, c1, sd_arr)
    print(f"contraction relational ES refs: {len(refs)} | tight/trading-range refs: {len(refs_tr)}")
    sess = sorted({r["sd"] for r in refs} | {r["sd"] for r in refs_tr})
    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd") if s in sess}

    def eval_variant(make_band, label, R):
        hits, nulls = [], []
        for r in R:
            g = groups[r["sd"]]
            gts = g.ts_event.dt.tz_convert(None).to_numpy()
            jbar = np.searchsorted(gts, r["t"], "right") - 2   # last COMPLETED bar
            hits.append(hit(make_band(r["sd"], jbar), r["px"], r["role"], r["relation"]))
        hv = [x for x in hits if x is not None]
        for perm in range(12):
            u = m = 0
            for r in R:
                g = groups[r["sd"]]; gr_i = np.flatnonzero((g.session == "RTH").to_numpy())
                if len(gr_i) < 40:
                    gr_i = np.arange(30, len(g))
                jj = int(gr_i[RNG.integers(20, len(gr_i))])
                gts = g.ts_event.dt.tz_convert(None).to_numpy()
                j1 = np.searchsorted(ts1, gts[jj], "right") - 1
                x = hit(make_band(r["sd"], jj - 1), c1[j1], r["role"], r["relation"])
                if x is not None:
                    u += x; m += 1
            nulls.append(u / max(1, m))
        nulls = np.array(nulls)
        hr = np.mean(hv) if hv else np.nan
        print(f"| {label} | {hr:.0%} (n={len(hv)}) | {nulls.mean():.0%} +/- {nulls.std():.0%} | {hr-nulls.mean():+.0%} |")
        return hr - nulls.mean()

    print("\n===== G4: CONTRACTION refs =====")
    print("| variant | his hit | null hit (12 perms) | gap |")
    C2cache = {}
    for W in (15, 30, 60):
        for q in (0.5, 0.67):
            def mk(sd, jbar, W=W, q=q):
                key = (sd, W, q)
                if key not in C2cache:
                    C2cache[key] = episodes_c2(groups[sd], W, q)
                eps, h, l = C2cache[key]
                return band_c2(eps, h, l, jbar, W) if jbar > W else None
            eval_variant(mk, f"C2 W={W} q={q}", refs)
    RBcache = {}
    for tf in (5, 15):
        def mk1(sd, jbar, tf=tf):
            key = (sd, tf)
            if key not in RBcache:
                rb = resample_tf(groups[sd][["ts_event", "open", "high", "low", "close",
                                             "is_roll_day", "session_date"]], tf)
                RBcache[key] = rb
            rb = RBcache[key]
            g = groups[sd]
            gts = g.ts_event.dt.tz_convert(None).to_numpy()
            if jbar < 0 or jbar >= len(gts):
                return None
            rts = rb.ts_event.dt.tz_convert(None).to_numpy() if rb.ts_event.dt.tz is not None else rb.ts_event.to_numpy()
            jb2 = np.searchsorted(rts, gts[jbar], "right") - 2
            return nr_band(rb, 7, jb2) if jb2 > 8 else None
        eval_variant(mk1, f"C1 NR7 {tf}m", refs)

    print("\n===== MERGE TEST: same variants vs his TIGHT/TRADING-RANGE refs =====")
    print("| variant | his hit | null hit | gap |")
    for W, q in ((30, 0.5), (30, 0.67), (60, 0.67)):
        def mk(sd, jbar, W=W, q=q):
            key = (sd, W, q)
            if key not in C2cache:
                C2cache[key] = episodes_c2(groups[sd], W, q)
            eps, h, l = C2cache[key]
            return band_c2(eps, h, l, jbar, W) if jbar > W else None
        eval_variant(mk, f"C2 W={W} q={q}", refs_tr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
