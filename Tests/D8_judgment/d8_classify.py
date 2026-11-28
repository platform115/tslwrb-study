#!/usr/bin/env python3
"""
d8_classify.py — D-8 STEP 0b-2: group-classify his episodes in the
quarantined months (2022-05, 2026-03) with the frozen A3 recipes.
DERIVES FROM (R-9 lineage): Tests/A2_measurement/a2_2_measurement.py
(T-IM41) structure_fields + kme phase; Tests/D29_m8/remint_sims.py
ctx_row/np_ (the HISW/HISQ recipes). Machinery copied verbatim.
R-9 CONTROL + STAMP-DRIFT FINDING (2026-11-28, flagged to J):
a2_features was built BEFORE the F-36 stamp fix and was never
re-minted - the groups of record (62/151) sit on PRE-fix squeeze
stamps. Post-fix re-classification of the certified months flips
exactly 5 of 307 episodes (ctx other<->squeeze; np_ identical on
all 307): W 62 -> 61, Q 151 -> 149. The control therefore pins
the POST-fix values: 307 joined, exactly 5 ctx flips, W/Q 61/149,
np_ mismatches 0. Abort on anything else. J decides at the G2-4
review whether the his-side re-mint becomes a registry item.
QUARANTINE HANDLING (J's preserve decision, 2026-11-28): the output
file holds every label, but this script PRINTS ONLY the G2 (squeeze
+news) and G3 (squeeze quiet) counts for the new months - the
unmined-group counts are written, not read, not reported.
RUN: python3 Tests/D8_judgment/d8_classify.py           (repo root)
OUT: Tests/D8_judgment/d8_his_groups.parquet
"""
import os, sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p6_24_s6_3_selectors import interact_edges              # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

FAMS = (("REA", 15), ("SQZ", 15), ("GAP", 5), ("SHD", 5))
FRESH_S = 5
EV_NS = np.asarray(news_sets(".")["all"], dtype=np.int64)  # ns

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")


def structure_fields(R, sd, t64, side, secs, mids, j):
    out = {}
    px = mids[j]
    for fam, M in FAMS:
        E = interact_edges(R, sd, t64, fam, M, secs, mids, side)
        out[f"{fam}_interact"] = bool(E)
    return out


def np_of(t):
    kk = int(np.searchsorted(EV_NS, t * 10**9, "right")) - 1
    mins = (t * 10**9 - EV_NS[kk]) / 60e9 if kk >= 0 else np.nan
    if np.isfinite(mins) and mins <= 5:
        return "burst"
    if np.isfinite(mins) and mins <= 45:
        return "window"
    return "none"


def ctx_of(row):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if row[f"{f_}_interact"]:
            return "squeeze" if f_ == "SQZ" else "other"
    return "other"


def classify(gt, months):
    rows = []
    for month in sorted(months):
        nxt = (pd.Timestamp(month + "-01") + pd.offsets.MonthBegin(1)
               ).strftime("%Y-%m-%d")
        bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < nxt)
               ].reset_index(drop=True)
        R = Resolver(bm, zr)
        fl = pd.read_parquet(
            f"Data/inputs/flow_per_sec_{month}_full.parquet")
        secs = fl.sec.to_numpy(np.int64)
        mids = fl.mid.to_numpy(float)
        gm = gt[gt.month == month]
        for _, r in gm.iterrows():
            t = int(r.entry_msg_s)
            d_ = 1 if r.side == "long" else -1
            j = int(np.searchsorted(secs, t, "right")) - 1
            fresh = j >= 0 and (t - secs[j]) <= FRESH_S
            row = dict(episode_id=int(r.episode_id), month=month,
                       sec=t, side=d_, data_fresh=fresh)
            if fresh and j >= 4100:
                t64 = np.datetime64(t, "s")
                row.update(structure_fields(R, r.session_date, t64,
                                            d_, secs, mids, j))
                row["np_"] = np_of(t)
                row["ctx"] = ctx_of(row)
            else:
                row["np_"] = None
                row["ctx"] = None
            rows.append(row)
    return pd.DataFrame(rows)


# ---------- R-9 CONTROL on the certified months ----------
gt_cert = pd.read_parquet("Data/inputs/a2_ground_truth.parquet")
C = classify(gt_cert, ["2022-02", "2025-10"])
F = pd.read_parquet("Data/inputs/a2_features.parquet")
F = F[(F.who == "his") & F.data_fresh].copy()
mm = F.kme_mins_since
F["np_"] = np.where(np.isfinite(mm) & (mm <= 5), "burst",
                    np.where(np.isfinite(mm) & (mm <= 45), "window",
                             "none"))
def ctx_row(r):
    for f_ in ("SQZ", "REA", "GAP", "SHD"):
        if r[f"{f_}_interact"]:
            return "squeeze" if f_ == "SQZ" else "other"
    return "other"
F["ctx"] = F.apply(ctx_row, axis=1)
n_w = len(F[(F.ctx == "squeeze") & (F.np_ == "window")])
n_q = len(F[(F.ctx == "squeeze") & (F.np_ == "none")])

# join key: (month, sec, side) - unique per his trade (episode_id
# restarts per month in these tables and is NOT a safe key)
Cf = C[C.data_fresh].set_index(["month", "sec", "side"])
Ff = F.set_index(["month", "sec", "side"])
join = Cf.join(Ff[["ctx", "np_"]], rsuffix="_cert", how="inner")
mism = join[(join.ctx != join.ctx_cert) | (join.np_ != join.np__cert)]
m_w = len(Cf[(Cf.ctx == "squeeze") & (Cf.np_ == "window")])
m_q = len(Cf[(Cf.ctx == "squeeze") & (Cf.np_ == "none")])
np_mism = int((join.np_ != join.np__cert).sum())
if (len(join), len(mism), m_w, m_q, n_w, n_q, np_mism) !=         (307, 5, 61, 149, 62, 151, 0):
    print(f"# D8 CLASSIFY ABORTED - R-9 CONTROL FAILED: joined "
          f"{len(join)} (need 307); ctx flips {len(mism)} (need 5, "
          f"the recorded stamp drift); np_ flips {np_mism} (need 0); "
          f"mine W/Q {m_w}/{m_q} (need 61/149); cert W/Q {n_w}/{n_q}"
          f" (need 62/151)")
    print(mism.head(10).to_string())
    sys.exit(1)
print(f"R-9 CONTROL PASS (post-fix pins): 307 joined; exactly the 5 "
      f"recorded stamp-drift ctx flips; np_ identical; W/Q 61/149 "
      f"post-fix vs 62/151 pre-fix record")

# ---------- new months ----------
gt_new = pd.read_parquet("Tests/D8_judgment/d8_ground_truth.parquet")
N = classify(gt_new[gt_new.month.isin(["2022-05", "2026-03"])],
             ["2022-05", "2026-03"])
N.to_parquet("Tests/D8_judgment/d8_his_groups.parquet", index=False)
for mo, g in N.groupby("month"):
    gf = g[g.data_fresh]
    g2 = len(gf[(gf.ctx == "squeeze") & (gf.np_ == "window")])
    g3 = len(gf[(gf.ctx == "squeeze") & (gf.np_ == "none")])
    rest = len(gf) - g2 - g3
    print(f"{mo}: episodes {len(g)}, fresh {len(gf)} | "
          f"G2 (squeeze+news) {g2} | G3 (squeeze quiet) {g3} | "
          f"other groups {rest} (labels written, UNREAD per J)")
print("D8 CLASSIFY 0b DONE")
