#!/usr/bin/env python3
"""
favorable_aggression_all_winners_included.py
-------------------------------------------------------------------------------
First MBP-10 exit-timing test (EXPLORATION). Deterministic, re-runnable.

Part 1  build grouping + windows from episodes + wrb_1m   (validated; no MBP-10 needed)
Part 2  compute oriented signed-aggressor-delta/sec per window from the MBP-10 windowed
        parquet, self-verify the sign convention, and compare target_reached vs failed_trades.

Run on the machine where the external-drive parquet lives.

    python favorable_aggression_all_winners_included.py --config config.toml --wrb /path/to/wrb_1m.parquet
    python favorable_aggression_all_winners_included.py --config config.toml --inspect   # dump MBP-10 schema first

WHY a CONFIG block: this script was written without sight of your windowed parquet. The MBP-10
column names and the buy/sell encoding of `side` are NOT assumed — they are set below and then
VERIFIED against the data (the script re-derives sign_mult and refuses to proceed if it can't).
If --inspect shows different column names, edit the CONFIG block once and re-run.
"""

import argparse, sys, tomllib
from math import erf, sqrt
import pandas as pd, numpy as np

# ----------------------------- CONFIG (confirm via --inspect) -----------------------------
INSTRUMENT_ID   = 294973        # ESZ5 (from project notes); set None to skip the filter
TRADE_FILTER    = ("action", "T")   # column, value that marks a trade print in MBP-10
SIDE_COL        = "side"        # aggressor side column
SIDE_BUY_VALUE  = "B"           # value of SIDE_COL meaning BUY-aggressor; VERIFIED at runtime
SIZE_COL        = "size"        # trade size (unsigned -> cast int64)
PRICE_COL       = "price"       # trade price (assumed already human-scaled; price_div=1.0 for ESZ5)
TS_COL          = "ts_event"    # event timestamp (UTC). NOTE: databento to_df puts ts_recv on the
                                # index; if your parquet has ts on the index, the loader resets it.
WRB_TIMEFRAME   = "1m"
MONTH           = "2025-10"
# ------------------------------------------------------------------------------------------

M = lambda n: pd.Timedelta(minutes=n)
floor_min = lambda t: t.floor("min")


def load_paths(config_path):
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    p = cfg["paths"]
    windowed = cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")
    return p["episodes"], windowed


# ------------------------------- PART 1: grouping + windows -------------------------------
def build_windows(episodes_path, wrb_path):
    lo = pd.Timestamp(f"{MONTH}-01"); hi = lo + pd.offsets.MonthBegin(1)      # month bounds
    lo_utc, hi_utc = lo.tz_localize("UTC"), hi.tz_localize("UTC")             # tz-aware variants

    ep = pd.read_parquet(episodes_path)
    ep["td"] = pd.to_datetime(ep["trading_date"])
    o = ep[(ep["td"] >= lo) & (ep["td"] < hi)].copy().reset_index(drop=True)

    wrb = pd.read_parquet(wrb_path)
    w = wrb[(wrb["ts_event"] >= lo_utc) & (wrb["ts_event"] < hi_utc)].copy()
    if "timeframe" in w.columns:
        w = w[w["timeframe"] == WRB_TIMEFRAME]
    w = w[w["symbol"] == "ESZ5"].sort_values("ts_event")

    rows = []
    for _, r in o.iterrows():
        side, entry, exit_ = r["side"], r["first_entry_utc"], r["last_exit_utc"]
        emin = floor_min(entry)
        want = "bullish" if side == "long" else "bearish"
        cand = w[(w["direction"] == want) & (w["ts_event"] >= emin)]          # INCLUSIVE of entry bar
        if len(cand) == 0:
            reached, pt1_open = False, pd.NaT
        else:
            pt1_open = cand.iloc[0]["ts_event"]
            reached = exit_ >= pt1_open + M(1)                                # pt1 completes at +60s
        anchor = pt1_open if reached else floor_min(exit_)
        lo = max(emin, anchor - M(3))
        bars = pd.date_range(lo, anchor - M(1), freq="1min") if anchor > lo else pd.DatetimeIndex([])
        if len(bars) == 0:                                                    # entry-bar fallback (both groups)
            bars = pd.DatetimeIndex([emin])
        ws, we = bars.min(), bars.max() + M(1)
        rows.append(dict(
            uid=f"{r['source_file']}::{r['episode_id']}", trading_date=r["trading_date"], side=side,
            entry_utc=entry, exit_utc=exit_,
            group="target_reached" if reached else "failed_trades",
            pt1_open_utc=pt1_open, is_entry_bar_pt1=bool(reached and pt1_open == emin),
            n_window_bars=len(bars), window_start_utc=ws, window_end_utc=we,
            window_seconds=int((we - ws).total_seconds()),
        ))
    t = pd.DataFrame(rows)
    assert t["uid"].is_unique, "uid collision"
    assert (t["window_seconds"] > 0).all(), "empty window slipped through"
    print(f"[part1] target_reached={int((t.group=='target_reached').sum())} "
          f"failed_trades={int((t.group=='failed_trades').sum())} entry_bar_pt1={int(t.is_entry_bar_pt1.sum())}")
    return t


# ------------------------------- PART 2: MBP-10 feature ----------------------------------
def _read_trades(windowed_parquet, t_min, t_max):
    """Stream trade prints in [t_min, t_max) from the windowed parquet (memory-friendly)."""
    import pyarrow.parquet as pq
    acol, aval = TRADE_FILTER
    need = [TS_COL, acol, SIDE_COL, SIZE_COL, PRICE_COL]
    if INSTRUMENT_ID is not None:
        need.append("instrument_id")
    pf = pq.ParquetFile(windowed_parquet)
    have = set(pf.schema_arrow.names)
    missing = [c for c in need if c not in have]
    if missing:
        raise SystemExit(f"[schema] columns {missing} not in parquet. Run --inspect and fix CONFIG. Have: {sorted(have)}")
    keep = []
    for batch in pf.iter_batches(columns=need):     # only the columns we use
        df = batch.to_pandas()
        df = df[df[acol] == aval]
        if INSTRUMENT_ID is not None:
            df = df[df["instrument_id"] == INSTRUMENT_ID]
        df[TS_COL] = pd.to_datetime(df[TS_COL], utc=True)
        df = df[(df[TS_COL] >= t_min) & (df[TS_COL] < t_max)]
        if len(df):
            keep.append(df[[TS_COL, SIDE_COL, SIZE_COL, PRICE_COL]].copy())
    if not keep:
        raise SystemExit(f"[part2] ZERO trade prints (action=='{aval}') found in range. "
                         f"Check TRADE_FILTER/INSTRUMENT_ID in CONFIG against --inspect output.")
    tr = pd.concat(keep, ignore_index=True)
    tr[SIZE_COL] = tr[SIZE_COL].astype("int64")            # unsigned -> int64 before arithmetic
    tr["s"] = np.where(tr[SIDE_COL] == SIDE_BUY_VALUE, 1, -1)
    return tr.sort_values(TS_COL)


def compute_feature(windows, windowed_parquet):
    t_min, t_max = windows["window_start_utc"].min(), windows["window_end_utc"].max()
    print(f"[part2] reading trades in [{t_min}, {t_max}) from {windowed_parquet}")
    trades = _read_trades(windowed_parquet, t_min, t_max)
    print(f"[part2] trade prints loaded: {len(trades):,}")

    recs = []
    for _, r in windows.iterrows():
        win = trades[(trades[TS_COL] >= r["window_start_utc"]) & (trades[TS_COL] < r["window_end_utc"])]
        n = len(win)
        signed_delta = int((win[SIZE_COL] * win["s"]).sum()) if n else 0
        price_change = float(win[PRICE_COL].iloc[-1] - win[PRICE_COL].iloc[0]) if n >= 2 else 0.0
        oriented = signed_delta * (1 if r["side"] == "long" else -1)
        recs.append(dict(uid=r["uid"], group=r["group"], side=r["side"],
                         is_entry_bar_pt1=r["is_entry_bar_pt1"], n_trades=n,
                         signed_delta=signed_delta, price_change=price_change,
                         favorable_aggression=oriented / r["window_seconds"]))
    f = pd.DataFrame(recs)

    # --- sign-convention self-check: buy-aggressor pressure should move price up ---
    chk = f[f["n_trades"] >= 2]
    corr = chk["signed_delta"].corr(chk["price_change"]) if len(chk) > 5 else float("nan")
    print(f"[selfcheck] corr(signed_delta, in-window price change) = {corr:.3f}  (expect > 0)")
    if pd.notna(corr) and corr < 0:
        sys.exit("[selfcheck] NEGATIVE correlation -> SIDE_BUY_VALUE is likely inverted. "
                 "Flip SIDE_BUY_VALUE in CONFIG and re-run.")
    zero = int((f["n_trades"] == 0).sum())
    if zero:
        print(f"[selfcheck] {zero} window(s) had ZERO trade prints -> feature set to 0 (flagged in output).")
    return f


# ------------------------------------ reporting ------------------------------------------
def mwu_auc(a, b):
    """Mann-Whitney U (a 'greater' than b), AUC=P(a>b), one-sided p via tie-corrected normal
    approx with continuity correction. Verified identical to scipy.stats.mannwhitneyu
    (alternative='greater', method='asymptotic') to machine precision. No scipy dependency."""
    a = np.asarray(a, float); b = np.asarray(b, float); n1, n2, n = len(a), len(b), len(a) + len(b)
    allv = np.concatenate([a, b]); order = allv.argsort(kind="mergesort")
    ranks = np.empty(n); sr = allv[order]; i = 0
    while i < n:                                     # average ranks within tie groups
        j = i
        while j + 1 < n and sr[j + 1] == sr[i]: j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1; i = j + 1
    U1 = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    auc = U1 / (n1 * n2)
    _, cnt = np.unique(allv, return_counts=True); tie = (cnt ** 3 - cnt).sum()
    mu = n1 * n2 / 2.0
    sig = sqrt((n1 * n2 / 12.0) * ((n + 1) - tie / (n * (n - 1)))) if n > 1 else 0.0
    z = (U1 - mu - 0.5) / sig if sig > 0 else 0.0    # continuity correction
    p = 1 - 0.5 * (1 + erf(z / sqrt(2)))
    return U1, auc, p


def report(f, label):
    a = f.loc[f.group == "target_reached", "favorable_aggression"].to_numpy()
    b = f.loc[f.group == "failed_trades", "favorable_aggression"].to_numpy()
    U, auc, p = mwu_auc(a, b)                         # pre-registered direction: reached > failed
    print(f"\n=== {label}  (reached n={len(a)}, failed n={len(b)}) ===")
    print(f"  median favorable_aggression: reached={np.median(a):+.3f}  failed={np.median(b):+.3f}")
    print(f"  AUC=P(reached>failed)={auc:.3f}   Mann-Whitney U one-sided p={p:.4g}  (exploration: descriptive)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True, help="path to wrb_1m parquet (not in config.toml)")
    ap.add_argument("--inspect", action="store_true", help="dump MBP-10 windowed-parquet schema and exit")
    ap.add_argument("--out", default="favorable_aggression_results.csv")
    ap.add_argument("--windows-out", default="windows_table.csv")
    args = ap.parse_args()

    episodes_path, windowed_parquet = load_paths(args.config)

    if args.inspect:
        import pyarrow.parquet as pq
        pf = pq.ParquetFile(windowed_parquet)
        print("SCHEMA:\n", pf.schema_arrow)
        print("\nSample rows:")
        print(next(pf.iter_batches(batch_size=5)).to_pandas().T)
        return

    windows = build_windows(episodes_path, args.wrb)
    windows.to_csv(args.windows_out, index=False)
    f = compute_feature(windows, windowed_parquet)
    f.to_csv(args.out, index=False)
    report(f, "PRIMARY: all winners included (52 vs 40)")
    report(f[~f.is_entry_bar_pt1], "STRATIFIED: entry-bar-pt1 removed (30 vs 40)")
    print(f"\nwrote {args.windows_out} and {args.out}")


if __name__ == "__main__":
    main()
