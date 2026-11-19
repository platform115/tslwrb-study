#!/usr/bin/env python3
"""
p6_15_g3_reaction.py — S3 GENERATOR 3: REACTION HIGHS / LOWS. (T-IM22.)
===============================================================================
DEFINITION (documented): a reaction high is a swing high — a bar whose high
exceeds the highs of the N bars on EACH side (reaction low = mirror).
"Reaction high/low" is Wilder's (1978) term; the N-each-side swing/fractal
form is the standard operational version (Williams fractal uses N=2).
No fixed universal N exists, so N ∈ {1, 2, 3} is calibrated.

LOOKAHEAD RULE: a swing at bar i is only KNOWN once the N following bars
have completed. comp = open_ts[i + N] + tf. A reference at time t may only
match swings with comp <= t.

OBJECT: a PRECISE LEVEL (the extreme price; band_lo == band_hi).
SELECTION: most-recent per (TF, side) is FORCED — 70 of his 76 reaction
references say "most recent" explicitly, the strongest selection phrase of
any object so far.
MATCHING: same machinery as G1/G2 — relation-aware (broken = price beyond
the level, up to 2x tol on the break side), side from the text
(high / low), fair permutation null, consistency pairs.
TFs 1/2/3/5/15m; roll-day bars cannot form a swing.

RUN: python3 Tests/P6_imitation_study/p6_15_g3_reaction.py            (repo root)
"""
import argparse, os, re, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p6_12_g1_hidden_gap import resample_tf                # noqa: E402
from p6_13_g1_identification import RELATIONAL             # noqa: E402

TFS = (1, 2, 3, 5, 15)
K_SESS = 5
TOL = 3.0
RNG = np.random.default_rng(53)
SIDE_RE = re.compile(r"reaction\s+(high|low)", re.I)


def swings(bars, tf, n):
    h = bars.high.to_numpy(); l = bars.low.to_numpy()
    roll = bars.is_roll_day.to_numpy(); ts = bars.ts_event.to_numpy()
    out = []
    for i in range(n, len(bars) - n):
        if roll[i]:
            continue
        if h[i] > h[i-n:i].max() and h[i] > h[i+1:i+1+n].max():
            out.append(dict(tf=tf, side="high", px=h[i],
                            comp=ts[i + n] + np.timedelta64(tf, "m")))
        if l[i] < l[i-n:i].min() and l[i] < l[i+1:i+1+n].min():
            out.append(dict(tf=tf, side="low", px=l[i],
                            comp=ts[i + n] + np.timedelta64(tf, "m")))
    return out


def match(t, px, sd0, side, relation, Z, sess_list, tol=TOL):
    """Most-recent per (TF, side) forced; precise-level matching."""
    si = sess_list.index(sd0)
    best = {}
    for k in range(K_SESS):
        if si - k < 0:
            break
        for tf in TFS:
            for z in Z[(sess_list[si - k], tf)]:
                if z["comp"] > t:
                    continue
                if side in ("high", "low") and z["side"] != side:
                    continue
                key = (z["tf"], z["side"])
                if key not in best or z["comp"] > best[key]["comp"]:
                    best[key] = z
    pool = list(best.values())

    def accept(z):
        if relation == "broken":
            if z["side"] == "low":                 # broken low: px below it
                return (z["px"] - 2*tol) <= px <= (z["px"] + tol)
            return (z["px"] - tol) <= px <= (z["px"] + 2*tol)
        return abs(px - z["px"]) <= tol
    near = [z for z in pool if accept(z)]
    # dedupe: same level (within 1 tick) across TFs is one object
    merged = []
    for z in sorted(near, key=lambda q: q["comp"], reverse=True):
        if not any(abs(z["px"] - m["px"]) <= 0.25 for m in merged):
            merged.append(z)
    return merged


def run(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    rh = zr[(zr.kind == "reaction_hl") & (zr.relation.isin(RELATIONAL))
            & (zr.instrument == "ES")].copy()
    print(f"relational ES reaction refs: {len(rh)} of {len(zr[zr.kind=='reaction_hl'])}")
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    c1 = b.close.to_numpy()
    sd_arr = b.sd.to_numpy(); sess_list = list(dict.fromkeys(sd_arr))

    def sd_at(t):
        j = np.searchsorted(ts1, np.datetime64(t), "right") - 1
        return sd_arr[j] if j >= 0 else None

    needed = set()
    for t in pd.to_datetime(rh.ts_utc, utc=True).dt.tz_convert(None):
        s = sd_at(t)
        if s:
            si = sess_list.index(s)
            needed |= {sess_list[si-k] for k in range(K_SESS) if si-k >= 0}
    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd") if s in needed}

    refs = []
    for _, r in rh.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None)); s = sd_at(t)
        if s is None or s not in groups:
            continue
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        sm = SIDE_RE.search(r.raw)
        refs.append(dict(t=t, px=c1[j], sd=s,
                         side=(sm.group(1).lower() if sm else "none"),
                         relation=r.relation, ts=pd.Timestamp(r.ts_utc)))
    print(f"usable refs: {len(refs)} | side stated: {sum(r['side']!='none' for r in refs)}")

    print(f"\n===== G3 IDENTIFICATION (precise levels, tol {TOL:g}, most-recent forced) =====")
    print("| N (bars each side) | swings/sess | miss / IDENTIFIED / ambiguous (med n) | fair null | gap | consistency |")
    print("|---|---|---|---|---|---|")
    for n in (1, 2, 3):
        Z = {}
        for s, g in groups.items():
            for tf in TFS:
                rb = resample_tf(g[["ts_event", "open", "high", "low", "close",
                                    "is_roll_day", "session_date"]], tf)
                rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
                Z[(s, tf)] = swings(rb, tf, n)
        per_sess = sum(len(v) for v in Z.values()) / max(1, len(needed))
        res = [match(r["t"], r["px"], r["sd"], r["side"], r["relation"], Z, sess_list)
               for r in refs]
        cnt = np.array([len(c) for c in res])
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
                u += len(match(t2, c1[j2], r["sd"], r["side"], r["relation"], Z, sess_list)) == 1
            nulls.append(u / len(refs))
        nulls = np.array(nulls)
        pairs = same = 0
        for i in range(len(refs)):
            for k in range(i+1, len(refs)):
                dt = abs((refs[k]["ts"] - refs[i]["ts"]).total_seconds())
                if dt > 1800 or refs[i]["side"] != refs[k]["side"] or refs[i]["side"] == "none":
                    continue
                a, bb = res[i], res[k]
                if len(a) == 1 == len(bb):
                    pairs += 1
                    same += (abs(a[0]["px"] - bb[0]["px"]) <= 0.25)
        amb = cnt[cnt > 1]
        print(f"| N={n} | {per_sess:.0f} | {(cnt==0).mean():.0%} / {(cnt==1).mean():.0%} / "
              f"{(cnt>1).mean():.0%} (med {np.median(amb) if len(amb) else 0:.0f}) "
              f"| {nulls.mean():.0%} +/- {nulls.std():.0%} | {(cnt==1).mean()-nulls.mean():+.0%} "
              f"| {same}/{pairs} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
