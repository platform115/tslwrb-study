#!/usr/bin/env python3
"""
p4_29_selection.py — P4.29: the selection gap — what he uses that the rule doesn't.
====================================================================================
USER (2026-11-15): "I think he's selecting better." His win rate on these months is
71-82%; every simulated config sits at 24-35%. Three questions, discovery months,
search-mode (findings become spec-v8 candidates, validated later):

A. WITHIN THE FLAGGED SET (v6 score >= 6): among signals the rule already likes,
   what separates the ones HE took from the ones he left? (AUC battery over every
   continuous feature; the rule's own inputs are controlled by construction.)
B. SIMULATED-OUTCOME STUDY: label each v2B-geometry simulated trade win/loss and
   ask which observable-at-entry conditions predicted OUR trade failing - these
   become skip-filters for the strategy, independent of imitating him.
C. DIRECTION AUTOPSY: for every flagged signal, the forward 9-bar net move =
   the "right" side in hindsight. Score candidate direction rules (5-min move /
   pressure sign / both-agree / 15-min move) and break accuracy down by hour,
   tape speed, and event recency to find where calls fail.

RUN: python3 Tests/P4_entry_determination/p4_29_selection.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_4_probes import rank_auc, boot_ci              # noqa: E402
from p4_2_entry_context import month_bounds, MONTHS    # noqa: E402

FEATS = ["mins_since_all", "body_tk", "body_r_prev", "body_r_tbar", "path3_r_tmed",
         "path5_r_tmed", "path10_r_tmed", "flow_5m", "flow_15m", "en08_vwap_z",
         "en08_net_5m_tk", "en05_tf1_edge_tk", "tod_ct", "twrb_med", "tbar_mean",
         "atr20_tk"]


def battery(T, K, label):
    print(f"\n----- {label} (n = {len(T)} vs {len(K)}) -----")
    out = []
    for c in FEATS:
        if c not in T or T[c].notna().sum() < 20 or K[c].notna().sum() < 20:
            continue
        a = rank_auc(T[c].astype(float), K[c].astype(float))
        out.append((abs(a - 0.5), a, c))
    out.sort(reverse=True)
    for _, a, c in out[:8]:
        ci = boot_ci(T[c].astype(float), K[c].astype(float)) if a > 0.5 else \
             boot_ci(-T[c].astype(float), -K[c].astype(float))
        star = "*" if ci["clears"] else " "
        d = "higher" if a > 0.5 else "lower"
        print(f"  {c:18s} AUC {a:.3f}{star} (group-1 {d}; CI [{ci['lo']:.3f},{ci['hi']:.3f}])")


def run(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_19_v6_table.csv"))
    f12 = pd.read_csv(os.path.join(HERE, "p4_12_features.csv"))
    add = [c for c in FEATS if c not in df.columns and c in f12.columns]
    df = df.merge(f12[["comp_ns"] + add], on="comp_ns", how="left")
    fl = df[df.score_v6 >= 6].copy()
    print(f"flagged signals (score>=6): {len(fl)}, he took {int(fl.taken.sum())}")

    # ---- A: within-flagged, taken vs skipped ----
    battery(fl[fl.taken], fl[~fl.taken], "A: flagged + HE TOOK vs flagged + he left")

    # ---- B: simulated outcomes (v2B geometry trades) ----
    tr = pd.read_csv(os.path.join(HERE, "p4_28_trades.csv"))     # v7 trades (have u, both months)
    tr["ts_ns"] = pd.DatetimeIndex(pd.to_datetime(tr.ts, utc=True)).as_unit("ns").asi8
    # join trade -> signal features via fill bar = signal comp minute
    df["comp_min_ns"] = df.comp_ns
    m = tr.merge(df, left_on="ts_ns", right_on="comp_min_ns", how="inner",
                 suffixes=("_t", ""))
    print(f"\nsimulated trades joined to signal features: {len(m)}/{len(tr)}")
    W, L = m[m.pnl_pts > 0], m[m.pnl_pts <= 0]
    battery(W, L, "B: our simulated WINNERS vs LOSERS (what predicts our trade failing)")

    # ---- C: direction autopsy ----
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    rows = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                  (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy()
        sub = fl[fl.month == month]
        for _, r in sub.iterrows():
            ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
            if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 15 or ib + 9 >= len(bts):
                continue
            fwd = cl[ib + 9] - cl[ib]
            if fwd == 0:
                continue
            mv5 = cl[ib] - cl[ib - 5]; mv15 = cl[ib] - cl[ib - 15]
            fl5 = r.flow_5m if np.isfinite(r.flow_5m) else np.nan
            # flow_5m is oriented by the SIGNAL's direction; re-orient to raw sign
            raw_flow = fl5 if r.direction == "bullish" else (-fl5 if np.isfinite(fl5) else np.nan)
            rows.append(dict(month=month, fwd_up=fwd > 0, mv5=mv5, mv15=mv15,
                             raw_flow=raw_flow, tod=r.tod_ct,
                             fast=r.path5_r_tmed, recent_ev=r.mins_since_all))
    c = pd.DataFrame(rows)
    print(f"\n----- C: direction autopsy on {len(c)} flagged signals (truth = 9-bar forward move) -----")
    rules = {
        "5-min move": c.mv5.apply(np.sign),
        "15-min move": c.mv15.apply(np.sign),
        "pressure sign": c.raw_flow.apply(lambda x: np.sign(x) if np.isfinite(x) else 0),
    }
    both = np.where((np.sign(c.mv5) == np.sign(c.raw_flow.fillna(0))) & (np.sign(c.mv5) != 0),
                    np.sign(c.mv5), 0)
    rules["both agree (else no call)"] = pd.Series(both, index=c.index)
    for name, s in rules.items():
        called = s != 0
        acc = ((s > 0) == c.fwd_up)[called].mean()
        print(f"  {name:26s}: accuracy {acc:.1%} on {called.sum()} calls ({called.mean():.0%} of signals)")
    print("\n  5-min-move accuracy by slice:")
    c["acc5"] = (np.sign(c.mv5) > 0) == c.fwd_up
    for lab, msk in [("morning (<10 CT)", c.tod < 10), ("midday (10-13)", (c.tod >= 10) & (c.tod < 13)),
                     ("late (>=13)", c.tod >= 13),
                     ("fast tape (>=1.5x)", c.fast >= 1.5), ("slow tape (<1.5x)", c.fast < 1.5),
                     ("event <=15 min", c.recent_ev <= 15), ("no recent event", c.recent_ev > 60)]:
        d = c[msk & (np.sign(c.mv5) != 0)]
        if len(d) > 30:
            print(f"    {lab:22s}: {d.acc5.mean():.1%} (n={len(d)})")
    print("\nREAD: search-mode on discovery; anything promising becomes a spec-v8 line and")
    print("is judged out-of-sample later.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
