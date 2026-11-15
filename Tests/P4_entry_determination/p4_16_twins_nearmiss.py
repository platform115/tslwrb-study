#!/usr/bin/env python3
"""
p4_16_twins_nearmiss.py — P4.16: (3) matched twins, (5) near-miss anatomy.
===========================================================================
3. MATCHED TWINS (case-control matching): for every taken signal, find its 5
   most similar SKIPPED signals on the features the v5 rule already uses
   (event recency, body vs yesterday, tape vs today, 5-min flow, 3m/5m zone,
   template), same month, z-scored euclidean distance. Then compare the taken
   signal to its twins on the OTHER features. Whatever still separates a trade
   from its near-identical untaken twins is something the rule does not capture.
   Read per feature: mean paired difference + share of pairs positive + a sign
   test (binomial, two-sided) - plain, deterministic.
5. NEAR-MISS ANATOMY: the strongest false alarms - skipped signals with v5
   score >= 4 (stricter than the rule's own cutoff 3). Who are they? Time of
   day, how long until/since his nearest entry that day, that day's trade
   count (absence proxy), the tree's flow ceiling, distance to reaction edge.

RUN: python3 Tests/P4_entry_determination/p4_16_twins_nearmiss.py            (repo root)
     python3 Tests/P4_entry_determination/p4_16_twins_nearmiss.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

MATCH_ON = ["mins_cap", "body_r_prev", "path5_r_tmed", "flow_fill", "ov35", "c6f"]
COMPARE = ["en05_tf1_edge_tk", "flow_15m", "en08_vwap_z", "en08_net_5m_tk",
           "tod_ct", "ov10", "ov15", "path3_r_tmed", "path10_r_tmed",
           "body_r_twrb", "body_r_tbar", "tf1_has_react"]
K_TWINS = 5


def sign_test_p(wins, n):
    """Two-sided binomial sign test, p(0.5)."""
    if n == 0:
        return np.nan
    k = min(wins, n - wins)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(p, 1.0)


def v5_score(df):
    mins = df.mins_since_all.to_numpy(float)
    c1 = (mins >= 0) & (mins <= 15)
    c2 = df.ov3.to_numpy(bool) | df.ov5.to_numpy(bool)
    c3 = df.body_tk.to_numpy(float) >= 2.0 * df.ref_body_tk.to_numpy(float)
    c4 = df.path5.to_numpy(float) >= 1.5 * df.tmed_path5.to_numpy(float)
    c5 = df.flow_5m.fillna(-9e9).to_numpy(float) > 2.0
    c6 = df.c6_template.to_numpy(bool)
    return (c1.astype(int) + c2.astype(int) + c3.astype(int) + c4.astype(int)
            + c5.astype(int) + c6.astype(int))


def prep():
    df = pd.read_csv(os.path.join(HERE, "p4_12_features.csv"))
    df["mins_cap"] = df.mins_since_all.clip(upper=300)
    df["flow_fill"] = df.flow_5m.fillna(0)
    df["ov35"] = (df.ov3 | df.ov5).astype(float)
    df["c6f"] = df.c6_template.astype(float)
    df["score_v5"] = v5_score(df)
    return df


def run(repo):
    df = prep()
    print(f"signals={len(df)} taken={int(df.taken.sum())}")

    # ---- 3. matched twins ----
    print("\n===== 3. MATCHED TWINS: what still differs from near-identical untaken signals =====")
    diffs = {c: [] for c in COMPARE}
    for month in df.month.unique():
        d = df[df.month == month]
        T = d[d.taken]; K = d[~d.taken]
        mu = d[MATCH_ON].mean(); sd = d[MATCH_ON].std(ddof=0).replace(0, 1)
        Zt = ((T[MATCH_ON] - mu) / sd).to_numpy()
        Zk = ((K[MATCH_ON] - mu) / sd).to_numpy()
        for i in range(len(T)):
            dist = np.sqrt(((Zk - Zt[i]) ** 2).sum(axis=1))
            tw = np.argsort(dist)[:K_TWINS]
            for c in COMPARE:
                tv = T[c].iloc[i]
                kv = K[c].iloc[tw].astype(float).mean()
                if np.isfinite(tv) and np.isfinite(kv):
                    diffs[c].append(float(tv) - float(kv))
    print(f"{'feature':18s} {'mean taken-twin diff':>21} {'taken higher':>13} {'sign test p':>12}")
    for c in COMPARE:
        a = np.array(diffs[c])
        if len(a) < 30:
            continue
        wins = int((a > 0).sum()); n = int((a != 0).sum())
        p = sign_test_p(wins, n)
        mark = " <-- differs" if p < 0.01 else ""
        print(f"{c:18s} {a.mean():>21.2f} {wins/max(n,1):>12.0%} {p:>12.4f}{mark}")

    # ---- 5. near-miss anatomy ----
    print("\n===== 5. NEAR-MISSES: skipped signals with v5 score >= 4 (the strongest false alarms) =====")
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc"])
    en_ns = np.sort(pd.DatetimeIndex(ep.first_entry_utc).as_unit("ns").asi8)
    en_day = pd.to_datetime(pd.Series(en_ns)).dt.date.astype(str)
    day_counts = en_day.value_counts()
    nm = df[(~df.taken) & (df.score_v5 >= 4)].copy()
    tk = df[df.taken & (df.score_v5 >= 4)].copy()
    print(f"near-misses: {len(nm)}  (taken at the same score level: {len(tk)})")
    for d_ in (nm, tk):
        j = np.searchsorted(en_ns, d_.comp_ns.to_numpy(np.int64))
        prev = np.where(j > 0, d_.comp_ns.to_numpy(np.int64) - en_ns[np.clip(j - 1, 0, None)], np.nan)
        nxt = np.where(j < len(en_ns), en_ns[np.clip(j, 0, len(en_ns) - 1)] - d_.comp_ns.to_numpy(np.int64), np.nan)
        d_["mins_to_nearest_entry"] = np.nanmin(np.c_[prev, nxt], axis=1) / 60e9
        d_["day"] = pd.to_datetime(d_.comp_ns).dt.date.astype(str)
        d_["day_trades"] = d_.day.map(day_counts).fillna(0)
    q = lambda s: s.dropna().quantile([.25, .5, .75]).round(1).tolist()
    for name, d_ in [("near-miss", nm), ("taken@4+", tk)]:
        print(f"  {name:10s}: hour-of-day {q(d_.tod_ct)} | mins to his nearest entry {q(d_.mins_to_nearest_entry)}"
              f" | that day's trade count {q(d_.day_trades)}")
        print(f"             15-min flow {q(d_.flow_15m)} (tree ceiling ~4.6) | edge dist {q(d_.en05_tf1_edge_tk)} tk"
              f" | share with 15-min flow > 4.6: {(d_.flow_15m > 4.6).mean():.0%}")
    nm.to_csv(os.path.join(HERE, "p4_16_near_misses.csv"), index=False)
    print("\nREAD: twins isolate what the rule misses; near-misses suggest veto conditions.")
    print("Both descriptive, search set. Anything promising becomes a rule for validation.")


def selftest():
    assert abs(sign_test_p(5, 10) - 1.0) < 1e-9
    assert sign_test_p(10, 10) == comb(10, 0) / 2 ** 10 * 2
    d = prep()
    assert d.score_v5.between(0, 6).all() and len(d) == 1865
    print("=== SELF-TEST ===\n  sign test + v5 score bounds OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
