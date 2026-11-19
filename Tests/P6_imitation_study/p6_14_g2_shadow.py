#!/usr/bin/env python3
"""
p6_14_g2_shadow.py — S3 GENERATOR 2: LONG UPPER/LOWER SHADOW INTERVALS +
IDENTIFICATION CALIBRATION. (T-IM21.)
===============================================================================
S2-approved candidates (user: "a bit less strict until we know more"):
  Anatomy: upper = high - max(o,c); lower = min(o,c) - low.
  D1(r): same-side shadow >= r x body AND >= opposite shadow; r grid
         {1.0, 1.5, 2.0} (2.0 = the documented rule of thumb; 1.0/1.5 looser).
  D2:    same-side shadow strictly > that side's shadow of EACH of the
         prior 3 bars (WRB-analogy, UNSOURCED - flagged at S2, approved to test).
  Noise floor (both): shadow >= 2 ticks (0.5 pt) [PROJECT CONVENTION - a
  1-tick wick is tape noise at any TF].
Stored object: the bar's FULL RANGE [low, high] (his "range of the
interval"), shadow sub-range kept. TFs: 1/2/3/5/15m. Roll days excluded.
<=t: bar must be completed.

CALIBRATION = the G1 identification machinery: his relational ES
shadow-interval refs; descriptors = side (upper/lower from text),
most-recent cue, Big; role-aware edges (S=low, R=high of the range);
relation-aware (broken = beyond edge). FAIR permutation null (descriptor
tuples at random same-session RTH times). Consistency pairs.

RUN: python3 Tests/P6_imitation_study/p6_14_g2_shadow.py              (repo root)
"""
import argparse, os, re, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p6_12_g1_hidden_gap import resample_tf, fill_state   # noqa: E402  (fill unused; resample reused)
from p6_13_g1_identification import RELATIONAL, BIGRE      # noqa: E402

TFS = (1, 2, 3, 5, 15)
K_SESS = 5
TOL = 3.0
MIN_SHADOW = 0.5
RNG = np.random.default_rng(41)
SIDE_RE = re.compile(r"long\s+(upper|lower)\s+shadow", re.I)


def shadow_intervals(bars, tf, mode, r=2.0):
    o = bars.open.to_numpy(); c = bars.close.to_numpy()
    h = bars.high.to_numpy(); l = bars.low.to_numpy()
    roll = bars.is_roll_day.to_numpy(); ts = bars.ts_event.to_numpy()
    up = h - np.maximum(o, c); dn = np.minimum(o, c) - l
    body = np.abs(c - o)
    out = []
    for i in range(3, len(bars)):
        if roll[i]:
            continue
        for side, sh, opp, prior in (("upper", up[i], dn[i], up[i-3:i]),
                                     ("lower", dn[i], up[i], dn[i-3:i])):
            if sh < MIN_SHADOW:
                continue
            if mode == "D1":
                q = sh >= r * max(body[i], 0.25) and sh >= opp
            else:                       # D2: > prior 3 same-side shadows
                q = sh > prior.max()
            if q:
                out.append(dict(tf=tf, dir=side, lo=l[i], hi=h[i],
                                sh_lo=(max(o[i], c[i]) if side == "upper" else l[i]),
                                sh_hi=(h[i] if side == "upper" else min(o[i], c[i])),
                                comp=ts[i] + np.timedelta64(tf, "m")))
    return out


def match(t, px, sd0, side, recent, big, role, relation, Z, sess_list, tol=TOL):
    si = sess_list.index(sd0)
    pool = []
    for k in range(K_SESS):
        if si - k < 0:
            break
        for tf in TFS:
            for z in Z[(sess_list[si - k], tf)]:
                if z["comp"] > t:
                    continue
                if side in ("upper", "lower") and z["dir"] != side:
                    continue
                pool.append(z)
    if big and pool:
        med = {tf: np.median([q["hi"] - q["lo"] for q in pool if q["tf"] == tf]) for tf in TFS}
        pool = [z for z in pool if (z["hi"] - z["lo"]) >= 1.5 * med.get(z["tf"], np.inf)]
    if recent and pool:
        best = {}
        for z in pool:
            key = (z["tf"], z["dir"])
            if key not in best or z["comp"] > best[key]["comp"]:
                best[key] = z
        pool = list(best.values())

    def accept(z):
        if role == "S":
            e = z["lo"]
            return (e - 2*tol) <= px <= (e + tol) if relation == "broken" else abs(px - e) <= tol
        if role == "R":
            e = z["hi"]
            return (e - tol) <= px <= (e + 2*tol) if relation == "broken" else abs(px - e) <= tol
        lo, hi = z["lo"], z["hi"]
        ex = 2*tol if relation == "broken" else tol
        return (lo - ex) <= px <= (hi + ex)
    near = [z for z in pool if accept(z)]
    merged = []
    for z in sorted(near, key=lambda q: q["hi"] - q["lo"], reverse=True):
        if not any(min(z["hi"], m["hi"]) - max(z["lo"], m["lo"]) >= 0.5*(z["hi"]-z["lo"])
                   for m in merged):
            merged.append(z)
    return merged


def run(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    sh = zr[(zr.kind == "shadow_interval") & (zr.relation.isin(RELATIONAL))
            & (zr.instrument == "ES")].copy()
    print(f"relational ES shadow refs: {len(sh)} of {len(zr[zr.kind=='shadow_interval'])}")
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    c1 = b.close.to_numpy()
    sd_arr = b.sd.to_numpy(); sess_list = list(dict.fromkeys(sd_arr))

    def sd_at(t):
        j = np.searchsorted(ts1, np.datetime64(t), "right") - 1
        return sd_arr[j] if j >= 0 else None

    needed = set()
    for t in pd.to_datetime(sh.ts_utc, utc=True).dt.tz_convert(None):
        s = sd_at(t)
        if s:
            si = sess_list.index(s)
            needed |= {sess_list[si-k] for k in range(K_SESS) if si-k >= 0}
    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd") if s in needed}

    refs = []
    for _, r in sh.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None)); s = sd_at(t)
        if s is None or s not in groups:
            continue
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        sm = SIDE_RE.search(r.raw)
        refs.append(dict(t=t, px=c1[j], sd=s,
                         side=(sm.group(1).lower() if sm else "none"),
                         recent=(r.recency_cue == "most_recent"),
                         big=bool(BIGRE.search(r.raw)),
                         role=(r.role if isinstance(r.role, str) else None),
                         relation=r.relation, ts=pd.Timestamp(r.ts_utc)))
    print(f"usable refs: {len(refs)} | side stated: "
          f"{sum(r['side']!='none' for r in refs)} | most-recent: {sum(r['recent'] for r in refs)}")

    variants = [("D1 r=1.0", ("D1", 1.0)), ("D1 r=1.5", ("D1", 1.5)),
                ("D1 r=2.0", ("D1", 2.0)), ("D2 prior-3", ("D2", 0))]
    print(f"\n===== G2 IDENTIFICATION (tol {TOL:g}, TFs 1/2/3/5/15, lookback {K_SESS} sessions) =====")
    print("| variant | intervals/sess | miss / IDENTIFIED / ambiguous (med n) | fair null unique (20 perms) | gap |")
    print("|---|---|---|---|---|")
    for name, (mode, rr) in variants:
        Z = {}
        for s, g in groups.items():
            for tf in TFS:
                rb = resample_tf(g[["ts_event", "open", "high", "low", "close",
                                    "is_roll_day", "session_date"]], tf)
                rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
                Z[(s, tf)] = shadow_intervals(rb, tf, mode, rr)
        per_sess = sum(len(v) for v in Z.values()) / max(1, len(needed))
        cnt = np.array([len(match(r["t"], r["px"], r["sd"], r["side"], r["recent"],
                                  r["big"], r["role"], r["relation"], Z, sess_list))
                        for r in refs])
        nulls = []
        for perm in range(20):
            u = 0
            for r in refs:
                g = groups[r["sd"]]; gr = g[g.session == "RTH"]
                if len(gr) < 30:
                    gr = g
                jj = RNG.integers(20, len(gr))
                t2 = np.datetime64(gr.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
                j2 = np.searchsorted(ts1, t2 - np.timedelta64(60, "s"), "right") - 1
                cs = match(t2, c1[j2], r["sd"], r["side"], r["recent"], r["big"],
                           r["role"], r["relation"], Z, sess_list)
                u += (len(cs) == 1)
            nulls.append(u / len(refs))
        nulls = np.array(nulls)
        amb = cnt[cnt > 1]
        print(f"| {name} | {per_sess:.0f} | {(cnt==0).mean():.0%} / {(cnt==1).mean():.0%} / "
              f"{(cnt>1).mean():.0%} (med {np.median(amb) if len(amb) else 0:.0f}) "
              f"| {nulls.mean():.0%} +/- {nulls.std():.0%} | {(cnt==1).mean()-nulls.mean():+.0%} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
