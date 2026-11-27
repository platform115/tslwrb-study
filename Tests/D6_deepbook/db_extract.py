#!/usr/bin/env python3
"""db_extract.py — T-BK02 on-device moment-feature extractor.
Streams the windowed MBP-10 parquet row-group by row-group, buffers
events for active moment windows ([t-35, t]), finalizes standardized
microstructure features per moment. Resumable: state pickled between
invocations. Modes: cert (reconcile one window's trade volume + last
mid vs the committed per-second flow file), run (continue until time
budget), status.
"""
import os, pickle, sys, time
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

T0 = time.time()
BUDGET = 130
D = os.path.expanduser("~/mnt/2TB-Lexar")
W = os.path.expanduser("~/mnt/tslwrb_windowed")
OUTD = os.path.join(D, "val_pipeline")
FILES = {"2022-02": "mbp10_ESH2_2022-02_windowed.parquet",
         "2025-10": "mbp10_ESZ5_2025-10_windowed.parquet"}
STATE = os.path.join(OUTD, "db_state.pkl")
RES = os.path.join(OUTD, "db_features.parquet")
LVL = [f"{s}_{k}_{i:02d}" for s in ("bid", "ask")
       for k in ("px", "sz") for i in range(10)]
COLS = ["ts_event", "action", "side", "size", "price"] + LVL

q1 = pd.read_csv(os.path.join(OUTD, "moments_q1.csv"))
q1["q"] = "q1"
q2 = pd.read_csv(os.path.join(OUTD, "moments_q2.csv"))
q2["q"] = "q2"
q2 = q2.rename(columns={"ep": "cid", "taken": "role"})
M = pd.concat([q1, q2], ignore_index=True)
M["mid_id"] = np.arange(len(M))

def feats(df, sdn):
    n = len(df)
    if n < 10:
        return None
    out = {}
    bpx = df[[f"bid_px_{i:02d}" for i in range(10)]].to_numpy(float)
    apx = df[[f"ask_px_{i:02d}" for i in range(10)]].to_numpy(float)
    bsz = df[[f"bid_sz_{i:02d}" for i in range(10)]].to_numpy(float)
    asz = df[[f"ask_sz_{i:02d}" for i in range(10)]].to_numpy(float)
    def ofi_level(px, sz):
        dpx = np.diff(px)
        e = np.where(dpx > 0, sz[1:],
                     np.where(dpx < 0, -sz[:-1],
                              sz[1:] - sz[:-1]))
        return np.nansum(e)
    ofi_b = ofi_level(bpx[:, 0], bsz[:, 0])
    ofi_a = ofi_level(apx[:, 0], asz[:, 0])
    out["OFI"] = (ofi_b - ofi_a) * sdn
    o10 = 0.0
    for k in range(10):
        o10 += ofi_level(bpx[:, k], bsz[:, k]) \
            - ofi_level(apx[:, k], asz[:, k])
    out["OFI10"] = o10 * sdn
    opx = apx[:, 0] if sdn > 0 else bpx[:, 0]
    osz = asz[:, 0] if sdn > 0 else bsz[:, 0]
    same = np.diff(opx) == 0
    d_ = np.diff(osz)
    mean_sz = max(np.nanmean(osz), 1.0)
    out["depl_opp"] = -d_[same & (d_ < 0)].sum() / 35.0 / mean_sz
    out["repl_opp"] = d_[same & (d_ > 0)].sum() / 35.0 / mean_sz
    act = df.action.to_numpy()
    sd_ = df.side.to_numpy()
    px = df.price.to_numpy(float)
    sz = df["size"].to_numpy(float)
    oppch = "A" if sdn > 0 else "B"
    at_best = np.abs(px - opx) <= 0.26
    nC = int(((act == "C") & (sd_ == oppch) & at_best).sum())
    nT_opp = int(((act == "T") & (sd_ == oppch)).sum())
    out["cancel_ratio"] = nC / max(nC + nT_opp, 1)
    isT = act == "T"
    tvol = sz[isT].sum()
    out["large_lot"] = sz[isT & (sz >= 10)].sum() / max(tvol, 1.0)
    prev_bsz = np.concatenate([[np.nan], bsz[:-1, 0]])
    prev_asz = np.concatenate([[np.nan], asz[:-1, 0]])
    disp = np.where(sd_ == "B", prev_asz, prev_bsz)
    out["hidden"] = int((isT & (sz > disp)).sum())
    prev_bb = np.concatenate([[np.nan], bpx[:-1, 0]])
    prev_ba = np.concatenate([[np.nan], apx[:-1, 0]])
    ref = np.where(sd_ == "B", prev_ba, prev_bb)
    out["sweep"] = int((isT & (np.abs(px - ref) >= 0.5)).sum())
    out["n_events"] = n
    out["t_vol"] = float(tvol)
    return out

mode = sys.argv[1] if len(sys.argv) > 1 else "run"

if mode == "cert":
    # one Q1 moment window in 2022-02: per-second trade vol + last mid
    mo = "2022-02"
    mm = M[(M.month == mo)].iloc[0]
    t_end = int(mm.t); t0 = t_end - 35
    pf = pq.ParquetFile(os.path.join(W, FILES[mo]))
    rows = []
    for b in pf.iter_batches(batch_size=400_000, columns=COLS):
        ts = b.column("ts_event").cast("int64").to_numpy(
            zero_copy_only=False) // 10**9
        if ts[0] > t_end:
            break
        m_ = (ts >= t0) & (ts <= t_end)
        if m_.any():
            d = b.to_pandas()[m_]
            d["sec"] = ts[m_]
            rows.append(d)
    d = pd.concat(rows)
    isT = d.action == "T"
    vol = d[isT].groupby("sec")["size"].sum()
    mid = ((d.bid_px_00 + d.ask_px_00) / 2).groupby(d.sec).last()
    fl = pd.read_parquet(os.path.join(
        W, f"flow_per_sec_{mo}_full.parquet"))
    fl = fl[(fl.sec >= t0) & (fl.sec <= t_end)]
    j = fl.set_index("sec").join(vol.rename("ev_vol")).join(
        mid.rename("ev_mid"))
    tv = (j.buyv + j.sellv).fillna(0)
    ev = j.ev_vol.fillna(0)
    print(f"CERT window {t0}-{t_end}: secs={len(j)}; "
          f"vol exact match {int((tv == ev).sum())}/{len(j)}; "
          f"mid exact {int((np.abs(j.mid - j.ev_mid) < 1e-9).sum())}"
          f"/{int(j.ev_mid.notna().sum())} of covered")
    sys.exit(0)

if os.path.exists(STATE):
    st = pickle.load(open(STATE, "rb"))
else:
    st = dict(month_ix=0, group=0, buffers={}, done=[])
months = list(FILES)
res_rows = st["done"]
while st["month_ix"] < len(months):
    mo = months[st["month_ix"]]
    mm = M[M.month == mo].sort_values("t").reset_index(drop=True)
    pf = pq.ParquetFile(os.path.join(W, FILES[mo]))
    ng = pf.metadata.num_row_groups
    while st["group"] < ng:
        b = pf.read_row_group(st["group"], columns=COLS).to_pandas()
        ts = b.ts_event.astype("int64").to_numpy() // 10**9
        b["sec"] = ts
        tmin, tmax = int(ts[0]), int(ts[-1])
        act_m = mm[(mm.t >= tmin - 1) & (mm.t - 35 <= tmax)]
        for _, r in act_m.iterrows():
            w = b[(b.sec >= r.t - 35) & (b.sec <= r.t)]
            if len(w):
                key = int(r.mid_id)
                st["buffers"].setdefault(key, []).append(
                    w.drop(columns=["ts_event"]))
        for key in list(st["buffers"]):
            r = M.iloc[key]
            if r.t < tmin - 1 or r.month != mo:
                df = pd.concat(st["buffers"].pop(key))
                f = feats(df, int(r.side))
                if f is not None:
                    f.update(dict(mid_id=key, month=r.month,
                                  t=int(r.t), side=int(r.side),
                                  cid=int(r.cid), role=int(r.role),
                                  q=r.q))
                    res_rows.append(f)
        st["group"] += 1
        if time.time() - T0 > BUDGET:
            st["done"] = res_rows
            pickle.dump(st, open(STATE, "wb"))
            print(f"CONTINUE {mo} group {st['group']}/{ng} "
                  f"({len(res_rows)} moments done)")
            sys.exit(0)
    for key in list(st["buffers"]):
        r = M.iloc[key]
        if r.month == mo:
            df = pd.concat(st["buffers"].pop(key))
            f = feats(df, int(r.side))
            if f is not None:
                f.update(dict(mid_id=key, month=r.month, t=int(r.t),
                              side=int(r.side), cid=int(r.cid),
                              role=int(r.role), q=r.q))
                res_rows.append(f)
    st["month_ix"] += 1
    st["group"] = 0
pd.DataFrame(res_rows).to_parquet(RES, index=False)
print(f"ALL DONE: {len(res_rows)} moment-feature rows -> {RES}")
