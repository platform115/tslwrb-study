#!/usr/bin/env python3
"""
refill_resiliency.py — Test 04
-------------------------------------------------------------------------------
Stall family: "refill slowing". On a DOM you cannot separate a cancel from a trade consuming size,
so refill is INFERRED (approximate), per Large (2007) resiliency / absorption.

Supporting side = bid (long) / ask (short). Over the window:
  consumed   = aggressor volume hitting the support  (sell-aggressor 'A' for long; buy-aggressor 'B' for short)
  net_change = supporting_depth_end - supporting_depth_start    (Sum of 10 levels)
  refill_ratio = 1 + net_change / consumed
    ~1  -> support replenished despite being hit (healthy / absorption)
    <1  -> support eroding faster than it refills (STALL)
    undefined if consumed == 0 (support not challenged) -> flagged & excluded
Pre-registered: target_reached > failed_trades.

Designs (as Tests 01/03): PRIMARY (pt1/exit anchored, 3-bar window, entry-bar fallback; 52/40 and
excl-22) + CONTROL Design A (cut-time-matched, auto-excludes the 22). Descriptive secondary:
supporting-depth slope per second. Relies on CURRENT_STATE conventions. Memory-safe streaming.

    python3 refill_resiliency.py --config config.toml --wrb /path/to/wrb_1m.parquet
"""

import argparse, tomllib
import numpy as np, pandas as pd

INSTRUMENT_ID = 294973
TS_COL = "ts_event"; ACT = "action"; SIDE = "side"; SZ = "size"
BID_SZ = [f"bid_sz_0{i}" for i in range(10)]; ASK_SZ = [f"ask_sz_0{i}" for i in range(10)]
WRB_TF, MONTH = "1m", "2025-10"
M = lambda n: pd.Timedelta(minutes=n); floor_min = lambda t: t.floor("min")


def load_paths(c):
    with open(c, "rb") as f: cfg = tomllib.load(f)
    return cfg["paths"]["episodes"], cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")


def build_groups(episodes_path, wrb_path):
    lo = pd.Timestamp(f"{MONTH}-01"); hi = lo + pd.offsets.MonthBegin(1)
    ep = pd.read_parquet(episodes_path); ep["td"] = pd.to_datetime(ep["trading_date"])
    o = ep[(ep["td"] >= lo) & (ep["td"] < hi)].copy().reset_index(drop=True)
    w = pd.read_parquet(wrb_path)
    w = w[(w["ts_event"] >= lo.tz_localize("UTC")) & (w["ts_event"] < hi.tz_localize("UTC"))].copy()
    if "timeframe" in w.columns: w = w[w["timeframe"] == WRB_TF]
    w = w[w["symbol"] == "ESZ5"].sort_values("ts_event")
    rows = []
    for _, r in o.iterrows():
        side, entry, exit_ = r["side"], r["first_entry_utc"], r["last_exit_utc"]
        emin = floor_min(entry); want = "bullish" if side == "long" else "bearish"
        cand = w[(w["direction"] == want) & (w["ts_event"] >= emin)]
        pt1 = cand.iloc[0]["ts_event"] if len(cand) else pd.NaT
        reached = (len(cand) > 0) and (exit_ >= pt1 + M(1))
        anchor = pt1 if reached else floor_min(exit_)
        lob = max(emin, anchor - M(3))
        bars = pd.date_range(lob, anchor - M(1), freq="1min") if anchor > lob else pd.DatetimeIndex([])
        if len(bars) == 0: bars = pd.DatetimeIndex([emin])
        rows.append(dict(uid=f"{r['source_file']}::{r['episode_id']}", side=side, entry=entry, exit=exit_,
                         group="target_reached" if reached else "failed_trades", hold=(exit_ - entry).total_seconds(),
                         pt1_open_el=((pt1 - entry).total_seconds() if reached else np.nan),
                         is_entry_bar_pt1=bool(reached and pt1 == emin), win_start=bars.min(), win_end=bars.max() + M(1)))
    return pd.DataFrame(rows)


def read_book_trades(windowed, t_min, t_max):
    """Per in-window row: ts, supporting sums (bid,ask), and trade volume split by aggressor. Memory-safe."""
    import pyarrow.parquet as pq, pyarrow as pa
    need = [TS_COL, ACT, SIDE, SZ, "instrument_id"] + BID_SZ + ASK_SZ
    pf = pq.ParquetFile(windowed)
    miss = [c for c in need if c not in set(pf.schema_arrow.names)]
    if miss: raise SystemExit(f"[schema] missing {miss}")
    tmin, tmax = pd.Timestamp(t_min).value, pd.Timestamp(t_max).value
    TS, BID, ASK, SELLV, BUYV = [], [], [], [], []
    for b in pf.iter_batches(batch_size=200_000, columns=need):
        ts = b.column(TS_COL).cast(pa.timestamp("ns")).cast(pa.int64()).to_numpy(zero_copy_only=False)
        m = (ts >= tmin) & (ts < tmax)
        if INSTRUMENT_ID is not None:
            m &= b.column("instrument_id").to_numpy(zero_copy_only=False) == INSTRUMENT_ID
        if not m.any(): continue
        idx = np.flatnonzero(m)
        bid = np.zeros(len(idx), "int64"); ask = np.zeros(len(idx), "int64")
        for c in BID_SZ: bid += b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64")
        for c in ASK_SZ: ask += b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64")
        act = b.column(ACT).to_numpy(zero_copy_only=False)[idx]
        sd  = b.column(SIDE).to_numpy(zero_copy_only=False)[idx]
        sz  = b.column(SZ).to_numpy(zero_copy_only=False)[idx].astype("int64")
        is_t = act == "T"
        sellv = np.where(is_t & (sd == "A"), sz, 0)   # sell-aggressor hits the BID (long support)
        buyv  = np.where(is_t & (sd == "B"), sz, 0)   # buy-aggressor hits the ASK (short support)
        TS.append(ts[idx]); BID.append(bid); ASK.append(ask); SELLV.append(sellv); BUYV.append(buyv)
    if not TS: raise SystemExit("[read] zero rows in range")
    ts = np.concatenate(TS); o = ts.argsort(kind="mergesort")
    return (ts[o], np.concatenate(BID)[o], np.concatenate(ASK)[o],
            np.concatenate(SELLV)[o], np.concatenate(BUYV)[o])


def refill_feat(arr, entry, ws, we, side):
    ts, bid, ask, sellv, buyv = arr
    a = np.searchsorted(ts, np.int64(ws.value), "left"); b = np.searchsorted(ts, np.int64(we.value), "left")
    if b - a < 2: return np.nan, np.nan, 0
    sup = bid[a:b] if side == "long" else ask[a:b]
    consumed = int(sellv[a:b].sum()) if side == "long" else int(buyv[a:b].sum())
    if consumed <= 0: return np.nan, np.nan, consumed          # support not challenged -> undefined
    ratio = 1.0 + (int(sup[-1]) - int(sup[0])) / consumed
    x = (ts[a:b] - ts[a]) / 1e9; vx = x.var()
    slope = (np.cov(x, sup.astype(float))[0, 1] / vx) if vx > 0 else 0.0   # supporting-depth slope (descriptive)
    return float(ratio), float(slope), consumed


def auc(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return ((a[:, None] > b[None, :]).sum() + 0.5 * (a[:, None] == b[None, :]).sum()) / (len(a) * len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--window-seconds", type=int, default=60); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="refill_resiliency_results.csv")
    args = ap.parse_args(); Wd = pd.Timedelta(seconds=args.window_seconds)
    ep_path, windowed = load_paths(args.config)
    g = build_groups(ep_path, args.wrb)
    F = g[g.group == "failed_trades"].reset_index(drop=True); R = g[g.group == "target_reached"].reset_index(drop=True)

    jobs = [("primary", r.uid, r.side, r.entry, r.win_start, r.win_end) for _, r in g.iterrows()]
    pairs = []
    for _, f in F.iterrows():
        jobs.append(("A_cut", f.uid, f.side, f.entry, max(f.entry, f["exit"] - Wd), f["exit"]))
        for _, rr in R[R.pt1_open_el > f.hold].iterrows():
            anc = rr.entry + pd.Timedelta(seconds=f.hold)
            jobs.append(("A_peer", (f.uid, rr.uid), rr.side, rr.entry, max(rr.entry, anc - Wd), anc)); pairs.append((f.uid, rr.uid))

    t_min = min(j[4] for j in jobs); t_max = max(j[5] for j in jobs)
    print(f"[build] failed={len(F)} reached={len(R)} A_pairs={len(pairs)} | reading [{t_min},{t_max})")
    arr = read_book_trades(windowed, t_min, t_max)
    print(f"[read] in-window rows: {len(arr[0]):,}")

    prim, cut, peer = {}, {}, {}; undef = 0
    for tag, key, side, entry, ws, we in jobs:
        ratio, slope, cons = refill_feat(arr, entry, ws, we, side)
        if np.isnan(ratio): undef += 1
        if tag == "primary": prim[key] = (ratio, slope)
        elif tag == "A_cut": cut[key] = ratio
        else: peer[key] = ratio
    print(f"[note] windows with undefined refill_ratio (no support-side aggression): {undef}")

    gp = g.copy(); gp["ratio"] = gp.uid.map(lambda u: prim[u][0]); gp["slope"] = gp.uid.map(lambda u: prim[u][1])
    def rep(d, lab):
        a = d.loc[d.group == "target_reached", "ratio"].dropna(); b = d.loc[d.group == "failed_trades", "ratio"].dropna()
        if len(a) < 3 or len(b) < 3: print(f"\n=== PRIMARY {lab}: too few defined ({len(a)}/{len(b)}) ==="); return
        print(f"\n=== PRIMARY {lab} (reached {len(a)}, failed {len(b)} defined) ===")
        print(f"  refill_ratio median reached={a.median():.3f} failed={b.median():.3f}  AUC(reached>failed)={auc(a,b):.3f}")
    rep(gp, "all (<=52/<=40)"); rep(gp[~gp.is_entry_bar_pt1], "excl entry-bar-pt1 (<=30/<=40)")

    fe = []
    for _, f in F.iterrows():
        cv = cut[f.uid]
        if np.isnan(cv): continue
        pv = np.array([peer[(f.uid, ru)] for ru in R[R.pt1_open_el > f.hold].uid]); pv = pv[~np.isnan(pv)]
        if len(pv): fe.append((np.sum(pv > cv) + 0.5 * np.sum(pv == cv)) / len(pv))
    fe = np.array(fe)
    if len(fe) >= 5:
        rng = np.random.default_rng(args.seed)
        boot = np.array([rng.choice(fe, len(fe), True).mean() for _ in range(10000)]); lo, hi = np.percentile(boot, [2.5, 97.5])
        print(f"\n=== CONTROL Design A (refill_ratio), W={args.window_seconds}s ===")
        print(f"  AUC(per-cut, {len(fe)}) = P(peer refill > cut refill) = {fe.mean():.3f}  95% CI [{lo:.3f}, {hi:.3f}]")
    else:
        print(f"\n=== CONTROL Design A: too few defined cuts ({len(fe)}) ===")
    gp.to_csv(args.out, index=False); print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
