#!/usr/bin/env python3
"""
favorable_aggression_cut_time_matched.py
-------------------------------------------------------------------------------
Design A (risk-set / cut-time-matched) symmetric-anchor test for favorable_aggression.

For each FAILED trade cut at elapsed time tau (= its hold), compare the favorable aggression in
its trailing W-second window-before-the-cut against the trailing W-second windows, ENDING AT THE
SAME ELAPSED tau, of every TARGET_REACHED trade that was still open AND still pre-pt1-open at tau
(the "risk set" — peers that were genuinely still working at that instant).

Why this peer rule: pre-pt1-open = "target bar not even started yet". It also auto-excludes the 22
entry-bar-pt1 trades (their pt1 opens before entry), so the contaminated set never enters as a peer.

Caveat (by design): the failed window ends on wrbtrader's discretionary cut; the reached windows end
on a matched clock. So this partly characterises what his cuts looked like vs peers still running --
informative, not fully exogenous. Read AUC + distribution, not the p-value.

    python3 favorable_aggression_cut_time_matched.py --config config.toml --wrb /path/to/wrb_1m.parquet
    python3 favorable_aggression_cut_time_matched.py --config ... --wrb ... --window-seconds 60
"""

import argparse, tomllib
from math import erf, sqrt
import pandas as pd, numpy as np

# --------- CONFIG: identical to Test 01; verified against the windowed parquet ---------
INSTRUMENT_ID  = 294973
TRADE_FILTER   = ("action", "T")
SIDE_COL       = "side"
SIDE_BUY_VALUE = "B"            # verified at runtime (sign self-check; was corr +0.76-0.78)
SIZE_COL       = "size"
PRICE_COL      = "price"
TS_COL         = "ts_event"
WRB_TIMEFRAME  = "1m"
MONTH          = "2025-10"
# ---------------------------------------------------------------------------------------

M = lambda n: pd.Timedelta(minutes=n)
floor_min = lambda t: t.floor("min")


def load_paths(config_path):
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    return cfg["paths"]["episodes"], cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")


def build_groups(episodes_path, wrb_path):
    lo = pd.Timestamp(f"{MONTH}-01"); hi = lo + pd.offsets.MonthBegin(1)
    lo_utc, hi_utc = lo.tz_localize("UTC"), hi.tz_localize("UTC")
    ep = pd.read_parquet(episodes_path); ep["td"] = pd.to_datetime(ep["trading_date"])
    o = ep[(ep["td"] >= lo) & (ep["td"] < hi)].copy().reset_index(drop=True)
    wrb = pd.read_parquet(wrb_path)
    w = wrb[(wrb["ts_event"] >= lo_utc) & (wrb["ts_event"] < hi_utc)].copy()
    if "timeframe" in w.columns:
        w = w[w["timeframe"] == WRB_TIMEFRAME]
    w = w[w["symbol"] == "ESZ5"].sort_values("ts_event")
    rows = []
    for _, r in o.iterrows():
        side, entry, exit_ = r["side"], r["first_entry_utc"], r["last_exit_utc"]
        emin = floor_min(entry); want = "bullish" if side == "long" else "bearish"
        cand = w[(w["direction"] == want) & (w["ts_event"] >= emin)]
        pt1_open = cand.iloc[0]["ts_event"] if len(cand) else pd.NaT
        reached = (len(cand) > 0) and (exit_ >= pt1_open + M(1))
        rows.append(dict(uid=f"{r['source_file']}::{r['episode_id']}", side=side, entry=entry, exit=exit_,
                         group="target_reached" if reached else "failed_trades",
                         hold=(exit_ - entry).total_seconds(),
                         pt1_open_el=((pt1_open - entry).total_seconds() if reached else np.nan)))
    return pd.DataFrame(rows)


def read_trades(windowed_parquet, t_min, t_max):
    import pyarrow.parquet as pq
    acol, aval = TRADE_FILTER
    need = [TS_COL, acol, SIDE_COL, SIZE_COL, PRICE_COL, "instrument_id"]
    pf = pq.ParquetFile(windowed_parquet)
    missing = [c for c in need if c not in set(pf.schema_arrow.names)]
    if missing:
        raise SystemExit(f"[schema] missing {missing}; check CONFIG.")
    keep = []
    for b in pf.iter_batches(columns=need):
        df = b.to_pandas()
        df = df[df[acol] == aval]
        if INSTRUMENT_ID is not None:
            df = df[df["instrument_id"] == INSTRUMENT_ID]
        df[TS_COL] = pd.to_datetime(df[TS_COL], utc=True)
        df = df[(df[TS_COL] >= t_min) & (df[TS_COL] < t_max)]
        if len(df):
            keep.append(df[[TS_COL, SIDE_COL, SIZE_COL, PRICE_COL]].copy())
    if not keep:
        raise SystemExit("[part2] zero trade prints in range; check CONFIG.")
    tr = pd.concat(keep, ignore_index=True).sort_values(TS_COL)
    tr[SIZE_COL] = tr[SIZE_COL].astype("int64")
    sgn = np.where(tr[SIDE_COL].to_numpy() == SIDE_BUY_VALUE, 1, -1)
    ts = tr[TS_COL].astype("int64").to_numpy()                  # ns
    signed = (tr[SIZE_COL].to_numpy() * sgn).astype("int64")
    price = tr[PRICE_COL].to_numpy()
    csum = np.concatenate([[0], np.cumsum(signed)])             # prefix sums for O(1) window sums
    return ts, signed, price, csum


def feat(ts, signed, price, csum, entry, win_start, win_end, side, W_eff):
    """oriented signed-delta per second over [win_start, win_end); also price change for self-check."""
    a = np.searchsorted(ts, np.int64(win_start.value), "left")
    b = np.searchsorted(ts, np.int64(win_end.value), "left")
    if b <= a:
        return 0.0, 0, 0.0
    sd = int(csum[b] - csum[a])
    pc = float(price[b - 1] - price[a])
    oriented = sd * (1 if side == "long" else -1)
    return oriented / W_eff, b - a, pc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--window-seconds", type=int, default=60)
    ap.add_argument("--out", default="favorable_aggression_cut_time_matched_results.csv")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    W = args.window_seconds; Wd = pd.Timedelta(seconds=W)

    ep_path, windowed = load_paths(args.config)
    g = build_groups(ep_path, args.wrb)
    F = g[g.group == "failed_trades"].reset_index(drop=True)
    R = g[g.group == "target_reached"].reset_index(drop=True)

    # build risk sets + the list of windows to evaluate
    jobs = []  # (kind, fail_uid, peer_uid, side, entry, win_start, win_end, W_eff)
    pairs_index = []  # (fail_uid, peer_uid)
    n_peers = []
    for _, f in F.iterrows():
        tau = f.hold; cut = f["exit"]
        ws = max(f.entry, cut - Wd)
        jobs.append(("fail", f.uid, None, f.side, f.entry, ws, cut, (cut - ws).total_seconds()))
        peers = R[R.pt1_open_el > tau]
        n_peers.append(len(peers))
        for _, r in peers.iterrows():
            anchor = r.entry + pd.Timedelta(seconds=tau)
            ws_r = max(r.entry, anchor - Wd)
            jobs.append(("peer", f.uid, r.uid, r.side, r.entry, ws_r, anchor, (anchor - ws_r).total_seconds()))
            pairs_index.append((f.uid, r.uid))
    n_peers = np.array(n_peers)
    print(f"[build] failed={len(F)} reached={len(R)} | risk-set size: min={n_peers.min()} "
          f"median={int(np.median(n_peers))} max={n_peers.max()} empty={int((n_peers==0).sum())} "
          f"| total pairs={int(n_peers.sum())} | W={W}s")

    t_min = min(j[5] for j in jobs); t_max = max(j[6] for j in jobs)
    ts, signed, price, csum = read_trades(windowed, t_min, t_max)
    print(f"[part2] trade prints loaded: {len(ts):,}")

    # evaluate every window once
    fail_feat = {}; peer_feat = {}; sd_pc = []
    for kind, fu, pu, side, entry, ws, we, Weff in jobs:
        val, n, pc = feat(ts, signed, price, csum, entry, ws, we, side, max(Weff, 1))
        if n >= 2:
            sd_pc.append((val * (1 if side == "long" else -1) * max(Weff, 1), pc))  # un-oriented signed_delta vs pc
        if kind == "fail":
            fail_feat[fu] = val
        else:
            peer_feat[(fu, pu)] = val

    # sign self-check
    if len(sd_pc) > 5:
        arr = np.array(sd_pc); corr = np.corrcoef(arr[:, 0], arr[:, 1])[0, 1]
        print(f"[selfcheck] corr(signed_delta, in-window price change) = {corr:.3f}  (expect > 0)")
        if corr < 0:
            raise SystemExit("[selfcheck] negative -> flip SIDE_BUY_VALUE and re-run.")

    # per-failed within-risk-set fraction of peers exceeding the cut (pre-registered: peers > cut)
    fe = []  # one value per failed trade = AUC within its risk set
    pooled_hi = pooled_n = 0
    rows = []
    for _, f in F.iterrows():
        fv = fail_feat[f.uid]; peers = R[R.pt1_open_el > f.hold]
        pv = np.array([peer_feat[(f.uid, ru)] for ru in peers.uid])
        if len(pv) == 0:
            continue
        exceed = np.sum(pv > fv) + 0.5 * np.sum(pv == fv)
        fe.append(exceed / len(pv)); pooled_hi += exceed; pooled_n += len(pv)
        rows.append(dict(fail_uid=f.uid, cut_feature=fv, n_peers=len(pv),
                         peer_median=float(np.median(pv)), frac_peers_above=exceed / len(pv)))
    fe = np.array(fe)
    auc_unit = fe.mean()                 # each cut = 1 obs (respects independence)
    auc_pool = pooled_hi / pooled_n      # each pair = 1 obs (overlapping)

    # cluster bootstrap CI over the failed trades (deterministic seed)
    rng = np.random.default_rng(args.seed)
    boot = np.array([rng.choice(fe, len(fe), replace=True).mean() for _ in range(10000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])

    pd.DataFrame(rows).to_csv(args.out, index=False)
    print(f"\n=== Design A: cut-time-matched (failed cut vs pre-pt1 peers at same elapsed tau), W={W}s ===")
    print(f"  AUC (per-cut, {len(fe)} cuts)   = P(peer favorable_aggression > cut) = {auc_unit:.3f}")
    print(f"     95% cluster-bootstrap CI     = [{lo:.3f}, {hi:.3f}]   (>0.5 supports 'cuts look worse')")
    print(f"  AUC (pooled over {pooled_n} pairs, overlapping) = {auc_pool:.3f}  (descriptive)")
    print(f"  median cut favorable_aggression = {np.median([r['cut_feature'] for r in rows]):+.3f}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
