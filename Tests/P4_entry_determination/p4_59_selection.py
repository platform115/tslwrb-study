#!/usr/bin/env python3
"""
p4_59_selection.py — P4.59 / Strategy 2: signals he took vs signals he didn't.
===============================================================================
Universe: every score>=6 completion in the training months (886). TAKEN = one
of his Group A entries follows within 5 min, same direction (~10% base rate).
Features, three families:
  OLD (bar-based, from the signal table): score, flow5/15, mins_since, edge_tk,
    body_r, tape_r, lag15_r, tod, shadows, contraction
  NEW per-second, at the completion second (toward signal direction): mid move
    last 10/30/60 s, signed volume last 10/30/60 s, 60 s range
  NEW level state: tick distance to nearest live knowable level, seconds since
    that level set was last touched
Output: AUC per feature (bootstrap CI; * = CI clears 0.5), condition-share
table, and ONE exploratory candidate gate (declared as defined after looking).
Training months only; validation locked.

RUN: python3 Tests/P4_entry_determination/p4_59_selection.py              (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_4_probes import rank_auc, boot_ci              # noqa: E402
from p4_49_sec_engine import Ctx                       # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_53_anchor_sweep import month_anchors           # noqa: E402

TICK = 0.25
LIFE_NS = 60 * int(60e9)
KNOWABLE = ["firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]
OLD = ["score", "mins_since", "flow5", "flow15", "edge_tk", "body_r", "tape_r",
       "lag15_r", "tod", "ush_tk", "lsh_tk", "shadow_r", "contr_n"]


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    rows = []
    for month, sym in MONTHS:
        cx = Ctx(repo, month, True)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        pts = sorted(sum((W[k] for k in KNOWABLE), []))
        lt = np.array([t for t, _ in pts], dtype=np.int64)
        lp = np.array([p for _, p in pts])
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64)
        mids = f.mid.to_numpy(float)
        sv = (f.buyv - f.sellv).to_numpy(float)
        csv_ = np.concatenate([[0.0], np.cumsum(sv)])
        near = np.zeros(len(secs), bool)
        for i in range(len(secs)):
            s_ns = secs[i] * 10**9
            a, b = np.searchsorted(lt, s_ns - LIFE_NS), np.searchsorted(lt, s_ns, side="right")
            if b > a and np.abs(mids[i] - lp[a:b]).min() / TICK <= 1:
                near[i] = True
        last_touch = np.full(len(secs), -10**18, dtype=np.int64)
        lts = -10**18
        for i in range(len(secs)):
            if near[i]:
                lts = secs[i]
            last_touch[i] = lts

        def mid_at(s):
            i = np.searchsorted(secs, s, "right") - 1
            return mids[i] if i >= 0 else np.nan

        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, True, e_m)
        eA = e_m[g == "A"]
        his_s = np.array([pd.Timestamp(x).value // 10**9 for x in eA.first_entry_utc], dtype=np.int64)
        his_d = np.array([1 if s == "long" else -1 for s in eA.side])
        sg = cx.sig[cx.sig.score >= 6]
        for _, r in sg.iterrows():
            s0 = int(r.comp_ns) // 10**9
            d = 1 if r.direction == "bullish" else -1
            taken = bool((((his_s - s0) >= 0) & ((his_s - s0) <= 300) & (his_d == d)).any())
            i = np.searchsorted(secs, s0, "right") - 1
            m0 = mid_at(s0)
            a60, b0 = np.searchsorted(secs, s0 - 60), np.searchsorted(secs, s0, "right")
            i10, i30, i60 = (np.searchsorted(secs, s0 - w) for w in (10, 30, 60))
            row = dict(month=month, taken=taken,
                       sec_mv10=d * (m0 - mid_at(s0 - 10)) / TICK,
                       sec_mv30=d * (m0 - mid_at(s0 - 30)) / TICK,
                       sec_mv60=d * (m0 - mid_at(s0 - 60)) / TICK,
                       sec_vol10=d * (csv_[b0] - csv_[i10]),
                       sec_vol30=d * (csv_[b0] - csv_[i30]),
                       sec_vol60=d * (csv_[b0] - csv_[i60]),
                       sec_rng60=(mids[a60:b0].max() - mids[a60:b0].min()) / TICK if b0 > a60 else np.nan,
                       lvl_dist=np.inf, lvl_touch_age=np.inf)
            if i >= 0:
                s_ns = s0 * 10**9
                a, b = np.searchsorted(lt, s_ns - LIFE_NS), np.searchsorted(lt, s_ns, side="right")
                if b > a:
                    row["lvl_dist"] = float(np.abs(m0 - lp[a:b]).min() / TICK)
                if last_touch[i] > -10**17:
                    row["lvl_touch_age"] = float(s0 - last_touch[i])
            for k in OLD + [f"k{j}" for j in range(1, 11)]:
                if k in r:
                    row[k] = r[k]
            rows.append(row)
    d = pd.DataFrame(rows)
    T, K = d[d.taken], d[~d.taken]
    print(f"score>=6 signals: {len(d)} | he took {len(T)} ({len(T)/len(d):.0%}) | didn't: {len(K)}\n")
    print("AUC battery (taken vs not; * = bootstrap CI clears 0.5):")
    print("| Feature | AUC | CI | Taken median | Not-taken median |")
    print("|---|---|---|---|---|")
    feats = ["sec_mv10", "sec_mv30", "sec_mv60", "sec_vol10", "sec_vol30", "sec_vol60",
             "sec_rng60", "lvl_dist", "lvl_touch_age"] + OLD
    found = []
    for k in feats:
        a_t = T[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
        a_k = K[k].replace([np.inf, -np.inf], np.nan).astype(float).dropna()
        if len(a_t) < 20:
            continue
        auc = rank_auc(a_t, a_k)
        ci = boot_ci(a_t, a_k) if auc > 0.5 else boot_ci(-a_t, -a_k)
        star = "*" if ci["clears"] else " "
        print(f"| {k} | {auc:.3f}{star} | [{ci['lo']:.3f},{ci['hi']:.3f}] "
              f"| {a_t.median():.2f} | {a_k.median():.2f} |")
        if ci["clears"]:
            found.append((k, auc))
    print("\nCondition flags (share true, taken vs not):")
    print("| Condition | Taken | Not taken |")
    print("|---|---|---|")
    names = ["news15", "zone3/5", "bigbody", "fasttape", "flow>2", "template",
             "edge24", "zone10", "not-exh", "vol-up"]
    for j, nm in enumerate(names, 1):
        k = f"k{j}"
        if k in d:
            print(f"| {nm} | {T[k].mean():.0%} | {K[k].mean():.0%} |")
    print(f"\nsignificant features: {[k for k, _ in found]}")
    d.to_csv(os.path.join(HERE, "p4_59_signals_labeled.csv"), index=False)
    days = 47
    print("\nEXPLORATORY gates (defined after the battery - recorded as such):")
    print("| Gate | Signals kept | Per day | His taken kept | Precision |")
    print("|---|---|---|---|---|")
    gates = {
        "score >= 7": d.score >= 7,
        "score >= 7 AND flow>2 (k5)": (d.score >= 7) & d.k5,
        "score >= 7 AND k5 AND fast tape (k4)": (d.score >= 7) & d.k5 & d.k4,
        "score >= 7 AND k5 AND 60s range >= 18tk": (d.score >= 7) & d.k5 & (d.sec_rng60 >= 18),
        "score >= 8 AND k5": (d.score >= 8) & d.k5,
    }
    for nm, m in gates.items():
        kept = d[m]
        print(f"| {nm} | {len(kept)} | {len(kept)/days:.1f} | "
              f"{int(kept.taken.sum())}/{int(d.taken.sum())} | {kept.taken.mean():.0%} |")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
