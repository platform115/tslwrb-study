#!/usr/bin/env python3
"""
p4_4_probes.py — P4.4: formal tests of the taken-trade trigger candidates.
===========================================================================
FRAME (user, 2026-11-14): characterize the TAKEN trades; the skipped pool is used
only as the yardstick that says which taken-trade properties are distinctive, never
to explain individual skips. Rules extracted here get applied forward later.

PRE-REGISTERED (directions and primary cells declared BEFORE any statistic was run;
the descriptive splits in p4_3b were seen first and motivated WHICH features are
tested - that provenance is recorded in each registry row):
  T-EN01  kme_born (all-events width), W grid {5,15,30} min; PRIMARY CELL W=15.
          Direction: taken > skipped (taken signals more often complete soon after
          a scheduled event). 3 cells -> 3 trials for the trial count.
  T-EN02  n_htf_overlap_dir (primary) / n_htf_overlap (secondary cell): how many of
          3/5/10/15m have a zone overlapping the signal's zone (direction-matched).
          Direction: taken > skipped. 2 cells.
  T-EN03  body_tk (WRB body, ticks). Direction: taken > skipped. 1 cell.
  T-EN04  at_kme_level, REBUILT at the all-events width (the ge20-only version in
          p4_3b was likely too narrow - this is its fair retest): signal price
          inside/near an older (>=30 min) zone born within 30 min after ANY event.
          Direction: taken > skipped. 1 cell.
  Statistic: rank AUC (P(taken value > skipped value), ties = 0.5) + two-sample
  bootstrap 95% CI (seed 0, 10000 draws, resample each arm) - same read as the exit
  program. A cell CLEARS iff the CI excludes 0.5 in the pre-registered direction.
  Pooled both months = PRIMARY; per-month printed as robustness. CAVEAT recorded:
  signals cluster within days; the bootstrap treats them as independent, so CIs are
  somewhat optimistic - holdout years are the real arbiter.
RUN: python3 Tests/P4_entry_determination/p4_4_probes.py            (repo root)
     python3 Tests/P4_entry_determination/p4_4_probes.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SEED, B = 0, 10_000
TICK = 0.25
NEAR_TK = 8
LEVEL_MIN_AGE_MIN = 30


# ---- stats (same construction as the exit program's range_expansion.py) ----
def rank_auc(pos, neg):
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos = pos[~np.isnan(pos)]; neg = neg[~np.isnan(neg)]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    allv = np.concatenate([pos, neg]); order = np.argsort(allv, kind="mergesort")
    ranks = np.empty(len(allv)); ranks[order] = np.arange(1, len(allv) + 1)
    u, inv, cnt = np.unique(allv, return_inverse=True, return_counts=True)
    ssum = np.zeros(len(u)); np.add.at(ssum, inv, ranks); ranks = (ssum / cnt)[inv]
    rp = ranks[:len(pos)].sum()
    return (rp - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def boot_ci(pos, neg, seed=SEED, nb=B):
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos = pos[~np.isnan(pos)]; neg = neg[~np.isnan(neg)]
    a = rank_auc(pos, neg)
    if not np.isfinite(a):
        return dict(auc=np.nan, lo=np.nan, hi=np.nan, clears=False)
    rng = np.random.default_rng(seed); boot = np.empty(nb)
    for i in range(nb):
        boot[i] = rank_auc(pos[rng.integers(0, len(pos), len(pos))],
                           neg[rng.integers(0, len(neg), len(neg))])
    lo, hi = float(np.nanpercentile(boot, 2.5)), float(np.nanpercentile(boot, 97.5))
    return dict(auc=float(a), lo=lo, hi=hi, clears=(lo > 0.5))   # pre-reg direction: taken>skipped


def rebuild_at_level_all(df, repo):
    """at_kme_level at the ALL-events width (T-EN04)."""
    from p4_2_entry_context import month_bounds, MONTHS
    from p4_2b_zone_mtf import zone_tables
    from p4_3_confluence_news import news_sets
    ev = news_sets(repo)["all"]
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    out = np.zeros(len(df), bool)
    for month, sym in MONTHS:
        m = df.month == month
        if not m.any():
            continue
        lo, hi = month_bounds(month)
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        zt = zone_tables(bars_m, month)
        ts_l, b_l, t_l = [], [], []
        for tf, t in zt.items():
            z = t[t.has_whg.fillna(False)]
            zts = pd.DatetimeIndex(z.ts_event).as_unit("ns").asi8
            zc = zts + tf * int(60e9)
            idx = np.searchsorted(ev, zc, side="right") - 1
            mins = np.where(idx >= 0, (zc - ev[np.clip(idx, 0, None)]) / 60e9, np.nan)
            keep = (mins >= 0) & (mins <= 30)
            ts_l.append(zts[keep]); b_l.append(z.whg_bottom.to_numpy()[keep]); t_l.append(z.whg_top.to_numpy()[keep])
        kz_ts = np.concatenate(ts_l); kz_b = np.concatenate(b_l); kz_t = np.concatenate(t_l)
        sub = df[m]
        comp = pd.DatetimeIndex(pd.to_datetime(sub.ts_event, utc=True)).as_unit("ns").asi8 + int(60e9)
        px = sub.close.to_numpy()
        vals = np.zeros(len(sub), bool)
        for i, cns in enumerate(comp):
            sel = (kz_ts <= cns - LEVEL_MIN_AGE_MIN * 60e9) & (kz_ts >= cns - 2 * 86400e9)
            if not sel.any():
                continue
            d = np.where(px[i] < kz_b[sel], kz_b[sel] - px[i],
                         np.where(px[i] > kz_t[sel], px[i] - kz_t[sel], 0.0)) / TICK
            vals[i] = bool((d <= NEAR_TK).any())
        out[np.flatnonzero(m.to_numpy())] = vals
    return out


CELLS = [
    ("T-EN01", "kme_born_5_all",   "KME-born <=5 min (all events)", False),
    ("T-EN01", "kme_born_15_all",  "KME-born <=15 min (all) [PRIMARY]", True),
    ("T-EN01", "kme_born_30_all",  "KME-born <=30 min (all)", False),
    ("T-EN02", "n_htf_overlap_dir", "HTF zone overlap, direction-matched [PRIMARY]", True),
    ("T-EN02", "n_htf_overlap",    "HTF zone overlap, any direction", False),
    ("T-EN03", "body_tk",          "WRB body size (ticks) [PRIMARY]", True),
    ("T-EN04", "at_kme_level_all", "at older KME-born level (all events) [PRIMARY]", True),
]


def run(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_3b_signal_table.csv"))
    df["at_kme_level_all"] = rebuild_at_level_all(df, repo)
    T, K = df[df.taken], df[~df.taken]
    print(f"[frame] taken={len(T)} skipped={len(K)} (pooled Oct-2025 + Feb-2022)\n")
    print(f"{'id':7s} {'cell':44s} {'AUC':>6} {'95% CI':>16} {'clears':>7}   taken vs skipped")
    results = []
    for tid, col, name, primary in CELLS:
        ci = boot_ci(T[col], K[col])
        tv, kv = float(np.nanmean(T[col].astype(float))), float(np.nanmean(K[col].astype(float)))
        flag = "** YES" if ci["clears"] else "no"
        print(f"{tid:7s} {name:44s} {ci['auc']:>6.3f} [{ci['lo']:.3f},{ci['hi']:.3f}] {flag:>7}   {tv:.3f} vs {kv:.3f}")
        results.append((tid, col, name, primary, ci, tv, kv))
    print("\nper-month robustness (AUC, primary cells only):")
    for month in df.month.unique():
        d = df[df.month == month]; t_, k_ = d[d.taken], d[~d.taken]
        line = []
        for tid, col, name, primary in CELLS:
            if primary:
                line.append(f"{col}={rank_auc(t_[col].astype(float), k_[col].astype(float)):.3f}")
        print(f"  {month}: " + "  ".join(line))
    print("\nREAD: a cell clears iff its 95% CI excludes 0.5 in the pre-registered direction")
    print("(taken > skipped). Day-clustering caveat applies; reserved years decide for real.")


def selftest():
    print("=== SELF-TEST ===")
    assert rank_auc([3, 4, 5], [0, 1, 2]) == 1.0 and rank_auc([1, 2, 3], [1, 2, 3]) == 0.5
    rng = np.random.default_rng(1)
    ci = boot_ci(rng.normal(1, 1, 150), rng.normal(0, 1, 1500), nb=2000)
    assert ci["clears"] and ci["auc"] > 0.6
    print(f"  separated arms clear: AUC={ci['auc']:.3f} [{ci['lo']:.3f},{ci['hi']:.3f}] OK")
    ci2 = boot_ci(rng.normal(0, 1, 150), rng.normal(0, 1, 1500), nb=2000)
    assert not ci2["clears"]
    print(f"  identical arms don't clear: AUC={ci2['auc']:.3f} OK")
    b = boot_ci(np.array([1, 1, 1, 0, 0]), np.array([0, 0, 0, 0, 1, 1]), nb=500)
    assert np.isfinite(b["auc"])
    print("  binary features handled OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
