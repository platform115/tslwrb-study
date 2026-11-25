#!/usr/bin/env python3
"""
a3b_grouping.py — A3b: corrected-encoding grouping re-run (T-IM45).
Spec: A3B_SPEC.md, committed before this file.
RUN: python3 Tests/A2_measurement/a3b_grouping.py > Tests/A2_measurement/A3B_REPORT.md
"""
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from sklearn.metrics import adjusted_rand_score, silhouette_score

RNG = np.random.default_rng(113)
FEATS = ["mv15", "flow1", "stall_5m_extreme", "vrate900", "Rest",
         "sig_best_score", "rng120", "REA_int_dist", "mins_vs_open",
         "kme_mins_since_c", "consec_10s", "dwell120",
         "last_bounce_ticks", "approach120", "mins_since_mention"]
MISS_FLAG = ["REA_int_dist", "dwell120", "last_bounce_ticks",
             "approach120", "mins_since_mention"]

F = pd.read_parquet("Data/inputs/a2_features.parquet")
H = F[(F.who == "his") & F.data_fresh].copy().reset_index(drop=True)

# change 1: minutes relative to the 8:30 CT bell (negative pre-open)
b = pd.read_parquet("Data/inputs/es_1m_front.parquet",
                    columns=["ts_event", "session", "session_date"])
b = b[b.session == "RTH"].sort_values("ts_event")
first = b.groupby(b.session_date.astype(str)).ts_event.min()
open_s = {d: int(t.tz_convert(None).value // 10**9) for d, t in first.items()}
H["mins_vs_open"] = [(int(r.sec) - open_s.get(r.session_date, np.nan)) / 60.0
                     if r.session_date in open_s else np.nan
                     for _, r in H.iterrows()]
# change 2: capped news clock (distance only)
H["kme_mins_since_c"] = H.kme_mins_since.clip(upper=480)

X = H[FEATS].copy()
flags = {f"miss_{c}": X[c].isna().astype(float) for c in MISS_FLAG}
for c in FEATS:
    med, q1, q3 = X[c].median(), X[c].quantile(.25), X[c].quantile(.75)
    iqr = (q3 - q1) or 1.0
    X[c] = (((X[c] - med) / iqr).fillna(0.0)).clip(-3, 3)  # change 3
for k, v in flags.items():
    X[k] = v
Xv = X.to_numpy()

print("# A3B REPORT — GROUPING, CORRECTED ENCODINGS (T-IM45)")
print("STATUS: CLOSED | 2026-11-25 | Spec: A3B_SPEC.md (committed first)")
print()
print("## CHOICE OF k")
print("| k | mean silhouette | per-cluster stability | all >= 0.6? |")
print("|---|---|---|---|")
stab = {}
for k in range(2, 9):
    lab = fcluster(linkage(Xv, method="ward"), k, criterion="maxclust")
    sil = silhouette_score(Xv, lab)
    J = np.zeros((100, k))
    for bb in range(100):
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
            J[bb, c - 1] = best
    mj = J.mean(axis=0)
    stab[k] = (lab, sil, mj)
    print(f"| {k} | {sil:.2f} | " + " ".join(f"{x:.2f}" for x in mj)
          + f" | {'YES' if (mj >= 0.6).all() else 'no'} |")
k_pick = max((k for k, (_, _, mj) in stab.items() if (mj >= 0.6).all()),
             default=2)
lab, sil, mj = stab[k_pick]
H["cluster_b"] = lab
print(f"\nPicked k = {k_pick}.")
print()
print("## THE GROUPS")
print("| group | n | stability | strongest traits (IQR units vs median trade) |")
print("|---|---|---|---|")
med_all = H[FEATS].median()
iqr_all = (H[FEATS].quantile(.75) - H[FEATS].quantile(.25)).replace(0, 1)
for c in range(1, k_pick + 1):
    g = H[H.cluster_b == c]
    dev = ((g[FEATS].median() - med_all) / iqr_all).sort_values(
        key=np.abs, ascending=False)
    traits = "; ".join(f"{f} {'high' if v > 0 else 'low'} ({v:+.1f})"
                       for f, v in dev.head(4).items())
    print(f"| {c} | {len(g)} | {mj[c - 1]:.2f} | {traits} |")
print()
print("## AGREEMENT WITH HAND TAXONOMY (ARI)")
for ax in ("ax_news", "ax_struct", "ax_sess", "hand_label"):
    # taxonomy columns were saved with A3 merge; recompute if absent
    if ax not in H:
        continue
    print(f"- {ax}: {adjusted_rand_score(H[ax], H.cluster_b):.2f}")
print()
# ---- taxonomy path A: combination table ----
N = F[(F.who == "null") & F.data_fresh]
def combo(df):
    return (df.REA_interact.map({True: "R", False: "-"})
            + df.SQZ_interact.map({True: "Q", False: "-"})
            + df.GAP_interact.map({True: "G", False: "-"})
            + df.SHD_interact.map({True: "S", False: "-"}))
H["combo"] = combo(H)
nc = combo(N).value_counts(normalize=True)
print("## PATH A — EXACT STRUCTURE COMBINATIONS (R=reaction Q=squeeze "
      "G=gap S=shadow, '-'=not interacting)")
print("| combo | his n | his % | null % | ratio |")
print("|---|---|---|---|---|")
hc = H.combo.value_counts()
for kk, v in hc.items():
    np_ = nc.get(kk, 0.0)
    ratio = (v / len(H)) / np_ if np_ > 0 else np.inf
    print(f"| {kk} | {v} | {v / len(H):.0%} | {np_:.0%} | {ratio:.1f}x |")
print()
# ---- path B: reversed priority ----
def struct_rev(r):
    if r.REA_interact:
        return "reaction"
    if r.SQZ_interact:
        return "squeeze-break"
    if r.GAP_interact or r.SHD_interact:
        return "zone"
    return "open-tape"
H["ax_struct_rev"] = H.apply(struct_rev, axis=1)
moved = (H.ax_struct_rev != H.ax_struct).mean() if "ax_struct" in H else np.nan
print("## PATH B — REVERSED PRIORITY (reaction checked first)")
print(H.ax_struct_rev.value_counts().to_string())
print(f"Labels changed by reversing the order: {moved:.0%} of trades - "
      "that share of the dominance is assignment order, not evidence.")
print()
# ---- path C: enrichment-based primary ----
amb = {f: N[f"{f}_interact"].mean() for f in ("REA", "SQZ", "GAP", "SHD")}
order = sorted(amb, key=amb.get)  # rarest at null first
def struct_enr(r):
    for f in order:
        if r[f"{f}_interact"]:
            return f
    return "none"
H["ax_struct_enr"] = H.apply(struct_enr, axis=1)
print("## PATH C — ENRICHMENT PRIMARY (rarest-at-null family wins; "
      f"null rates: {', '.join(f'{f} {amb[f]:.0%}' for f in order)})")
print(H.ax_struct_enr.value_counts().to_string())
print()
out = F.merge(H[["episode_id", "month", "sec", "cluster_b", "combo",
                "ax_struct_rev", "ax_struct_enr", "mins_vs_open"]],
              on=["episode_id", "month", "sec"], how="left")
out.to_parquet("Data/inputs/a2_features.parquet", index=False)
print("Labels appended. Registry: T-IM45.")
