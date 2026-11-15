#!/usr/bin/env python3
"""
p4_15_ceiling_shap.py — P4.15: (1) the ceiling test, (2) per-trade explanations.
=================================================================================
1. CEILING: how much taken-vs-skipped signal do our 23 features contain AT ALL?
   A gradient-boosted model, cross-validated BY DAY (whole days held out, so the
   model never peeks at the day it predicts - the honest in-sample ceiling for
   this feature set). Its best F1 over all probability cutoffs is directly
   comparable to the rule's F1 (v5 = 0.289 in-sample):
     model ceiling ~ rule F1  -> the features are exhausted; stop engineering,
                                 missing signal is something unmeasured
     model ceiling >> rule F1 -> the hand-rule family is leaving structure behind
2. SHAP (Lundberg & Lee 2017): decompose each individual taken signal into which
   features pushed it toward "take" - trade-by-trade reasons, plus a global view
   that catches nonlinear shapes (like the 15-min flow ceiling) systematically.
   Model fitted on all data for the explanations (in-sample by design, search set).

RUN: python3 Tests/P4_entry_determination/p4_15_ceiling_shap.py            (repo root)
     python3 Tests/P4_entry_determination/p4_15_ceiling_shap.py --selftest
OUT: p4_15_shap_taken.csv (per taken signal: top pushing features)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_13_tree import FEATURES, load   # noqa: E402


def best_f1_curve(y, p):
    """Best F1 over all probability cutoffs + the precision/recall there."""
    order = np.argsort(-p)
    ys = y[order]
    tp = np.cumsum(ys); fp = np.cumsum(~ys)
    prec = tp / (tp + fp); rec = tp / ys.sum()
    f1 = np.where(prec + rec > 0, 2 * prec * rec / (prec + rec), 0)
    i = int(np.argmax(f1))
    return float(f1[i]), float(prec[i]), float(rec[i]), int(i + 1)


def run(repo):
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.model_selection import GroupKFold
    import shap
    df, X, y = load()
    days = pd.to_datetime(df.comp_ns).dt.date.astype(str).to_numpy()
    print(f"signals={len(df)} taken={int(y.sum())} days={len(set(days))} features={len(FEATURES)}")

    # ---- 1. ceiling: day-grouped cross-validation ----
    oof = np.full(len(df), np.nan)
    gkf = GroupKFold(n_splits=5)
    for tr, te in gkf.split(X, y, groups=days):
        m = HistGradientBoostingClassifier(random_state=0, max_depth=4,
                                           class_weight="balanced")
        m.fit(X.iloc[tr], y[tr])
        oof[te] = m.predict_proba(X.iloc[te])[:, 1]
    f1b, pb, rb, nflag = best_f1_curve(y, oof)
    base = y.mean()
    print("\n===== 1. CEILING (day-held-out predictions - the model never sees the day it scores) =====")
    print(f"best F1 over all cutoffs: {f1b:.3f}  (precision {pb:.1%} = {pb/base:.1f}x, "
          f"capture {rb:.1%}, flags {nflag})")
    print(f"rule v5, in-sample:       0.289  (precision 22.6% = 2.4x, capture 40.2%)")
    print("NOTE: the rule number is in-sample (optimistic); the ceiling is day-held-out")
    print("(honest). A rule at or near an honest ceiling is a GOOD sign, not a tie.")

    # ---- 2. SHAP on the full-fit model ----
    mfull = HistGradientBoostingClassifier(random_state=0, max_depth=4,
                                           class_weight="balanced").fit(X, y)
    ex = shap.TreeExplainer(mfull)
    sv = ex.shap_values(X)
    if isinstance(sv, list):
        sv = sv[1]
    imp = np.abs(sv).mean(axis=0)
    order = np.argsort(-imp)
    print("\n===== 2. SHAP global view (mean absolute push per feature) =====")
    for i in order[:12]:
        hi = X.iloc[:, i] >= np.nanmedian(X.iloc[:, i])
        dirn = "+" if np.nanmean(sv[hi, i]) > np.nanmean(sv[~hi, i]) else "-"
        print(f"  {FEATURES[i]:18s} {imp[i]:.3f}  (high value pushes {'TOWARD' if dirn=='+' else 'AWAY from'} taking)")
    # per-taken-signal top reasons
    tk = np.flatnonzero(y)
    rows = []
    for j in tk:
        top = np.argsort(-sv[j])[:3]
        rows.append(dict(comp_ns=df.comp_ns.iloc[j], month=df.month.iloc[j],
                         r1=FEATURES[top[0]], r2=FEATURES[top[1]], r3=FEATURES[top[2]]))
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "p4_15_shap_taken.csv"), index=False)
    print("\n===== per-trade: the #1 'reason' feature across his 179 taken signals =====")
    for name, n in out.r1.value_counts().head(8).items():
        print(f"  {name:18s} leads for {n:3d} trades ({n/len(out):.0%})")
    print("\nREAD: ceiling honest (day-held-out); SHAP in-sample on the search set.")


def selftest():
    y = np.array([True, False, True, False])
    p = np.array([0.9, 0.8, 0.7, 0.1])
    f1b, pb, rb, n = best_f1_curve(y, p)
    assert abs(f1b - 0.8) < 1e-9 and n == 3, (f1b, n)   # flag top3: P=2/3, R=1 -> F1 0.8
    print("=== SELF-TEST ===\n  best-F1 curve OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
