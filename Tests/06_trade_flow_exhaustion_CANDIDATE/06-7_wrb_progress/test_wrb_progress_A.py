#!/usr/bin/env python3
"""
test_wrb_progress_A.py — #1-A: early WRB body-progress as a FORWARD exit-timing signal
-------------------------------------------------------------------------------
HYPOTHESIS: a WRB trade that is going to work shows a developing directional BODY early; a dud stays
flat. Measured at a fixed early checkpoint (entry+T), this is FORWARD-predictive and PRICE-ONLY (no
flow) — the price/structure signal that survived (WRB) rather than the flow that did not (exit-impact).

FEATURE (body-ratio; his-framework flavored, but tested as a generic progress signal)
  checkpoint = min(entry + T, exit)                              # causal guard: never read past exit
  developing_body(T) = (mid_at[checkpoint] - entry_price) * sign  # favorable NET displacement (body, not extreme)
  prior_body_max     = max |close-open| of the 3 completed 1m bars BEFORE the entry bar (WRB threshold)
  body_ratio(T)      = developing_body(T) / prior_body_max
  High = displaced ~a WRB's worth in favor by T (move came). Low/neg = flat/adverse (dud).
  Net displacement (not favorable extreme): a spike-then-fade reads ~0 = correctly "no WRB body".

NON-CIRCULARITY (the central risk — pt1 IS the first WRB in direction)
  body_ratio(T) is GRADED progress at a fixed early T, NOT the binary "did a WRB ever print" (= pt1 =
  the label). A slow runner (WRB at minute 5) has LOW body_ratio(60s). To prove it is not the label in
  disguise, this reports the WITHIN-reached and WITHIN-failed spread. If body_ratio is bimodal exactly
  on the reached/failed line, it is the label -> #1-A is dead. If reached shows real spread (slow
  builders with low early body), it is a genuine forward signal.

PRE-REGISTERED: reached expected HIGHER body_ratio (move came early). Two-sided CI read. T in
{30,60,90}s swept as DIAGNOSTIC (60 primary; not picking best T). Entry-anchored population AUC =
P(reached body_ratio > cut body_ratio); cluster-bootstrap CI over the CUT arm (early_flow_confirmation
construction; NOT Design A — this is forward/entry-anchored, no exit matching).
POPULATIONS (both): clean = losing_trade(16) vs reached_target(47); pt1 = failed_trades(40) vs
target_reached(52). Deterministic (seed 0). Read-only. n small; October discovery. Not financial advice.

RUN (from its subfolder)
  python3 test_wrb_progress_A.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups, read_per_second, S, M

import os as _os
INSTRUMENT_ID = int(_os.environ.get("TSLWRB_IID", "294973"))
MONTH = _os.environ.get("TSLWRB_MONTH", "2025-10")
SYMBOL = _os.environ.get("TSLWRB_SYMBOL", "ESZ5")
print(f"[env] MONTH={MONTH} SYMBOL={SYMBOL} INSTRUMENT_ID={INSTRUMENT_ID}", flush=True)
LO = pd.Timestamp(f"{MONTH}-01", tz="UTC"); HI = LO + pd.offsets.MonthBegin(1)
TS = [30, 60, 90]; T_PRIMARY = 60


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    ep_path = cfg["paths"]["episodes"]
    windowed = cfg["run"]["resolved"]["windowed_parquet"]; es1m = cfg["paths"]["es_1m_front"]
    g = build_groups(ep_path, wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(ep_path)
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, windowed, es1m


def load_bars(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "open", "close"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.open.to_numpy(), d.close.to_numpy()


def prior_body_max(bar_sec, bopen, bclose, entry_ts):
    """max |close-open| of the 3 completed bars before the entry bar. NaN if <3 available."""
    e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
    j = int(np.searchsorted(bar_sec, e_s, "left"))   # first bar at/after entry-bar start
    if j < 3:
        return np.nan
    bodies = np.abs(bclose[j-3:j] - bopen[j-3:j])
    return float(bodies.max()) if len(bodies) == 3 else np.nan


def mid_at(sec, mid, t_ts):
    t_s = np.int64(pd.Timestamp(t_ts).value // 1_000_000_000)
    i = int(np.searchsorted(sec, t_s, "right") - 1)
    return float(mid[i]) if i >= 0 else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    g, windowed, es1m = load(args.config, args.wrb)
    bar_sec, bopen, bclose = load_bars(es1m)
    t_min = g["entry"].min() - M(5); t_max = g["exit"].max() + M(1)
    print(f"[1A] streaming per-second mid in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[1A] per-second rows: {len(sec):,}  bars: {len(bar_sec):,}")

    # per-trade body_ratio at each T (with causal guard + truncation flag)
    rows = []
    for _, r in g.iterrows():
        pbm = prior_body_max(bar_sec, bopen, bclose, r.entry)
        sgn = 1.0 if r.side == "long" else -1.0
        rec = dict(uid=r.uid, group=r.group, is_loser=bool(r.is_loser))
        for T in TS:
            cp = min(r.entry + S(T), r.exit)
            trunc = (r.entry + S(T)) > r.exit
            m = mid_at(sec, mid, cp)
            dev = (m - r.entry_price) * sgn if not np.isnan(m) else np.nan
            rec[f"br_{T}"] = (dev / pbm) if (pbm and pbm > 0 and not np.isnan(dev)) else np.nan
            rec[f"trunc_{T}"] = bool(trunc)
        rows.append(rec)
    d = pd.DataFrame(rows)
    print(f"[1A] prior_body_max NaN (｜<3 prior bars): {int(d[[f'br_{T}' for T in TS]].isna().all(axis=1).sum())} trades")

    pops = {
        "clean (losing16 vs reached47)": (d[d.is_loser], d[(d.group == "target_reached") & (~d.is_loser)]),
        "pt1   (failed40 vs reached52)": (d[d.group == "failed_trades"], d[d.group == "target_reached"]),
    }

    for pop_name, (cut, spared) in pops.items():
        print(f"\n================ POPULATION: {pop_name} ================")
        print(f"  cut n={len(cut)}  spared n={len(spared)}   (pre-registered: spared/reached HIGHER body_ratio)")
        for T in TS:
            cv = cut[f"br_{T}"].to_numpy(); sv = spared[f"br_{T}"].to_numpy()
            cv = cv[~np.isnan(cv)]; sv = sv[~np.isnan(sv)]
            # per-cut AUC = P(reached > cut); cluster bootstrap over cut arm
            per_cut = [float((np.sum(sv > c) + 0.5 * np.sum(sv == c)) / len(sv)) for c in cv] if len(sv) else []
            ci = spine.cluster_boot_ci(per_cut, seed=args.seed)
            tag = "PRIMARY" if T == T_PRIMARY else "diag"
            trunc_n = int(cut[f"trunc_{T}"].sum() + spared[f"trunc_{T}"].sum())
            flag = ("CI excl 0.5" if ci["excludes_half"] else "CI incl 0.5")
            star = "  <<<" if T == T_PRIMARY else ""
            print(f"  T={T:>2}s [{tag:7}] AUC={ci['mean']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
                  f"-> {flag} | med reached={np.nanmedian(sv):+.2f} cut={np.nanmedian(cv):+.2f} "
                  f"| trunc={trunc_n}{star}")
        # NON-CIRCULARITY: within-group spread at primary T (is it graded, or the pt1 label?)
        cvP = spared[f"br_{T_PRIMARY}"].dropna(); fvP = cut[f"br_{T_PRIMARY}"].dropna()
        def spread(a): return f"p10={np.percentile(a,10):+.2f} p50={np.median(a):+.2f} p90={np.percentile(a,90):+.2f}"
        print(f"  [non-circularity @T={T_PRIMARY}s] within reached: {spread(cvP)}")
        print(f"                                    within cut:     {spread(fvP)}")
        print(f"    (overlapping spreads / reached showing low values = GRADED signal, not the pt1 label.")
        print(f"     reached all-high & cut all-low with no overlap = label in disguise -> #1-A void.)")

    print(f"\n[1A] DONE. Read: PRIMARY T=60s AUC + CI per population; then the non-circularity spreads")
    print(f"  (if reached has real low-end spread, the early-body signal is distinct from pt1).")


if __name__ == "__main__":
    main()
