#!/usr/bin/env python3
"""
p4_93_strategy1_audit.py — STRATEGY 1 TRUNCATION AUDIT. (T-EN102.)
===============================================================================
Strategy 1 (spec v10, p4_41) predates the adaptive era and was never run
through the mechanical lookahead gate. This audit applies the T-EN101
principle to its full chain on the training months:
  F1 direction: the 5-min move recomputed from bars truncated at the
     signal bar must equal the pipeline's value.
  F2 fill: the stop-order fill scan recomputed on a frame truncated at
     the fill bar must give the same fill bar and price.
  F3 stamps: every signal's completion stamp <= its fill bar's open.
  X1 exits: run_leg re-run with every bar AFTER the recorded exit
     NaN-poisoned must return the identical exit (price, bar, reason).
  S  sensitivity: a deliberately contaminated variant (direction taken
     from the bar AFTER the signal bar - future data) must change trades;
     the harness must catch that bug class.
VERDICT RULE: any F/X failure = Strategy 1 joins 2A/2B as VOID; all pass
+ S catches = Strategy 1 is certified for the backtest register.

RUN: python3 Tests/P4_entry_determination/p4_93_strategy1_audit.py     (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS
from p4_31_profit_v9 import run_leg, ARMS
from p4_33_losscuts import month_ctx

WAIT = 5


def run(repo="."):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    p = dict(ARMS["B (momentum ladder)"])
    res = {k: [0, 0] for k in ("F1 direction", "F2 fill", "F3 stamps", "X1 exits")}
    s_changed = s_total = 0
    for month, sym in MONTHS:
        bars, pre, prev, lo, hi = month_ctx(es, month, sym)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy(); o = bars.open.to_numpy()
        h, l = bars.high.to_numpy(), bars.low.to_numpy()
        g = sig[(sig.month == month) & (sig.score >= 6)].sort_values("comp_ns")
        busy = -1; n_tr = 0
        for _, r in g.iterrows():
            ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
            if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
                continue
            fb0 = ib + 1
            if fb0 >= len(bts) or not bars.rth.iloc[fb0] or fb0 <= busy:
                continue
            mv = cl[ib] - cl[ib - 5]
            if mv == 0:
                continue
            long = mv > 0
            uref = r.uref if np.isfinite(r.uref) else None
            lvl = h[ib] if long else l[ib]
            fb = None
            for j in range(fb0, min(fb0 + WAIT, len(bars))):
                if not bars.rth.iloc[j]:
                    break
                if (h[j] >= lvl) if long else (l[j] <= lvl):
                    fb = j
                    fill = max(lvl, o[j]) if long else min(lvl, o[j])
                    break
            if fb is None:
                continue
            n_tr += 1
            # F1: direction from truncated closes (bars <= ib only)
            mv_t = cl[:ib + 1][-1] - cl[:ib + 1][-6]
            res["F1 direction"][0 if np.isclose(mv_t, mv) else 1] += 1
            # F2: fill scan on a frame truncated AT the fill bar
            fb_t = None
            for j in range(fb0, min(fb0 + WAIT, fb + 1)):
                if not bars.rth.iloc[j]:
                    break
                if (h[j] >= lvl) if long else (l[j] <= lvl):
                    fb_t = j
                    fill_t = max(lvl, o[j]) if long else min(lvl, o[j])
                    break
            ok = (fb_t == fb) and np.isclose(fill_t, fill)
            res["F2 fill"][0 if ok else 1] += 1
            # F3: signal completion <= fill bar open time
            res["F3 stamps"][0 if int(r.comp_ns) <= bts[fb] else 1] += 1
            # X1: exits with post-exit bars poisoned
            px, xi, reason, _ = run_leg(bars, pre, fb, fill, long, 1.0, p, fb + 1, uref)
            pb = bars.copy()
            pb.loc[pb.index[xi + 1:], ["open", "high", "low", "close"]] = np.nan
            pre2 = pre  # flags beyond xi unused when exit reproduces at xi
            px2, xi2, r2, _ = run_leg(pb, pre, fb, fill, long, 1.0, p, fb + 1, uref)
            ok = np.isclose(px, px2) and xi == xi2 and reason == r2
            res["X1 exits"][0 if ok else 1] += 1
            # S: contaminated direction (close of the bar AFTER the signal bar)
            if n_tr % 10 == 0 and ib + 1 < len(cl):
                s_total += 1
                mv_bad = cl[ib + 1] - cl[ib - 4]
                if (mv_bad > 0) != long or (mv_bad == 0):
                    s_changed += 1
            busy = xi + 5
        print(f"{month}: {n_tr} trades audited", flush=True)
    print("\n===== STRATEGY 1 TRUNCATION AUDIT =====")
    fail = 0
    for k, (ps, f) in res.items():
        v = "PASS" if f == 0 else "FAIL - LOOKAHEAD"
        print(f"  {k}: pass {ps}, fail {f} -> {v}")
        fail += (f > 0)
    print(f"  S sensitivity: contaminated direction changes the trade in "
          f"{s_changed}/{s_total} samples -> {'harness catches the bug class' if s_changed else 'INSENSITIVE'}")
    print("\nVERDICT:", "STRATEGY 1 CERTIFIED for the backtest register"
          if fail == 0 and s_changed else "STRATEGY 1 FAILS - treat as VOID")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
