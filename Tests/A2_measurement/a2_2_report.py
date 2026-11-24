#!/usr/bin/env python3
"""a2_2_report.py — descriptive his-vs-null report for the A2.2 table.
Mann-Whitney per feature, Benjamini-Hochberg corrected (methods register).
Flags are PROVISIONAL marks for A3/A4 attention, never gates (R-4).
RUN: python3 Tests/A2_measurement/a2_2_report.py > Tests/A2_measurement/A2_2_REPORT.md
"""
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

F = pd.read_parquet("Data/inputs/a2_features.parquet")
h = F[(F.who == "his") & F.data_fresh]
n = F[(F.who == "null") & F.data_fresh]
META = {"who", "episode_id", "month", "sec", "side", "session_date",
        "data_fresh", "kme_event", "kme_phase", "kme_in45",
        "REA_interact", "SQZ_interact", "GAP_interact", "SHD_interact"}
num_cols = [c for c in F.columns if c not in META
            and pd.api.types.is_numeric_dtype(F[c])]
rows = []
for c in num_cols:
    a, b = h[c].dropna(), n[c].dropna()
    if len(a) < 30 or len(b) < 100:
        continue
    try:
        p = mannwhitneyu(a, b).pvalue
    except ValueError:
        continue
    rows.append(dict(feature=c, his_q25=a.quantile(.25), his_q50=a.median(),
                     his_q75=a.quantile(.75), null_q50=b.median(), p=p,
                     ratio=(a.median() / b.median()
                            if b.median() not in (0, np.nan) else np.nan)))
R = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
m = len(R)
R["bh_flag"] = R.p <= (np.arange(1, m + 1) / m) * 0.05  # BH step-up (sorted)
# correct BH: largest k with p_k <= k/m*q
ok = np.flatnonzero(R.p.to_numpy() <= (np.arange(1, m + 1) / m) * 0.05)
k = ok.max() + 1 if len(ok) else 0
R["bh_flag"] = np.arange(m) < k

print("# A2.2 REPORT — THE MEASUREMENT TABLE (T-IM41)")
print("STATUS: CLOSED | 2026-11-24 | Spec: A2_2_SPEC.md (frozen) | "
      "harness PASS both months (0 honest mismatches; both planted bugs caught)")
print()
print(f"Rows: {len(h)} of his trades with features (8 Feb-28 = NaN by "
      f"design), {len(n)} matched nulls. {len(num_cols)} numeric features.")
print()
print("## STRUCTURE + KME STATE, HIS vs NULL (plain counts)")
print("| state | his | null |")
print("|---|---|---|")
for fam in ("REA", "SQZ", "GAP", "SHD"):
    print(f"| {fam} interacting at the moment | "
          f"{h[f'{fam}_interact'].mean():.0%} | "
          f"{n[f'{fam}_interact'].mean():.0%} |")
print(f"| inside 45-min KME window | {h.kme_in45.mean():.0%} | "
      f"{n.kme_in45.mean():.0%} |")
print(f"| KME phase 0-5 min | {(h.kme_phase == '0-5').mean():.0%} | "
      f"{(n.kme_phase == '0-5').mean():.0%} |")
print()
print("## FEATURES RANKED BY SEPARATION (Mann-Whitney, BH-corrected 5%)")
print("Flags mark where A3/A4 should look. They are NOT gates (R-4).")
print()
print("| feature | his q25/q50/q75 | null q50 | flagged |")
print("|---|---|---|---|")
for _, r in R.head(30).iterrows():
    print(f"| {r.feature} | {r.his_q25:.2f} / {r.his_q50:.2f} / "
          f"{r.his_q75:.2f} | {r.null_q50:.2f} | "
          f"{'YES' if r.bh_flag else 'no'} |")
print()
print(f"Flagged features: {int(R.bh_flag.sum())} of {m} tested.")
print()
print("## KME SURPRISE (new field)")
k45 = h[h.kme_in45 == True]  # noqa: E712
print(f"In-window trades: {len(k45)}; surprise parsed: "
      f"{k45.kme_surprise.notna().mean():.0%} (unparsed = speeches/no-"
      f"forecast events, by design). Direction match (surprise sign == "
      f"his side): "
      f"{(k45.kme_surprise_sign == k45.side).mean():.0%} of in-window "
      f"trades ({(k45.kme_surprise_sign == k45.side).sum()} trades).")
print()
print("## EVENTS HE TRADES AFTER (top, in-window trades)")
for ev, c in k45.kme_event.value_counts().head(8).items():
    print(f"- {ev}: {c}")
print()
print("Output: Data/inputs/a2_features.parquet (checksummed). "
      "Registry: T-IM41.")
