#!/usr/bin/env python3
"""
test_wrb_progress_A_trunccheck.py — #1-A with truncation EXCLUDED vs included
-------------------------------------------------------------------------------
Settles whether #1-A's strong 60/90s AUC was real signal or truncation/outcome-absorption.
Same body_ratio(T) feature as test_wrb_progress_A.py. For each population and T, reports:
  ALL  : every scored trade, truncated ones measured at min(entry+T, exit) -> reproduces the prior
         run (regression check) BUT a truncated trade's "early body" is really its body AT EXIT
         (the outcome leaking into the feature).
  OPEN : only trades STILL OPEN at entry+T (truncation excluded). This is BOTH de-confounded AND
         the operationally honest read: a live entry+T checkpoint indicator can NEVER fire on a
         trade that already exited before T. If ALL>>OPEN, the strength was truncation, not signal.
Per-arm truncation breakdown included (tests the "fast losers drive it" claim, not just asserts it).
Deterministic (seed 0). Read-only. n small; October discovery.

RUN (from 06-7_wrb_progress inside the 06 folder)
  python3 test_wrb_progress_A_trunccheck.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
TS = [30, 60, 90]; T_PRIMARY = 60


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["run"]["resolved"]["windowed_parquet"], cfg["paths"]["es_1m_front"]


def load_bars(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "open", "close"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.open.to_numpy(), d.close.to_numpy()


def prior_body_max(bar_sec, bopen, bclose, entry_ts):
    e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
    j = int(np.searchsorted(bar_sec, e_s, "left"))
    if j < 3:
        return np.nan
    return float(np.abs(bclose[j-3:j] - bopen[j-3:j]).max())


def mid_at(sec, mid, t_ts):
    t_s = np.int64(pd.Timestamp(t_ts).value // 1_000_000_000)
    i = int(np.searchsorted(sec, t_s, "right") - 1)
    return float(mid[i]) if i >= 0 else np.nan


def auc_ci(cut_vals, spared_vals, seed=0):
    cv = cut_vals[~np.isnan(cut_vals)]; sv = spared_vals[~np.isnan(spared_vals)]
    if len(cv) == 0 or len(sv) == 0:
        return dict(mean=np.nan, lo=np.nan, hi=np.nan, n=0, excludes_half=False), len(cv), len(sv)
    per_cut = [float((np.sum(sv > c) + 0.5 * np.sum(sv == c)) / len(sv)) for c in cv]
    return spine.cluster_boot_ci(per_cut, seed=seed), len(cv), len(sv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    g, windowed, es1m = load(args.config, args.wrb)
    bar_sec, bopen, bclose = load_bars(es1m)
    t_min = g["entry"].min() - M(5); t_max = g["exit"].max() + M(1)
    print(f"[1A-trunc] streaming per-second mid in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[1A-trunc] per-second rows: {len(sec):,}  bars: {len(bar_sec):,}")

    rows = []
    for _, r in g.iterrows():
        pbm = prior_body_max(bar_sec, bopen, bclose, r.entry)
        sgn = 1.0 if r.side == "long" else -1.0
        rec = dict(uid=r.uid, group=r.group, is_loser=bool(r.is_loser))
        for T in TS:
            cp = min(r.entry + S(T), r.exit); trunc = (r.entry + S(T)) > r.exit
            m = mid_at(sec, mid, cp)
            dev = (m - r.entry_price) * sgn if not np.isnan(m) else np.nan
            rec[f"br_{T}"] = (dev / pbm) if (pbm and pbm > 0 and not np.isnan(dev)) else np.nan
            rec[f"trunc_{T}"] = bool(trunc)
        rows.append(rec)
    d = pd.DataFrame(rows)

    pops = {
        "clean (losing16 vs reached47)": (d[d.is_loser], d[(d.group == "target_reached") & (~d.is_loser)]),
        "pt1   (failed40 vs reached52)": (d[d.group == "failed_trades"], d[d.group == "target_reached"]),
    }
    for pop_name, (cut, spared) in pops.items():
        print(f"\n================ {pop_name} ================")
        for T in TS:
            tag = "PRIMARY" if T == T_PRIMARY else "diag"
            # ALL (truncated measured at exit -> outcome leak)
            ci_all, nc_a, ns_a = auc_ci(cut[f"br_{T}"].to_numpy(), spared[f"br_{T}"].to_numpy(), args.seed)
            # OPEN (still open at entry+T)
            co = cut[~cut[f"trunc_{T}"]]; so = spared[~spared[f"trunc_{T}"]]
            ci_op, nc_o, ns_o = auc_ci(co[f"br_{T}"].to_numpy(), so[f"br_{T}"].to_numpy(), args.seed)
            # per-arm truncation
            ct = int(cut[f"trunc_{T}"].sum()); st = int(spared[f"trunc_{T}"].sum())
            f_all = "excl" if ci_all["excludes_half"] else "incl"
            f_op = "excl" if ci_op["excludes_half"] else "incl"
            floor = "" if nc_o >= 8 else f"  <CUT n={nc_o} < 8 floor>"
            print(f"  T={T:>2}s [{tag:7}] "
                  f"ALL  AUC={ci_all['mean']:.3f} CI[{ci_all['lo']:.3f},{ci_all['hi']:.3f}] {f_all} (cut{nc_a}) | "
                  f"OPEN AUC={ci_op['mean']:.3f} CI[{ci_op['lo']:.3f},{ci_op['hi']:.3f}] {f_op} (cut{nc_o}) | "
                  f"trunc cut={ct} spared={st}{floor}")
        # non-circularity spreads on the OPEN set at primary T
        co = cut[~cut[f"trunc_{T_PRIMARY}"]]; so = spared[~spared[f"trunc_{T_PRIMARY}"]]
        cvP = so[f"br_{T_PRIMARY}"].dropna(); fvP = co[f"br_{T_PRIMARY}"].dropna()
        sp = lambda a: f"p10={np.percentile(a,10):+.2f} p50={np.median(a):+.2f} p90={np.percentile(a,90):+.2f}"
        print(f"  [non-circularity @T={T_PRIMARY}s, OPEN only] reached: {sp(cvP)} | cut: {sp(fvP)}")

    print(f"\n[1A-trunc] READ: if ALL >> OPEN, the strength was truncation/outcome-absorption, not a")
    print(f"  forward signal. OPEN is the operationally honest magnitude (indicator can't fire on")
    print(f"  trades already exited). Watch the CUT n on OPEN at T=90s (truncation shrinks it).")


if __name__ == "__main__":
    main()
