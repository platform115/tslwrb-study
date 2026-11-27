#!/usr/bin/env python3
"""db3_analysis.py — T-BK04 analysis. Spec D28_SPEC.md.
RUN: python3 Tests/D6_deepbook/db3_analysis.py > Tests/D6_deepbook/D28_REPORT.md
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

F = pd.read_parquet("Data/inputs/db3_features.parquet")
BASE = ["OFI", "OFI10", "depl_opp", "repl_opp", "cancel_ratio",
        "large_lot", "hidden", "sweep"]
MONTHS = ("2022-02", "2025-10")
T = pd.read_parquet("Data/inputs/xd_trades.parquet")
T2 = T[T.month.isin(MONTHS)].reset_index(drop=True)
T2["cid"] = np.arange(len(T2))
MB = pd.read_csv("Tests/D6_deepbook/mb_outcomes.csv")

print("# D28 REPORT — ENTRY-SIDE BOOK AT THE DECISION SECONDS "
      "(T-BK04)")
print("STATUS: CLOSED | 2026-11-27 | Spec: D28_SPEC.md (frozen "
      "first) | horizons 3/10/30s | certified extractor lineage | "
      "F-14/F-18 framing: design input, never a gate")
print()
cov = F.groupby("q").size().to_dict()
print(f"Coverage: {cov} (of 757 fills / 1263 touches; news-window "
      "book coverage).")

def block(sub, label, posname, negname, posmask):
    print(f"## {label}")
    print(f"| horizon | feature | {posname} med | {negname} med | p "
          "| BH | months same dir | verdict |")
    print("|---|---|---|---|---|---|---|---|")
    hits = []
    for h in (3, 10, 30):
        ps = {}
        for f0 in BASE:
            f = f"{f0}_{h}"
            if f not in sub:
                ps[f0] = None
                continue
            a = sub[posmask][f].dropna()
            c = sub[~posmask][f].dropna()
            if len(a) < 20 or len(c) < 20:
                ps[f0] = None
                continue
            ps[f0] = (mannwhitneyu(a, c).pvalue, a.median(),
                      c.median())
        valid = sorted([(v[0], f0) for f0, v in ps.items() if v])
        bh_pass = set()
        for rank, (p, f0) in enumerate(valid, 1):
            if p <= 0.10 * rank / max(len(valid), 1):
                bh_pass = set(f2 for p2, f2 in valid[:rank])
        for f0 in BASE:
            if ps.get(f0) is None:
                continue
            p, am, cm = ps[f0]
            f = f"{f0}_{h}"
            sgn = np.sign(am - cm)
            nsame = 0
            for mo in MONTHS:
                a_ = sub[posmask & (sub.month == mo)][f].dropna()
                c_ = sub[~posmask & (sub.month == mo)][f].dropna()
                if len(a_) >= 10 and len(c_) >= 10 and \
                   np.sign(a_.median() - c_.median()) == sgn:
                    nsame += 1
            bh = f0 in bh_pass
            v = ("FINDING" if (bh and nsame == 2) else
                 ("suggestive" if p <= 0.05 else "null"))
            if v != "null":
                hits.append((h, f0, am, cm, p, v))
            if v != "null" or p <= 0.2:
                print(f"| {h}s | {f0} | {am:.2f} | {cm:.2f} | "
                      f"{p:.4f} | {'Y' if bh else 'n'} | {nsame}/2 "
                      f"| {v} |")
    if not hits:
        print("| - | all others null (rows p>0.2 suppressed for "
              "space) | | | | | | |")
    print()
    return hits

# M-A: earners vs rest at the fill second
A = F[F.q == "ma"].merge(T2[["cid", "pnl"]], on="cid", how="left")
A["earner"] = (A.pnl >= 1.38)
ha = block(A, f"M-A — OUR FILL SECONDS: EARNERS vs REST "
           f"(n={int(A.earner.sum())} vs {int((~A.earner).sum())})",
           "earner", "rest", A.earner)
# M-B: hold vs break at the touch
B = F[F.q == "mb"].merge(MB[["cid", "outcome"]], on="cid",
                         how="left")
B = B[B.outcome.isin(["HOLD", "BREAK"])]
hb = block(B, f"M-B — THE TOUCH AT LEVELS: HOLD vs BREAK "
           f"(n={int((B.outcome == 'HOLD').sum())} vs "
           f"{int((B.outcome == 'BREAK').sum())})",
           "hold", "break", B.outcome == "HOLD")
print(f"Non-null rows: M-A {len(ha)}, M-B {len(hb)}. "
      "Registry: T-BK04.")
