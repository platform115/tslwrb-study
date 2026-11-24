#!/usr/bin/env python3
"""
a3_grouping.py — A3: group his trades (T-IM44). Spec: A3_SPEC.md,
committed before this file existed (pre-registration provable in git).
RUN: python3 Tests/A2_measurement/a3_grouping.py > Tests/A2_measurement/A3_REPORT.md
"""
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import adjusted_rand_score, silhouette_score

RNG = np.random.default_rng(113)
FEATS = ["mv15", "flow1", "stall_5m_extreme", "vrate900", "Rest",
         "sig_best_score", "rng120", "REA_int_dist", "mins_open",
         "kme_mins_since", "consec_10s", "dwell120", "last_bounce_ticks",
         "approach120", "mins_since_mention"]
MISS_FLAG = ["REA_int_dist", "dwell120", "last_bounce_ticks",
             "approach120", "mins_since_mention"]

F = pd.read_parquet("Data/inputs/a2_features.parquet")
H = F[(F.who == "his") & F.data_fresh].copy().reset_index(drop=True)

# ---- hand taxonomy (deterministic, from the frozen spec) ----
def phase(r):
    m = r.kme_mins_since
    if np.isfinite(m) and m <= 5:
        return "news-burst"
    if np.isfinite(m) and m <= 45:
        return "news-window"
    return "no-news"


def struct(r):
    if r.SQZ_interact:
        return "squeeze-break"
    if r.REA_interact:
        return "reaction"
    if r.GAP_interact or r.SHD_interact:
        return "zone"
    return "open-tape"


def sess(r):
    m = r.mins_open
    if not np.isfinite(m) or m < 0:
        return "overnight"
    if m < 90:
        return "open"
    if m <= 240:
        return "midday"
    return "late"


H["ax_news"] = H.apply(phase, axis=1)
H["ax_struct"] = H.apply(struct, axis=1)
H["ax_sess"] = H.apply(sess, axis=1)
H["hand_label"] = H.ax_news + "|" + H.ax_struct + "|" + H.ax_sess

# ---- clustering features ----
X = H[FEATS].copy()
flags = {}
for c in MISS_FLAG:
    flags[f"miss_{c}"] = X[c].isna().astype(float)
for c in FEATS:
    med, q1, q3 = X[c].median(), X[c].quantile(.25), X[c].quantile(.75)
    iqr = (q3 - q1) or 1.0
    X[c] = ((X[c] - med) / iqr).fillna(0.0)
for k, v in flags.items():
    X[k] = v
Xv = X.to_numpy()
Z = linkage(Xv, method="ward")

print("# A3 REPORT — GROUPING HIS TRADES (T-IM44)")
print("STATUS: CLOSED | 2026-11-25 | Spec: A3_SPEC.md (committed before "
      "this script existed)")
print()
print(f"{len(H)} trades (training months). Hand taxonomy assigned first, "
      "deterministically; clustering ran blind to it.")
print()
print("## CHOICE OF k (both yardsticks, all k shown)")
print("| k | mean silhouette | per-cluster stability (bootstrap Jaccard) "
      "| all >= 0.6? |")
print("|---|---|---|---|")
stab_by_k = {}
for k in range(2, 9):
    lab = fcluster(Z, k, criterion="maxclust")
    sil = silhouette_score(Xv, lab)
    # Hennig 2007 bootstrap stability
    J = np.zeros((100, k))
    for b in range(100):
        idx = RNG.choice(len(Xv), size=len(Xv), replace=True)
        lb = fcluster(linkage(Xv[idx], method="ward"), k,
                      criterion="maxclust")
        for c in range(1, k + 1):
            orig = set(np.flatnonzero(lab[idx] == c))
            best = 0.0
            for c2 in range(1, k + 1):
                new = set(np.flatnonzero(lb == c2))
                if orig | new:
                    best = max(best, len(orig & new) / len(orig | new))
            J[b, c - 1] = best
    mj = J.mean(axis=0)
    stab_by_k[k] = (lab, sil, mj)
    print(f"| {k} | {sil:.2f} | " + " ".join(f"{x:.2f}" for x in mj)
          + f" | {'YES' if (mj >= 0.6).all() else 'no'} |")
k_pick = max((k for k, (_, _, mj) in stab_by_k.items()
              if (mj >= 0.6).all()), default=2)
lab, sil, mj = stab_by_k[k_pick]
H["cluster"] = lab
print(f"\nPicked k = {k_pick} (largest k with every cluster >= 0.6, "
      "per spec).")
print()
print("## THE GROUPS (plain descriptions from median features)")
print("| group | n | stability | strongest traits (vs the median trade) |")
print("|---|---|---|---|")
med_all = H[FEATS].median()
iqr_all = (H[FEATS].quantile(.75) - H[FEATS].quantile(.25)).replace(0, 1)
for c in range(1, k_pick + 1):
    g = H[H.cluster == c]
    dev = ((g[FEATS].median() - med_all) / iqr_all).sort_values(
        key=np.abs, ascending=False)
    traits = "; ".join(f"{f} {'high' if v > 0 else 'low'} ({v:+.1f})"
                       for f, v in dev.head(3).items())
    print(f"| {c} | {len(g)} | {mj[c - 1]:.2f} | {traits} |")
print()
print("## GROUP x TAXONOMY CROSS-COUNTS")
for ax in ("ax_news", "ax_struct", "ax_sess"):
    ct = pd.crosstab(H.cluster, H[ax])
    print(f"\n### {ax}")
    print(ct.to_markdown())
print()
print("## AGREEMENT (Adjusted Rand Index: 0 = chance, 1 = identical)")
print("| taxonomy axis | ARI vs clusters |")
print("|---|---|")
for ax in ("ax_news", "ax_struct", "ax_sess", "hand_label"):
    print(f"| {ax} | {adjusted_rand_score(H[ax], H.cluster):.2f} |")
print()
print("## OCCUPIED TAXONOMY CELLS (counts >= 5)")
vc = H.hand_label.value_counts()
for kk, v in vc[vc >= 5].items():
    print(f"- {kk}: {v}")
print(f"(cells with <5 trades: {int((vc < 5).sum())}, holding "
      f"{int(vc[vc < 5].sum())} trades)")
print()
print("## MANDATORY INVESTIGATION LIST (clustered together, taxonomy apart)")
big = []
for c in range(1, k_pick + 1):
    g = H[H.cluster == c]
    mix = g.hand_label.value_counts()
    if len(mix) > 1 and len(g) >= 15:
        big.append((len(g), c, mix))
for n, c, mix in sorted(big, reverse=True)[:4]:
    print(f"- cluster {c} (n={n}) spans {len(mix)} taxonomy cells; "
          f"largest: {mix.index[0]} ({mix.iloc[0]}), "
          f"{mix.index[1]} ({mix.iloc[1]})")
print()
# persist labels
out = F.copy()
out = out.merge(H[["episode_id", "month", "sec", "hand_label", "cluster"]],
                on=["episode_id", "month", "sec"], how="left")
out.to_parquet("Data/inputs/a2_features.parquet", index=False)
print("Labels appended to Data/inputs/a2_features.parquet. "
      "Registry: T-IM44.")
