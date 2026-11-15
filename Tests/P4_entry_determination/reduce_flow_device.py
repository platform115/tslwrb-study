#!/usr/bin/env python3
"""Per-second flow reduction for T-EN09 — RUN ON THE USER'S MAC (2026-11-15)
against /Volumes/2TB-Lexar/tslwrb_windowed/mbp10_{ESZ5_2025-10,ESH2_2022-02}_windowed.parquet
(instrument_ids 294973 / 5782). Output committed as Data/inputs/flow_per_sec_<month>.parquet
(checksums in Data/inputs/CHECKSUMS.sha256). Same construction as the exit program's
read_per_second: buyv = buy-aggressor volume, sellv = sell-aggressor volume, mid = last
(bid+ask)/2, grouped per epoch second. Usage: reduce_flow_device.py SRC IID OUT"""
import sys, numpy as np, pandas as pd
import pyarrow.parquet as pq, pyarrow as pa

src, iid, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
pf = pq.ParquetFile(src)
need = ["ts_event", "action", "side", "size", "bid_px_00", "ask_px_00", "instrument_id"]
miss = [c for c in need if c not in set(pf.schema_arrow.names)]
if miss: raise SystemExit(f"[schema] missing {miss}")
parts = []
for b in pf.iter_batches(batch_size=400_000, columns=need):
    m = b.column("instrument_id").to_numpy(zero_copy_only=False) == iid
    if not m.any(): continue
    idx = np.flatnonzero(m)
    ts = b.column("ts_event").cast(pa.timestamp("ns")).cast(pa.int64()).to_numpy(zero_copy_only=False)[idx]
    act = b.column("action").to_numpy(zero_copy_only=False)[idx]
    sd = b.column("side").to_numpy(zero_copy_only=False)[idx]
    sz = b.column("size").to_numpy(zero_copy_only=False)[idx].astype("int64")
    bp = b.column("bid_px_00").to_numpy(zero_copy_only=False)[idx]
    ap = b.column("ask_px_00").to_numpy(zero_copy_only=False)[idx]
    is_t = act == "T"
    df = pd.DataFrame({"sec": ts // 1_000_000_000,
                       "buyv": np.where(is_t & (sd == "B"), sz, 0),
                       "sellv": np.where(is_t & (sd == "A"), sz, 0),
                       "mid": (bp + ap) / 2})
    parts.append(df.groupby("sec").agg(buyv=("buyv","sum"), sellv=("sellv","sum"), mid=("mid","last")))
o = pd.concat(parts).groupby(level=0).agg(buyv=("buyv","sum"), sellv=("sellv","sum"),
                                          mid=("mid","last")).sort_index().reset_index()
o.to_parquet(out, index=False)
print(f"rows={len(o)} span={pd.to_datetime(o.sec.min(),unit='s')}..{pd.to_datetime(o.sec.max(),unit='s')} -> {out}")
