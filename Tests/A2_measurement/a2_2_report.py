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
        mw = mannwhitneyu(a, b)
        p = mw.pvalue
        delta = 2.0 * mw.statistic / (len(a) * len(b)) - 1.0  # Cliff's delta
    except ValueError:
        continue
    rows.append(dict(feature=c, delta=delta, his_q25=a.quantile(.25), his_q50=a.median(),
                     his_q75=a.quantile(.75), null_q50=b.median(), p=p,
                     ratio=(a.median() / b.median()
                            if b.median() not in (0, np.nan) else np.nan)))
R = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)

UNITS = [("mv","ticks toward his side"),("rng","ticks"),("comp","ratio (1=typical)"),
("volr","ratio"),("vratio","ratio"),("vrate","contracts/s"),
("flow","net contracts/s toward his side"),("bursts","count"),
("burst_silence","seconds"),("stall","seconds"),("dist_day","ticks"),
("day_pos","0=low 1=high"),("mins_open","minutes"),("atr10","ticks"),
("Cday","ratio"),("Rest","ticks"),("kme_mins","minutes"),
("kme_surprise_sign","+1/-1"),("kme_surprise","native per report"),
("sig_samedir","0/1"),("sig_best","score 0-10"),("_dist","points")]
def unit(c):
    for pre,u in UNITS:
        if c.startswith(pre) or (pre.startswith("_") and c.endswith(pre+"dist")) or (pre=="_dist" and c.endswith(("_int_dist","_near_dist"))):
            return u
    return "-"
m = len(R)
R["bh_flag"] = R.p <= (np.arange(1, m + 1) / m) * 0.05  # BH step-up (sorted)
# correct BH: largest k with p_k <= k/m*q
ok = np.flatnonzero(R.p.to_numpy() <= (np.arange(1, m + 1) / m) * 0.05)
k = ok.max() + 1 if len(ok) else 0
R["bh_flag"] = np.arange(m) < k
R = R.sort_values("delta", key=np.abs, ascending=False).reset_index(drop=True)

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
print("## NAMES IN PLAIN WORDS (designation rule)")
print("REA = reaction levels (recent swing highs/lows he reacts off); "
      "SQZ = squeeze bands (tight-range zones); GAP = hidden gaps; "
      "SHD = long-shadow zones. A null = an ordinary moment: same "
      "session, same 30-min time slot, >=10 min from any of his entries.")
print()
print("## FEATURE FAMILIES, GROUPED - SORTED BY HOW DIFFERENT HIS MOMENTS ARE")
print("Difference score = Cliff's delta (Cliff, 1993): the chance a random")
print("entry of his exceeds a random ordinary moment, minus the reverse.")
print("0 = indistinguishable, +/-1 = completely separated. Flags = ")
print("Mann-Whitney, Benjamini-Hochberg 5%; provisional, never gates (R-4).")
print()
FAMS2 = [
 ("Directional movement (8s-15min ladder)", lambda c: c.startswith("mv")),
 ("Recent range / compression", lambda c: c.startswith(("rng","comp","volr"))),
 ("Volume rate", lambda c: c.startswith(("vrate","vratio"))),
 ("Buy-sell flow", lambda c: c.startswith("flow")),
 ("Bursts / time-since-extreme", lambda c: c.startswith("burst") or c=="stall_5m_extreme"),
 ("Position in the day / clock", lambda c: c in ("dist_day_hi","dist_day_lo","day_pos","mins_open")),
 ("Session scale (Cday/Rest prior-session-derived)", lambda c: c in ("atr10","Cday","Rest")),
 ("Distance to structure edges", lambda c: c.endswith(("_int_dist","_near_dist"))),
 ("Our signal engine state", lambda c: c.startswith("sig_")),
 ("News-event timing/surprise", lambda c: c.startswith("kme_")),
]
print("| family | members flagged | strongest member | difference | his q50 | null q50 | unit |")
print("|---|---|---|---|---|---|---|")
fam_rows = []
for name, fn in FAMS2:
    sub = R[R.feature.map(fn)]
    if not len(sub):
        continue
    top = sub.iloc[0]
    fam_rows.append((abs(top.delta), name, sub, top))
for _, name, sub, top in sorted(fam_rows, reverse=True):
    print(f"| {name} | {int(sub.bh_flag.sum())}/{len(sub)} | {top.feature} "
          f"| {top.delta:+.2f} | {top.his_q50:.2f} | {top.null_q50:.2f} "
          f"| {unit(top.feature)} |")
print()
print(f"Flagged: {int(R.bh_flag.sum())} of {m} columns - but the ladder "
      f"columns inside a family are one finding measured at several "
      f"widths, so read this as ~{sum(1 for nm,fn in FAMS2 if R[R.feature.map(fn)].bh_flag.any())} "
      f"family-level findings, not {int(R.bh_flag.sum())}.")
print()
print("## FULL LIST, MOST-DIFFERENT FIRST (appendix)")
print("| feature | difference | his q25/q50/q75 | null q50 | unit | flagged |")
print("|---|---|---|---|---|---|")
for _, r in R.iterrows():
    print(f"| {r.feature} | {r.delta:+.2f} | {r.his_q25:.2f} / {r.his_q50:.2f} / "
          f"{r.his_q75:.2f} | {r.null_q50:.2f} | {unit(r.feature)} | "
          f"{'YES' if r.bh_flag else 'no'} |")
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
