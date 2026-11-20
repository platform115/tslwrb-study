#!/usr/bin/env python3
"""
p6_20_s5b_improvements.py — S5b: WEAK-KIND VARIABLE SWEEPS + IMPLIED KEY-ZONE
LIST. (T-IM27.) User direction: reaction + contraction results not good
enough - test more variables; Key-zone list derivable through implications.

A. REACTION sweep (59 relational ES refs; hit at the single most-recent
   object per side; tol 3; fair null 12 perms):
   - swing TF x N full grid: TF {1,2,3,5,15} x N {1,2,3}
   - percentage zigzag (documented, scale-adaptive): rev {0.05%, 0.08%, 0.12%}
   - best-of-two-families union (swing 5m N=2 OR pct zigzag 0.08%)
B. CONTRACTION sweep (95 refs; role-stated subset n=34 is the decision
   metric): W {10,15,20,30} x q {0.6,0.67,0.75}; band = extremes vs
   close-quantile (5/95); min episode length 5 bars variant.
C. IMPLIED KEY-ZONE LIST: every relational ES Key-zone ref deposits an
   implied anchor at market price. Forward test: refs in session s scored
   against anchors from sessions < s only (no same-session, no self).
   Expiry grid. Null: random RTH times, same sessions.
MULTIPLICITY NOTE: many cells; decisions use the pre-named metric (gap on
the decision subset), all cells reported, winners need a margin, not a tie.

RUN: python3 Tests/P6_imitation_study/p6_20_s5b_improvements.py       (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p6_12_g1_hidden_gap import resample_tf                # noqa: E402
from p6_15_g3_reaction import swings, SIDE_RE              # noqa: E402
from p6_16_g4_contraction import episodes_c2               # noqa: E402
from p6_13_g1_identification import RELATIONAL             # noqa: E402

TOL = 3.0
RNG = np.random.default_rng(97)


def setup(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    return b, zr, ts1, b.close.to_numpy(), b.sd.to_numpy()


def fair_null_times(refs, groups, n_perm=12):
    out = []
    for perm in range(n_perm):
        pts = []
        for r in refs:
            g = groups[r["sd"]]; gr = np.flatnonzero((g.session == "RTH").to_numpy())
            if len(gr) < 40:
                gr = np.arange(30, len(g))
            pts.append(int(gr[RNG.integers(20, len(gr))]))
        out.append(pts)
    return out


def hit_level(level, px, side, relation, tol=TOL):
    if level is None:
        return None
    if relation == "broken":
        lo, hi = (level - 2*tol, level + tol) if side == "low" else (level - tol, level + 2*tol)
        return lo <= px <= hi
    return abs(px - level) <= tol


def reaction_sweep(b, zr, ts1, c1, sd_arr):
    rh = zr[(zr.kind == "reaction_hl") & (zr.relation.isin(RELATIONAL))
            & (zr.instrument == "ES")]
    refs = []
    for _, r in rh.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None))
        j = np.searchsorted(ts1, t, "right") - 1
        sm = SIDE_RE.search(r.raw)
        if j < 1 or not sm:
            continue
        refs.append(dict(t=t, px=c1[j-1], sd=sd_arr[j], side=sm.group(1).lower(),
                         relation=r.relation, j=j))
    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd")
              if s in {r["sd"] for r in refs}}
    nulls_idx = fair_null_times(refs, groups)
    print(f"\n===== A. REACTION sweep ({len(refs)} refs) =====")
    print("| variant | his hit | null | gap |")

    def score(level_fn):
        hits = [hit_level(level_fn(r["sd"], r["t"]), r["px"], r["side"], r["relation"])
                for r in refs]
        hv = [x for x in hits if x is not None]
        ns = []
        for pts in nulls_idx:
            u = m = 0
            for r, jj in zip(refs, pts):
                g = groups[r["sd"]]
                t2 = np.datetime64(g.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
                j2 = np.searchsorted(ts1, t2, "right") - 1
                x = hit_level(level_fn(r["sd"], t2), c1[j2-1], r["side"], r["relation"])
                if x is not None:
                    u += x; m += 1
            ns.append(u / max(1, m))
        return (np.mean(hv) if hv else np.nan), np.array(ns)

    swing_cache = {}
    cols = ["ts_event", "open", "high", "low", "close", "is_roll_day", "session_date"]
    side_hold = {}

    def swing_fn(tf, n):
        def fn(sd, t):
            key = (sd, tf, n)
            if key not in swing_cache:
                rb = resample_tf(groups[sd][cols], tf)
                rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
                swing_cache[key] = swings(rb, tf, n)
            best = None
            side = side_hold["s"]
            for z in swing_cache[key]:
                if z["comp"] <= t and z["side"] == side:
                    if best is None or z["comp"] > best["comp"]:
                        best = z
            return best["px"] if best else None
        return fn

    def scored(fn_maker, label):
        def level_fn(sd, t):
            return fn_maker(sd, t)
        hits = []
        for r in refs:
            side_hold["s"] = r["side"]
            hits.append(hit_level(level_fn(r["sd"], r["t"]), r["px"], r["side"], r["relation"]))
        hv = [x for x in hits if x is not None]
        ns = []
        for pts in nulls_idx:
            u = m = 0
            for r, jj in zip(refs, pts):
                side_hold["s"] = r["side"]
                g = groups[r["sd"]]
                t2 = np.datetime64(g.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
                j2 = np.searchsorted(ts1, t2, "right") - 1
                x = hit_level(level_fn(r["sd"], t2), c1[j2-1], r["side"], r["relation"])
                if x is not None:
                    u += x; m += 1
            ns.append(u / max(1, m))
        ns = np.array(ns)
        hr = np.mean(hv)
        print(f"| {label} | {hr:.0%} | {ns.mean():.0%} +/- {ns.std():.0%} | {hr-ns.mean():+.0%} |")
        return hr - ns.mean()

    for tf in (1, 2, 3, 5, 15):
        for n in (1, 2, 3):
            scored(swing_fn(tf, n), f"swing {tf}m N={n}")

    zz_cache = {}
    def zz_fn(pct):
        def fn(sd, t):
            g = groups[sd]
            key = (sd, pct)
            if key not in zz_cache:
                gts = g.ts_event.dt.tz_convert(None).to_numpy()
                hh, ll = g.high.to_numpy(), g.low.to_numpy()
                piv = []          # (confirm_ts, side, price)
                mode = 0; ext = hh[0]; ext_l = ll[0]
                for k in range(1, len(hh)):
                    rev = hh[k] * pct / 100.0
                    if mode >= 0:
                        if hh[k] > ext:
                            ext = hh[k]
                        if ext - ll[k] >= rev:
                            piv.append((gts[k], "high", ext)); mode = -1; ext_l = ll[k]
                    if mode <= 0:
                        if ll[k] < ext_l:
                            ext_l = ll[k]
                        if hh[k] - ext_l >= rev:
                            piv.append((gts[k], "low", ext_l)); mode = 1; ext = hh[k]
                zz_cache[key] = piv
            best = None
            side = side_hold["s"]
            for (cts, sd_, p) in zz_cache[key]:
                if cts <= t and sd_ == side:
                    best = p
            return best
        return fn

    for pct in (0.05, 0.08, 0.12):
        scored(zz_fn(pct), f"pct-zigzag {pct}%")

    def union_fn(sd, t):
        a = swing_fn(5, 2)(sd, t)
        z = zz_fn(0.08)(sd, t)
        if a is None:
            return z
        if z is None:
            return a
        # nearest to current price can't be known without px; return both-test:
        return a   # union handled below
    # union: hit if EITHER family hits
    hits = []
    for r in refs:
        side_hold["s"] = r["side"]
        h1 = hit_level(swing_fn(5, 2)(r["sd"], r["t"]), r["px"], r["side"], r["relation"])
        h2 = hit_level(zz_fn(0.08)(r["sd"], r["t"]), r["px"], r["side"], r["relation"])
        hits.append((h1 or h2) if (h1 is not None or h2 is not None) else None)
    hv = [x for x in hits if x is not None]
    ns = []
    for pts in nulls_idx:
        u = m = 0
        for r, jj in zip(refs, pts):
            side_hold["s"] = r["side"]
            g = groups[r["sd"]]
            t2 = np.datetime64(g.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
            j2 = np.searchsorted(ts1, t2, "right") - 1
            h1 = hit_level(swing_fn(5, 2)(r["sd"], t2), c1[j2-1], r["side"], r["relation"])
            h2 = hit_level(zz_fn(0.08)(r["sd"], t2), c1[j2-1], r["side"], r["relation"])
            x = (h1 or h2) if (h1 is not None or h2 is not None) else None
            if x is not None:
                u += x; m += 1
        ns.append(u / max(1, m))
    ns = np.array(ns)
    print(f"| UNION swing5mN2 OR zz0.08 | {np.mean(hv):.0%} | {ns.mean():.0%} +/- {ns.std():.0%} | {np.mean(hv)-ns.mean():+.0%} |")


def contraction_sweep(b, zr, ts1, c1, sd_arr):
    from p6_16_g4_contraction import hit as hit_band
    cz = zr[(zr.kind == "contraction") & (zr.relation.isin(RELATIONAL))
            & (zr.instrument == "ES")]
    refs = []
    for _, r in cz.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None))
        j = np.searchsorted(ts1, t, "right") - 1
        if j < 1:
            continue
        refs.append(dict(t=t, px=c1[j-1], sd=sd_arr[j],
                         role=(r.role if isinstance(r.role, str) else None),
                         relation=r.relation))
    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd")
              if s in {r["sd"] for r in refs}}
    nulls_idx = fair_null_times(refs, groups)
    role_mask = np.array([r["role"] in ("S", "R") for r in refs])
    print(f"\n===== B. CONTRACTION sweep ({len(refs)} refs; decision subset: role-stated n={role_mask.sum()}) =====")
    print("| variant | ALL hit/null/gap | ROLE hit/null/gap |")
    cache = {}

    def band_fn(W, q, qband, minlen):
        def fn(sd, jbar):
            key = (sd, W, q)
            if key not in cache:
                cache[key] = episodes_c2(groups[sd], W, q)
            eps, h, l = cache[key]
            g = groups[sd]
            cc = g.close.to_numpy()
            best = None
            for (a, e) in eps:
                if a <= jbar and (e - a + 1) >= minlen:
                    best = (a, min(e, jbar))
            if best is None:
                return None
            a, e = best
            a0 = max(0, a - W + 1)
            if qband:
                seg = cc[a0:e+1]
                return float(np.quantile(seg, 0.05)), float(np.quantile(seg, 0.95))
            return float(l[a0:e+1].min()), float(h[a0:e+1].max())
        return fn

    def scored(fn, label):
        res = {}
        for name, mask in (("ALL", np.ones(len(refs), bool)), ("ROLE", role_mask)):
            sub = [r for r, m in zip(refs, mask) if m]
            hits = []
            for r in sub:
                g = groups[r["sd"]]
                gts = g.ts_event.dt.tz_convert(None).to_numpy()
                jbar = np.searchsorted(gts, r["t"], "right") - 2
                hits.append(hit_band(fn(r["sd"], jbar), r["px"], r["role"], r["relation"]))
            hv = [x for x in hits if x is not None]
            ns = []
            for pts in nulls_idx:
                u = m = 0
                for (r, mm), jj in zip(zip(refs, mask), pts):
                    if not mm:
                        continue
                    g = groups[r["sd"]]
                    j1 = np.searchsorted(ts1, np.datetime64(g.ts_event.iloc[jj].tz_convert(None)), "right") - 1
                    x = hit_band(fn(r["sd"], jj - 1), c1[j1], r["role"], r["relation"])
                    if x is not None:
                        u += x; m += 1
                ns.append(u / max(1, m))
            ns = np.array(ns)
            hr = np.mean(hv) if hv else np.nan
            res[name] = f"{hr:.0%}/{ns.mean():.0%}/{hr-ns.mean():+.0%}"
        print(f"| {label} | {res['ALL']} | {res['ROLE']} |")

    for W in (10, 15, 20, 30):
        for q in (0.6, 0.67, 0.75):
            scored(band_fn(W, q, False, 1), f"W={W} q={q} extremes")
    scored(band_fn(15, 0.67, True, 1), "W=15 q=0.67 close-quantile band")
    scored(band_fn(15, 0.67, False, 5), "W=15 q=0.67 minlen=5")


def implied_keyzones(b, zr, ts1, c1, sd_arr):
    k = zr[(zr.kind == "key_kme_wrb") & (zr.instrument == "ES")
           & (zr.relation.isin(RELATIONAL))].copy()
    k["t"] = pd.to_datetime(k.ts_utc, utc=True).dt.tz_convert(None)
    k = k.sort_values("t").reset_index(drop=True)
    anchors = []     # (ts, sd, price): implied zone location = market at ref
    tlist = []
    for _, r in k.iterrows():
        t = np.datetime64(r.t)
        j = np.searchsorted(ts1, t, "right") - 1
        if j < 1:
            continue
        anchors.append((t, sd_arr[j], float(c1[j-1])))
        tlist.append((t, sd_arr[j], float(c1[j-1])))
    A = pd.DataFrame(anchors, columns=["t", "sd", "px"])
    print(f"\n===== C. IMPLIED KEY-ZONE LIST ({len(A)} implied anchors) =====")
    print("Forward test: ref scored vs anchors from STRICTLY EARLIER SESSIONS.")
    ats = A.t.to_numpy(); asd = A.sd.to_numpy(); apx = A.px.to_numpy()
    sess_of = {s: i for i, s in enumerate(dict.fromkeys(sd_arr))}

    def on_list(t, sd0, px, E_days, tol=3.0):
        cut = np.searchsorted(ats, t)
        if cut == 0:
            return None
        age = (t - ats[:cut]) / np.timedelta64(1, "D")
        ok = (age <= E_days) & (asd[:cut] != sd0)
        sel = apx[:cut][ok]
        if not len(sel):
            return None
        return bool(np.min(np.abs(sel - px)) <= tol)

    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd")
              if s in set(asd)}
    for E in (10, 30, 90):
        hits = []
        for (t, sd0, px) in zip(ats, asd, apx):
            x = on_list(t, sd0, px, E)
            if x is not None:
                hits.append(x)
        ns = []
        for perm in range(15):
            u = m = 0
            for (t, sd0, px) in zip(ats, asd, apx):
                g = groups.get(sd0)
                if g is None or len(g) < 60:
                    continue
                gr = np.flatnonzero((g.session == "RTH").to_numpy())
                if len(gr) < 40:
                    gr = np.arange(30, len(g))
                jj = int(gr[RNG.integers(20, len(gr))])
                t2 = np.datetime64(g.ts_event.iloc[jj].tz_convert(None))
                j2 = np.searchsorted(ts1, t2, "right") - 1
                x = on_list(t2, sd0, float(c1[j2]), E)
                if x is not None:
                    u += x; m += 1
            ns.append(u / max(1, m))
        ns = np.array(ns)
        hr = np.mean(hits)
        print(f"  expiry {E:>3}d: his refs on prior-session implied list {hr:.0%} "
              f"(n={len(hits)}) | null {ns.mean():.0%} +/- {ns.std():.0%} | gap {hr-ns.mean():+.0%}")


if __name__ == "__main__":
    repo = "." if len(sys.argv) < 2 else sys.argv[1]
    env = setup(repo)
    reaction_sweep(*env)
    contraction_sweep(*env)
    implied_keyzones(*env)
