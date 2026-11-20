#!/usr/bin/env python3
"""
p6_18_s4_link.py — S4 STEP 2: REFERENCE LINKING + STEP 3: LIFETIME
MEASUREMENT. (T-IM25.)
===============================================================================
Links every PRICE-ANCHORED reference of his (relational / explicit-price /
event rows; mentions carry no location) to emitted objects
(s4_objects.parquet), then measures object lifetimes from the links.

LINKING per kind (ES refs only; tol 3 pts; <=t via knowable_ts):
  hidden_gap            -> g1_whg, direction-matched when stated
  shadow_interval       -> g2_shadow_d2 AND g2_shadow_d1 (arbitration)
  reaction_hl           -> g3_swing, each param sibling (arbitration)
  contraction           -> g4_c2 W15
  tight/trading_range   -> g4_c2 W30
  level_sr / zone_area / key_kme_wrb / wrb_zone -> ANY generator's band
     (exploratory: which generator's objects his zone/level talk lands on)
A ref may link to several objects (all within tol recorded, with distance
and whether the object was the MOST RECENT of its generator/side then).

LIFETIME MEASURES per linked object:
  age at each link = link_ts - knowable_ts
  span = last link - first link
  stale-reference share = links where a NEWER same-generator/side object
     already existed (the persistence phenomenon the G4 anchors exposed)
Output: Data/inputs/s4_ref_links.parquet + printed lifetime report.

RUN: python3 Tests/P6_imitation_study/p6_18_s4_link.py                (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TOL = 3.0
K_SESS = 5
KIND2GEN = {
    "hidden_gap": [("g1_whg", None)],
    "shadow_interval": [("g2_shadow_d2", None), ("g2_shadow_d1", None)],
    "reaction_hl": [("g3_swing", "N2"), ("g3_swing", "N3"), ("g3_swing", "N1")],
    "contraction": [("g4_c2", "W15")],
    "tight_range": [("g4_c2", "W30")],
    "trading_range": [("g4_c2", "W30")],
    "level_sr": [("*", None)],
    "zone_area": [("*", None)],
    "key_kme_wrb": [("*", None)],
    "wrb_zone": [("*", None)],
}
DIRMAP = {"up": "up", "down": "down", "upper": "upper", "lower": "lower",
          "high": "high", "low": "low"}


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"),
                        columns=["ts_event", "close", "session_date"])
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    c1 = b.close.to_numpy()
    sd_arr = b.sd.to_numpy()
    sess_list = list(dict.fromkeys(sd_arr))
    sess_idx = {s: i for i, s in enumerate(sess_list)}

    O = pd.read_parquet(os.path.join(repo, "Data/inputs/s4_objects.parquet"))
    O["kts"] = pd.to_datetime(O.knowable_ts).to_numpy()
    by_sess = {s: g for s, g in O.groupby("session_date")}

    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = zr[(zr.instrument == "ES")
           & (zr.ref_type.isin(["relational", "explicit_price", "event"]))
           & (zr.kind.isin(KIND2GEN))].copy()
    print(f"price-anchored ES refs to link: {len(R)}", flush=True)

    links = []
    for ridx, r in R.iterrows():
        t = np.datetime64(pd.Timestamp(r.ts_utc).tz_convert(None))
        j = np.searchsorted(ts1, t, "right") - 1
        if j < 0:
            continue
        sd0 = sd_arr[j]
        px = float(r.price_1) if np.isfinite(r.price_1) else float(c1[max(0, j - 1)])
        anchor = "stated" if np.isfinite(r.price_1) else "market"
        si = sess_idx.get(sd0)
        if si is None:
            continue
        frames = [by_sess[sess_list[si - k]] for k in range(K_SESS)
                  if si - k >= 0 and sess_list[si - k] in by_sess]
        if not frames:
            continue
        cand = pd.concat(frames)
        cand = cand[cand.kts.to_numpy() <= t]
        if not len(cand):
            continue
        want = DIRMAP.get(str(r.direction), None)
        for gen, param in KIND2GEN[r.kind]:
            g = cand if gen == "*" else cand[cand.generator == gen]
            if param is not None:
                g = g[g.param == param]
            if want and gen != "*":
                g = g[(g.dir_side == want) | (g.dir_side == "")]
            if not len(g):
                continue
            lo = g.band_lo.to_numpy(); hi = g.band_hi.to_numpy()
            inside = (lo - TOL <= px) & (px <= hi + TOL)
            d = np.where((lo <= px) & (px <= hi), 0.0,
                         np.minimum(np.abs(px - lo), np.abs(px - hi)))
            sel = np.flatnonzero(inside)
            if not len(sel):
                continue
            kts = g.kts.to_numpy()
            # newest knowable same-gen/side object at t (for staleness)
            newest = kts.max()
            for k in sel:
                links.append(dict(
                    ref_idx=ridx, ts=t, kind=r.kind, relation=r.relation,
                    anchor=anchor, generator=g.generator.iloc[k] if gen == "*" else gen,
                    param=(g.param.iloc[k] if gen == "*" else (param or "")),
                    object_id=int(g.object_id.iloc[k]),
                    dist=float(d[k]),
                    age_min=float((t - kts[k]) / np.timedelta64(1, "m")),
                    is_newest=bool(kts[k] == newest)))
    L = pd.DataFrame(links)
    out = os.path.join(repo, "Data/inputs/s4_ref_links.parquet")
    L.to_parquet(out)
    print(f"links: {len(L)} rows -> {out}\n", flush=True)

    print("## Links per kind (refs linked / refs total)")
    for kind in KIND2GEN:
        sub = R[R.kind == kind]
        linked = L[L.kind == kind].ref_idx.nunique()
        print(f"  {kind}: {linked}/{len(sub)}")
    print("\n## AGE AT REFERENCE (minutes, by generator) - the lifetime question")
    for gen, g in L.groupby("generator"):
        q = g.age_min.quantile([.25, .5, .75, .9]).round(0).tolist()
        stale = 1 - g.is_newest.mean()
        print(f"  {gen}: n={len(g)} age q25/50/75/90 = {q} | stale-ref share {stale:.0%}")
    print("\n## OBJECT SPANS (objects with >=2 linked refs)")
    sp = L.groupby("object_id").agg(n=("ts", "size"), first=("ts", "min"),
                                    last=("ts", "max"), gen=("generator", "first"))
    sp = sp[sp.n >= 2]
    sp["span_min"] = (sp["last"] - sp["first"]) / np.timedelta64(1, "m")
    print(f"  objects referenced >=2 times: {len(sp)}")
    for gen, g in sp.groupby("gen"):
        print(f"  {gen}: n={len(g)} span q50/q90 = "
              f"{g.span_min.quantile(.5):.0f}/{g.span_min.quantile(.9):.0f} min, max {g.span_min.max():.0f}")
    print("\n## ZONE/LEVEL TALK LANDS ON (exploratory '*' kinds, by generator)")
    zz = L[L.kind.isin(["level_sr", "zone_area", "key_kme_wrb", "wrb_zone"])]
    print(zz.generator.value_counts().to_string())
    return L


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
