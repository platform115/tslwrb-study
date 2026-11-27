#!/usr/bin/env python3
"""db_analysis.py — T-BK02 analysis (container side). Spec DB_SPEC.md.
RUN: python3 Tests/D6_deepbook/db_analysis.py > Tests/D6_deepbook/DB_REPORT.md
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(113)
F = pd.read_parquet("Data/inputs/db_features.parquet")
FEATS = ["OFI", "OFI10", "depl_opp", "repl_opp", "cancel_ratio",
         "large_lot", "hidden", "sweep"]
MONTHS = ("2022-02", "2025-10")

print("# DB REPORT — EVENT-LEVEL BOOK ROUND (T-BK02)")
print("STATUS: CLOSED | 2026-11-27 | Spec: DB_SPEC.md (committed "
      "first) | extractor CERTIFIED vs committed per-second files "
      "(36/36 exact vol+mid) | features: standardized microstructure "
      "(CKS OFI etc.), 30s trailing windows")
print()
cov = F.groupby("q").size().to_dict()
print(f"Coverage: {cov} of 1007 Q1 / 53 Q2 moments "
      f"(windows with <10 events dropped by rule).")
print()

def paired_block(sub, label, posname, negname):
    print(f"## {label}")
    groups = [g for _, g in sub.groupby("cid")
              if g.role.sum() == 1 and len(g) >= 2]
    print(f"Paired groups: {len(groups)}.")
    print(f"| feature | {posname} med | {negname} med | direction | "
          f"perm p | BH | months same dir | verdict |")
    print("|---|---|---|---|---|---|---|---|")
    NPERM = 10000
    ps = {}
    for f in FEATS:
        obs = 0.0
        nulls = np.zeros(NPERM)
        ng = 0
        for g in groups:
            v = g[f].to_numpy(float)
            if np.isnan(v).all() or len(v) < 2:
                continue
            r_ = pd.Series(v).rank(pct=True).to_numpy()
            ci = np.flatnonzero(g.role.to_numpy() == 1)
            if not len(ci) or np.isnan(v[ci[0]]):
                continue
            obs += float(r_[ci[0]])
            nulls += r_[RNG.integers(0, len(v), NPERM)]
            ng += 1
        if ng < 10:
            ps[f] = None
            continue
        obs /= ng
        nulls /= ng
        p = float(min((nulls >= obs).mean(),
                      (nulls <= obs).mean()) * 2)
        ps[f] = (min(p, 1.0), obs)
    valid = sorted([(v[0], f) for f, v in ps.items() if v])
    bh_pass = set()
    for rank, (p, f) in enumerate(valid, 1):
        if p <= 0.10 * rank / len(valid):
            bh_pass = set(f2 for p2, f2 in valid[:rank])
    for f in FEATS:
        if ps.get(f) is None:
            print(f"| {f} | - | - | - | - | - | - | insufficient |")
            continue
        p, obs = ps[f]
        am = sub[sub.role == 1][f].median()
        cm = sub[sub.role == 0][f].median()
        sgn = np.sign(am - cm)
        nsame = 0
        for mo in MONTHS:
            a_ = sub[(sub.role == 1) & (sub.month == mo)][f].dropna()
            b_ = sub[(sub.role == 0) & (sub.month == mo)][f].dropna()
            if len(a_) >= 5 and len(b_) >= 5 and \
               np.sign(a_.median() - b_.median()) == sgn:
                nsame += 1
        bh = f in bh_pass
        v = ("FINDING" if (bh and nsame == 2) else
             ("suggestive" if p <= 0.05 else "null"))
        dr = f"{posname} HIGHER" if obs > 0.5 else f"{posname} LOWER"
        print(f"| {f} | {am:.2f} | {cm:.2f} | {dr} | {p:.4f} | "
              f"{'Y' if bh else 'n'} | {nsame}/2 | {v} |")
    print()

paired_block(F[F.q == "q1"],
             "Q1 — HIS EXIT MOMENTS vs MATCHED HOLD MOMENTS "
             "(duration AND profit matched)", "exit", "hold")
paired_block(F[F.q == "q2"],
             "Q2 — HIS TAKEN CROSSES vs PASSED SIBLINGS",
             "taken", "passed")
print("Registry: T-BK02.")
