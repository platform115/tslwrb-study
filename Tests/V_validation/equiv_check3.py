#!/usr/bin/env python3
"""Stage 1 - EQUIVALENCE (T: converter certification, no validation data).
From raw MBP-10 day 20241105: (a) emulate tbbo (action=T rows with top),
(b) emulate bbo-1s (last top per second). Run the NEW converter aggregation
on the emulations and compare vs the OLD pipeline's committed
flow_per_sec_2024-11_full.parquet on that day's seconds.
Writes progress to equiv3_progress.txt and results to equiv3_result.json.
"""
import json, os, sys, traceback
import numpy as np
import pandas as pd
import pyarrow.parquet as pq, pyarrow as pa

D = os.path.expanduser("~/mnt/2TB-Lexar")
TMP = os.path.join(D, "_equiv_tmp")
OUTD = os.path.join(D, "val_pipeline")
PROG = os.path.join(OUTD, "equiv3_progress.txt")
def log(m):
    with open(PROG, "a") as f:
        f.write(m + "\n")

try:
    log("start decode 20241105")
    from databento import DBNStore
    src = os.path.join(TMP, "glbx-mdp3-20241105.mbp-10.dbn.zst")
    pqt = os.path.join(TMP, "day1105.parquet")
    if not os.path.exists(pqt):
        DBNStore.from_file(src).to_parquet(pqt)
    log("decoded")
    # old pipeline's front id for 2024-11: resolve from committed flow by
    # volume? The old file doesn't store id. Resolve = highest trade volume
    # in THIS day among ids (ESZ4 dominates mid-month).
    pf = pq.ParquetFile(pqt)
    NEED = ["ts_event", "action", "side", "size",
            "bid_px_00", "ask_px_00", "bid_sz_00", "ask_sz_00",
            "instrument_id"]
    names = set(pf.schema_arrow.names)
    cols = [c for c in NEED if c in names]
    vol = {}
    for b in pf.iter_batches(batch_size=400_000,
                             columns=["action", "instrument_id", "size"]):
        act = b.column("action").to_numpy(zero_copy_only=False)
        ids = b.column("instrument_id").to_numpy(zero_copy_only=False)
        sz = b.column("size").to_numpy(zero_copy_only=False).astype("int64")
        m = act == "T"
        u, inv = np.unique(ids[m], return_inverse=True)
        s = np.zeros(len(u), "int64"); np.add.at(s, inv, sz[m])
        for k, v in zip(u, s):
            vol[int(k)] = vol.get(int(k), 0) + int(v)
    iid = max(vol, key=vol.get)
    log(f"front id {iid} vol {vol[iid]}")
    # emulate tbbo (trades w/ top) and bbo-1s (last top per sec); aggregate
    tb_parts, bb_last = [], {}
    for b in pf.iter_batches(batch_size=400_000, columns=cols):
        ids = b.column("instrument_id").to_numpy(zero_copy_only=False)
        m = ids == iid
        if not m.any():
            continue
        ts = b.column("ts_event").cast(pa.timestamp("ns")).cast(
            pa.int64()).to_numpy(zero_copy_only=False)[m]
        act = b.column("action").to_numpy(zero_copy_only=False)[m]
        sd = b.column("side").to_numpy(zero_copy_only=False)[m]
        sz = b.column("size").to_numpy(zero_copy_only=False)[m].astype("int64")
        bp = b.column("bid_px_00").to_numpy(zero_copy_only=False)[m].astype("float64")
        ap = b.column("ask_px_00").to_numpy(zero_copy_only=False)[m].astype("float64")
        if np.nanmedian(ap[ap > 0]) > 1e6:
            bp, ap = bp / 1e9, ap / 1e9
        sec = ts // 1_000_000_000
        it = act == "T"
        tb_parts.append(pd.DataFrame({
            "sec": sec[it],
            "buyv": np.where(sd[it] == "B", sz[it], 0),
            "sellv": np.where(sd[it] == "A", sz[it], 0)}))
        # bbo-1s emulation: last top state per second (any event)
        ok = (bp > 0) & (ap > 0)
        if ok.any():
            dfb = pd.DataFrame({"sec": sec[ok],
                                "mid": (bp[ok] + ap[ok]) / 2})
            last = dfb.groupby("sec").last()
            for s_, m_ in zip(last.index, last.mid):
                bb_last[int(s_)] = float(m_)
    TB = pd.concat(tb_parts).groupby("sec")[["buyv", "sellv"]].sum()
    BB = pd.Series(bb_last).sort_index()
    log(f"emulated: {len(TB)} trade-secs, {len(BB)} book-secs")
    # NEW converter output shape: sec/buyv/sellv/mid on the union of secs
    secs = BB.index.to_numpy()
    out = pd.DataFrame({"sec": secs, "mid": BB.to_numpy()})
    out = out.merge(TB.reset_index(), on="sec", how="left").fillna(0)
    # compare vs old committed flow for this day
    old = pd.read_parquet(os.path.join(
        D, "tslwrb_windowed", "flow_per_sec_2024-11_full.parquet"))
    lo, hi = int(secs.min()), int(secs.max())
    old = old[(old.sec >= lo) & (old.sec <= hi)]
    j = old.merge(out, on="sec", suffixes=("_old", "_new"), how="inner")
    res = dict(
        day="20241105", front_id=iid,
        old_secs=int(len(old)), new_secs=int(len(out)),
        joined=int(len(j)),
        buyv_exact=float((j.buyv_old == j.buyv_new).mean()),
        sellv_exact=float((j.sellv_old == j.sellv_new).mean()),
        buyv_sum_old=int(j.buyv_old.sum()), buyv_sum_new=int(j.buyv_new.sum()),
        sellv_sum_old=int(j.sellv_old.sum()), sellv_sum_new=int(j.sellv_new.sum()),
        mid_equal=float((np.abs(j.mid_old - j.mid_new) < 1e-9).mean()),
        mid_within_tick=float((np.abs(j.mid_old - j.mid_new) <= 0.25).mean()),
        mid_max_abs=float(np.abs(j.mid_old - j.mid_new).max()),
        secs_only_old=int(len(set(old.sec) - set(out.sec))),
        secs_only_new=int(len(set(out.sec) - set(old.sec))))
    with open(os.path.join(OUTD, "equiv3_result.json"), "w") as f:
        json.dump(res, f, indent=1)
    log("DONE " + json.dumps(res))
except Exception:
    log("ERROR\n" + traceback.format_exc())
