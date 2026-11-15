#!/usr/bin/env python3
"""
p4_13_tree.py — P4.13: reverse-engineering pass 1 — let the data pick the rules.
=================================================================================
USER (2026-11-15): instead of proposing ideas and testing them, look at the taken
signals and let the entries themselves say what separates them.
Two standard tools (search set = discovery months, by design):
  1. A small DECISION TREE (CART - Breiman et al. 1984): depth-limited so the
     output is readable rules; it picks the split variables AND thresholds.
     Settings fixed before running: max_depth 4, min 40 signals per leaf,
     class-weight balanced, seed 0; missing values filled with the column median
     plus a "was missing" flag (flow is unknowable for 27% of signals).
  2. PERMUTATION IMPORTANCE on a gradient-boosted model that handles missing
     values natively (the feature-ranking approach in Lopez de Prado 2018):
     which columns actually carry the taken-vs-skipped separation, including
     ones our hand-built rules never used.

RUN: python3 Tests/P4_entry_determination/p4_13_tree.py            (repo root)
     python3 Tests/P4_entry_determination/p4_13_tree.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FEATURES = [
    "mins_since_all", "ov3", "ov5", "ov10", "ov15", "body_tk",
    "body_r_prev", "body_r_twrb", "body_r_tbar",
    "path3_r_prev", "path5_r_prev", "path10_r_prev",
    "path3_r_tmed", "path5_r_tmed", "path10_r_tmed",
    "flow_5m", "flow_15m", "en08_vwap_z", "en08_net_5m_tk",
    "en05_tf1_edge_tk", "tf1_has_react", "c6_template", "tod_ct",
]


def load():
    df = pd.read_csv(os.path.join(HERE, "p4_12_features.csv"))
    X = df[FEATURES].copy()
    for c in FEATURES:
        X[c] = pd.to_numeric(X[c], errors="coerce")
    return df, X, df.taken.to_numpy(bool)


def run(repo):
    from sklearn.tree import DecisionTreeClassifier, export_text
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.inspection import permutation_importance
    df, X, y = load()
    print(f"signals={len(df)} taken={int(y.sum())} features={len(FEATURES)}")

    # ---- 1. readable tree (median fill + missing flags) ----
    Xt = X.copy()
    for c in X.columns:
        if X[c].isna().any():
            Xt[f"{c}_missing"] = X[c].isna()
            Xt[c] = X[c].fillna(X[c].median())
    tree = DecisionTreeClassifier(max_depth=4, min_samples_leaf=40,
                                  class_weight="balanced", random_state=0)
    tree.fit(Xt, y)
    print("\n===== decision tree (data-chosen splits; leaf lines appended with raw counts) =====")
    print(export_text(tree, feature_names=list(Xt.columns), max_depth=4, decimals=2))
    leaf = tree.apply(Xt)
    rows = []
    for lf in np.unique(leaf):
        m = leaf == lf
        rows.append((lf, int(m.sum()), int(y[m].sum()), y[m].mean()))
    rows.sort(key=lambda r: -r[3])
    print("leaves by take rate (leaf id, signals, taken, take rate):")
    for lf, n, t, p in rows:
        print(f"  leaf {lf:3d}: {n:5d} signals, {t:3d} taken, {p:6.1%}")

    # ---- 2. permutation importance (native missing handling) ----
    hgb = HistGradientBoostingClassifier(random_state=0, max_depth=4,
                                         class_weight="balanced")
    hgb.fit(X, y)
    pi = permutation_importance(hgb, X, y, n_repeats=10, random_state=0,
                                scoring="average_precision")
    order = np.argsort(-pi.importances_mean)
    print("\n===== permutation importance (what the separation actually uses) =====")
    for i in order[:14]:
        print(f"  {FEATURES[i]:18s} {pi.importances_mean[i]:+.4f} +/- {pi.importances_std[i]:.4f}")
    print("\nREAD: in-sample by design (search set). Anything new the tree/importances")
    print("surface gets distilled into a plain rule and judged on the reserved years.")


def selftest():
    from sklearn.tree import DecisionTreeClassifier
    rng = np.random.default_rng(0)
    X = pd.DataFrame(dict(a=rng.normal(size=400), b=rng.normal(size=400)))
    y = (X.a > 0.5).to_numpy()
    t = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X, y)
    assert t.score(X, y) > 0.95 and t.tree_.feature[0] == 0   # splits on 'a'
    print("=== SELF-TEST ===\n  tree finds the true split variable OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
