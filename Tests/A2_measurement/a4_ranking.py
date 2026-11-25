#!/usr/bin/env python3
"""
a4_ranking.py — A4: candidate ranking (T-IM46). Spec: A4_SPEC.md
(committed before this file).
RUN: python3 Tests/A2_measurement/a4_ranking.py > Tests/A2_measurement/A4_REPORT.md
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

RNG = np.random.default_rng(113)
REPS = ["mv15", "flow1", "stall_5m_extreme", "vrate900", "Rest",
        "sig_best_score", "rng120", "REA_int_dist", "mins_vs_open",
        "kme_mins_since", "consec_10s", "dwell120", "last_bounce_ticks",
        "approach120", "mins_since_mention"]

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[F.data_fresh].copy()
# group labels: trades have them via the approved definition; rebuild
# deterministically (same rules as A3_GROUPS_OF_RECORD) and give each
# null its trade's group.
m = F.kme_mins_since
F["np_"] = np.where(np.isfinite(m) & (m <= 5), "burst",
                    np.where(np.isfinite(m) & (m <= 45), "window", "none"))
F["ctx"] = F.ax_struct_enr.map({"SQZ": "squeeze", "REA": "reaction"})
# nulls lack ax_struct_enr (computed on trades only) -> derive directly
amb_order = ["SQZ", "REA", "GAP", "SHD"]  # rarest-at-null first (T-IM45)
def ctx_row(r):
    for f in amb_order:
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
def grp(r):
    if r.np_ == "burst":
        return "G1 news-burst"
    if r.ctx == "squeeze":
        return "G2 squeeze+news" if r.np_ == "window" else "G3 squeeze quiet"
    if r.ctx == "reaction":
        return "G4 reaction+news" if r.np_ == "window" else "G5 reaction quiet"
    return "G6 rare contexts"
# AMENDMENT (disclosed): episode_id proved NON-UNIQUE within a month
# (restarts per source file), so trade->null inheritance is unreliable.
# Each null is instead grouped by ITS OWN context with the same rules -
# a stricter, context-matched comparison. mins_vs_open is recomputed for
# ALL rows (it previously existed only on trade rows = leakage).
b_ = pd.read_parquet("Data/inputs/es_1m_front.parquet",
                     columns=["ts_event", "session", "session_date"])
b_ = b_[b_.session == "RTH"].sort_values("ts_event")
_open = {d: int(t.tz_convert(None).value // 10**9) for d, t in
         b_.groupby(b_.session_date.astype(str)).ts_event.min().items()}
F["mins_vs_open"] = [(int(s) - _open[d]) / 60.0 if d in _open else np.nan
                     for s, d in zip(F.sec, F.session_date)]
F["grp"] = F.apply(grp, axis=1)
H = F[F.who == "his"].copy()
N = F[F.who == "null"].copy()
GROUPS = sorted(H.grp.unique())

print("# A4 REPORT — CANDIDATE RANKING (T-IM46)")
print("STATUS: CLOSED | 2026-11-25 | Spec: A4_SPEC.md (committed first)")
print()


def delta(a, b):
    a, b = a.dropna(), b.dropna()
    if len(a) < 8 or len(b) < 30:
        return np.nan
    return 2.0 * mannwhitneyu(a, b).statistic / (len(a) * len(b)) - 1.0


# ---- (a) separability + (b) stability ----
print("## (a)+(b) PER-GROUP SEPARABILITY AND MONTH STABILITY")
print("| group | n (22-02/25-10) | features with diff >= 0.3 | top three "
      "(value) | stable-sign share |")
print("|---|---|---|---|---|")
sep_summary = {}
for g in GROUPS:
    hg, ng = H[H.grp == g], N[N.grp == g]
    ds = {c: delta(hg[c], ng[c]) for c in REPS}
    ds = {c: v for c, v in ds.items() if np.isfinite(v)}
    big = {c: v for c, v in ds.items() if abs(v) >= 0.3}
    top = sorted(ds.items(), key=lambda kv: -abs(kv[1]))[:3]
    stab = []
    for c in ds:
        ss = []
        for mo in ("2022-02", "2025-10"):
            d2 = delta(hg[hg.month == mo][c], ng[ng.month == mo][c])
            if np.isfinite(d2) and abs(d2) >= 0.1:
                ss.append(np.sign(d2))
        if len(ss) == 2:
            stab.append(ss[0] == ss[1])
    n1, n2 = (hg.month == "2022-02").sum(), (hg.month == "2025-10").sum()
    sh = f"{np.mean(stab):.0%} of {len(stab)}" if stab else "n/a"
    tt = "; ".join(f"{c} {v:+.2f}" for c, v in top)
    print(f"| {g} | {len(hg)} ({n1}/{n2}) | {len(big)}/{len(ds)} | {tt} "
          f"| {sh} |")
    sep_summary[g] = (len(big), np.mean(stab) if stab else np.nan)
print()

# ---- (c) ceiling model ----
drop = {"who", "episode_id", "month", "sec", "side", "session_date",
        "data_fresh", "kme_event", "kme_phase", "hand_label", "cluster",
        "cluster_b", "combo", "ax_struct_rev", "ax_struct_enr", "np_",
        "ctx", "grp", "kme_mins_since_c"}
A = pd.concat([H, N], ignore_index=True)
feats = [c for c in A.columns if c not in drop
         and pd.api.types.is_numeric_dtype(A[c])]
X = A[feats].astype(float)
for c in feats:
    X[f"m_{c}"] = X[c].isna().astype(float)
    X[c] = X[c].fillna(X[c].median())
y = (A.who == "his").astype(int).to_numpy()
sess = A.session_date.to_numpy()
oof = np.full(len(A), np.nan)
imps = []
for tr, te in GroupKFold(5).split(X, y, groups=sess):
    rf = RandomForestClassifier(n_estimators=500, random_state=113,
                                n_jobs=-1)
    rf.fit(X.iloc[tr], y[tr])
    oof[te] = rf.predict_proba(X.iloc[te])[:, 1]
    pi = permutation_importance(rf, X.iloc[te], y[te], n_repeats=5,
                                random_state=113, n_jobs=-1,
                                scoring="roc_auc")
    imps.append(pd.Series(pi.importances_mean, index=X.columns))
auc_all = roc_auc_score(y, oof)
print("## (c) CEILING MODEL (instrument only - never a strategy)")
print(f"Overall out-of-fold AUC: {auc_all:.2f} (0.5 = measurements add "
      "nothing; 1.0 = fully separate his moments from matched ordinary "
      "ones)")
print()
print("| group | AUC within group | n his / n null |")
print("|---|---|---|")
auc_g = {}
for g in GROUPS:
    msk = (A.grp == g).to_numpy()
    if y[msk].sum() >= 8 and (1 - y[msk]).sum() >= 30:
        a = roc_auc_score(y[msk], oof[msk])
    else:
        a = np.nan
    auc_g[g] = a
    print(f"| {g} | {a:.2f} | {int(y[msk].sum())} / "
          f"{int((1 - y[msk]).sum())} |")
IM = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
print()
print("Top 10 measurements by held-out permutation importance:")
for c, v in IM.head(10).items():
    print(f"- {c}: {v:.3f}")
print()

# ---- (d) stacking study ----
print("## (d) STACKING STUDY (conditions from the frozen spec; "
      "thresholds = null percentiles, a range each)")
cond_defs = {}
for name, col, side_signed in (("move", "mv15", True),
                               ("flow", "flow1", True)):
    base = N[col].dropna()
    for pct in (50, 75, 90):
        thr = np.percentile(base, pct)
        cond_defs[f"{name}>p{pct}"] = (col, thr)
conds = {}
for df in (H, N):
    c = {}
    c["structure"] = df[[f"{f}_interact" for f in amb_order]].any(axis=1)
    for k, (col, thr) in cond_defs.items():
        c[k] = df[col] > thr
    for k, thr in (("persist>=1", 1), ("persist>=2", 2), ("persist>=3", 3)):
        c[k] = df.consec_10s >= thr
    for k, thr in (("news45", 45), ("news15", 15), ("news5", 5)):
        c[k] = df.kme_mins_since <= thr
    c["signal"] = df.sig_samedir_5m > 0
    conds[id(df)] = pd.DataFrame(c)
CH, CN = conds[id(H)], conds[id(N)]
FAMILIES = {"structure": ["structure"],
            "move": ["move>p50", "move>p75", "move>p90"],
            "persist": ["persist>=1", "persist>=2", "persist>=3"],
            "flow": ["flow>p50", "flow>p75", "flow>p90"],
            "news": ["news45", "news15", "news5"],
            "signal": ["signal"]}
import itertools
print("| depth | best conjunction | capture (his) | null pass | lift |")
print("|---|---|---|---|---|")
best_at = {}
for depth in (1, 2, 3, 4):
    best = None
    for fams in itertools.combinations(FAMILIES, depth):
        for combo in itertools.product(*(FAMILIES[f] for f in fams)):
            hm = np.ones(len(CH), bool)
            nm = np.ones(len(CN), bool)
            for cc in combo:
                hm &= CH[cc].to_numpy()
                nm &= CN[cc].to_numpy()
            cap, npass = hm.mean(), nm.mean()
            if cap < 0.10 or npass == 0:
                continue
            lift = cap / npass
            score = cap * lift
            if best is None or score > best[0]:
                best = (score, combo, cap, npass, lift)
    if best:
        _, combo, cap, npass, lift = best
        best_at[depth] = best
        print(f"| {depth} | {' AND '.join(combo)} | {cap:.0%} | "
              f"{npass:.1%} | {lift:.1f}x |")
print()
print("Reading: capture = share of his 307 entries passing; null pass = "
      "share of matched ordinary moments passing; lift = concentration. "
      "Fires-per-day costing happens at the selector stage (B), as "
      "specified.")
print()
# ---- ranking table ----
print("## THE RANKED EVIDENCE TABLE (rubric from the spec; J picks)")
print("| group | n | sep. breadth (>=0.3) | ceiling AUC | stable share |")
print("|---|---|---|---|---|")
order = sorted(GROUPS, key=lambda g: -(0 if np.isnan(auc_g[g]) else
                                       auc_g[g]))
for g in order:
    b, st = sep_summary[g]
    print(f"| {g} | {(H.grp == g).sum()} | {b} | "
          f"{auc_g[g]:.2f} | {st:.0%} |" if np.isfinite(st) else
          f"| {g} | {(H.grp == g).sum()} | {b} | {auc_g[g]:.2f} | n/a |")
print()
print("Registry: T-IM46.")
