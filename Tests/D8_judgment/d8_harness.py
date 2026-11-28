#!/usr/bin/env python3
"""
d8_harness.py — D-8 STEP 0c: R-1 truncation harness on the
QUARANTINED months (2022-05, 2026-03). Makes the no-lookahead
certification month-specific before any system report exists.
DERIVES FROM (R-9 lineage): Tests/D32_structsel/rh_round.py
(T-RH01/v3, harness-certified 0/240 post-F-36) - edges_prod /
edges_trunc / edges_fullday machinery copied verbatim; only the
month set and the sampled moments differ.
SAMPLE: per month, 30 candidate fills from cand_ctrl parts + 20 of
his entry moments (ground truth) = 100 comparisons total, full
edge-SET equality (stronger than any single derived value), plus a
30-moment poison arm (full-day structures) that must hit >= 1.
PASS: 0 production mismatches AND poison >= 1. Abort to J otherwise.
RUN: python3 Tests/D8_judgment/d8_harness.py            (repo root)
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402

rng = np.random.default_rng(42)
MONTHS = {"2022-05": "2022-06-01", "2026-03": "2026-04-01"}

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
b["tsec"] = b.ts_event.dt.tz_convert(None).astype("int64") // 10**9
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
rth_b = b[b.session.eq("RTH") & ~b.is_roll_day]
pd_hi = rth_b.groupby("sd").high.max().reindex(days_all).to_numpy()
pd_lo = rth_b.groupby("sd").low.min().reindex(days_all).to_numpy()
pd_cl = rth_b.groupby("sd").close.last().reindex(days_all).to_numpy()
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
bb = b[~b.is_roll_day]


def build_wrb(frame):
    out = {}
    for tfm, tfs in (("5min", 300), ("15min", 900)):
        for sd, g in frame.groupby("sd"):
            r = g.set_index("ts_event").resample(tfm).agg(
                {"open": "first", "close": "last"}).dropna()
            body = (r.close - r.open).abs().to_numpy()
            pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
            w_ = body > pm
            comp = (r.index.astype("int64").to_numpy() // 10**9
                    + tfs)[w_]
            for c_, o, cl_ in zip(comp, r.open.to_numpy()[w_],
                                  r.close.to_numpy()[w_]):
                out.setdefault(sd, []).append(
                    (int(c_), float(max(o, cl_))))
                out.setdefault(sd, []).append(
                    (int(c_), float(min(o, cl_))))
    for sd in out:
        out[sd].sort()
    return out


wrb_day = build_wrb(bb)

RES = {}
for mo, nxt in MONTHS.items():
    bm_ = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
            ].reset_index(drop=True)
    RES[mo] = Resolver(bm_, zr)


def edges_prod(mo, sd0, t, di, wrb=wrb_day, pdh=pd_hi, pdl=pd_lo,
               pdc=pd_cl, res=None):
    R = res if res is not None else RES[mo]
    out = []
    for fam in ("SQZ", "GAP", "SHD", "REA"):
        out += [float(e) for e in
                edges_at(R, sd0, np.datetime64(int(t), "s"), fam)]
    if sd0 in wrb:
        out += [p for c_, p in wrb[sd0] if c_ <= t]
    if di is not None and di >= 1 and np.isfinite(pdh[di - 1]):
        out += [float(pdh[di - 1]), float(pdl[di - 1]),
                float(pdc[di - 1])]
    return sorted(set(out))


def sd_of(t):
    kb = int(np.searchsorted(b.tsec.to_numpy(), t, "right")) - 1
    return b.sd.iloc[kb]


def edges_trunc(mo, sd0, t, di):
    nxt = MONTHS[mo]
    bm_t = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
             & (b.tsec + 60 <= t)].reset_index(drop=True)
    R_t = Resolver(bm_t, zr)
    wrb_t = build_wrb(b[(~b.is_roll_day) & (b.sd == sd0)
                        & (b.tsec + 60 <= t)])
    bprior = b[(~b.is_roll_day) & (b.sd < sd0)
               & b.session.eq("RTH")]
    ph = bprior.groupby("sd").high.max().reindex(days_all).to_numpy()
    pl = bprior.groupby("sd").low.min().reindex(days_all).to_numpy()
    pc = bprior.groupby("sd").close.last().reindex(days_all
                                                   ).to_numpy()
    return edges_prod(mo, sd0, t, di, wrb=wrb_t, pdh=ph, pdl=pl,
                      pdc=pc, res=R_t)


def edges_fullday(mo, sd0, t, di):
    t_eod = t + 86400
    nxt = MONTHS[mo]
    bm_f = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
             & (b.tsec + 60 <= t_eod)].reset_index(drop=True)
    R_f = Resolver(bm_f, zr)
    wrb_f = build_wrb(bm_f[~bm_f.is_roll_day])
    wrb_open = {sd: [(0, p) for c_, p in v]
                for sd, v in wrb_f.items()}
    return edges_prod(mo, sd0, t, di, wrb=wrb_open, res=R_f)


# ---- sampled moments ----
gt = pd.read_parquet("Tests/D8_judgment/d8_ground_truth.parquet")
moments = []
for mo in MONTHS:
    C = pd.read_parquet(
        f"Tests/D8_judgment/parts/cand_ctrl_{mo}.parquet"
        ).sample(n=30, random_state=42)
    for r in C.itertuples():
        moments.append((mo, int(r.tf)))
    H = gt[gt.month == mo].sample(n=20, random_state=42)
    for r in H.itertuples():
        moments.append((mo, int(r.entry_msg_s)))

mism, n_ok = [], 0
for mo, t in moments:
    sd0 = sd_of(t); di = day_ix.get(sd0)
    ep = edges_prod(mo, sd0, t, di)
    et = edges_trunc(mo, sd0, t, di)
    if ep == et:
        n_ok += 1
    else:
        dd = set(ep) ^ set(et)
        mism.append((mo, t, sorted(dd)[:6]))

poison_hits = 0
PO = rng.choice(len(moments), size=30, replace=False)
for ix in PO:
    mo, t = moments[ix]
    sd0 = sd_of(t); di = day_ix.get(sd0)
    ep = edges_prod(mo, sd0, t, di)
    ef = edges_fullday(mo, sd0, t, di)
    if ep != ef:
        poison_hits += 1

print("# D8 HARNESS — R-1 TRUNCATION ON THE QUARANTINED MONTHS (0c)")
print(f"- comparisons: {len(moments)} (30 candidate fills + 20 his "
      f"entries per month), FULL edge-set equality")
print(f"- production mismatches: {len(mism)}")
for m in mism[:10]:
    print(f"  - {m}")
print(f"- poison arm: {poison_hits}/30 mismatched (needs >= 1)")
ok = len(mism) == 0 and poison_hits >= 1
print(f"VERDICT: {'PASS' if ok else 'FAIL - ABORT TO J'}")
sys.exit(0 if ok else 1)
