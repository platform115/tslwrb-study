#!/usr/bin/env python3
"""Stage 2 v3 - resumable per-day conversion of the purchased months.
Each invocation works up to ~140s then exits "CONTINUE"; when every day
part exists it assembles outputs + QA and prints "ALL DONE".
Conventions certified by equiv_check3 (buyv: side B; sellv: side A;
mid last-in-second; front id = top volume over last 3 tbbo day-files)."""
import glob, json, os, re, time, zipfile
import numpy as np
import pandas as pd
import pyarrow.parquet as pq, pyarrow as pa
from databento import DBNStore

T0 = time.time()
BUDGET = 140
D = os.path.expanduser("~/mnt/2TB-Lexar")
OUTD = os.path.join(D, "val_pipeline")
PARTS = os.path.join(OUTD, "parts")
TMP = os.path.join(D, "_flow_tmp")
os.makedirs(PARTS, exist_ok=True)
os.makedirs(TMP, exist_ok=True)
JOBS = {"2023-05": ("GLBX-20261126-LJNLAWJDTM.zip",
                    "GLBX-20261126-LP5HY33ATB.zip"),
        "2024-05": ("GLBX-20261126-5QRJSDPDXY.zip",
                    "GLBX-20261126-ND57PU8Q5X.zip")}

def decode(zf, member):
    raw = os.path.join(TMP, os.path.basename(member) + ".tmp")
    with zf.open(member) as src, open(raw, "wb") as dst:
        while chunk := src.read(1 << 24):
            dst.write(chunk)
    pqt = raw + ".parquet"
    DBNStore.from_file(raw).to_parquet(pqt)
    return pqt

def px(col, m):
    v = col.to_numpy(zero_copy_only=False)[m].astype("float64")
    good = v[v > 0]
    if len(good) and np.nanmedian(good) > 1e6:
        v = v / 1e9
    return v

for mo, (ztb, zbb) in JOBS.items():
    fjson = os.path.join(OUTD, f"front_{mo}.json")
    zf_tb = zipfile.ZipFile(os.path.join(D, ztb))
    zf_bb = zipfile.ZipFile(os.path.join(D, zbb))
    tb_days = sorted(m for m in zf_tb.namelist()
                     if m.endswith(".tbbo.dbn.zst"))
    bb_days = sorted(m for m in zf_bb.namelist()
                     if m.endswith(".bbo-1s.dbn.zst"))
    if not os.path.exists(fjson):
        vol = {}
        for member in tb_days[-3:]:
            pqt = decode(zf_tb, member)
            pf = pq.ParquetFile(pqt)
            for b in pf.iter_batches(batch_size=400_000,
                                     columns=["instrument_id", "size"]):
                ids = b.column("instrument_id").to_numpy(
                    zero_copy_only=False)
                sz = b.column("size").to_numpy(zero_copy_only=False
                                               ).astype("int64")
                u, inv = np.unique(ids, return_inverse=True)
                s = np.zeros(len(u), "int64"); np.add.at(s, inv, sz)
                for k, v in zip(u, s):
                    vol[int(k)] = vol.get(int(k), 0) + int(v)
        iid = max(vol, key=vol.get)
        json.dump(dict(front_id=iid, vol=vol[iid]), open(fjson, "w"))
        print(f"{mo} front id {iid}")
        if time.time() - T0 > BUDGET:
            print("CONTINUE"); raise SystemExit
    iid = json.load(open(fjson))["front_id"]
    for member in tb_days:
        day = re.search(r"(\d{8})", member).group(1)
        part = os.path.join(PARTS, f"tb_{mo}_{day}.parquet")
        if os.path.exists(part):
            continue
        pqt = decode(zf_tb, member)
        pf = pq.ParquetFile(pqt)
        tb_p, qa_p = [], []
        for b in pf.iter_batches(batch_size=400_000):
            ids = b.column("instrument_id").to_numpy(zero_copy_only=False)
            m = ids == iid
            if not m.any():
                continue
            ts = b.column("ts_event").cast(pa.timestamp("ns")).cast(
                pa.int64()).to_numpy(zero_copy_only=False)[m]
            sd = b.column("side").to_numpy(zero_copy_only=False)[m]
            sz = b.column("size").to_numpy(zero_copy_only=False
                                           )[m].astype("int64")
            bp = px(b.column("bid_px_00"), m)
            ap = px(b.column("ask_px_00"), m)
            sec = ts // 1_000_000_000
            tb_p.append(pd.DataFrame({
                "sec": sec,
                "buyv": np.where(sd == "B", sz, 0),
                "sellv": np.where(sd == "A", sz, 0)}))
            ok = (bp > 0) & (ap > 0)
            qa_p.append(pd.DataFrame({"sec": sec[ok],
                                      "tmid": (bp[ok] + ap[ok]) / 2}
                                     ).groupby("sec").last(
                                     ).reset_index())
        TB = (pd.concat(tb_p).groupby("sec")[["buyv", "sellv"]].sum()
              if tb_p else pd.DataFrame(columns=["buyv", "sellv"]))
        QA = (pd.concat(qa_p).groupby("sec").last()
              if qa_p else pd.DataFrame(columns=["tmid"]))
        TB.reset_index().to_parquet(part, index=False)
        QA.reset_index().to_parquet(
            os.path.join(PARTS, f"qa_{mo}_{day}.parquet"), index=False)
        print(f"{mo} tb {day} ok")
        if time.time() - T0 > BUDGET:
            print("CONTINUE"); raise SystemExit
    for member in bb_days:
        day = re.search(r"(\d{8})", member).group(1)
        part = os.path.join(PARTS, f"bb_{mo}_{day}.parquet")
        if os.path.exists(part):
            continue
        pqt = decode(zf_bb, member)
        pf = pq.ParquetFile(pqt)
        bb_p = []
        for b in pf.iter_batches(batch_size=400_000):
            ids = b.column("instrument_id").to_numpy(zero_copy_only=False)
            m = ids == iid
            if not m.any():
                continue
            ts = b.column("ts_event").cast(pa.timestamp("ns")).cast(
                pa.int64()).to_numpy(zero_copy_only=False)[m]
            bp = px(b.column("bid_px_00"), m)
            ap = px(b.column("ask_px_00"), m)
            bs = b.column("bid_sz_00").to_numpy(zero_copy_only=False
                                                )[m].astype("int64")
            as_ = b.column("ask_sz_00").to_numpy(zero_copy_only=False
                                                 )[m].astype("int64")
            sec = ts // 1_000_000_000
            ok = (bp > 0) & (ap > 0)
            bb_p.append(pd.DataFrame({
                "sec": sec[ok], "mid": (bp[ok] + ap[ok]) / 2,
                "bid0": bs[ok], "ask0": as_[ok]}
                ).groupby("sec").last().reset_index())
        BB = (pd.concat(bb_p).groupby("sec").last()
              if bb_p else pd.DataFrame(columns=["mid", "bid0", "ask0"]))
        BB.reset_index().to_parquet(part, index=False)
        print(f"{mo} bb {day} ok")
        if time.time() - T0 > BUDGET:
            print("CONTINUE"); raise SystemExit
# assembly
for mo in JOBS:
    fout = os.path.join(OUTD, f"flow_per_sec_{mo}_full.parquet")
    bout = os.path.join(OUTD, f"book_top_per_sec_{mo}.parquet")
    # always rebuild (stale outputs from the filename bug are overwritten)
    tbs = sorted(glob.glob(os.path.join(PARTS, f"tb_{mo}_*.parquet")))
    bbs = sorted(p for p in glob.glob(os.path.join(PARTS, f"bb_{mo}_*.parquet")) if re.search(r"bb_.+_\d{8}\.parquet$", p))
    qas = sorted(glob.glob(os.path.join(PARTS, f"qa_{mo}_*.parquet")))
    TB = pd.concat([pd.read_parquet(p) for p in tbs]).groupby(
        "sec")[["buyv", "sellv"]].sum()
    BB = pd.concat([pd.read_parquet(p) for p in bbs]).groupby(
        "sec").last().sort_index()
    QA = pd.concat([pd.read_parquet(p) for p in qas]).groupby(
        "sec").last()
    flow = BB[["mid"]].reset_index().merge(
        TB.reset_index(), on="sec", how="left").fillna(
        {"buyv": 0, "sellv": 0})
    flow[["buyv", "sellv"]] = flow[["buyv", "sellv"]].astype("int64")
    flow[["sec", "buyv", "sellv", "mid"]].to_parquet(fout, index=False)
    BB[["bid0", "ask0"]].reset_index().to_parquet(bout, index=False)
    qj = QA.merge(BB[["mid"]], left_index=True, right_index=True,
                  how="inner")
    qa = dict(month=mo, front_id=json.load(
        open(os.path.join(OUTD, f"front_{mo}.json")))["front_id"],
        flow_secs=int(len(flow)), trade_secs=int(len(TB)),
        mid_vs_tbbo_within_tick=float(
            (np.abs(qj.tmid - qj.mid) <= 0.25).mean()),
        mid_vs_tbbo_max=float(np.abs(qj.tmid - qj.mid).max()))
    json.dump(qa, open(os.path.join(OUTD, f"qa_{mo}.json"), "w"),
              indent=1)
    print(f"{mo} assembled: {qa}")
print("ALL DONE")
