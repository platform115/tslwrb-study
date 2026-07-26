#!/usr/bin/env python3
"""
test_vx_level_entry.py — VIX TEST #2: front-month VX FUTURES level at entry vs cut/reached
-------------------------------------------------------------------------------
Does the vol level at entry separate cuts from reached trades? Uses FRONT-MONTH VX FUTURES (the
tradeable VIX product) as the vol-regime proxy.

IMPORTANT: this is VX FUTURES, not the spot VIX index. The front future = market's expectation of VIX
~30d out; related to spot but smoother and offset by contango/backwardation. It is a legitimate vol-
REGIME proxy and, unlike spot VIX or VIX options, trades ~24h so it COVERS his overnight ES entries.
Reported as "front VX", not "VIX".

Front-month logic (deterministic, CBOE rule — not hand-set): each outright VX contract's final settlement
= the Wednesday 30 days before the THIRD FRIDAY of the month FOLLOWING the contract month. Front-month at
a trade's entry = the nearest outright whose expiry date is AFTER the entry date (rolls on expiry day).
Spreads (symbols with ':'/'-') excluded. For Oct 2025: V5 (Oct, expiry ~Oct 22) -> X5 (Nov) at the roll.

vx_at_entry = front-month close at the most recent 1m bar at/before entry. AUC two-sided + cluster-boot
CI, both populations: clean (losing16 vs reached47) and pt1 (failed40 vs target_reached52). October,
in-sample. Not advice.

RUN (from its subfolder; --vx points at the VX futures dbn.zst)
  python3 test_vx_level_entry.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet \
      --vx /path/to/xcbf-pitch-20251001-20251031.ohlcv-1m.dbn.zst
"""

# --- path bootstrap ---
# spine (horse_race_spine, trade_flow_exhaustion) lives in the 06 candidate folder, a sibling branch
# under Tests/ — not a parent of this file. Point at it explicitly.
import sys as _sys, os as _os
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))  # .../Tests
_sys.path.insert(0, _os.path.join(_TESTS, "06_trade_flow_exhaustion_CANDIDATE"))
# --- end ---

import argparse, tomllib, re, calendar
from datetime import timedelta
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups

MONTHS = {"F":1,"G":2,"H":3,"J":4,"K":5,"M":6,"N":7,"Q":8,"U":9,"V":10,"X":11,"Z":12}


def scalar(v): return float(np.asarray(v).ravel()[0])


def third_friday(y, m):
    fr = [d for d in calendar.Calendar().itermonthdates(y, m) if d.month == m and d.weekday() == 4]
    return fr[2]


def vx_expiry(sym):
    # sym like 'VX/V5' -> contract month/year -> CBOE final settlement date
    code = sym.split("/")[1]; mon = MONTHS[code[0]]; yr = 2020 + int(code[1])
    fy, fm = (yr + 1, 1) if mon == 12 else (yr, mon + 1)
    return third_friday(fy, fm) - timedelta(days=30)


def load_groups(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    return g


def build_front_vx(vx_path):
    import databento as db
    df = db.DBNStore.from_file(vx_path).to_df().reset_index()
    out = df[df["symbol"].str.match(r"^VX/[FGHJKMNQUVXZ]\d$")].copy()
    out["ts"] = pd.to_datetime(out["ts_event"], utc=True)
    out["expiry"] = out["symbol"].map(vx_expiry)
    contracts = {}
    for s, sub in out.groupby("symbol"):
        sub = sub.sort_values("ts")
        contracts[s] = dict(expiry=sub["expiry"].iloc[0],
                            ts=(sub["ts"].astype("int64") // 1_000_000_000).to_numpy(),
                            close=sub["close"].to_numpy())
    return contracts


def front_close_at(contracts, entry_ts):
    d = pd.Timestamp(entry_ts).date()
    cand = sorted([(c["expiry"], s) for s, c in contracts.items() if c["expiry"] > d])
    if not cand: return np.nan, None
    s = cand[0][1]; c = contracts[s]
    t = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
    i = int(np.searchsorted(c["ts"], t, "right") - 1)
    return (float(c["close"][i]) if i >= 0 else np.nan), s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--vx", required=True); ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    g = load_groups(args.config, args.wrb)
    contracts = build_front_vx(args.vx)
    print(f"[vx#2] outright contracts: {sorted(contracts.keys())}")
    print(f"[vx#2] expiries: " + ", ".join(f"{s}={contracts[s]['expiry']}" for s in sorted(contracts)))

    vals, fronts = [], []
    for _, r in g.iterrows():
        v, s = front_close_at(contracts, r["entry"]); vals.append(v); fronts.append(s)
    g = g.assign(vx=vals, front=fronts)
    valid = g.dropna(subset=["vx"])
    print(f"\n[vx#2] trades with valid front-VX at entry: {len(valid)}/{len(g)}")
    print(f"  front-month usage: {valid['front'].value_counts().to_dict()}")
    print(f"  front-VX range over entries: {valid.vx.min():.2f} - {valid.vx.max():.2f} "
          f"(median {valid.vx.median():.2f})  [vol points]")

    def auc_block(name, cutm, sparedm):
        cut = valid[cutm].vx.to_numpy(); spared = valid[sparedm].vx.to_numpy()
        if len(cut) < 5 or len(spared) < 5:
            print(f"\n  {name}: too few ({len(cut)}/{len(spared)})"); return
        auc, _, _ = spine.rank_auc(spared, cut)
        per = [float((np.sum(spared > c) + 0.5 * np.sum(spared == c)) / len(spared)) for c in cut]
        ci = spine.cluster_boot_ci(per, seed=args.seed)
        hi = "reached" if auc > 0.5 else "cut"
        print(f"\n  {name}")
        print(f"    median front-VX: cut={np.median(cut):.2f}  spared={np.median(spared):.2f}")
        print(f"    AUC={auc:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}]  (>0.5 => reached enter at higher vol; "
              f"<0.5 => cut enter at higher vol; here: {hi} higher)")

    auc_block("clean (cut=losing16 / spared=reached47)", valid.is_loser,
              (valid.group == "target_reached") & ~valid.is_loser)
    auc_block("pt1   (cut=failed40 / spared=reached52)", valid.group == "failed_trades",
              valid.group == "target_reached")

    print(f"\n[vx#2] READ: CI excluding 0.5 => vol level at entry separates outcomes (a REGIME effect).")
    print(f"  CI spanning 0.5 => no entry-vol-level signal. Front VX = vol-regime proxy, not spot VIX;")
    print(f"  ~24h coverage so overnight entries included. In-sample, n-limited. #3 (intra-trade) next.")


if __name__ == "__main__":
    main()
