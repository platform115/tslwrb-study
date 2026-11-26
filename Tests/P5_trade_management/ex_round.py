#!/usr/bin/env python3
"""
ex_round.py — T-MG19: exit-switch remainder via the order book.
Spec: EX_SPEC.md (committed first). Study only.
RUN: python3 Tests/P5_trade_management/ex_round.py > Tests/P5_trade_management/EX_REPORT.md
"""
import sys
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

RNG = np.random.default_rng(113)
MONTHS = ("2022-02", "2025-10")

gt = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
gt = gt[gt.month.isin(MONTHS)].copy()
lag = gt.posting_lag_s.where(np.isfinite(gt.posting_lag_s), 0.0)
gt["t_entry"] = gt.entry_msg_s - lag
basis_lagged = int(np.isfinite(gt.posting_lag_s).sum())
gt["sd_n"] = gt.side.map({"long": 1, "short": -1})
gt = gt[np.isfinite(gt.hold_s) & (gt.hold_s >= 30)
        & gt.sd_n.notna()].copy()
gt["t_exit"] = gt.t_entry + gt.hold_s

BK = {}
FL = {}
for mo in MONTHS:
    bk = pd.read_parquet(f"Data/inputs/book_per_sec_{mo}.parquet")
    BK[mo] = (bk.sec.to_numpy(), bk.bid0.to_numpy().astype(float),
              bk.ask0.to_numpy().astype(float),
              bk.bid10.to_numpy().astype(float),
              bk.ask10.to_numpy().astype(float))
    fl = pd.read_parquet(f"Data/inputs/flow_per_sec_{mo}_full.parquet")
    FL[mo] = (fl.sec.to_numpy(),
              np.concatenate([[0.0], np.cumsum(
                  (fl.buyv - fl.sellv).to_numpy().astype(float))]))

def book_at(mo, t):
    bsec, b0, a0, b10, a10 = BK[mo]
    k = int(np.searchsorted(bsec, t, "right")) - 1
    if k < 0 or t - bsec[k] > 5:
        return None
    return b0[k], a0[k], b10[k], a10[k]

def flow30(mo, t, sdn):
    fsec, cnet = FL[mo]
    i = int(np.searchsorted(fsec, t - 30))
    j = int(np.searchsorted(fsec, t, "right"))
    return float((cnet[j] - cnet[i]) * sdn)

FEATS = ["sup0", "opp0", "sup10", "opp10", "imb0", "imb10",
         "d30_sup0", "depth_tot", "flow_net_30"]

def feats_at(mo, t, sdn):
    bnow = book_at(mo, t)
    if bnow is None:
        return None
    b0, a0, b10, a10 = bnow
    sup0 = b0 if sdn > 0 else a0
    opp0 = a0 if sdn > 0 else b0
    sup10 = b10 if sdn > 0 else a10
    opp10 = a10 if sdn > 0 else b10
    bprev = book_at(mo, t - 30)
    d30 = (sup0 - (bprev[0] if sdn > 0 else bprev[1])) \
        if bprev is not None else np.nan
    return dict(sup0=sup0, opp0=opp0, sup10=sup10, opp10=opp10,
                imb0=(sup0 - opp0) / max(sup0 + opp0, 1.0),
                imb10=(sup10 - opp10) / max(sup10 + opp10, 1.0),
                d30_sup0=d30, depth_tot=b10 + a10,
                flow_net_30=flow30(mo, t, sdn))

print("# EX REPORT — EXIT-SWITCH REMAINDER VIA THE ORDER BOOK "
      "(T-MG19)")
print("STATUS: CLOSED | 2026-11-26 | Spec: EX_SPEC.md (committed "
      "first) | study only | book = per-second drive reduction "
      "(news-window coverage)")
print()
print(f"Population: {len(gt)} audited exits with hold >= 30s "
      f"({(gt.month == '2022-02').sum()}/"
      f"{(gt.month == '2025-10').sum()} per month); entry-time basis: "
      f"{basis_lagged} rows had a finite posting lag applied.")
print()

# ---------- ANALYSIS A: duration-matched case-control ----------
pairs = []           # list of (case_id, is_case, featdict)
no_book = no_ctrl = 0
cid = 0
for _, r in gt.iterrows():
    mo = r.month
    fe = feats_at(mo, r.t_exit, r.sd_n)
    if fe is None:
        no_book += 1
        continue
    dur = r.hold_s
    pool = gt[(gt.month == mo) & (gt.index != r.name)
              & (gt.hold_s >= 1.2 * dur)]
    ctr = []
    for _, c in pool.iterrows():
        fc = feats_at(mo, c.t_entry + dur, c.sd_n)
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
ncases = D[D.case == 1].cid.nunique()
print("## ANALYSIS A — HIS EXIT MOMENT vs SAME-DURATION HOLD MOMENTS "
      "IN HIS OTHER TRADES")
print(f"Cases with book + >=1 duration-matched control: {ncases} "
      f"(dropped: {no_book} no book second, {no_ctrl} no eligible "
      f"control).")
print()
print("| feature | exit med | hold med | direction | perm p | "
      "verdict (alpha .0056 / .05) |")
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
    if ng < 10:
        print(f"| {f} | - | - | - | - | insufficient |")
        continue
    obs /= ng
    nulls /= ng
    p = float(min((nulls >= obs).mean(), (nulls <= obs).mean()) * 2)
    p = min(p, 1.0)
    em = D[D.case == 1][f].median()
    hm = D[D.case == 0][f].median()
    # month consistency
    same = True
    base_sign = np.sign(em - hm)
    for mo in MONTHS:
        a_ = D[(D.case == 1) & (D.month == mo)][f].dropna()
        b_ = D[(D.case == 0) & (D.month == mo)][f].dropna()
        if len(a_) and len(b_) and \
           np.sign(a_.median() - b_.median()) != base_sign:
            same = False
    dr = "exit HIGHER" if obs > 0.5 else "exit LOWER"
    v_ = ("FINDING" if (p <= 0.0056 and same) else
          ("suggestive" if p <= 0.05 else "null"))
    if v_ == "FINDING" and not same:
        v_ = "null"
    print(f"| {f} | {em:.2f} | {hm:.2f} | {dr} | {p:.4f} | {v_}"
          f"{'' if same else ' (month-inconsistent)'} |")
print()

# ---------- ANALYSIS B: the long-hold remainder at t=480 ----------
print("## ANALYSIS B — AT THE CLOCK (480s): WHO KEEPS HOLDING?")
ce = gt[(gt.hold_s >= 400) & (gt.hold_s <= 560)]
hd = gt[gt.hold_s >= 700]
rows_b = {"CLOCK-EXITERS": [], "HOLDERS": []}
for nm, sub in (("CLOCK-EXITERS", ce), ("HOLDERS", hd)):
    for _, r in sub.iterrows():
        fe = feats_at(r.month, r.t_entry + 480, r.sd_n)
        if fe is not None:
            fe["month"] = r.month
            rows_b[nm].append(fe)
CE = pd.DataFrame(rows_b["CLOCK-EXITERS"])
HD = pd.DataFrame(rows_b["HOLDERS"])
print(f"n with book at t=480: clock-exiters {len(CE)}, holders "
      f"{len(HD)}. Power is thin; stated, not hidden.")
if len(CE) >= 8 and len(HD) >= 8:
    print("| feature | exiter med | holder med | p | both months same "
          "dir | verdict |")
    print("|---|---|---|---|---|---|")
    for f in FEATS:
        a_, b_ = CE[f].dropna(), HD[f].dropna()
        if len(a_) < 5 or len(b_) < 5:
            print(f"| {f} | - | - | - | - | insufficient |")
            continue
        p = mannwhitneyu(a_, b_).pvalue
        same = True
        sgn = np.sign(a_.median() - b_.median())
        for mo in MONTHS:
            am = CE[CE.month == mo][f].dropna()
            bm = HD[HD.month == mo][f].dropna()
            if len(am) >= 3 and len(bm) >= 3 and \
               np.sign(am.median() - bm.median()) != sgn:
                same = False
        v_ = ("FINDING" if (p <= 0.0056 and same) else
              ("suggestive" if p <= 0.05 else "null"))
        print(f"| {f} | {a_.median():.2f} | {b_.median():.2f} | "
              f"{p:.4f} | {'yes' if same else 'NO'} | {v_} |")
else:
    print("Below the pre-stated minimum (8 per group with book "
          "coverage) — Analysis B returns INSUFFICIENT, not a null.")
print()
print("Registry: T-MG19.")
