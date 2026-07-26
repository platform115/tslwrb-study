#!/usr/bin/env python3
"""
test_whg_fill_hazard.py — STEP 2: WHG-fill as a structure-invalidation exit signal
-------------------------------------------------------------------------------
Tests whether the pre-entry WRB Hidden Gap getting FILLED during the trade predicts the eventual cut.
Uses the verified whg_1m / whg_5m tables from build_whg_series.py (step 1).

DESIGN (all settled with the user)
- Per trade, per timeframe (1m, 5m): the most-recent WHG whose WRB bar COMPLETED before entry (either
  direction). Record zone, direction, age.
- PRE-ENTRY fill status reported SEPARATELY (diagnostic): was that WHG already filled before the trade
  began? Pre-filled WHGs are "already dead" — excluded from the signal population.
- SIGNAL = IN-TRADE fill: among trades whose WHG was LIVE at entry, at elapsed tau on STILL-OPEN trades,
  has price filled the zone between entry and min(entry+tau, exit)? Causal guard — only bars strictly
  before the checkpoint/exit count. Binary fill -> the read is a HAZARD RATE (P(cut|filled) vs
  P(cut|intact)), NOT an AUC. Two-sided.

FILL DETECTION [DEVIATION FROM DEFINITION, FLAGGED]
  Definition file says fill = a SINGLE bar's range covers the zone. Here fill = CUMULATIVE full traversal
  detected on 1m bars (running max high >= whg_top AND running min low <= whg_bottom within the window),
  for BOTH 1m and 5m zones. Rationale: user tracks the 5m WHG ON THE 1m, and losers hold ~1.7min < one
  5m bar, so single-5m-bar fill is unobservable in-trade. Strict single-bar fill = a one-line change.

Bar-level only -> NO SSD needed. Both populations (clean 16/47, pt1 52/40). Deterministic. Read-only.
n small; October discovery. Not financial advice.

RUN (from 06-10_whg_fill/, after build_whg_series.py has written the tables there)
  python3 test_whg_fill_hazard.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups, S, M

import os as _os
INSTRUMENT_ID = int(_os.environ.get("TSLWRB_IID", "294973"))
MONTH = _os.environ.get("TSLWRB_MONTH", "2025-10")
SYMBOL = _os.environ.get("TSLWRB_SYMBOL", "ESZ5")
print(f"[env] MONTH={MONTH} SYMBOL={SYMBOL} INSTRUMENT_ID={INSTRUMENT_ID}", flush=True)
LO = pd.Timestamp(f"{MONTH}-01", tz="UTC"); HI = LO + pd.offsets.MonthBegin(1)
TAUS = [60, 120, 180, 300, 480]; TAU_PRIMARY = 180
TF_DUR = {"1m": 60, "5m": 300}


def load_groups(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    return g, cfg["paths"]["es_1m_front"]


def load_1m_bars(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "high", "low"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.high.to_numpy(), d.low.to_numpy()


def traversed(bsec, bhi, blo, top, bot, t0, t1):
    """cumulative full traversal on 1m bars in [t0, t1): running max high >= top AND running min low <= bot."""
    i0 = int(np.searchsorted(bsec, t0, "left")); i1 = int(np.searchsorted(bsec, t1, "left"))
    if i1 <= i0:
        return False
    return bool(bhi[i0:i1].max() >= top and blo[i0:i1].min() <= bot)


def recent_whg(whg, entry_ts, tf):
    """most-recent WHG whose WRB bar completed (<=) before entry. Returns (top, bot, dir, complete_s) or None."""
    e_s = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
    z = whg[whg.has_whg].copy()
    z["complete_s"] = (z.ts_event.astype("int64") // 1_000_000_000) + TF_DUR[tf]
    z = z[z.complete_s <= e_s]
    if len(z) == 0:
        return None
    r = z.iloc[-1]
    return float(r.whg_top), float(r.whg_bottom), str(r.direction), int(r.complete_s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--whg_dir", default=".")
    args = ap.parse_args()

    g, es1m = load_groups(args.config, args.wrb)
    bsec, bhi, blo = load_1m_bars(es1m)
    tables = {tf: pd.read_parquet(_os.path.join(args.whg_dir, f"whg_{tf}_{MONTH}.parquet")) for tf in TF_DUR}

    for tf in ["1m", "5m"]:
        whg = tables[tf]
        print(f"\n############### TIMEFRAME: {tf} (zone ~{'1' if tf=='1m' else '5'}pt typical) ###############")
        recs = []
        for _, r in g.iterrows():
            e_s = np.int64(pd.Timestamp(r.entry).value // 1_000_000_000)
            x_s = np.int64(pd.Timestamp(r.exit).value // 1_000_000_000)
            w = recent_whg(whg, r.entry, tf)
            rec = dict(uid=r.uid, group=r.group, is_loser=bool(r.is_loser),
                       has_whg=(w is not None), pre_filled=False, live=False, age_min=np.nan)
            if w is not None:
                top, bot, _, comp_s = w
                rec["age_min"] = (e_s - comp_s) / 60.0
                rec["pre_filled"] = traversed(bsec, bhi, blo, top, bot, comp_s, e_s)
                rec["live"] = not rec["pre_filled"]
                rec["_top"] = top; rec["_bot"] = bot
            for tau in TAUS:
                cp = min(e_s + tau, x_s)
                rec[f"open_{tau}"] = x_s > e_s + tau
                rec[f"fill_{tau}"] = (traversed(bsec, bhi, blo, rec.get("_top", np.nan), rec.get("_bot", np.nan),
                                                e_s, cp) if rec["live"] else False)
            recs.append(rec)
        d = pd.DataFrame(recs)

        # PRE-ENTRY diagnostic
        print(f"  PRE-ENTRY status (n={len(d)}): no-WHG={int((~d.has_whg).sum())}  "
              f"pre-filled={int(d.pre_filled.sum())}  LIVE-at-entry={int(d.live.sum())}  "
              f"| median WHG age={np.nanmedian(d.age_min):.1f} min")

        pops = {
            "clean (losing16 vs reached47)": d.is_loser | ((d.group == "target_reached") & ~d.is_loser),
            "pt1   (failed40 vs reached52)": (d.group == "failed_trades") | (d.group == "target_reached"),
        }
        cutdef = {"clean": d.is_loser, "pt1": d.group == "failed_trades"}
        for pop_name, popmask in pops.items():
            key = "clean" if pop_name.startswith("clean") else "pt1"
            base = d[popmask & d.live]            # signal population = live-at-entry, in this contrast
            iscut = cutdef[key]
            print(f"\n  == {pop_name} ==  live-at-entry in contrast: {len(base)}")
            print(f"     IN-TRADE FILL hazard — P(cut) among still-open trades, filled vs intact by tau:")
            print(f"     {'tau(s)':>6} {'n_fill':>6} {'P(cut|fill)':>11} {'n_intact':>8} {'P(cut|intact)':>13} {'diff':>6}")
            for tau in TAUS:
                sub = base[base[f"open_{tau}"]]
                fl = sub[sub[f"fill_{tau}"]]; it = sub[~sub[f"fill_{tau}"]]
                pf = iscut[fl.index].mean() if len(fl) else np.nan
                pi = iscut[it.index].mean() if len(it) else np.nan
                diff = (pf - pi) if (not np.isnan(pf) and not np.isnan(pi)) else np.nan
                star = "  <<<" if tau == TAU_PRIMARY else ""
                print(f"     {tau:>6} {len(fl):>6} {pf if not np.isnan(pf) else float('nan'):>11.2f} "
                      f"{len(it):>8} {pi if not np.isnan(pi) else float('nan'):>13.2f} "
                      f"{diff if not np.isnan(diff) else float('nan'):>6.2f}{star}")

    print(f"\n[whg] READ: diff = P(cut|filled) - P(cut|intact). Positive = filling the WHG in-trade predicts")
    print(f"  a cut (structure invalidation). Two-sided. Watch n_fill / n_intact cell sizes (small here);")
    print(f"  if n_fill is ~everyone (esp. 1m), fill is ubiquitous -> uninformative, not 'no effect'.")


if __name__ == "__main__":
    main()
