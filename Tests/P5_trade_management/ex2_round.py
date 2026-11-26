#!/usr/bin/env python3
"""
ex2_round.py — T-MG20: excursion-matched robustness check for imb10.
Spec: EX2_SPEC.md (committed first).
RUN: python3 Tests/P5_trade_management/ex2_round.py > Tests/P5_trade_management/EX2_REPORT.md
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_66_context_ablation import prep                      # noqa: E402

RNG = np.random.default_rng(113)
MONTHS = ("2022-02", "2025-10")

gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
gt = gt[gt.month.isin(MONTHS)].copy()
lag = gt.posting_lag_s.where(np.isfinite(gt.posting_lag_s), 0.0)
gt["t_entry"] = gt.entry_msg_s - lag
gt["sd_n"] = gt.side.map({"long": 1, "short": -1})
gt = gt[np.isfinite(gt.hold_s) & (gt.hold_s >= 30) & gt.sd_n.notna()
        & np.isfinite(gt.entry_price)].copy()
gt["t_exit"] = gt.t_entry + gt.hold_s

BK, MIDS = {}, {}
for mo in MONTHS:
    bk = pd.read_parquet(f"Data/inputs/book_per_sec_{mo}.parquet")
    BK[mo] = (bk.sec.to_numpy(), bk.bid0.to_numpy().astype(float),
              bk.ask0.to_numpy().astype(float),
              bk.bid10.to_numpy().astype(float),
              bk.ask10.to_numpy().astype(float))
    P = prep(".", mo)
    MIDS[mo] = (P["secs"], P["mids"])

def book_at(mo, t):
    bsec, b0, a0, b10, a10 = BK[mo]
    k = int(np.searchsorted(bsec, t, "right")) - 1
    if k < 0 or t - bsec[k] > 5:
        return None
    return b0[k], a0[k], b10[k], a10[k]

def mid_at(mo, t):
    secs, mids = MIDS[mo]
    k = int(np.searchsorted(secs, t, "right")) - 1
    if k < 0 or t - secs[k] > 5:
        return None
    return float(mids[k])

def feats_at(mo, t, sdn):
    bnow = book_at(mo, t)
    if bnow is None:
        return None
    b0, a0, b10, a10 = bnow
    sup0 = b0 if sdn > 0 else a0
    opp0 = a0 if sdn > 0 else b0
    sup10 = b10 if sdn > 0 else a10
    opp10 = a10 if sdn > 0 else b10
    return dict(imb0=(sup0 - opp0) / max(sup0 + opp0, 1.0),
                imb10=(sup10 - opp10) / max(sup10 + opp10, 1.0),
                depth_tot=b10 + a10)

FEATS = ["imb10", "imb0", "depth_tot"]
pairs = []
no_book = no_mid = no_ctrl = 0
cid = 0
for _, r in gt.iterrows():
    mo = r.month
    fe = feats_at(mo, r.t_exit, r.sd_n)
    m_case = mid_at(mo, r.t_exit)
    if fe is None:
        no_book += 1
        continue
    if m_case is None:
        no_mid += 1
        continue
    exc_case = (m_case - r.entry_price) * r.sd_n
    tol = max(0.5, 0.25 * abs(exc_case))
    dur = r.hold_s
    pool = gt[(gt.month == mo) & (gt.index != r.name)
              & (gt.hold_s >= 1.2 * dur)]
    ctr = []
    for _, c in pool.iterrows():
        tm = c.t_entry + dur
        mc = mid_at(mo, tm)
        if mc is None:
            continue
        exc_c = (mc - c.entry_price) * c.sd_n
        if abs(exc_c - exc_case) > tol:
            continue
        fc = feats_at(mo, tm, c.sd_n)
        if fc is not None:
            ctr.append(fc)
        if len(ctr) >= 3:
            break
    if not ctr:
        no_ctrl += 1
        continue
    cid += 1
    pairs.append((cid, mo, 1, fe))
    for fc in ctr:
        pairs.append((cid, mo, 0, fc))
D = pd.DataFrame([dict(cid=a, month=m, case=c, **f)
                  for a, m, c, f in pairs])
ncases = D[D.case == 1].cid.nunique() if len(D) else 0
print("# EX2 REPORT — EXCURSION-MATCHED ROBUSTNESS CHECK (T-MG20)")
print("STATUS: CLOSED | 2026-11-26 | Spec: EX2_SPEC.md (committed "
      "first)")
print()
print(f"Cases with book + mid + >=1 duration-AND-excursion-matched "
      f"control: {ncases} (dropped: {no_book} no book, {no_mid} no "
      f"mid, {no_ctrl} no excursion-matched control).")
print()
if ncases < 30:
    print("Below a workable paired sample (30) — result is "
          "INSUFFICIENT, not a verdict; the finding stays UNRESOLVED "
          "and the registry row says so.")
else:
    print("| feature | exit med | hold med | direction | perm p | "
          "verdict (alpha .0167 / .05) |")
    print("|---|---|---|---|---|---|")
    NPERM = 10000
    groups = [g for _, g in D.groupby("cid")]
    for f in FEATS:
        obs = 0.0
        nulls = np.zeros(NPERM)
        ng = 0
        for g in groups:
            v = g[f].to_numpy()
            if np.isnan(v).all() or len(v) < 2:
                continue
            r_ = pd.Series(v).rank(pct=True).to_numpy()
            ci = np.flatnonzero(g.case.to_numpy() == 1)
            if not len(ci) or np.isnan(v[ci[0]]):
                continue
            obs += float(r_[ci[0]])
            nulls += r_[RNG.integers(0, len(v), NPERM)]
            ng += 1
        obs /= ng
        nulls /= ng
        p = float(min((nulls >= obs).mean(),
                      (nulls <= obs).mean()) * 2)
        p = min(p, 1.0)
        em = D[D.case == 1][f].median()
        hm = D[D.case == 0][f].median()
        same = True
        sgn = np.sign(em - hm)
        for mo in MONTHS:
            a_ = D[(D.case == 1) & (D.month == mo)][f].dropna()
            b_ = D[(D.case == 0) & (D.month == mo)][f].dropna()
            if len(a_) and len(b_) and \
               np.sign(a_.median() - b_.median()) != sgn:
                same = False
        dr = "exit HIGHER" if obs > 0.5 else "exit LOWER"
        v_ = ("SURVIVES" if (p <= 0.0167 and same) else
              ("suggestive" if p <= 0.05 else "dies"))
        print(f"| {f} | {em:.3f} | {hm:.3f} | {dr} | {p:.4f} | {v_}"
              f"{'' if same else ' (month-inconsistent)'} |")
print()
print("Registry: T-MG20.")
