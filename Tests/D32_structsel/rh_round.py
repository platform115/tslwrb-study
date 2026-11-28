#!/usr/bin/env python3
"""
rh_round.py — T-RH01: R-1 truncation harness on FL-RWY. Spec:
RH_SPEC.md (frozen first). Production machinery verbatim from the
certified g3rwy/m8g2 lineage; truncated recomputation rebuilds every
structure input from data <= t per the P0 harness rules.
RUN: python3 Tests/D32_structsel/rh_round.py > Tests/D32_structsel/RH_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402

rng = np.random.default_rng(42)
MONTHS = {"2021-09": "2021-10-01", "2022-02": "2022-03-01",
          "2023-05": "2023-06-01", "2024-05": "2024-06-01",
          "2024-11": "2024-12-01", "2025-10": "2025-11-01"}
DEPTH = ("2022-02", "2025-10")

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

# ---- production machinery (certified path) ----
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

def rwy_from(edges, E, d):
    ah = [(p - E) * d for p in edges if (p - E) * d > 0.5]
    return min(ah) if ah else np.inf

def sd_of(t):
    kb = int(np.searchsorted(b.tsec.to_numpy(), t, "right")) - 1
    return b.sd.iloc[kb]

# ---- truncated recomputation ----
def edges_trunc(mo, sd0, t, di):
    nxt = MONTHS[mo]
    bm_t = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
             & (b.tsec + 60 <= t)].reset_index(drop=True)
    R_t = Resolver(bm_t, zr)
    # WRB truncation: production parity needs the session's FULL bar
    # set (incl. overnight prefix), truncated at t - only sd0 matters
    # for the comparison (v1's month-frame cut was a harness artifact)
    wrb_t = build_wrb(b[(~b.is_roll_day) & (b.sd == sd0)
                        & (b.tsec + 60 <= t)])
    # prior-day aggregates from sessions strictly before t's session
    bprior = b[(~b.is_roll_day) & (b.sd < sd0)
               & b.session.eq("RTH")]
    ph = bprior.groupby("sd").high.max().reindex(days_all).to_numpy()
    pl = bprior.groupby("sd").low.min().reindex(days_all).to_numpy()
    pc = bprior.groupby("sd").close.last().reindex(days_all
                                                  ).to_numpy()
    return edges_prod(mo, sd0, t, di, wrb=wrb_t, pdh=ph, pdl=pl,
                      pdc=pc, res=R_t)

def edges_fullday(mo, sd0, t, di):
    # POISON: structures from the whole day (future contamination)
    t_eod = t + 86400
    nxt = MONTHS[mo]
    bm_f = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
             & (b.tsec + 60 <= t_eod)].reset_index(drop=True)
    R_f = Resolver(bm_f, zr)
    wrb_f = build_wrb(bm_f[~bm_f.is_roll_day])
    wrb_open = {sd: [(0, p) for c_, p in v]
                for sd, v in wrb_f.items()}   # comps ignored
    return edges_prod(mo, sd0, np.int64(t) + 86400 - 86400, di,
                      wrb=wrb_open, res=R_f) if False else \
        edges_prod(mo, sd0, t_eod, di, wrb=wrb_open, res=R_f)

# ---- sample ----
T_ = pd.read_csv("Tests/D32_structsel/lvl_touch_moments_rwy.csv")
T_["ctx"] = np.where(T_.rwy.isna(), "na", "x")
strat = []
for mo in DEPTH:
    sub = T_[T_.month == mo]
    strat.append(sub.sample(n=75, random_state=42))
SAMP_T = pd.concat(strat)
cands = []
for mo in MONTHS:
    cq = pd.read_parquet(
        f"Tests/D5_quiet/parts/cand_quiet_{mo}.parquet").sample(
        n=8, random_state=42)
    cw = pd.read_parquet(
        f"Tests/D11_unmatched/parts/cand_full_{mo}.parquet").sample(
        n=7, random_state=42)
    for r in pd.concat([cq, cw]).itertuples():
        cands.append(dict(month=mo, t=int(r.tf), side=int(r.d),
                          E=float(r.e + 1.25 * r.d)))
C_ = pd.DataFrame(cands)

mism, n_ok = [], 0
rows_poison = 0
poison_hits = 0
for r in SAMP_T.itertuples():
    mo, t, d, L = r.month, int(r.t), int(r.side), float(r.level)
    E = L + 0.75 * d
    sd0 = sd_of(t); di = day_ix.get(sd0)
    vp = rwy_from(edges_prod(mo, sd0, t, di), E, d)
    bank = float(r.rwy) if np.isfinite(r.rwy) else np.inf
    if not (vp == bank or abs(vp - bank) < 1e-9):
        mism.append(("touch-bankdiff", mo, t, bank, vp))
        continue
    vt = rwy_from(edges_trunc(mo, sd0, t, di), E, d)
    if vp == vt or abs(vp - vt) < 1e-9 or (np.isinf(vp)
                                           and np.isinf(vt)):
        n_ok += 1
    else:
        mism.append(("touch", mo, t, vp, vt))
for r in C_.itertuples():
    mo, t, d, E = r.month, int(r.t), int(r.side), float(r.E)
    sd0 = sd_of(t); di = day_ix.get(sd0)
    vp = rwy_from(edges_prod(mo, sd0, t, di), E, d)
    vt = rwy_from(edges_trunc(mo, sd0, t, di), E, d)
    if vp == vt or abs(vp - vt) < 1e-9 or (np.isinf(vp)
                                           and np.isinf(vt)):
        n_ok += 1
    else:
        mism.append(("cand", mo, t, vp, vt))
PO = SAMP_T.sample(n=60, random_state=7)
for r in PO.itertuples():
    mo, t, d, L = r.month, int(r.t), int(r.side), float(r.level)
    E = L + 0.75 * d
    sd0 = sd_of(t); di = day_ix.get(sd0)
    vp = rwy_from(edges_prod(mo, sd0, t, di), E, d)
    vf = rwy_from(edges_fullday(mo, sd0, t, di), E, d)
    rows_poison += 1
    if not (vp == vf or abs(vp - vf) < 1e-9
            or (np.isinf(vp) and np.isinf(vf))):
        poison_hits += 1

print("# RH REPORT — R-1 TRUNCATION HARNESS ON FL-RWY (T-RH01)")
print("STATUS: CLOSED | 2026-11-28 | Spec: RH_SPEC.md (frozen "
      "first) | P0 harness rules (T-EN99/100 lineage)")
print()
print(f"- production comparisons: {n_ok + len(mism)} "
      f"(150 touches incl. banked-value re-derivation + 90 fills, "
      f"six months, quiet + window)")
print(f"- mismatches: {len(mism)}")
for m in mism[:20]:
    print(f"  - {m}")
print(f"- poison arm (end-of-day structures): {poison_hits}/"
      f"{rows_poison} mismatched (sensitivity requires >= 1)")
print()
ok = (len(mism) == 0 and poison_hits >= 1)
print("## VERDICT")
print(f"- zero production mismatches: "
      f"{'PASS' if len(mism) == 0 else 'FAIL'}")
print(f"- poison sensitivity: "
      f"{'PASS' if poison_hits >= 1 else 'INCONCLUSIVE'}")
print(f"OVERALL: {'R-1 PASS - FL-RWY is lookahead-clean' if ok else 'FAIL - FL-RWY systems frozen pending anatomy'}")
print()
print("Registry: T-RH01.")
