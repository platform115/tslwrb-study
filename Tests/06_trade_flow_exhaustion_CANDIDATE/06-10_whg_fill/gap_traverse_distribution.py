#!/usr/bin/env python3
"""
gap_traverse_distribution.py — DESCRIPTIVE: how much of the gap gets traversed?
-------------------------------------------------------------------------------
Full traversal (100% coverage) was rare (6/34). This asks the prior question: per gap-arrival trade,
what is the MAX fraction of the gap price traverses toward the far edge during [entry, exit]? If most
trades reach 80-100% but stop just short of the exact edge, "full traversal" was too strict a label.
If traversal is spread all over, it's genuinely variable. COUNTS/DISTRIBUTION ONLY — no test, no label,
no outcome-driven threshold.

TRAVERSAL FRACTION (directional, toward the far edge of the gap, 1m TRUE extremes):
  long  (pointed up):   (max_high_in_trade - whg_bottom) / (whg_top - whg_bottom)   [far edge = top]
  short (pointed down): (whg_top - min_low_in_trade)     / (whg_top - whg_bottom)   [far edge = bottom]
  >= 1.0 means the far edge was reached (gap fully traversed in the trade direction).

Population: 5m INSIDE+NEAR pointed-through gap-arrivals, 2d validity window (same as the exit test).
Read-only. 1m bars (NO SSD). October ESZ5. Descriptive only. Not financial advice.

RUN (from 06-10_whg_fill/)
  python3 gap_traverse_distribution.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups

import os as _os
INSTRUMENT_ID = int(_os.environ.get("TSLWRB_IID", "294973"))
MONTH = _os.environ.get("TSLWRB_MONTH", "2025-10")
SYMBOL = _os.environ.get("TSLWRB_SYMBOL", "ESZ5")
print(f"[env] MONTH={MONTH} SYMBOL={SYMBOL} INSTRUMENT_ID={INSTRUMENT_ID}", flush=True)
LO = pd.Timestamp(f"{MONTH}-01", tz="UTC"); HI = LO + pd.offsets.MonthBegin(1)
TF_DUR_5M = 300; WIN_S = 2 * 86400; NEAR = 8 * 0.25


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["paths"]["es_1m_front"], cfg["paths"]["es_5m_front"]


def load_bars(path):
    d = pd.read_parquet(path, columns=["ts_event", "instrument_id", "open", "high", "low", "close", "session_date"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    return d.sort_values("ts_event").reset_index(drop=True)


def identify_whg(df):
    o = df.open.to_numpy(); c = df.close.to_numpy()
    sd = df.session_date.astype(str).to_numpy(); body = np.abs(c - o); n = len(df); out = []
    for i in range(3, n):
        if not (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) or body[i] <= 0:
            continue
        if not (body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]):
            continue
        if c[i] > o[i]:
            pbh = max(max(o[i-1], c[i-1]), max(o[i-2], c[i-2]), max(o[i-3], c[i-3]))
            if c[i] > pbh: out.append((i, "bullish", pbh, c[i]))
        elif c[i] < o[i]:
            pbl = min(min(o[i-1], c[i-1]), min(o[i-2], c[i-2]), min(o[i-3], c[i-3]))
            if c[i] < pbl: out.append((i, "bearish", c[i], pbl))
    return out


def fill_s(bsec, bhi, blo, top, bot, idx, dur):
    hi = bhi[idx+1:]; lo = blo[idx+1:]; ss = bsec[idx+1:]
    if len(hi) == 0: return np.inf
    both = (np.maximum.accumulate(hi) >= top) & (np.minimum.accumulate(lo) <= bot)
    k = int(np.argmax(both)) if both.any() else -1
    return float(ss[k] + dur) if k >= 0 else np.inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    args = ap.parse_args()
    g, es1m, es5m = load(args.config, args.wrb)

    b5 = load_bars(es5m); s5 = (b5.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    h5 = b5.high.to_numpy(); l5 = b5.low.to_numpy()
    W = pd.DataFrame([dict(comp_s=int(s5[i] + TF_DUR_5M), fill_s=fill_s(s5, h5, l5, top, bot, i, TF_DUR_5M),
                           top=top, bot=bot) for (i, d, bot, top) in identify_whg(b5)])

    b1 = load_bars(es1m); s1 = (b1.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    h1 = b1.high.to_numpy(); l1 = b1.low.to_numpy()

    rows = []
    for _, r in g.iterrows():
        e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000); ep = r.entry_price
        x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000)
        live = W[(W.comp_s <= e_s) & (W.comp_s >= e_s - WIN_S) & (W.fill_s > e_s)]
        if len(live) == 0: continue
        d_in = (live.bot <= ep) & (ep <= live.top)
        if d_in.any():
            ch = live[d_in].iloc[int(live[d_in].comp_s.values.argmax())]; dist = 0.0
        else:
            bot_a = live.bot.to_numpy(); top_a = live.top.to_numpy()
            dd = np.where(ep < bot_a, bot_a - ep, np.where(ep > top_a, ep - top_a, 0.0))
            j = int(np.argmin(dd)); dist = float(dd[j]); ch = live.iloc[j]
        if dist > NEAR: continue
        toward = (r.side == "long" and ch.top >= ep) or (r.side == "short" and ch.bot <= ep)
        if not toward: continue
        top, bot = float(ch.top), float(ch.bot); zone = top - bot
        i0 = np.searchsorted(s1, e_s, "left"); i1 = np.searchsorted(s1, x_s, "left")
        if i1 <= i0: continue
        mx = h1[i0:i1].max(); mn = l1[i0:i1].min()
        frac = (mx - bot) / zone if r.side == "long" else (top - mn) / zone
        rows.append(dict(uid=r.uid, group=r.group, is_loser=bool(r.is_loser),
                         zone=zone, frac=max(0.0, frac)))
    d = pd.DataFrame(rows)
    print(f"\n[dist] gap-arrival trades: {len(d)}  (zone median {d.zone.median():.2f} pt)")
    print(f"[dist] traversal fraction toward far edge (>=1.0 = far edge reached):")
    print(f"       median={d.frac.median():.2f}  mean={d.frac.mean():.2f}")
    print(f"       reached >=100% (full): {int((d.frac>=1.0).sum())}/{len(d)} ({(d.frac>=1.0).mean()*100:.0f}%)")
    print(f"       reached >= 90%:        {int((d.frac>=0.9).sum())}/{len(d)} ({(d.frac>=0.9).mean()*100:.0f}%)")
    print(f"       reached >= 80%:        {int((d.frac>=0.8).sum())}/{len(d)} ({(d.frac>=0.8).mean()*100:.0f}%)")
    print(f"       reached >= 50%:        {int((d.frac>=0.5).sum())}/{len(d)} ({(d.frac>=0.5).mean()*100:.0f}%)")
    print(f"\n[dist] histogram of traversal fraction:")
    bins = [(0,0.2),(0.2,0.4),(0.4,0.6),(0.6,0.8),(0.8,1.0),(1.0,1.5),(1.5,np.inf)]
    for lob,hib in bins:
        m=(d.frac>=lob)&(d.frac<hib); n=int(m.sum())
        lbl=f"{int(lob*100)}-{int(hib*100)}%" if np.isfinite(hib) else f">{int(lob*100)}%"
        bar="#"*n
        print(f"       {lbl:>9}: {n:>2}  {bar}")
    print(f"\n[dist] by eventual group (descriptive):")
    for grp in ["target_reached","failed_trades"]:
        sub=d[d.group==grp]
        if len(sub): print(f"       {grp:>15}: n={len(sub)} median frac={sub.frac.median():.2f} "
                            f">=80%: {int((sub.frac>=0.8).sum())}")
    print(f"\n[dist] READ: if most cluster 80-100%+, 'full traversal' (exact far edge) was too strict a")
    print(f"  success label -> ~80% is the natural threshold. If spread out, traversal is genuinely variable.")


if __name__ == "__main__":
    main()
