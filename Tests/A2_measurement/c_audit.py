#!/usr/bin/env python3
"""
c_audit.py — T-IM53: squeeze-detector coverage audit (the 9 edge_absent
G2 trades). Spec: C_AUDIT_SPEC.md (committed first; shipped cells
corrected to W={10,30}, q=0.67 per the certified generator code).
RUN: python3 Tests/A2_measurement/c_audit.py > Tests/A2_measurement/C_AUDIT_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402

RNG = np.random.default_rng(113)
MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01"}
WS = (10, 15, 20, 30, 45)
QS = (0.5, 0.67, 0.8)

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)

def recent_band(g, upto, W, q):
    """Most recent C2 episode band (active or ended) using bars [:upto]."""
    h = g.high.to_numpy()[:upto]; l = g.low.to_numpy()[:upto]
    n = len(h)
    if n < W + 12:
        return None
    rng_w = np.full(n, np.nan)
    for i in range(W, n):
        rng_w[i] = h[i - W + 1:i + 1].max() - l[i - W + 1:i + 1].min()
    med = np.full(n, np.nan)
    for i in range(W, n):
        prior = rng_w[max(W, i - 60):i]
        prior = prior[np.isfinite(prior)]
        if len(prior) >= 10:
            med[i] = np.median(prior)
    active = np.isfinite(rng_w) & np.isfinite(med) & (rng_w <= q * med)
    idx = np.flatnonzero(active)
    if not len(idx):
        return None
    # last maximal run
    end = idx[-1]
    start = end
    while start - 1 in idx:
        start -= 1
    s0 = max(0, start - W + 1)
    return float(l[s0:end + 1].min()), float(h[s0:end + 1].max())

# ---- find the 9 edge_absent trades (A5 logic) ----
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f}_interact"]:
            return {"SQZ": "squeeze", "REA": "reaction"}.get(f, "other")
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
G2H = F[(F.ctx == "squeeze") & (F.np_ == "window")]
D = pd.read_parquet("Data/inputs/b2_candidates.parquet")
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")
import importlib
from p4_66_context_ablation import prep
absent = []
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
            continue
        t64 = np.datetime64(int(h.sec), "s")
        E = edges_at(R, h.session_date, t64, "SQZ")
        j = int(np.searchsorted(secs, int(h.sec), "right")) - 1
        px = mids[j]
        if not [e for e in E if abs(px - e) <= 5.0]:
            absent.append((mo, h.session_date, int(h.sec), float(px)))
print("# C AUDIT REPORT — SQUEEZE COVERAGE (T-IM53)")
print("STATUS: CLOSED | 2026-11-26 | Spec: C_AUDIT_SPEC.md | shipped "
      "cells = W{10,30} q0.67 (spec's 15/30 corrected from code)")
print()
print(f"edge_absent trades found: {len(absent)}")
print()
# ---- per-trade coverage across the grid ----
cover = {(W, q): 0 for W in WS for q in QS}
for mo, sd0, sec, px in absent:
    g = b[b.sd == sd0].reset_index(drop=True)
    bt = g.ts_event.dt.tz_convert(None).astype("int64").to_numpy() // 10**9
    upto = int(np.searchsorted(bt + 60, sec, "right"))  # completed bars
    for W in WS:
        for q in QS:
            band = recent_band(g, upto, W, q)
            if band and min(abs(px - band[0]), abs(px - band[1])) <= 5.0:
                cover[(W, q)] += 1
# ---- ambient cost ----
amb = {(W, q): [] for W in WS for q in QS}
for mo, nxt in MONTHS.items():
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)]
    rth = bm[bm.session == "RTH"]
    pick = rth.sample(min(150, len(rth)), random_state=113)
    for _, r in pick.iterrows():
        g = b[b.sd == r.sd].reset_index(drop=True)
        bt = g.ts_event.dt.tz_convert(None).astype("int64").to_numpy()
        upto = int(np.searchsorted(bt, r.ts_event.tz_convert(None).value))
        for W in WS:
            for q in QS:
                band = recent_band(g, upto, W, q)
                amb[(W, q)].append(bool(band and min(
                    abs(r.close - band[0]), abs(r.close - band[1]))
                    <= 5.0))
print("| W | q | covers (of %d) | ambient edge-within-5 rate |" % len(absent))
print("|---|---|---|---|")
for W in WS:
    for q in QS:
        tag = " (shipped)" if (W in (10, 30) and q == 0.67) else ""
        print(f"| {W}{tag} | {q} | {cover[(W,q)]} | "
              f"{np.mean(amb[(W,q)]):.0%} |")
print()
print("Reading: a cell is only worth adopting if it covers several of "
      "the missed trades WITHOUT a much higher ambient rate than the "
      "shipped cells. Adoption = Strategy 4 revision = full B2->B4 "
      "re-run + fresh validation (J's call). Registry: T-IM53.")
