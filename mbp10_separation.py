#!/usr/bin/env python3
"""
mbp10_separation.py -- does pre-move MBP-10 flow differ between
target_reached and failed_trade slices?

Reads episode_slices.csv (from label_episodes.py) + the windowed MBP-10 parquet.
Computes 3 signed, in-direction features per slice [slice_start_utc, slice_end_utc):
  1. sig_delta    : net in-direction aggressor volume (buys-sells for long; flipped for short)
  2. ofi          : best-level order-flow imbalance (Cont-Kukanov-Stoikov 2014), in-direction
  3. queue_imb    : resting depth lean at the touch (Gould-Bonart 2016), in-direction
Then contrasts target_reached vs failed_trade: Cliff's delta + permutation p per feature,
and a 3-feature energy-distance omnibus. Deterministic, seeded. LLM computes nothing.

EDIT THESE TWO PATHS, then: python3 mbp10_separation.py
"""
import numpy as np, pandas as pd, sys

SLICES_CSV = "episode_slices.csv"
MBP10_PARQUET = "/Volumes/2TB-Lexar/tslwrb_windowed/mbp10_ESZ5_2025-10_windowed.parquet"   # <-- set to SSD path
SEED, N_PERM = 20251007, 10000

REQUIRED = ["ts_event","side","price","size",
            "bid_px_00","ask_px_00","bid_sz_00","ask_sz_00"]

def load_book():
    df = pd.read_parquet(MBP10_PARQUET)
    print("MBP-10 columns:", list(df.columns))
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        sys.exit(f"FATAL: windowed parquet missing required columns: {missing}\n"
                 f"Edit REQUIRED/feature code to match actual names and rerun.")
    df["ts_event"] = pd.to_datetime(df.ts_event, utc=True)
    # unsigned -> int64 before any arithmetic (silent-wraparound guard)
    for c in ["size","bid_sz_00","ask_sz_00"]:
        df[c] = df[c].astype("int64")
    return df.sort_values("ts_event").reset_index(drop=True)

def features_for_slice(book, t0, t1, side):
    """side: 'long'|'short'. Positive feature = pressure in the trade's direction."""
    w = book[(book.ts_event >= t0) & (book.ts_event < t1)]
    sgn = 1 if side == "long" else -1
    # 1. signed aggressor delta: trade prints only (side in B/A)
    tr = w[w.side.isin(["B","A"])]
    buy  = tr.loc[tr.side=="B","size"].sum()
    sell = tr.loc[tr.side=="A","size"].sum()
    sig_delta = sgn * (buy - sell)
    # 2. OFI at best (Cont-Kukanov-Stoikov 2014): sum of bid/ask depth+price events
    bp, ap = w.bid_px_00.values, w.ask_px_00.values
    bs, as_ = w.bid_sz_00.values, w.ask_sz_00.values
    if len(w) < 2:
        ofi = np.nan; queue_imb = np.nan
    else:
        dbid = np.where(bp[1:]>=bp[:-1], bs[1:], 0) - np.where(bp[1:]<=bp[:-1], bs[:-1], 0)
        dask = np.where(ap[1:]<=ap[:-1], as_[1:], 0) - np.where(ap[1:]>=ap[:-1], as_[:-1], 0)
        ofi = sgn * float((dbid - dask).sum())
        # 3. queue imbalance (Gould-Bonart 2016): mean (bid-ask)/(bid+ask) at touch
        denom = bs + as_
        qi = np.where(denom>0, (bs - as_)/denom, 0.0).mean()
        queue_imb = sgn * float(qi)
    return sig_delta, ofi, queue_imb

def cliffs_delta(a, b):
    a, b = np.asarray(a,float), np.asarray(b,float)
    gt = sum((a[:,None] >  b[None,:]).sum(0))
    lt = sum((a[:,None] <  b[None,:]).sum(0))
    return (gt - lt) / (len(a)*len(b))

def perm_p(a, b, rng, n=N_PERM):
    obs = abs(np.mean(a) - np.mean(b))
    pool = np.concatenate([a,b]); na = len(a)
    cnt = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(pool[:na].mean() - pool[na:].mean()) >= obs: cnt += 1
    return (cnt+1)/(n+1)

def energy_distance(A, B, rng, n=N_PERM):
    # standardized multivariate energy distance + permutation p
    A, B = np.asarray(A,float), np.asarray(B,float)
    X = np.vstack([A,B]); mu, sd = X.mean(0), X.std(0); sd[sd==0]=1
    A=(A-mu)/sd; B=(B-mu)/sd
    def ed(A,B):
        def md(P,Q): return np.sqrt(((P[:,None]-Q[None,:])**2).sum(-1)).mean()
        return 2*md(A,B) - md(A,A) - md(B,B)
    obs = ed(A,B); pool=np.vstack([A,B]); na=len(A); cnt=0
    idx=np.arange(len(pool))
    for _ in range(n):
        rng.shuffle(idx)
        if ed(pool[idx[:na]], pool[idx[na:]]) >= obs: cnt+=1
    return obs, (cnt+1)/(n+1)

def main():
    sl = pd.read_csv(SLICES_CSV, parse_dates=["slice_start_utc","slice_end_utc"])
    book = load_book()
    rows=[]
    for _,r in sl.iterrows():
        f = features_for_slice(book, r.slice_start_utc, r.slice_end_utc, r.side)
        rows.append((r.episode_uid, r.label, *f))
    feat = pd.DataFrame(rows, columns=["episode_uid","label","sig_delta","ofi","queue_imb"])
    n_in = feat.dropna().shape[0]
    print(f"\nslices with computable features: {n_in}/{len(feat)} "
          f"(dropped {len(feat)-n_in} for <2 book rows in window)")
    feat = feat.dropna().reset_index(drop=True)
    feat.to_csv("mbp10_features.csv", index=False)

    print("\nclass counts:", feat.label.value_counts().to_dict())
    A = feat[feat.label=="target_reached"]; B = feat[feat.label=="failed_trade"]
    rng = np.random.default_rng(SEED)
    print(f"\n{'feature':12} {'tgt_med':>9} {'fail_med':>9} {'cliffs_d':>9} {'perm_p':>8}")
    for c in ["sig_delta","ofi","queue_imb"]:
        d  = cliffs_delta(A[c].values, B[c].values)
        p  = perm_p(A[c].values, B[c].values, rng)
        print(f"{c:12} {A[c].median():9.2f} {B[c].median():9.2f} {d:9.3f} {p:8.4f}")
    ed, edp = energy_distance(A[["sig_delta","ofi","queue_imb"]].values,
                              B[["sig_delta","ofi","queue_imb"]].values, rng)
    print(f"\n3-feature energy-distance omnibus: stat={ed:.4f}  perm_p={edp:.4f}")
    print(f"\nSEED={SEED} N_PERM={N_PERM} | wrote mbp10_features.csv")

if __name__ == "__main__":
    main()
