#!/usr/bin/env python3
"""
p7_2_strategy1_m1.py — STRATEGY 1 ENTRIES x M1 MANAGEMENT. (T-BS02.)
===============================================================================
Entries: the certified Strategy 1 chain (T-EN102), unchanged - score>=6 at
a 1m WRB completion, direction = prior 5-min close move, stop-order fill
at the signal bar's momentum-side extreme, valid 5 bars, RTH signals,
5-min cooldown. Fill second resolved on per-second mids (first second in
the fill bar at/through the level; gap-through = first second of the bar).
Management: M1 FROZEN (stall S=30 RTH / 90 ETH, stop 4.0, time 27 bars,
session close) via leg().
Months: 2025-10 and 2022-02 (the signal CSV's coverage).
Output: RESULTS_DISPLAY_STANDARD blocks, with exact points won/lost, MAE
per trade (per-second adverse excursion), and the activity block - catch
defined as: one of HIS entries within +/-5 min of one of our fills with
the same direction (definition stated, first use for a fill-based rule).

RUN: python3 Tests/P7_bounded_search/p7_2_strategy1_m1.py              (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P5_trade_management"))
from p4_66_context_ablation import prep
from p4_2_entry_context import month_bounds
from p5_10_stall_stack_dials import leg

P4 = os.path.join(T, "P4_entry_determination")
WAIT = 5
Q_RTH = dict(early=4.0, stop=4.0, time_bars=27, S=30)


def run(repo="."):
    sig_all = pd.read_csv(os.path.join(P4, "p4_36_all_signals.csv"))
    for month in ("2025-10", "2022-02"):
        P = prep(repo, month)
        cx = P["cx"]
        secs, mids = P["secs"], P["mids"]
        o, h, l, c = cx.bars.open.to_numpy(), cx.h, cx.l, cx.c
        bts = cx.bts
        g = sig_all[(sig_all.month == month) & (sig_all.score >= 6)].sort_values("comp_ns")
        trades = []
        busy = -1
        for _, r in g.iterrows():
            ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
            if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
                continue
            fb0 = ib + 1
            if fb0 >= len(bts) or not cx.rth[fb0] or fb0 <= busy:
                continue
            mv = c[ib] - c[ib - 5]
            if mv == 0:
                continue
            long = mv > 0
            lvl = h[ib] if long else l[ib]
            fb = None
            for j in range(fb0, min(fb0 + WAIT, len(bts))):
                if not cx.rth[j]:
                    break
                if (h[j] >= lvl) if long else (l[j] <= lvl):
                    fb = j
                    fill = max(lvl, o[j]) if long else min(lvl, o[j])
                    break
            if fb is None:
                continue
            # fill second on per-second mids within bar fb (1-second mandate)
            b0 = int(cx.bsec[fb]); b1 = b0 + 60
            j0 = int(np.searchsorted(secs, b0)); j1 = int(np.searchsorted(secs, b1))
            seg = mids[j0:j1]
            if not len(seg):
                continue
            if (fill != lvl):                       # gap-through: first second
                js = j0
            else:
                cross = np.flatnonzero(seg >= lvl) if long else np.flatnonzero(seg <= lvl)
                js = j0 + (int(cross[0]) if len(cross) else 0)
            fill_s = int(secs[js])
            px, xs, xb, reason = leg(cx, fb, fill, fill_s, long, Q_RTH)
            pnl = (px - fill) if long else (fill - px)
            # MAE from per-second mids during the trade
            j2 = int(np.searchsorted(secs, int(xs), "right")) - 1
            w = mids[js:j2 + 1]
            mae = (fill - w.min()) if long else (w.max() - fill) if len(w) else np.nan
            trades.append(dict(fill_s=fill_s, side=1 if long else -1,
                               pnl=pnl, mae=mae, reason=reason))
            busy = xb + 5
        D = pd.DataFrame(trades)
        # HIS same period
        ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                             ).dropna(subset=["first_entry_utc"])
        lo, hi = month_bounds(month)
        em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        his = []
        his_t = []
        for _, r in em.iterrows():
            ents = np.atleast_1d(r.entry_prices).astype(float)
            exts = np.atleast_1d(r.exit_prices).astype(float)
            ents, exts = ents[np.isfinite(ents)], exts[np.isfinite(exts)]
            if len(ents) and len(exts):
                d = 1 if r.side == "long" else -1
                his.append(((exts.mean() - ents.mean()) * d, d,
                            int(pd.Timestamp(r.first_entry_utc).value // 10**9)))
        ha = np.array([x[0] for x in his])
        # catch: his entry within +/-300s of one of our fills, same direction
        caught = 0
        fs = D[["fill_s", "side"]].to_numpy()
        for pnl_, d_, t_ in his:
            if len(fs) and np.any((np.abs(fs[:, 0] - t_) <= 300) & (fs[:, 1] == d_)):
                caught += 1
        ndays = len(set(P["sd"]))
        a = D.pnl.to_numpy(); wn = a > 0
        hw = ha[ha > 0]; hl = ha[ha <= 0]
        dd = -min(0.0, float(np.min(np.cumsum(a))))
        hdd = -min(0.0, float(np.min(np.cumsum(ha))))
        print(f"\n===== Strategy 1 | M1 | {month} | RTH =====")
        print(f"A: his trades {len(ha)} | fills {len(D)} ({len(D)/ndays:.1f}/day) "
              f"| his caught (+/-5min, dir-matched) {caught} ({caught/len(ha):.0%}) "
              f"| fills without his trade: {len(D)-caught} (approx)")
        print("| metric | HIS | OURS |")
        print(f"| trades | {len(ha)} | {len(D)} |")
        print(f"| win rate | {(ha>0).mean():.0%} | {wn.mean():.0%} |")
        print(f"| points won / lost | {hw.sum():+.1f} / {hl.sum():+.1f} | {a[wn].sum():+.1f} / {a[~wn].sum():+.1f} |")
        print(f"| net points | {ha.sum():+.1f} | {a.sum():+.1f} |")
        print(f"| avg win / avg loss | +{hw.mean():.2f} / {hl.mean():.2f} | +{a[wn].mean():.2f} / {a[~wn].mean():.2f} |")
        print(f"| worst single trade / worst MAE | {ha.min():+.2f} / - | {a.min():+.2f} / {D.mae.max():.2f} |")
        print(f"| max drawdown from start | {hdd:.1f} | {dd:.1f} |")
        print(f"exit reasons: {dict(D.reason.value_counts())}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
