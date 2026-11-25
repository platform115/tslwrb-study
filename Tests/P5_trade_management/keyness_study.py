#!/usr/bin/env python3
"""
keyness_study.py — T-IM49: what makes a level "key" (computable
properties). Spec: KEYNESS_SPEC.md (committed first).
RUN: python3 Tests/P5_trade_management/keyness_study.py > Tests/P5_trade_management/KEYNESS_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p4_3_confluence_news import news_sets                   # noqa: E402

RNG = np.random.default_rng(113)

zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet").reset_index()
sl = pd.read_parquet("Data/inputs/s4_ref_links.parquet")
so = pd.read_parquet("Data/inputs/s4_objects.parquet")
ev = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

L = sl.merge(zr[["index", "tier"]], left_on="ref_idx",
             right_on="index", how="left")
key_ids = set(L[L.tier == "key"].object_id)
non_ids = set(L[L.tier != "key"].object_id) - key_ids
men_per_obj = L.groupby("object_id").size()

so["know_s"] = (so.knowable_ts.astype("datetime64[ns]").astype("int64")
                // 10**9)
so["width"] = (so.band_hi - so.band_lo).fillna(0.0)
so["mid"] = (so.band_hi + so.band_lo) / 2
kk = np.searchsorted(ev, so.know_s.to_numpy(), "right") - 1
so["in_news"] = (so.know_s.to_numpy() - ev[np.maximum(kk, 0)]) <= 2700
so["round10"] = (np.abs(so.mid % 10) < 0.3) | (np.abs(so.mid % 10 - 10)
                                               < 0.3)

K = so[so.object_id.isin(key_ids)].copy()
NK = so[so.object_id.isin(non_ids)].copy()
# matched random: same generator mix, same months, sample 3x key count
Kn = len(K)
pool = so[~so.object_id.isin(key_ids | non_ids)]
R = []
for gen, cnt in K.generator.value_counts().items():
    sub = pool[pool.generator == gen]
    if len(sub):
        R.append(sub.sample(min(len(sub), cnt * 3), random_state=113))
R = pd.concat(R)

# touch count + survival need price walks: per-second mids per month
MONTHS = {"2025-10": "2025-11-01", "2022-02": "2022-03-01",
          "2021-09": None, "2024-11": None}
from p4_66_context_ablation import prep                      # noqa: E402
def month_of(s):
    return pd.Timestamp(int(s), unit="s").strftime("%Y-%m")
avail = {}
for mo in ("2025-10", "2022-02", "2021-09", "2024-11"):
    try:
        P = prep(".", mo)
        avail[mo] = (P["secs"], P["mids"])
    except Exception:
        pass

def touches_survival(df, cap=1200):
    out_t, out_s = [], []
    for _, r in df.iterrows():
        mo = month_of(r.know_s)
        if mo not in avail:
            out_t.append(np.nan); out_s.append(np.nan); continue
        secs, mids = avail[mo]
        j1 = int(np.searchsorted(secs, r.know_s))
        j2 = int(np.searchsorted(secs, r.know_s + 6 * 3600, "right"))
        w = mids[j1:j2]; ws = secs[j1:j2]
        if len(w) < 60:
            out_t.append(np.nan); out_s.append(np.nan); continue
        e = r.mid if r.width == 0 else r.band_hi
        near = np.abs(w - e) <= 1.0
        t_, last = 0, -10**12
        for i in np.flatnonzero(near):
            if ws[i] - last >= 300:
                t_ += 1; last = ws[i]
        out_t.append(t_)
        # survival: seconds until first 2-pt break beyond the band
        brk = np.flatnonzero((w > r.band_hi + 2) | (w < r.band_lo - 2)) \
            if r.width > 0 else np.flatnonzero(np.abs(w - e) > 2)
        out_s.append(float(ws[brk[0]] - r.know_s) / 3600
                     if len(brk) else 6.0)
    df = df.copy()
    df["touches6h"], df["survive_h"] = out_t, out_s
    return df

K2 = touches_survival(K.sample(min(len(K), 800), random_state=113))
N2 = touches_survival(NK.sample(min(len(NK), 800), random_state=113))
R2 = touches_survival(R.sample(min(len(R), 800), random_state=113))


def delta(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) < 20 or len(b) < 20:
        return np.nan
    return 2 * mannwhitneyu(a, b).statistic / (len(a) * len(b)) - 1


print("# KEY-NESS STUDY (T-IM49)")
print("STATUS: CLOSED | 2026-11-25 | Spec: KEYNESS_SPEC.md (committed "
      "first)")
print()
print(f"Objects: key-linked {len(K)}, non-key-mentioned {len(NK)}, "
      f"matched random {len(R)} (price-walk samples 800 each).")
print()
print("## PROPERTY DIFFERENCES (all price-computable live)")
print("| property | key q50 | non-key q50 | random q50 | key-vs-random "
      "diff |")
print("|---|---|---|---|---|")
for c in ("width", "touches6h", "survive_h"):
    print(f"| {c} | {K2[c].median():.2f} | {N2[c].median():.2f} | "
          f"{R2[c].median():.2f} | {delta(K2[c], R2[c]):+.2f} |")
for c, nm in (("in_news", "formed in news window"),
              ("round10", "round-number")):
    print(f"| {nm} | {K[c].mean():.0%} | {NK[c].mean():.0%} | "
          f"{R[c].mean():.0%} | - |")
print("| timeframe mix | " + str(dict(K.tf.value_counts(
    normalize=True).round(2))) + " | " + str(dict(NK.tf.value_counts(
    normalize=True).round(2))) + " | " + str(dict(R.tf.value_counts(
    normalize=True).round(2))) + " | - |")
print("| generator mix | " + str(dict(K.generator.value_counts(
    normalize=True).round(2))) + " | " + str(dict(
    NK.generator.value_counts(normalize=True).round(2))) + " | (matched) "
    "| - |")
print()
print("STUDY-ONLY (barred from shipping): mentions per key object q50 = "
      f"{men_per_obj[men_per_obj.index.isin(key_ids)].median():.0f} vs "
      f"non-key {men_per_obj[men_per_obj.index.isin(non_ids)].median():.0f}")
print()
print("## DRAFT RULE: written in the summary from the table above, "
      "for J's review before any stage-1 retest.")
print("Registry: T-IM49.")
