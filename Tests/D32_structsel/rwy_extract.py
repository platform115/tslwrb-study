#!/usr/bin/env python3
"""rwy_extract.py — T-SR06 on-device extractor (raw MBP-10 path).
Decodes raw GLBX day files, filters the front contract, buffers
[t-35, t] windows for all 1,264 touch moments, computes db3's
feats_multi VERBATIM per moment. Resumable day-by-day.
Modes: status | run | cert | concat
"""
import glob, json, os, sys, time
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

T0 = time.time()
BUDGET = 150
D = os.path.expanduser("~/mnt/2TB-Lexar")
W = os.path.expanduser("~/mnt/tslwrb_windowed")
OUTD = os.path.join(D, "val_pipeline")
PARTS = os.path.join(OUTD, "rwy_parts")
os.makedirs(PARTS, exist_ok=True)
STATE = os.path.join(OUTD, "rwy_state.json")
RAW = {"2022-02": os.path.join(D, "GLBX-20260607-UDES9FRSPK"),
       "2025-10": os.path.join(D, "GLBX-20260606-B8YDY9S86Q")}
WFILES = {"2022-02": "mbp10_ESH2_2022-02_windowed.parquet",
          "2025-10": "mbp10_ESZ5_2025-10_windowed.parquet"}
LVL = [f"{s}_{k}_{i:02d}" for s in ("bid", "ask")
       for k in ("px", "sz") for i in range(10)]
COLS = ["ts_event", "action", "side", "size", "price",
        "instrument_id"] + LVL

M = pd.read_csv(os.path.join(OUTD, "lvl_touch_moments_rwy.csv"))
M["mid_id"] = np.arange(len(M))
M["day"] = pd.to_datetime(M.t, unit="s").dt.strftime("%Y%m%d")

def front_id(mo):
    pf = pq.ParquetFile(os.path.join(W, WFILES[mo]))
    b = pf.read_row_group(0, columns=["instrument_id"])
    u = np.unique(b.column("instrument_id").to_numpy(
        zero_copy_only=False))
    assert len(u) == 1, u
    return int(u[0])

def pxfix(v):
    v = v.astype("float64")
    good = v[np.isfinite(v) & (v > 0)]
    if len(good) and np.nanmedian(good) > 1e6:
        v = v / 1e9
    return v

def feats_one(df, sdn):
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

def feats_multi(df, sdn, t_end):
    out = {}
    for h in (3, 10, 30):
        w = df[df.sec >= t_end - h]
        fh = feats_one(w, sdn)
        if fh is None:
            fh = {}
        for k, v in fh.items():
            out[f"{k}_{h}"] = v
    return out if out else None

st = json.load(open(STATE)) if os.path.exists(STATE) \
    else {"done": []}
st.setdefault("pending", None)
jobs = []
for mo in RAW:
    for day in sorted(M[M.month == mo].day.unique()):
        key = f"{mo}:{day}"
        if key not in st["done"]:
            jobs.append((mo, day))

mode = sys.argv[1] if len(sys.argv) > 1 else "status"
if mode == "status":
    print(f"days done {len(st['done'])}, remaining {len(jobs)}")
    sys.exit(0)

if mode == "concat":
    ps = sorted(glob.glob(os.path.join(PARTS, "*.parquet")))
    df = pd.concat([pd.read_parquet(p) for p in ps],
                   ignore_index=True)
    df.to_parquet(os.path.join(OUTD, "rwy_features.parquet"),
                  index=False)
    print(f"concat {len(ps)} parts -> {len(df)} rows")
    sys.exit(0)

if mode == "cert":
    ps = sorted(glob.glob(os.path.join(PARTS, "*.parquet")))
    if not ps:
        print("no parts yet"); sys.exit(0)
    R = pd.concat([pd.read_parquet(p) for p in ps],
                  ignore_index=True)
    F3 = pd.read_parquet(os.path.join(OUTD, "db3_features.parquet"))
    mb = pd.read_csv(os.path.join(OUTD, "moments_mb.csv"))
    F3 = F3[F3.q == "mb"].merge(
        mb[["cid", "month", "t", "side"]], on="cid",
        suffixes=("", "_m"))
    j = R.merge(F3, left_on=["month", "t", "side"],
                right_on=["month", "t", "side"],
                suffixes=("", "_old"))
    bad = 0
    for c in ("depl_opp_3", "repl_opp_3", "sweep_3", "OFI10_3"):
        d_ = (j[c] - j[f"{c}_old"]).abs()
        nb = int((d_ > 1e-6).sum())
        print(f"{c}: overlap {d_.notna().sum()}, mismatches {nb}, "
              f"max|d| {d_.max():.2e}")
        bad += nb
    print("CERT", "PASS" if bad == 0 else "FAIL")
    sys.exit(0 if bad == 0 else 1)

# mode == run — phase machine: decode | extract, one day at a time
try:
    from databento import DBNStore
except Exception as e:
    print("databento import failed:", e); sys.exit(1)
FID = {mo: front_id(mo) for mo in RAW}
tmp = os.path.join(OUTD, "rwy_tmp_day.parquet")

def do_extract(mo, day):
    mm = M[(M.month == mo) & (M.day == day)]
    bufs = {int(r.mid_id): [] for r in mm.itertuples()}
    pf = pq.ParquetFile(tmp)
    have = set(pf.schema_arrow.names)
    cols = [c for c in COLS if c in have]
    md = pf.metadata
    names = [md.row_group(0).column(c).path_in_schema
             for c in range(md.row_group(0).num_columns)]
    ci = names.index("ts_event")
    wins = [(int(r.t) - 35, int(r.t)) for r in mm.itertuples()]
    for g in range(md.num_row_groups):
        stat = md.row_group(g).column(ci).statistics
        g0 = int(pd.Timestamp(stat.min).value // 10**9)
        g1 = int(pd.Timestamp(stat.max).value // 10**9)
        if not any(w0 <= g1 and w1 >= g0 for w0, w1 in wins):
            continue
        b = pf.read_row_group(g, columns=cols).to_pandas()
        b = b[b.instrument_id.to_numpy() == FID[mo]]
        if not len(b):
            continue
        ts = b.ts_event.astype("int64").to_numpy() // 10**9
        b = b.assign(sec=ts)
        for r in mm.itertuples():
            w = b[(b.sec >= int(r.t) - 35) & (b.sec <= int(r.t))]
            if len(w):
                bufs[int(r.mid_id)].append(
                    w.drop(columns=["ts_event", "instrument_id"]))
    rows = []
    for r in mm.itertuples():
        parts = bufs[int(r.mid_id)]
        row = dict(mid_id=int(r.mid_id), month=mo, t=int(r.t),
                   side=int(r.side), level=float(r.level),
                   rwy=float(r.rwy))
        if parts:
            df = pd.concat(parts, ignore_index=True)
            for c in ["price"] + [f"{s_}_px_{i:02d}"
                                  for s_ in ("bid", "ask")
                                  for i in range(10)]:
                df[c] = pxfix(df[c].to_numpy())
            f_ = feats_multi(df, int(r.side), int(r.t))
            if f_:
                row.update(f_)
        rows.append(row)
    pd.DataFrame(rows).to_parquet(
        os.path.join(PARTS, f"{mo}_{day}.parquet"), index=False)

while True:
    el = time.time() - T0
    if st["pending"]:
        mo, day = st["pending"]
        if el > 110:
            break
        do_extract(mo, day)
        st["done"].append(f"{mo}:{day}")
        st["pending"] = None
        json.dump(st, open(STATE, "w"))
        print(f"{mo}:{day} extracted", flush=True)
        continue
    jobs = [(mo, day) for mo in RAW
            for day in sorted(M[M.month == mo].day.unique())
            if f"{mo}:{day}" not in st["done"]]
    if not jobs:
        print("ALL DAYS DONE")
        break
    if el > 15:
        break
    mo, day = jobs[0]
    raw = os.path.join(RAW[mo], f"glbx-mdp3-{day}.mbp-10.dbn.zst")
    if not os.path.exists(raw):
        st["done"].append(f"{mo}:{day}")
        json.dump(st, open(STATE, "w"))
        print(f"{mo}:{day} RAW MISSING - skipped")
        continue
    DBNStore.from_file(raw).to_parquet(tmp)
    st["pending"] = [mo, day]
    json.dump(st, open(STATE, "w"))
    print(f"{mo}:{day} decoded", flush=True)
rem = len([1 for mo in RAW
           for day in sorted(M[M.month == mo].day.unique())
           if f"{mo}:{day}" not in st["done"]])
print(f"remaining days: {rem}; pending: {st['pending']}")
