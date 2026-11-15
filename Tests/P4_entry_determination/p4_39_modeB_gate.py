#!/usr/bin/env python3
"""
p4_39_modeB_gate.py — P4.39: the quiet mode's gate — his score-5 signals vs the rest.
======================================================================================
Mode B = his entries whose best same-direction signal scored < 6 (94 entries; 51
at score 5). Question: within the SAME score stratum, what separates the quiet
signals he traded from the ones he ignored?
  1. Which of the 10 conditions his-B signals DO hold (the quiet mode's shape)
  2. AUC battery over continuous + NEW structural features (shadows, contraction
     run, tape/body ratios, time of day) - his-B vs other signals, score 4-5
  3. Any separation found -> a candidate mode-B gate, measured: his-B coverage,
     flag count, and profit with v9-B exits (user-mandated table)

RUN: python3 Tests/P4_entry_determination/p4_39_modeB_gate.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_4_probes import boot_ci                           # noqa: E402
from p4_31_profit_v9 import run_leg, ARMS                 # noqa: E402
from p4_33_losscuts import month_ctx, row                 # noqa: E402

FEATS = ["mins_since", "flow5", "flow15", "edge_tk", "body_r", "tape_r", "lag15_r",
         "tod", "ush_tk", "lsh_tk", "shadow_r", "contr_n"]
CONDS = [f"k{i}" for i in range(1, 11)]
CNAMES = ["news15", "zone3/5", "bigbody", "fasttape", "flow>2", "template",
          "edge24", "zone10", "not-exh", "vol-up"]


def label(repo, sig):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    sig = sig.copy(); sig["hisB"] = False; sig["hisA"] = False
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        sm = sig[sig.month == month]
        comp = sm.comp_ns.to_numpy(np.int64); dirs = sm.direction.to_numpy()
        sc = sm.score.to_numpy()
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        for _, t in e_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            want = "bullish" if t.side == "long" else "bearish"
            md = (comp >= en - 5 * 60_000_000_000) & (comp < en) & (dirs == want)
            if md.any():
                idx = np.flatnonzero(md)
                best = idx[np.argmax(sc[idx])]
                col = "hisA" if sc[best] >= 6 else "hisB"
                sig.loc[sm.index[best], col] = True
    return sig


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = label(repo, pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv")))
    q = sig[(sig.score >= 4) & (sig.score <= 5)]
    T, K = q[q.hisB], q[~q.hisB & ~q.hisA]
    print(f"quiet stratum (score 4-5): {len(q)} signals | his-B {len(T)} | others {len(K)}")

    print("\n1. which conditions his quiet signals HOLD (share true, his-B vs others):")
    for c, name in zip(CONDS, CNAMES):
        print(f"  {name:10s} {T[c].mean():5.0%} vs {K[c].mean():5.0%}"
              f"{'  <-- differs' if abs(T[c].mean() - K[c].mean()) > 0.15 else ''}")

    print("\n2. AUC battery (his-B vs others, same stratum; * = CI excludes 0.5):")
    found = []
    for f in FEATS:
        a_t, a_k = T[f].astype(float), K[f].astype(float)
        if a_t.notna().sum() < 20:
            continue
        from p4_4_probes import rank_auc
        a = rank_auc(a_t, a_k)
        ci = boot_ci(a_t, a_k) if a > 0.5 else boot_ci(-a_t, -a_k)
        star = "*" if ci["clears"] else " "
        print(f"  {f:12s} AUC {a:.3f}{star} [{ci['lo']:.3f},{ci['hi']:.3f}]")
        if ci["clears"]:
            found.append((f, a))

    # 3. candidate gate from whatever separated; fallback = the conditions profile
    #    (defined AFTER seeing 1&2 - recorded as exploratory, honest)
    print("\n3. candidate gate test (exploratory, defined after the profile):")
    gate = (sig.score.between(4, 5) & sig.k2 & sig.k9 & sig.k10 &
            (sig.tod.between(13.5, 18)))
    g = sig[gate]
    print(f"   gate = score 4-5 AND zone3/5 AND not-exhausted AND vol-up AND 13:30-18:00 UTC")
    print(f"   flags: {len(g)} | catches his-B: {int(g.hisB.sum())}/{int(sig.hisB.sum())} "
          f"| his share of flags: {g.hisB.mean():.1%} (stratum base {q.hisB.mean():.1%})")
    p = dict(ARMS["B (momentum ladder)"])
    pnl = []
    for month, sym in MONTHS:
        bars, pre, prev, lo, hi = month_ctx(es, month, sym)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy(); o = bars.open.to_numpy()
        busy = -1
        for _, r in g[g.month == month].sort_values("comp_ns").iterrows():
            ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
            if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
                continue
            fb = ib + 1
            if fb >= len(bts) or not bars.rth.iloc[fb] or fb <= busy:
                continue
            mv = cl[ib] - cl[ib - 5]
            if mv == 0:
                continue
            long = mv > 0
            uref = r.uref if np.isfinite(r.uref) else None
            fill = o[fb]
            px, xi, reason, _ = run_leg(bars, pre, fb, fill, long, 1.0, p, fb, uref)
            tot = (px - fill) if long else (fill - px)
            if reason == "faststop":
                px2, xi2, _, _ = run_leg(bars, pre, xi, px, not long, 1.0, p, xi + 1, uref)
                tot += (px2 - px) if (not long) else (px - px2)
                xi = xi2
            pnl.append(tot)
            busy = xi + 5
    print("\n| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    print(row("mode-B gate candidate (v9-B exits)", pnl))
    print("| mode-A standalone (reference) | 116 | 41% | +6.09 / -3.66 | +43.2 pts |")
    print("\nREAD: parts 1-2 are the evidence; part 3 is exploratory (defined after")
    print("seeing them) and would need freezing + out-of-sample like everything else.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
