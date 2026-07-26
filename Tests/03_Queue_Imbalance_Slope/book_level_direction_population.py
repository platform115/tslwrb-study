#!/usr/bin/env python3
"""
book_level_direction_population.py
-------------------------------------------------------------------------------
Population diagnostic (NOT a hypothesis test of the 52/40 groups). Establishes, on the full book-
snapshot population in the windowed parquet, the SIGN / DEPTH / HORIZON of the relationship between
queue-imbalance LEVEL and forward mid return. Output is a durable convention -> promote the chosen
(sign, depth, horizon) into CURRENT_STATE and use it to re-orient Test 03 and to build Phase B.

Independent of trade outcomes, so using it to set feature orientation is legitimate (not post-hoc on
the group labels). Memory-safe: streams batches, downsamples to one snapshot per second.

imbalance(depth) = (Sum bid_sz[:depth] - Sum ask_sz[:depth]) / (Sum both)   in [-1,1]
forward return(h) = mid(t+h) - mid(t)        mid = (bid_px_00 + ask_px_00)/2
Reported per (depth, horizon): Pearson corr(imbalance, forward return) and directional hit-rate
P(sign imbalance == sign forward return). corr>0 => bid-heavy predicts UP (continuation); corr<0 =>
bid-heavy precedes DOWN (price moves toward the heavy side / absorption).

    python3 book_level_direction_population.py --config config.toml
"""

import argparse, tomllib
import numpy as np, pandas as pd

INSTRUMENT_ID = 294973
TS_COL = "ts_event"
BID_SZ = [f"bid_sz_0{i}" for i in range(10)]
ASK_SZ = [f"ask_sz_0{i}" for i in range(10)]
BID_PX0, ASK_PX0 = "bid_px_00", "ask_px_00"
DEPTHS = {"L1": 1, "L1-5": 5, "L1-10": 10}
HORIZONS = [1, 5, 15, 30, 60]            # seconds


def load_windowed(config_path):
    with open(config_path, "rb") as f:
        return tomllib.load(f).get("run", {}).get("resolved", {}).get("windowed_parquet")


def stream_per_second(windowed):
    """Return a per-second frame: index ts_sec (int), cols mid, imb_L1, imb_L5, imb_L10. Memory-safe."""
    import pyarrow.parquet as pq, pyarrow as pa
    need = [TS_COL, BID_PX0, ASK_PX0, "instrument_id"] + BID_SZ + ASK_SZ
    pf = pq.ParquetFile(windowed)
    miss = [c for c in need if c not in set(pf.schema_arrow.names)]
    if miss:
        raise SystemExit(f"[schema] missing {miss}")
    parts = []
    for b in pf.iter_batches(batch_size=200_000, columns=need):
        ts = b.column(TS_COL).cast(pa.timestamp("ns")).cast(pa.int64()).to_numpy(zero_copy_only=False)
        keep = np.ones(len(ts), bool)
        if INSTRUMENT_ID is not None:
            keep = b.column("instrument_id").to_numpy(zero_copy_only=False) == INSTRUMENT_ID
        if not keep.any():
            continue
        idx = np.flatnonzero(keep)
        bs = np.stack([b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64") for c in BID_SZ], 1)
        as_ = np.stack([b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64") for c in ASK_SZ], 1)
        mid = (b.column(BID_PX0).to_numpy(zero_copy_only=False)[idx] +
               b.column(ASK_PX0).to_numpy(zero_copy_only=False)[idx]) / 2
        d = {"ts_sec": ts[idx] // 1_000_000_000, "mid": mid}
        for name, k in DEPTHS.items():
            bsum = bs[:, :k].sum(1); asum = as_[:, :k].sum(1); tot = bsum + asum
            d[f"imb_{name}"] = np.where(tot > 0, (bsum - asum) / np.where(tot > 0, tot, 1), np.nan)
        df = pd.DataFrame(d)
        parts.append(df.groupby("ts_sec").last())        # last snapshot per second, per batch
    if not parts:
        raise SystemExit("[read] no rows")
    out = pd.concat(parts).groupby(level=0).last().sort_index()   # cross-batch dedup
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", default="book_level_direction_population.csv")
    args = ap.parse_args()
    windowed = load_windowed(args.config)
    print(f"[read] streaming per-second snapshots from {windowed} ...")
    g = stream_per_second(windowed)
    print(f"[read] per-second snapshots: {len(g):,} (span {len(g)/3600:.1f} grid-hours)")

    mid = g["mid"]
    rows = []
    for h in HORIZONS:
        fwd = mid.reindex(mid.index + h).to_numpy() - mid.to_numpy()   # NaN across gaps/sessions
        for name in DEPTHS:
            x = g[f"imb_{name}"].to_numpy()
            ok = ~np.isnan(fwd) & ~np.isnan(x)
            xo, fo = x[ok], fwd[ok]
            corr = np.corrcoef(xo, fo)[0, 1] if len(xo) > 100 else np.nan
            nz = (xo != 0) & (fo != 0)
            hit = float(np.mean(np.sign(xo[nz]) == np.sign(fo[nz]))) if nz.any() else np.nan
            rows.append(dict(horizon_s=h, depth=name, n=int(ok.sum()), corr=round(corr, 4),
                             dir_hit_rate=round(hit, 4)))
    res = pd.DataFrame(rows)
    res.to_csv(args.out, index=False)
    print("\ncorr(imbalance LEVEL, forward mid return):  >0 = bid-heavy->UP (continuation); <0 = ->toward heavy side")
    print(res.pivot(index="depth", columns="horizon_s", values="corr").to_string())
    print("\ndirectional hit-rate (sign agreement; 0.5 = none):")
    print(res.pivot(index="depth", columns="horizon_s", values="dir_hit_rate").to_string())
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
