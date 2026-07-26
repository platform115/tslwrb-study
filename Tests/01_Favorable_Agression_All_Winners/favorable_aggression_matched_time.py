#!/usr/bin/env python3
"""
favorable_aggression_matched_time.py
-------------------------------------------------------------------------------
SYMMETRIC-ANCHOR CONTROL for favorable_aggression_all_winners_included.

Purpose: the primary test anchored target_reached on the pt1 bar and failed_trades on the
exit bar -- structurally different events. That asymmetry is the prime suspect for the observed
reversal. This control removes it: BOTH groups are measured over the SAME window relative to a
common clock -- the first T seconds after entry -- and labeled by eventual outcome. If favorable
aggression still fails to separate here, the negative is the FEATURE; if it now separates, the
primary's result was a DESIGN (anchor) artifact.

Window = [entry_utc, entry_utc + T) measured from the exact entry timestamp (causal, post-entry
only -> no entry-bar/pre-entry contamination). Same construction for both groups.

Sample = trades still open at entry+T (hold >= T). Trades cut before T are out-of-sample (no
decision is possible at T). NOTE: this drops the fastest cuts -> the test speaks only to trades
that survived >= T seconds.

Default T = 60s (sample 50 reached / 32 failed for Oct-2025; pre-registered single value, no sweep).

    python3 favorable_aggression_matched_time.py --config config.toml --wrb /path/to/wrb_1m.parquet
    python3 favorable_aggression_matched_time.py --config config.toml --wrb ... --t-seconds 60
"""

import argparse, tomllib
from math import erf, sqrt
import pandas as pd, numpy as np

# --------- CONFIG: identical to the primary test; verified against the windowed parquet ---------
INSTRUMENT_ID  = 294973
TRADE_FILTER   = ("action", "T")
SIDE_COL       = "side"
SIDE_BUY_VALUE = "B"            # verified at runtime via the sign self-check (corr +0.755 in primary)
SIZE_COL       = "size"
PRICE_COL      = "price"
TS_COL         = "ts_event"
WRB_TIMEFRAME  = "1m"
MONTH          = "2025-10"
# ------------------------------------------------------------------------------------------------

M = lambda n: pd.Timedelta(minutes=n)
floor_min = lambda t: t.floor("min")


def load_paths(config_path):
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    return cfg["paths"]["episodes"], cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")


def mwu_auc(a, b):
    """Mann-Whitney U (a>b), AUC, one-sided p; tie-corrected normal w/ continuity. == scipy. No scipy."""
    a = np.asarray(a, float); b = np.asarray(b, float); n1, n2, n = len(a), len(b), len(a) + len(b)
    allv = np.concatenate([a, b]); order = allv.argsort(kind="mergesort")
    ranks = np.empty(n); sr = allv[order]; i = 0
    while i < n:
        j = i
        while j + 1 < n and sr[j + 1] == sr[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    U1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    auc = U1 / (n1 * n2)
    _, cnt = np.unique(allv, return_counts=True); tie = (cnt ** 3 - cnt).sum()
    mu = n1 * n2 / 2.0
    sig = sqrt((n1 * n2 / 12.0) * ((n + 1) - tie / (n * (n - 1)))) if n > 1 else 0.0
    z = (U1 - mu - 0.5) / sig if sig > 0 else 0.0
    return U1, auc, 1 - 0.5 * (1 + erf(z / sqrt(2)))


def build_matched(episodes_path, wrb_path, T):
    lo = pd.Timestamp(f"{MONTH}-01"); hi = lo + pd.offsets.MonthBegin(1)
    lo_utc, hi_utc = lo.tz_localize("UTC"), hi.tz_localize("UTC")
    ep = pd.read_parquet(episodes_path); ep["td"] = pd.to_datetime(ep["trading_date"])
    o = ep[(ep["td"] >= lo) & (ep["td"] < hi)].copy().reset_index(drop=True)
    wrb = pd.read_parquet(wrb_path)
    w = wrb[(wrb["ts_event"] >= lo_utc) & (wrb["ts_event"] < hi_utc)].copy()
    if "timeframe" in w.columns:
        w = w[w["timeframe"] == WRB_TIMEFRAME]
    w = w[w["symbol"] == "ESZ5"].sort_values("ts_event")

    dt = pd.Timedelta(seconds=T)
    rows = []
    for _, r in o.iterrows():
        side, entry, exit_ = r["side"], r["first_entry_utc"], r["last_exit_utc"]
        emin = floor_min(entry); want = "bullish" if side == "long" else "bearish"
        cand = w[(w["direction"] == want) & (w["ts_event"] >= emin)]            # inclusive (same grouping as primary)
        pt1_open = cand.iloc[0]["ts_event"] if len(cand) else pd.NaT
        reached = (len(cand) > 0) and (exit_ >= pt1_open + M(1))
        hold_s = (exit_ - entry).total_seconds()
        rows.append(dict(
            uid=f"{r['source_file']}::{r['episode_id']}", side=side,
            group="target_reached" if reached else "failed_trades",
            is_entry_bar_pt1=bool(reached and pt1_open == emin),
            hold_s=hold_s, in_sample=hold_s >= T,
            window_start_utc=entry, window_end_utc=entry + dt, window_seconds=T,
        ))
    t = pd.DataFrame(rows)
    ins = t[t.in_sample]
    print(f"[build] T={T}s  in-sample: reached={int((ins.group=='target_reached').sum())} "
          f"failed={int((ins.group=='failed_trades').sum())}  "
          f"| dropped (hold<T): reached={int(((~t.in_sample)&(t.group=='target_reached')).sum())} "
          f"failed={int(((~t.in_sample)&(t.group=='failed_trades')).sum())}")
    return t


def read_trades(windowed_parquet, t_min, t_max):
    import pyarrow.parquet as pq
    acol, aval = TRADE_FILTER
    need = [TS_COL, acol, SIDE_COL, SIZE_COL, PRICE_COL, "instrument_id"]
    pf = pq.ParquetFile(windowed_parquet)
    missing = [c for c in need if c not in set(pf.schema_arrow.names)]
    if missing:
        raise SystemExit(f"[schema] missing {missing}; check CONFIG against --inspect of the primary script.")
    keep = []
    for batch in pf.iter_batches(columns=need):
        df = batch.to_pandas()
        df = df[df[acol] == aval]
        if INSTRUMENT_ID is not None:
            df = df[df["instrument_id"] == INSTRUMENT_ID]
        df[TS_COL] = pd.to_datetime(df[TS_COL], utc=True)
        df = df[(df[TS_COL] >= t_min) & (df[TS_COL] < t_max)]
        if len(df):
            keep.append(df[[TS_COL, SIDE_COL, SIZE_COL, PRICE_COL]].copy())
    if not keep:
        raise SystemExit("[part2] zero trade prints in range; check CONFIG.")
    tr = pd.concat(keep, ignore_index=True)
    tr[SIZE_COL] = tr[SIZE_COL].astype("int64")
    tr["s"] = np.where(tr[SIDE_COL] == SIDE_BUY_VALUE, 1, -1)
    return tr.sort_values(TS_COL)


def compute_feature(windows, windowed_parquet):
    ins = windows[windows.in_sample].copy()
    tr = read_trades(windowed_parquet, ins.window_start_utc.min(), ins.window_end_utc.max())
    print(f"[part2] trade prints loaded: {len(tr):,}")
    recs = []
    for _, r in ins.iterrows():
        win = tr[(tr[TS_COL] >= r.window_start_utc) & (tr[TS_COL] < r.window_end_utc)]
        n = len(win)
        sd = int((win[SIZE_COL] * win["s"]).sum()) if n else 0
        pc = float(win[PRICE_COL].iloc[-1] - win[PRICE_COL].iloc[0]) if n >= 2 else 0.0
        oriented = sd * (1 if r.side == "long" else -1)
        recs.append(dict(uid=r.uid, group=r.group, side=r.side, is_entry_bar_pt1=r.is_entry_bar_pt1,
                         n_trades=n, signed_delta=sd, price_change=pc,
                         favorable_aggression=oriented / r.window_seconds))
    f = pd.DataFrame(recs)
    chk = f[f.n_trades >= 2]
    corr = chk.signed_delta.corr(chk.price_change) if len(chk) > 5 else float("nan")
    print(f"[selfcheck] corr(signed_delta, in-window price change) = {corr:.3f}  (expect > 0)")
    if pd.notna(corr) and corr < 0:
        raise SystemExit("[selfcheck] negative corr -> flip SIDE_BUY_VALUE and re-run.")
    return f


def report(f, label):
    a = f.loc[f.group == "target_reached", "favorable_aggression"].to_numpy()
    b = f.loc[f.group == "failed_trades", "favorable_aggression"].to_numpy()
    U, auc, p = mwu_auc(a, b)
    print(f"\n=== {label}  (reached n={len(a)}, failed n={len(b)}) ===")
    print(f"  median favorable_aggression: reached={np.median(a):+.3f}  failed={np.median(b):+.3f}")
    print(f"  AUC=P(reached>failed)={auc:.3f}   one-sided p={p:.4g}  (exploration: descriptive)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--t-seconds", type=int, default=60)
    ap.add_argument("--out", default="favorable_aggression_matched_time_results.csv")
    args = ap.parse_args()
    episodes_path, windowed_parquet = load_paths(args.config)
    windows = build_matched(episodes_path, args.wrb, args.t_seconds)
    f = compute_feature(windows, windowed_parquet)
    f.to_csv(args.out, index=False)
    report(f, f"MATCHED-TIME control: first {args.t_seconds}s after entry, symmetric anchor")
    report(f[~f.is_entry_bar_pt1], f"  same, entry-bar-pt1 removed (for parity with primary)")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
