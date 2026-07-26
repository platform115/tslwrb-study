#!/usr/bin/env python3
"""
probe_whg_arrival.py — PROBE (not a test): do entries arrive at live unfilled WHGs?
-------------------------------------------------------------------------------
User's mechanism: a WHG forms, price wanders off, later RETURNS to the gap, a trade is entered AS price
arrives, and lasts a few minutes WHILE it traverses the gap. Gap-arrival is ONE setup among several
(not all 92 entries). Success can be full-traversal OR reaching the gap (not yet fixed -> NOT tested
here). So before designing any statistic we must learn whether a gap-arrival population even exists and
how big it is. This is COUNTS/DISTRIBUTIONS ONLY — no AUC, no hazard, no outcome-driven thresholds.
Picking a success rule or a subset before this probe would be fitting; this probe gates that.

LIVE WHG at entry = WRB bar completed within the validity window before entry AND not yet filled by
entry. A WHG is DEAD the moment it is fully traversed (high>=top AND low<=bottom by any 1m bar),
regardless of window. Validity window swept: 1 / 2 / 3 trading days. 1m and 5m run separately.

PER ENTRY, reports:
  - distance (ticks/points) from entry price to the nearest LIVE WHG zone (0 if inside a zone)
  - bucket: INSIDE / NEAR (<= NEAR_TICKS) / FAR
  - direction-through-gap: is the trade pointed toward traversing that gap (long into a zone above,
    short into a zone below)?  [consistency check for "entered to traverse"]
  - descriptive only: did that gap eventually fill, and the trade's group (count table, no statistic)

Read-only. Bar-level (NO SSD). October ESZ5. Not financial advice.

RUN (from 06-10_whg_fill/)
  python3 probe_whg_arrival.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
TF_DUR = {"1m": 60, "5m": 300}
WINDOWS_DAYS = [1, 2, 3]
NEAR_TICKS = 8          # 8 ticks = 2.0 pts on ES (0.25/tick); "near" bucket. Diagnostic only.
TICK = 0.25


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["paths"]["es_1m_front"], cfg["paths"].get("es_5m_front")


def load_bars(path):
    d = pd.read_parquet(path, columns=["ts_event", "instrument_id", "open", "high", "low", "close", "session_date"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    return d.sort_values("ts_event").reset_index(drop=True)


def identify_whg(df):
    o = df.open.to_numpy(); c = df.close.to_numpy()
    sd = df.session_date.astype(str).to_numpy(); body = np.abs(c - o); n = len(df)
    rows = []
    for i in range(3, n):
        if not (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) or body[i] <= 0:
            continue
        if not (body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]):
            continue
        if c[i] > o[i]:
            pbh = max(max(o[i-1], c[i-1]), max(o[i-2], c[i-2]), max(o[i-3], c[i-3]))
            if c[i] > pbh:
                rows.append((i, "bullish", pbh, c[i]))
        elif c[i] < o[i]:
            pbl = min(min(o[i-1], c[i-1]), min(o[i-2], c[i-2]), min(o[i-3], c[i-3]))
            if c[i] < pbl:
                rows.append((i, "bearish", c[i], pbl))
    return rows   # (bar_idx, direction, bottom, top)


def fill_time_s(bsec, bhi, blo, top, bot, start_idx, bar_secs):
    """first second by which the zone is fully traversed (cumulative) after formation; np.inf if never."""
    hi = bhi[start_idx+1:]; lo = blo[start_idx+1:]; ss = bsec[start_idx+1:]
    cov_top = np.maximum.accumulate(hi) >= top if len(hi) else np.array([], bool)
    cov_bot = np.minimum.accumulate(lo) <= bot if len(lo) else np.array([], bool)
    both = cov_top & cov_bot
    k = np.argmax(both) if both.any() else -1
    return float(ss[k] + bar_secs) if k >= 0 else np.inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    args = ap.parse_args()
    g, es1m, es5m = load(args.config, args.wrb)
    srcs = {"1m": es1m, "5m": es5m}

    for tf in ["1m", "5m"]:
        if not srcs[tf]:
            print(f"\n### {tf}: config[paths][es_{tf}_front] not set — skipping"); continue
        bars = load_bars(srcs[tf]); dur = TF_DUR[tf]
        bsec = (bars.ts_event.astype("int64") // 1_000_000_000).to_numpy()
        bhi = bars.high.to_numpy(); blo = bars.low.to_numpy()
        whgs = identify_whg(bars)
        # precompute each WHG: formation_complete_s, fill_s
        W = []
        for (i, d, bot, top) in whgs:
            comp_s = int(bsec[i] + dur)
            fs = fill_time_s(bsec, bhi, blo, top, bot, i, dur)
            W.append(dict(comp_s=comp_s, fill_s=fs, top=top, bot=bot, direction=d))
        W = pd.DataFrame(W)
        print(f"\n############### {tf}: {len(W)} WHGs (Oct ESZ5) ###############")

        for win_d in WINDOWS_DAYS:
            win_s = win_d * 86400
            inside = near = far = 0
            through = 0; live_total = 0
            tab = {"INSIDE": {}, "NEAR": {}}
            for _, r in g.iterrows():
                e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000); ep = r.entry_price
                live = W[(W.comp_s <= e_s) & (W.comp_s >= e_s - win_s) & (W.fill_s > e_s)]
                if len(live) == 0:
                    far += 1; continue
                # distance to nearest live zone (0 if inside)
                d_in = ((live.bot <= ep) & (ep <= live.top))
                if d_in.any():
                    dist = 0.0; chosen = live[d_in].iloc[(live[d_in].comp_s.values.argmax())]
                else:
                    above = (live.bot - ep).to_numpy(); below = (ep - live.top).to_numpy()
                    bot_a = live.bot.to_numpy(); top_a = live.top.to_numpy()
                    dd = np.where(ep < bot_a, above, np.where(ep > top_a, below, 0.0))
                    j = int(np.argmin(dd)); dist = float(dd[j]); chosen = live.iloc[j]
                live_total += 1
                bucket = "INSIDE" if dist == 0 else ("NEAR" if dist <= NEAR_TICKS * TICK else "FAR")
                if bucket == "INSIDE": inside += 1
                elif bucket == "NEAR": near += 1
                else: far += 1
                # direction-through-gap: long expects to traverse a zone at/above; short at/below
                if bucket in ("INSIDE", "NEAR"):
                    toward = (r.side == "long" and chosen.top >= ep) or (r.side == "short" and chosen.bot <= ep)
                    through += int(toward)
                    tab[bucket][r.group] = tab[bucket].get(r.group, 0) + 1
            print(f"  window={win_d}d:  INSIDE={inside}  NEAR(<= {NEAR_TICKS}t)={near}  FAR/none={far}  "
                  f"| of INSIDE+NEAR, pointed THROUGH gap={through}/{inside+near}")
            print(f"     group mix INSIDE: {tab['INSIDE']}   NEAR: {tab['NEAR']}")

    print(f"\n[probe] READ: do entries cluster INSIDE/NEAR live WHGs, and are they pointed through the gap?")
    print(f"  Large INSIDE+NEAR with through-gap => a real gap-arrival population worth a pre-registered")
    print(f"  test. Mostly FAR/none, or not pointed through => gap-arrival is rare here -> close #3.")
    print(f"  (Counts only. No success rule chosen yet — pick traversal-vs-touch BEFORE any outcome test.)")


if __name__ == "__main__":
    main()
