#!/usr/bin/env python3
"""db2_analysis.py — T-BK03 analysis. Spec DB2_SPEC.md + addendum 1.
RUN: python3 Tests/D6_deepbook/db2_analysis.py > Tests/D6_deepbook/DB2_REPORT.md
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

F = pd.read_parquet("Data/inputs/db2_features.parquet")
O = pd.read_csv("Tests/D6_deepbook/e1_outcomes.csv")
O["cid"] = np.arange(len(O))
E1 = F[F.q == "e1"].merge(O[["cid", "outcome", "level", "his",
                             "his_side"]], on="cid", how="left")
FEATS = ["OFI", "OFI10", "depl_opp", "repl_opp", "cancel_ratio",
         "large_lot", "hidden", "sweep"]
MONTHS = ("2022-02", "2025-10")

print("# DB2 REPORT — LEVEL-APPROACH UNIVERSE + G3 FEATURES (T-BK03)")
print("STATUS: CLOSED | 2026-11-27 | Spec: DB2_SPEC.md + addendum 1 "
      "(touch-required outcomes; base-rate tell caught the flaw "
      "pre-analysis) | extractor: certified T-BK02 lineage")
print()
tot = pd.read_csv("Tests/D6_deepbook/moments_e1.csv")
print(f"E1 universe: {len(tot)} approaches; with book features "
      f"{len(E1)} (windowed MBP-10 covers news windows only - "
      f"coverage {len(E1)/len(tot):.0%}, skewed to news-window "
      f"approaches by construction; stated).")
print(f"Outcome base rates (with-features set): "
      f"{E1.outcome.value_counts().to_dict()}")
print()
sub = E1[E1.outcome.isin(["HOLD", "BREAK"])].copy()
print(f"## HOLDS vs BREAKS ON BOOK STATE AT THE APPROACH "
      f"(n={int((sub.outcome == 'HOLD').sum())} vs "
      f"{int((sub.outcome == 'BREAK').sum())})")
print("NOTE: features were extracted signed by APPROACH direction "
      "(side = direction of travel toward the level), so positive "
      "OFI = flow pressing TOWARD the level.")
print("| feature | hold med | break med | p | BH | months same dir | "
      "verdict |")
print("|---|---|---|---|---|---|---|")
ps = {}
for f in FEATS:
    a = sub[sub.outcome == "HOLD"][f].dropna()
    c = sub[sub.outcome == "BREAK"][f].dropna()
    if len(a) < 20 or len(c) < 20:
        ps[f] = None
        continue
    ps[f] = (mannwhitneyu(a, c).pvalue, a.median(), c.median())
valid = sorted([(v[0], f) for f, v in ps.items() if v])
bh_pass = set()
for rank, (p, f) in enumerate(valid, 1):
    if p <= 0.10 * rank / len(valid):
        bh_pass = set(f2 for p2, f2 in valid[:rank])
findings = []
for f in FEATS:
    if ps.get(f) is None:
        print(f"| {f} | - | - | - | - | - | insufficient |")
        continue
    p, am, cm = ps[f]
    sgn = np.sign(am - cm)
    nsame = 0
    for mo in MONTHS:
        a_ = sub[(sub.outcome == "HOLD") & (sub.month == mo)][f].dropna()
        c_ = sub[(sub.outcome == "BREAK") & (sub.month == mo)][f].dropna()
        if len(a_) >= 10 and len(c_) >= 10 and \
           np.sign(a_.median() - c_.median()) == sgn:
            nsame += 1
    bh = f in bh_pass
    v = ("FINDING" if (bh and nsame == 2) else
         ("suggestive" if p <= 0.05 else "null"))
    if v == "FINDING":
        findings.append((f, am, cm, p))
    print(f"| {f} | {am:.2f} | {cm:.2f} | {p:.4f} | "
          f"{'Y' if bh else 'n'} | {nsame}/2 | {v} |")
print()
print("## HIS BEHAVIOR AT THESE APPROACHES (descriptive)")
ht = E1[E1.his == 1]
if len(ht):
    tab = ht.groupby("outcome").agg(
        n=("his", "size"),
        fade_side=("his_side", lambda s: int((s == -ht.loc[s.index,
            "side"]).sum() if len(s) else 0))).reset_index()
    for _, r in tab.iterrows():
        print(f"- {r.outcome}: {r.n} approaches he traded "
              f"(fading the approach on {r.fade_side})")
print()
e2n = int((F.q == "e2").sum())
print(f"## E2 — G3 FEATURE BANK: {e2n} of 151 G3 entries have "
      "event-book features (saved in db2_features.parquet for the "
      "D-5 cycle; no analysis this round).")
print()
print(f"FINDINGS ({len(findings)}) -> D-25 design inputs (J gates).")
print("Registry: T-BK03.")
