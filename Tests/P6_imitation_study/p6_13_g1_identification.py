#!/usr/bin/env python3
"""
p6_13_g1_identification.py — S3-G1 CALIBRATION, ITERATION 2: OBJECT
IDENTIFICATION. (T-IM18.) Which hidden gap is he referencing?
===============================================================================
USER DIRECTION (2026-11-20): gaps are everywhere all the time - that was
known. The task is identifying THE ONES HE REFERENCES; TF prior is
1m/3m/5m unless he specifies otherwise.

For each RELATIONAL hidden-gap reference (price interacting with a
pre-existing gap: back_to/broken/testing/hugging/reached/inside/...):
  candidate gaps at t (<=t, roll-excluded, unfilled or partial), then apply
  THE MESSAGE'S OWN descriptors:
    direction stated        -> direction match
    "most recent" stated    -> latest non-filled per (TF, dir)
    "Big/huge/large" stated -> relative size: gap size / median size of
                               same-TF gaps in the window >= RBIG
  then candidates within TOL points of the anchor price (inside = 0).
Outcome per ref: 0 candidates (miss) / exactly 1 (IDENTIFIED) / n>1
(ambiguous, n recorded). Scenarios: TF sets {1,3,5} (prior), {1,2,3,5,15}
(S0 set), each single TF. NULL: same procedure at random RTH times with
random descriptors - if uniqueness is trivial, the null shows it.

RUN: python3 Tests/P6_imitation_study/p6_13_g1_identification.py      (repo root)
"""
import argparse, os, re, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p6_12_g1_hidden_gap import resample_tf, whg_zones, fill_state   # noqa: E402

TFS_ALL = (1, 2, 3, 5, 15)
K_SESS = 5
TOL = 3.0
RBIG = 1.5          # "Big" = >= 1.5x median same-TF gap size in window (sens: 1.25/2.0)
N_NULL = 300
RNG = np.random.default_rng(23)
RELATIONAL = {"back_to", "broken", "testing", "hugging", "reached", "inside",
              "approaching", "failed_held", "at_near", "above", "below"}
BIGRE = re.compile(r"\bbig\b|\bhuge\b|\blarge\b", re.I)


def candidates(t, px, sd0, msg_dir, msg_recent, msg_big, Z, sess_list,
               ts1, h1, l1, tfs, tol=TOL):
    si = sess_list.index(sd0)
    pool = []
    for k in range(K_SESS):
        if si - k < 0:
            break
        for tf in tfs:
            for z in Z[(sess_list[si - k], tf)]:
                if z["comp"] > t:
                    continue
                if msg_dir in ("up", "down") and z["dir"] != msg_dir:
                    continue
                pool.append(z)
    pool = [z for z in pool if fill_state(z, h1, l1, ts1, t) != "FILLED"]
    if msg_big and pool:
        med = {tf: np.median([q["hi"] - q["lo"] for q in pool if q["tf"] == tf])
               for tf in tfs}
        pool = [z for z in pool
                if (z["hi"] - z["lo"]) >= RBIG * med.get(z["tf"], np.inf)]
    if msg_recent and pool:
        best = {}
        for z in pool:
            key = (z["tf"], z["dir"])
            if key not in best or z["comp"] > best[key]["comp"]:
                best[key] = z
        pool = list(best.values())
    near = [z for z in pool
            if (z["lo"] - tol) <= px <= (z["hi"] + tol)]
    # dedupe near-identical bands across TFs (same object seen twice):
    # two candidates whose bands overlap >=50% of the smaller are one object
    merged = []
    for z in sorted(near, key=lambda q: q["hi"] - q["lo"], reverse=True):
        dup = False
        for m in merged:
            ov = min(z["hi"], m["hi"]) - max(z["lo"], m["lo"])
            if ov > 0 and ov >= 0.5 * (z["hi"] - z["lo"]):
                dup = True
                break
        if not dup:
            merged.append(z)
    return merged


def run(repo):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    hg = zr[(zr.kind == "hidden_gap") & (zr.relation.isin(RELATIONAL))].copy()
    print(f"relational hidden-gap refs: {len(hg)} of {len(zr[zr.kind=='hidden_gap'])}")
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    h1, l1, c1 = b.high.to_numpy(), b.low.to_numpy(), b.close.to_numpy()
    sd_arr = b.sd.to_numpy()
    sess_list = list(dict.fromkeys(sd_arr))

    def sd_at(t):
        j = np.searchsorted(ts1, np.datetime64(t), "right") - 1
        return sd_arr[j] if j >= 0 else None

    needed = set()
    for t in pd.to_datetime(hg.ts_utc, utc=True).dt.tz_convert(None):
        s = sd_at(t)
        if s:
            si = sess_list.index(s)
            needed |= {sess_list[si - k] for k in range(K_SESS) if si - k >= 0}
    groups = {s: g.reset_index(drop=True) for s, g in b.groupby("sd") if s in needed}
    Z = {}
    for s, g in groups.items():
        for tf in TFS_ALL:
            rb = resample_tf(g[["ts_event", "open", "high", "low", "close",
                                "is_roll_day", "session_date"]], tf)
            rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            Z[(s, tf)] = whg_zones(rb, tf)
    print(f"zones over {len(needed)} sessions x {len(TFS_ALL)} TFs: "
          f"{sum(len(v) for v in Z.values())}")

    refs = []
    for _, r in hg.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None))
        s = sd_at(t)
        if s is None or s not in groups:
            continue
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        refs.append(dict(t=t, px=c1[j], sd=s, dir=r.direction,
                         recent=(r.recency_cue == "most_recent"),
                         big=bool(BIGRE.search(r.raw)), raw=r.raw))

    # null: random RTH-session times from the same sessions, random descriptors
    rth = b[b.session == "RTH"]
    nulls = []
    sess_pool = [r["sd"] for r in refs]
    for _ in range(N_NULL):
        s = sess_pool[RNG.integers(len(sess_pool))]
        g = groups[s]; gr = g[g.session == "RTH"]
        if len(gr) < 30:
            gr = g
        jj = RNG.integers(20, len(gr))
        t = np.datetime64(gr.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(60, "s")
        j = np.searchsorted(ts1, t - np.timedelta64(60, "s"), "right") - 1
        nulls.append(dict(t=t, px=c1[j], sd=s,
                          dir=["up", "down", "none"][RNG.integers(3)],
                          recent=bool(RNG.integers(2)), big=bool(RNG.integers(2))))

    scen = [("1/3/5 (prior)", (1, 3, 5)), ("1/2/3/5/15 (S0 set)", TFS_ALL)] + \
           [(f"{tf}m only", (tf,)) for tf in TFS_ALL]
    print(f"\n===== IDENTIFICATION (tol {TOL:g} pts, Big = >= {RBIG}x median same-TF gap) =====")
    print("| TF set | refs: miss / IDENTIFIED / ambiguous (med n) | null: miss / unique / ambiguous |")
    print("|---|---|---|")
    results = {}
    for name, tfs in scen:
        cnt = []
        for r in refs:
            cs = candidates(r["t"], r["px"], r["sd"], r["dir"], r["recent"],
                            r["big"], Z, sess_list, ts1, h1, l1, tfs)
            cnt.append(len(cs))
        cnt = np.array(cnt)
        ncnt = []
        for r in nulls:
            cs = candidates(r["t"], r["px"], r["sd"], r["dir"], r["recent"],
                            r["big"], Z, sess_list, ts1, h1, l1, tfs)
            ncnt.append(len(cs))
        ncnt = np.array(ncnt)
        amb = cnt[cnt > 1]
        print(f"| {name} | {(cnt==0).mean():.0%} / {(cnt==1).mean():.0%} / "
              f"{(cnt>1).mean():.0%} (med {np.median(amb) if len(amb) else 0:.0f}) "
              f"| {(ncnt==0).mean():.0%} / {(ncnt==1).mean():.0%} / {(ncnt>1).mean():.0%} |")
        results[name] = cnt
    # per-descriptor breakdown on the prior set
    cnt = results["1/3/5 (prior)"]
    print("\n## 1/3/5 prior set — identification by descriptor availability")
    for lab, mask in (("dir stated", [r["dir"] in ("up", "down") for r in refs]),
                      ("most-recent stated", [r["recent"] for r in refs]),
                      ("Big stated", [r["big"] for r in refs]),
                      ("no descriptors", [r["dir"] not in ("up", "down")
                                          and not r["recent"] and not r["big"] for r in refs])):
        m = np.array(mask)
        if m.sum():
            print(f"  {lab}: n={m.sum()}  identified {( (cnt==1)&m ).sum()/m.sum():.0%}  "
                  f"ambiguous {((cnt>1)&m).sum()/m.sum():.0%}  miss {((cnt==0)&m).sum()/m.sum():.0%}")
    return refs, results


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
