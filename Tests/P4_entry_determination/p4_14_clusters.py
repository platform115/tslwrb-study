#!/usr/bin/env python3
"""
p4_14_clusters.py — P4.14: reverse-engineering pass 2 — are there several entry TYPES?
=======================================================================================
The single-rule assumption has been silent so far. If his entries fall into distinct
groups (say news-burst entries vs quiet zone entries), one averaged rule will always
look mediocre and the right structure is one rule per type.
METHOD (fixed before running): the 179 taken signals, 9 features standardized to
z-scores (flow filled with 0 for its 3 missing, edge distance with the median),
k-means for k=2..5 with seed 0, k chosen by silhouette score (standard cluster-
quality measure); each cluster described by its feature means, month mix, time of
day and share of all taken signals. Descriptive on the search set; any per-type
rule would be judged on the reserved years like everything else.

RUN: python3 Tests/P4_entry_determination/p4_14_clusters.py            (repo root)
     python3 Tests/P4_entry_determination/p4_14_clusters.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

FEATS = ["mins_since_all", "body_r_prev", "path3_r_tmed", "flow_5m", "flow_15m",
         "n_overlap", "en05_tf1_edge_tk", "en08_vwap_z", "tod_ct"]


def prep():
    df = pd.read_csv(os.path.join(HERE, "p4_12_features.csv"))
    df["n_overlap"] = df[["ov3", "ov5", "ov10", "ov15"]].sum(axis=1)
    T = df[df.taken].reset_index(drop=True)
    X = T[FEATS].copy()
    X["flow_5m"] = X.flow_5m.fillna(0); X["flow_15m"] = X.flow_15m.fillna(0)
    X["en05_tf1_edge_tk"] = X.en05_tf1_edge_tk.fillna(X.en05_tf1_edge_tk.median())
    X["mins_since_all"] = X.mins_since_all.clip(upper=300)   # cap: beyond 5h "no recent event"
    Z = (X - X.mean()) / X.std(ddof=0)
    return T, X, Z


def run(repo):
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    T, X, Z = prep()
    print(f"taken signals clustered: {len(T)} | features: {', '.join(FEATS)}")
    best = None
    for k in range(2, 6):
        km = KMeans(n_clusters=k, random_state=0, n_init=10).fit(Z)
        s = silhouette_score(Z, km.labels_)
        print(f"  k={k}: silhouette {s:.3f}")
        if best is None or s > best[1]:
            best = (k, s, km.labels_)
    k, s, lab = best
    print(f"\nchosen k={k} (silhouette {s:.3f}; below ~0.25 means weak/no real clusters)")
    print(f"\n===== the {k} groups (feature means, raw units) =====")
    hdr = ["n", "share"] + FEATS + ["Oct share"]
    rows = []
    for c in range(k):
        m = lab == c
        r = [int(m.sum()), f"{m.mean():.0%}"]
        r += [f"{X[f][m].mean():.1f}" for f in FEATS]
        r += [f"{(T.month[m] == '2025-10').mean():.0%}"]
        rows.append(r)
    w = pd.DataFrame(rows, columns=hdr, index=[f"group {c}" for c in range(k)])
    with pd.option_context("display.width", 250):
        print(w.to_string())
    print("\nREAD: silhouette near or below ~0.25 = his entries are ONE population with")
    print("graded intensity, not distinct types - the single-rule structure is right.")
    print("Clearly separated groups = consider one rule per type (reserved years judge).")


def selftest():
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    rng = np.random.default_rng(0)
    a = rng.normal(0, .3, (50, 2)); b = rng.normal(5, .3, (50, 2))
    Z = np.vstack([a, b])
    km = KMeans(n_clusters=2, random_state=0, n_init=10).fit(Z)
    assert silhouette_score(Z, km.labels_) > 0.8
    print("=== SELF-TEST ===\n  two planted groups found with high silhouette OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
