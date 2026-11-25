#!/usr/bin/env python3
"""
a5_gap_autopsy.py — A5: gap autopsy (T-IM48). Spec: A5_SPEC.md
(committed first).
RUN: python3 Tests/A2_measurement/a5_gap_autopsy.py > Tests/A2_measurement/A5_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination"):
    sys.path.insert(0, os.path.join(T, d))
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[F.data_fresh].copy()
m = F.kme_mins_since
F["np_"] = np.where(np.isfinite(m) & (m <= 5), "burst",
                    np.where(np.isfinite(m) & (m <= 45), "window", "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
def grp(r):
    if r.np_ == "burst":
        return "G1"
    if r.ctx == "squeeze":
        return "G2" if r.np_ == "window" else "G3"
    if r.ctx == "reaction":
        return "G4" if r.np_ == "window" else "G5"
    return "G6"
F["grp"] = F.apply(grp, axis=1)
# mins_vs_open recompute (T-IM46 fix)
b_ = pd.read_parquet("Data/inputs/es_1m_front.parquet",
                     columns=["ts_event", "session", "session_date"])
b_ = b_[b_.session == "RTH"].sort_values("ts_event")
_open = {d: int(t.tz_convert(None).value // 10**9) for d, t in
         b_.groupby(b_.session_date.astype(str)).ts_event.min().items()}
F["mins_vs_open"] = [(int(s) - _open[d]) / 60.0 if d in _open else np.nan
                     for s, d in zip(F.sec, F.session_date)]

print("# A5 REPORT — GAP AUTOPSY (T-IM48)")
print("STATUS: CLOSED | 2026-11-25 | Spec: A5_SPEC.md (committed first)")
print()
# ================= HALF 1.1: ceiling model blind set =================
drop = {"who", "episode_id", "month", "sec", "side", "session_date",
        "data_fresh", "kme_event", "kme_phase", "hand_label", "cluster",
        "cluster_b", "combo", "ax_struct_rev", "ax_struct_enr", "np_",
        "ctx", "grp", "kme_mins_since_c"}
feats = [c for c in F.columns if c not in drop
         and pd.api.types.is_numeric_dtype(F[c])]
X = F[feats].astype(float)
for c in feats:
    X[f"m_{c}"] = X[c].isna().astype(float)
    X[c] = X[c].fillna(X[c].median())
y = (F.who == "his").astype(int).to_numpy()
oof = np.full(len(F), np.nan)
for tr_i, te_i in GroupKFold(5).split(X, y, groups=F.session_date):
    rf = RandomForestClassifier(n_estimators=500, random_state=113,
                                n_jobs=-1)
    rf.fit(X.iloc[tr_i], y[tr_i])
    oof[te_i] = rf.predict_proba(X.iloc[te_i])[:, 1]
F["score"] = oof
H = F[F.who == "his"].copy()
null_med = F[F.who == "null"].score.median()
H["blind"] = H.score < null_med
B, S = H[H.blind], H[~H.blind]
print(f"## HALF 1.1 — THE BLIND SET")
print(f"His trades the model scores below the typical ordinary moment: "
      f"{len(B)}/{len(H)} ({len(B)/len(H):.0%}).")
print()
print("| axis | blind set | the rest |")
print("|---|---|---|")
for ax in ("grp", "np_", "month"):
    bb = B[ax].value_counts(normalize=True).round(2).to_dict()
    ss = S[ax].value_counts(normalize=True).round(2).to_dict()
    print(f"| {ax} | {bb} | {ss} |")
def delta(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) < 8 or len(b) < 8:
        return np.nan
    return 2 * mannwhitneyu(a, b).statistic / (len(a) * len(b)) - 1
REPS = ["mv15", "flow1", "vrate900", "consec_10s", "stall_5m_extreme",
        "rng120", "dwell120", "mins_vs_open", "sig_best_score",
        "mins_since_mention"]
dd = sorted(((delta(B[c], S[c]), c) for c in REPS),
            key=lambda kv: -abs(kv[0] if np.isfinite(kv[0]) else 0))
print()
print("What blind trades lack vs the rest (difference score, blind vs "
      "seen):")
for v, c in dd[:6]:
    print(f"- {c}: {v:+.2f} (blind q50 {B[c].median():.2f} vs "
          f"{S[c].median():.2f})")
print()
# ================= HALF 1.2: B2-uncaught decomposition ===============
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
G2H = H[H.grp == "G2"]
b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
causes = {"caught": 0, "edge_absent": 0, "no_cross": 0,
          "window_miss": 0, "order_unfilled": 0}
det = []
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    sub = D[(D.month == mo) & (D.disp == 1.25)]
    for _, h in G2H[G2H.month == mo].iterrows():
        hit = sub[(sub.d == h.side) & (abs(sub.tf - h.sec) <= 300)]
        if len(hit):
            causes["caught"] += 1
            continue
        t64 = np.datetime64(int(h.sec), "s")
        E = edges_at(R, h.session_date, t64, "SQZ")
        j = int(np.searchsorted(secs, int(h.sec), "right")) - 1
        px = mids[j]
        near = [e for e in E if abs(px - e) <= 5.0]
        if not near:
            causes["edge_absent"] += 1
            det.append((mo, h.sec, "edge_absent"))
            continue
        j0 = int(np.searchsorted(secs, int(h.sec) - 300))
        crossed = False
        for e in near:
            w = mids[j0:j + 1]
            if (w < e).any() and (w > e).any():
                crossed = True
        if not crossed:
            causes["no_cross"] += 1
            det.append((mo, h.sec, "no_cross"))
            continue
        # window check: was a trigger scanned near this time at all?
        any_fire = sub[abs(sub.t - h.sec) <= 600]
        if not len(any_fire):
            causes["window_miss"] += 1
            det.append((mo, h.sec, "window_miss"))
        else:
            causes["order_unfilled"] += 1
            det.append((mo, h.sec, "order_unfilled"))
print("## HALF 1.2 — WHY THE TRIGGER MISSED 17 G2 TRADES "
      "(mechanical causes)")
for k, v in causes.items():
    print(f"- {k}: {v}")
print()
# ================= HALF 2: exit gap ==================================
G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
GT = G2H.merge(G, left_on=["month", "sec"],
               right_on=["month", "entry_msg_s"], suffixes=("", "_gt"))
gaps = []
for mo in MONTHS:
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in GT[GT.month == mo].iterrows():
        if not np.isfinite(r.entry_price) or not np.isfinite(r.pnl_stated):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.sec) + 1800, "right"))
        exc = (mids[j1:j2] - r.entry_price) * r.side
        ts = (secs[j1:j2] - int(r.sec)).astype(int)
        peak, tp = 0.0, 0
        ix, why = len(exc) - 1, "end"
        for i in range(len(exc)):
            if exc[i] > peak:
                peak, tp = exc[i], ts[i]
            if exc[i] <= -3.75:
                ix, why = i, "stop"
                break
            if ts[i] - tp >= 60:
                ix, why = i, "stall"
                break
            if ts[i] >= 480:
                ix, why = i, "time"
                break
        ours = -3.75 if why == "stop" else exc[ix]
        gap = r.pnl_stated - ours
        cause = "SMALL"
        if abs(gap) > 1:
            if why == "stop":
                cause = "STOP"
            elif why == "time":
                cause = "TIME"
            else:
                # stall-early: did price reach his exit value later,
                # before his actual exit?
                hold = int(r.hold_s) if np.isfinite(r.hold_s) else 1800
                j3 = int(np.searchsorted(secs, int(r.sec) + hold, "right"))
                later = exc[ix:max(ix + 1, j3 - j1)]
                cause = "STALL-EARLY" if (len(later)
                        and later.max() >= r.pnl_stated - 0.5) else \
                    "OTHER"
        gaps.append(dict(month=mo, sec=int(r.sec), gap=gap, cause=cause,
                         his=r.pnl_stated, ours=ours,
                         event=r.kme_event, mv15=r.mv15,
                         vrate900=r.vrate900, sig=r.sig_samedir_5m))
GP = pd.DataFrame(gaps)
print("## HALF 2 — THE EXIT GAP, DISSECTED (his P&L minus M3A's, "
      "same fills)")
print(f"Total gap: {GP.gap.sum():+.1f} pts over {len(GP)} trades.")
print("| cause | trades | gap points |")
print("|---|---|---|")
for c, g in GP.groupby("cause"):
    print(f"| {c} | {len(g)} | {g.gap.sum():+.1f} |")
big = GP[GP.gap > 1]
print()
print("Conditioning evidence - do big-gap trades differ at ENTRY "
      "(knowable)?")
rest = GP[GP.gap <= 1]
for c in ("mv15", "vrate900", "sig"):
    print(f"- {c}: big-gap q50 {big[c].median():.2f} vs rest "
          f"{rest[c].median():.2f} (difference {delta(big[c], rest[c]):+.2f})")
print()
print("## VERDICT (for J's pick - nothing built here)")
print("Written in the summary message with the evidence above.")
print()
print("Registry: T-IM48.")
