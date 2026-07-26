#!/usr/bin/env python3
"""
queue_imbalance_slope.py  — Test 03
-------------------------------------------------------------------------------
Stall feature: does the SLOPE of oriented queue (depth) imbalance over the window distinguish
target_reached from failed_trades? "Stalling" = favorable book support fading across the window
(negative slope). Book-side feature, orthogonal to the trade-side delta exhausted in Tests 01/02.

Imbalance (per book snapshot) = (Sum bid_sz_00..09 - Sum ask_sz_00..09) / (Sum both)  in [-1,1]
oriented = imbalance * (+1 long / -1 short)   (positive = book supports the trade direction)
feature  = OLS slope of oriented-imbalance on elapsed seconds within the window  (per-second)

Two designs in one run (a primary-only look is misleading — see Tests 01/02):
  PRIMARY     : anchor = pt1 bar (reached) / exit bar (failed); window = up to 3 1m bars before
                anchor, floored at entry, anchor excluded, entry-bar fallback. Report 52/40 and
                excl-22 (30/40). Pre-registered: reached slope > failed slope.
  CONTROL (A) : cut-time-matched — each failed cut vs the same-elapsed-tau windows of reached trades
                still open & pre-pt1-open (auto-excludes the 22). Pre-registered: peer slope > cut slope.

Relies on CURRENT_STATE conventions (open-stamp; WRB+60s; MBP-10 schema; ESZ5; sizes uint32->int64).

    python3 queue_imbalance_slope.py --config config.toml --wrb /path/to/wrb_1m.parquet
"""

import argparse, tomllib
import pandas as pd, numpy as np

INSTRUMENT_ID = 294973
TS_COL  = "ts_event"
LEVELS  = 10                         # full visible DOM; pre-registered (changing = new pre-registration)
BID_SZ  = [f"bid_sz_0{i}" for i in range(LEVELS)]
ASK_SZ  = [f"ask_sz_0{i}" for i in range(LEVELS)]
BID_PX0, ASK_PX0 = "bid_px_00", "ask_px_00"
WRB_TIMEFRAME, MONTH = "1m", "2025-10"
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
    if "timeframe" in w.columns: w = w[w["timeframe"] == WRB_TIMEFRAME]
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
                         group="target_reached" if reached else "failed_trades",
                         hold=(exit_ - entry).total_seconds(),
                         pt1_open_el=((pt1 - entry).total_seconds() if reached else np.nan),
                         is_entry_bar_pt1=bool(reached and pt1 == emin),
                         win_start=bars.min(), win_end=bars.max() + M(1)))
    return pd.DataFrame(rows)


def read_book(windowed, t_min, t_max):
    """Memory-safe: collapse each batch to (ts, bid_sum, ask_sum, mid) and filter to the window range
    INSIDE the loop, so peak memory is ~one batch, not the whole file. (The previous version kept
    full wide rows for every book update -> tens of millions of rows x 23 cols -> blew up RAM.)"""
    import pyarrow.parquet as pq
    import pyarrow as pa
    need = [TS_COL, BID_PX0, ASK_PX0, "instrument_id"] + BID_SZ + ASK_SZ
    pf = pq.ParquetFile(windowed)
    miss = [c for c in need if c not in set(pf.schema_arrow.names)]
    if miss:
        raise SystemExit(f"[schema] missing {miss}; check CONFIG against --inspect.")
    tmin_ns = pd.Timestamp(t_min).value; tmax_ns = pd.Timestamp(t_max).value
    ts_a, imb_a, mid_a = [], [], []
    for b in pf.iter_batches(batch_size=200_000, columns=need):   # bounded batch
        ts = b.column(TS_COL).cast(pa.timestamp("ns")).cast(pa.int64()).to_numpy(zero_copy_only=False)  # ns, unit-proof
        m = (ts >= tmin_ns) & (ts < tmax_ns)                      # window filter FIRST
        if INSTRUMENT_ID is not None:
            m &= (b.column("instrument_id").to_numpy(zero_copy_only=False) == INSTRUMENT_ID)
        if not m.any():
            continue
        idx = np.flatnonzero(m)
        bid = np.zeros(len(idx), "int64"); ask = np.zeros(len(idx), "int64")
        for c in BID_SZ:
            bid += b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64")
        for c in ASK_SZ:
            ask += b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64")
        tot = bid + ask
        ok = tot > 0
        if not ok.any():
            continue
        imb = (bid[ok] - ask[ok]) / tot[ok]
        bp = b.column(BID_PX0).to_numpy(zero_copy_only=False)[idx][ok]
        ap = b.column(ASK_PX0).to_numpy(zero_copy_only=False)[idx][ok]
        ts_a.append(ts[idx][ok]); imb_a.append(imb); mid_a.append((bp + ap) / 2)
    if not ts_a:
        raise SystemExit("[read] zero book snapshots in range; check CONFIG.")
    ts = np.concatenate(ts_a); order = ts.argsort(kind="mergesort")
    return ts[order], np.concatenate(imb_a)[order], np.concatenate(mid_a)[order]


def slope_feature(ts, imb, mid, entry, ws, we, side):
    a = np.searchsorted(ts, np.int64(ws.value), "left"); b = np.searchsorted(ts, np.int64(we.value), "left")
    if b - a < 2: return 0.0, 0.0, b - a, 0.0
    x = (ts[a:b] - ts[a]) / 1e9                       # elapsed seconds
    y = imb[a:b] * (1 if side == "long" else -1)      # oriented imbalance
    vx = x.var()
    slope = (np.cov(x, y)[0, 1] / vx) if vx > 0 else 0.0
    level = float(y.mean())
    pchg = float(mid[b - 1] - mid[a]) * (1 if side == "long" else -1)
    return float(slope), level, b - a, pchg


def auc_pair(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    gt = sum((a[:, None] > b[None, :]).sum() + 0.5 * (a[:, None] == b[None, :]).sum() for _ in [0])
    return gt / (len(a) * len(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--window-seconds", type=int, default=60)   # for Design A trailing window
    ap.add_argument("--out", default="queue_imbalance_slope_results.csv"); ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    Wd = pd.Timedelta(seconds=args.window_seconds)

    ep_path, windowed = load_paths(args.config)
    g = build_groups(ep_path, args.wrb)
    F = g[g.group == "failed_trades"].reset_index(drop=True); R = g[g.group == "target_reached"].reset_index(drop=True)

    # collect every window we must evaluate (primary anchors + Design A risk sets)
    jobs = []  # (tag, key, side, entry, ws, we)
    for _, r in g.iterrows():
        jobs.append(("primary", r.uid, r.side, r.entry, r.win_start, r.win_end))
    A_pairs = []
    for _, f in F.iterrows():
        cut = f["exit"]; jobs.append(("A_cut", f.uid, f.side, f.entry, max(f.entry, cut - Wd), cut))
        for _, rr in R[R.pt1_open_el > f.hold].iterrows():
            anc = rr.entry + pd.Timedelta(seconds=f.hold)
            jobs.append(("A_peer", (f.uid, rr.uid), rr.side, rr.entry, max(rr.entry, anc - Wd), anc))
            A_pairs.append((f.uid, rr.uid))

    t_min = min(j[4] for j in jobs); t_max = max(j[5] for j in jobs)
    print(f"[build] failed={len(F)} reached={len(R)} | A pairs={len(A_pairs)} | reading book in [{t_min},{t_max})")
    ts, imb, mid = read_book(windowed, t_min, t_max)
    print(f"[read] book snapshots: {len(ts):,}")

    prim, cut, peer, chk = {}, {}, {}, []
    for tag, key, side, entry, ws, we in jobs:
        s, lvl, n, pc = slope_feature(ts, imb, mid, entry, ws, we, side)
        if n >= 2: chk.append((lvl, pc))
        if tag == "primary": prim[key] = (s, lvl)
        elif tag == "A_cut": cut[key] = s
        else: peer[key] = s

    arr = np.array(chk)
    corr = np.corrcoef(arr[:, 0], arr[:, 1])[0, 1] if len(arr) > 5 else float("nan")
    print(f"[selfcheck] corr(mean oriented imbalance, oriented mid change) = {corr:.3f}  (expect > 0; "
          f"if < 0 the bid/ask size columns are swapped)")

    # ---- PRIMARY 52/40 and excl-22 ----
    gp = g.copy(); gp["slope"] = gp.uid.map(lambda u: prim[u][0]); gp["level"] = gp.uid.map(lambda u: prim[u][1])
    def prim_report(d, label):
        a = d.loc[d.group == "target_reached", "slope"]; b = d.loc[d.group == "failed_trades", "slope"]
        print(f"\n=== PRIMARY {label} (reached {len(a)}, failed {len(b)}) ===")
        print(f"  slope  median reached={a.median():+.4f}/s  failed={b.median():+.4f}/s  AUC(reached>failed)={auc_pair(a,b):.3f}")
        la = d.loc[d.group=='target_reached','level']; lb = d.loc[d.group=='failed_trades','level']
        print(f"  level  median reached={la.median():+.3f}    failed={lb.median():+.3f}   (descriptive)")
    prim_report(gp, "all (52/40)")
    prim_report(gp[~gp.is_entry_bar_pt1], "excl entry-bar-pt1 (30/40)")

    # ---- CONTROL: Design A cut-time-matched ----
    fe = []
    for _, f in F.iterrows():
        cv = cut[f.uid]; pv = np.array([peer[(f.uid, ru)] for ru in R[R.pt1_open_el > f.hold].uid])
        if len(pv): fe.append((np.sum(pv > cv) + 0.5 * np.sum(pv == cv)) / len(pv))
    fe = np.array(fe); rng = np.random.default_rng(args.seed)
    boot = np.array([rng.choice(fe, len(fe), True).mean() for _ in range(10000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"\n=== CONTROL Design A: cut-time-matched, W={args.window_seconds}s (slope) ===")
    print(f"  AUC(per-cut, {len(fe)}) = P(peer slope > cut slope) = {fe.mean():.3f}  95% CI [{lo:.3f}, {hi:.3f}]")

    gp.to_csv(args.out, index=False); print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
