#!/usr/bin/env python3
"""
p4_35_selection_alignment.py — P4.35: priority 1 — where do his entries fall vs our rule?
==========================================================================================
Decompose all 313 discovery entries into:
  A  signal-matched AND flagged (a 1m desk-window WRB signal in the 5 min before
     his entry, same direction, scoring >= 6)             <- the rule's overlap
  B  signal-matched but UNDER-SCORED (< 6): how short? which of the 10 conditions
     were the misses - a point away, or a different animal?
  C  NOT signal-matched at all: was there any 1m WRB near the entry (any
     direction / wrong direction / none)? A 3m WRB instead? -> is there a second
     trigger type our signal definition never sees?
Plus the KME-list gate check: his entries' timing vs HIS OWN posted daily lists
(his_kme_times.parquet) vs the all-events calendar - does HIS list time his
entries better than the generic calendar?

RUN: python3 Tests/P4_entry_determination/p4_35_selection_alignment.py      (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies                # noqa: E402
from p4_2b_zone_mtf import resample                       # noqa: E402
from p4_3_confluence_news import news_sets                # noqa: E402

CONDS = ["c1_kme_born15", "c2_small_tf_zone_any", "c3_body", "c4_tape",
         "c5_flow", "c6_template", "c7_edge", "c8_ov10", "c9_not_exh", "c10_vol_up"]


def cond_frame(sig):
    """Reconstruct the 10 v6 conditions as booleans from the p4_19 table columns."""
    d = pd.DataFrame(index=sig.index)
    d["c1_kme_born15"] = (sig.mins_since_all >= 0) & (sig.mins_since_all <= 15)
    d["c2_small_tf_zone_any"] = sig.ov3.astype(bool) | sig.ov5.astype(bool)
    d["c3_body"] = sig.body_tk >= 2.0 * sig.ref_body_tk
    d["c4_tape"] = sig.path5 >= 1.5 * sig.tmed_path5
    d["c5_flow"] = sig.flow_5m.fillna(-9e9) > 2.0
    d["c6_template"] = sig.c6_template.astype(bool)
    d["c7_edge"] = sig.en05_tf1_edge_tk.fillna(9e9) <= 24
    d["c8_ov10"] = sig.ov10.astype(bool)
    d["c9_not_exh"] = ~(sig.flow_15m > 4.6).fillna(False)
    d["c10_vol_up"] = sig.c10_vol_up.astype(bool)
    return d.fillna(False)


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    sig = pd.read_csv(os.path.join(HERE, "p4_19_v6_table.csv"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    his = pd.read_parquet(os.path.join(repo, "Data/inputs/his_kme_times.parquet"))
    his_ns = np.sort(his.ts_utc_ns.to_numpy(np.int64))
    ev_all = news_sets(repo)["all"]
    conds = cond_frame(sig)
    groups = {"A flagged": 0, "B underscored": 0, "C unmatched": 0}
    b_scores, b_missing, c_kind = [], [], []
    kme_rows = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        sm = sig[sig.month == month]
        comp = sm.comp_ns.to_numpy(np.int64)
        dirs = sm.direction.to_numpy()
        scores = sm.score_v6.to_numpy()
        cm = conds.loc[sm.index]
        bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                  (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        w1 = wrb_bodies(bars)                       # all-session 1m WRBs
        w1c = pd.DatetimeIndex(w1.ts_event).as_unit("ns").asi8 + 60_000_000_000
        w1d = w1.direction.to_numpy()
        w3 = wrb_bodies(resample(bars, 3))
        w3c = pd.DatetimeIndex(w3.ts_event).as_unit("ns").asi8 + 180_000_000_000
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        for _, t in e_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            want = "bullish" if t.side == "long" else "bearish"
            m = (comp >= en - 5 * 60_000_000_000) & (comp < en) & (dirs == want)
            if m.any():
                best = int(np.flatnonzero(m)[np.argmax(scores[np.flatnonzero(m)])])
                if scores[best] >= 6:
                    groups["A flagged"] += 1
                else:
                    groups["B underscored"] += 1
                    b_scores.append(int(scores[best]))
                    b_missing.append(~cm.iloc[best].to_numpy())
            else:
                groups["C unmatched"] += 1
                near1 = (w1c >= en - 5 * 60_000_000_000) & (w1c <= en + 60_000_000_000)
                if (near1 & (w1d == want)).any():
                    c_kind.append("1m WRB right dir (missed by signal def)")
                elif near1.any():
                    c_kind.append("1m WRB wrong direction only")
                elif ((w3c >= en - 6 * 60_000_000_000) & (w3c <= en + 60_000_000_000)).any():
                    c_kind.append("3m WRB nearby (no 1m)")
                else:
                    c_kind.append("no WRB at all")
            # KME timing: his list vs full calendar
            i = int(np.searchsorted(his_ns, en)) - 1
            mins_his = (en - his_ns[i]) / 60e9 if i >= 0 else np.inf
            j = int(np.searchsorted(ev_all, en)) - 1
            mins_cal = (en - ev_all[j]) / 60e9 if j >= 0 else np.inf
            kme_rows.append(dict(mins_his=mins_his, mins_cal=mins_cal))
    n = sum(groups.values())
    print(f"=== his {n} discovery entries vs the rule ===")
    for g, v in groups.items():
        print(f"  {g:16s}: {v:4d} ({v/n:.0%})")
    bs = pd.Series(b_scores)
    print(f"\nB (underscored) score distribution: " +
          ", ".join(f"{k}:{v}" for k, v in bs.value_counts().sort_index(ascending=False).items()))
    miss = pd.DataFrame(b_missing, columns=CONDS).mean().sort_values(ascending=False)
    print("B: share of underscored signals MISSING each condition:")
    for c, v in miss.items():
        print(f"  {c:22s} {v:.0%}")
    print("\nC (unmatched) nearest-trigger breakdown:")
    for k, v in pd.Series(c_kind).value_counts().items():
        print(f"  {k:40s} {v:4d}")
    k = pd.DataFrame(kme_rows)
    print(f"\nKME gate: entries within 30 min of HIS posted list: {(k.mins_his <= 30).mean():.0%}"
          f" | of ANY calendar event: {(k.mins_cal <= 30).mean():.0%}")
    print(f"  (his lists exist for only some days; within 60 min: {(k.mins_his <= 60).mean():.0%} vs {(k.mins_cal <= 60).mean():.0%})")
    print("\nREAD: search-mode decomposition; alignment changes get frozen and re-tested.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
