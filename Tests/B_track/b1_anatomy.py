#!/usr/bin/env python3
"""
b1_anatomy.py — B1: anatomy of the G2 target (T-IM47). Spec: B1_SPEC.md
(committed first).
RUN: python3 Tests/B_track/b1_anatomy.py > Tests/B_track/B1_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination"):
    sys.path.insert(0, os.path.join(T, d))
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_24_s6_3_selectors import interact_edges              # noqa: E402
from p4_66_context_ablation import prep                      # noqa: E402

MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
amb_order = ["SQZ", "REA", "GAP", "SHD"]

F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
m = F.kme_mins_since
F["np_"] = np.where(np.isfinite(m) & (m <= 5), "burst",
                    np.where(np.isfinite(m) & (m <= 45), "window", "none"))
def ctx_row(r):
    for f in amb_order:
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
G2 = F[(F.ctx == "squeeze") & (F.np_ == "window")].copy()

G = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
G2 = G2.merge(G, left_on=["month", "sec"],
              right_on=["month", "entry_msg_s"],
              suffixes=("", "_gt"))
assert len(G2) == 62, f"expected 62 G2 trades, got {len(G2)}"

def q(s, ps=(25, 50, 75)):
    v = pd.Series(s).dropna()
    return " / ".join(f"{np.percentile(v, p):.2f}" for p in ps) \
        if len(v) else "-"

print("# B1 REPORT — ANATOMY OF G2 (squeeze + news window) (T-IM47)")
print("STATUS: CLOSED | 2026-11-25 | Spec: B1_SPEC.md (committed first)")
print()
# ---- 1. worth replicating? ----
print("## 1. IS THE GROUP WORTH REPLICATING? (his own results)")
print("| month | trades | win rate | points won / lost | net | avg win / "
      "loss | worst |")
print("|---|---|---|---|---|---|---|")
for mo, g in list(G2.groupby("month")) + [("BOTH", G2)]:
    p = g.pnl_stated.dropna()
    w = p > 0
    print(f"| {mo} | {len(g)} | {w.mean():.0%} | +{p[w].sum():.1f} / "
          f"{p[~w].sum():.1f} | {p.sum():+.1f} | +{p[w].mean():.2f} / "
          f"{p[~w].mean():.2f} | {p.min():+.2f} |")
print()
# ---- 2. entry anatomy ----
print("## 2. ENTRY ANATOMY (all knowable at entry)")
# trigger edge + displacement via resolver
b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
disp, br_match = [], []
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in G2[G2.month == mo].iterrows():
        t64 = np.datetime64(int(r.sec), "s")
        E = interact_edges(R, r.session_date, t64, "SQZ", 15, secs, mids,
                           int(r.side))
        if E and np.isfinite(r.entry_price):
            e = min(E, key=lambda x: abs(r.entry_price - x))
            disp.append((r.entry_price - e) * r.side)
            j = int(np.searchsorted(secs, int(r.sec), "right")) - 1
            br_match.append(np.sign(mids[j] - e) == np.sign(r.side))
print(f"- trigger edge found for {len(disp)}/62; DISPLACEMENT (fill past "
      f"the band edge, pts): q25/50/75 = {q(disp)}")
print(f"- his side matches the band's break side: "
      f"{np.mean(br_match):.0%}")
print(f"- minutes since the release: q25/50/75 = {q(G2.kme_mins_since)}")
print(f"- events he trades in G2: "
      + ", ".join(f"{k} ({v})" for k, v in
                  G2.kme_event.value_counts().head(6).items()))
print(f"- movement mv15 at entry (ticks, his way): {q(G2.mv15)}")
print(f"- 10s persistence runs: {q(G2.consec_10s)}")
print(f"- flow toward side (contracts/s, 1 min): {q(G2.flow1)}")
print(f"- same-direction signal in last 5 min: "
      f"{(G2.sig_samedir_5m > 0).mean():.0%} of entries")
print()
# ---- 3. outcome anatomy ----
print("## 3. OUTCOME ANATOMY (labels - what the trades DID)")
print(f"- MFE (best excursion, pts): q25/50/75 = {q(G2.mfe_pts)}")
print(f"- MAE (worst excursion, pts): q50/75/90 = "
      f"{q(G2.mae_pts, (50, 75, 90))}")
print(f"- hold (seconds): q25/50/75 = {q(G2.hold_s)}")
w = G2.pnl_stated > 0
print(f"- scratch-vs-runner: {int((G2.pnl_stated.abs() <= 1).sum())} "
      f"scratches (|P&L| <= 1 pt), "
      f"{int((G2.pnl_stated > 4).sum())} runners (> 4 pts)")
# time-to-peak needs per-second walk
ttp = []
for mo, nxt in MONTHS.items():
    P = prep(".", mo)
    secs, mids = P["secs"], P["mids"]
    for _, r in G2[G2.month == mo].iterrows():
        if not (np.isfinite(r.entry_price) and r.exit_msg_s
                and r.exit_msg_s > r.sec):
            continue
        j1 = int(np.searchsorted(secs, int(r.sec)))
        j2 = int(np.searchsorted(secs, int(r.exit_msg_s), "right"))
        if j2 <= j1:
            continue
        exc = (mids[j1:j2] - r.entry_price) * r.side
        ttp.append(int(secs[j1 + int(np.argmax(exc))] - r.sec))
print(f"- time to the trade's best point (seconds): q25/50/75 = {q(ttp)}"
      f" - the 'moves quickly' clause, measured")
print()
# ---- 4. barrier grid ----
print("## 4. THE TRIPLE-BARRIER GRID (handed to B2; ranges, not picks)")
mfe = G2.mfe_pts.dropna(); mae = G2.mae_pts.dropna()
hold = G2.hold_s.dropna()
print("| barrier | candidates (from his quantiles) |")
print("|---|---|")
print(f"| profit (pts) | {np.percentile(mfe,25):.2f} / "
      f"{np.percentile(mfe,50):.2f} / {np.percentile(mfe,75):.2f} |")
print(f"| stop (pts) | {np.percentile(mae,50):.2f} / "
      f"{np.percentile(mae,75):.2f} / {np.percentile(mae,90):.2f} |")
print(f"| time (s) | {np.percentile(hold,50):.0f} / "
      f"{np.percentile(hold,75):.0f} / {np.percentile(hold,90):.0f} |")
print()
print("Registry: T-IM47.")
