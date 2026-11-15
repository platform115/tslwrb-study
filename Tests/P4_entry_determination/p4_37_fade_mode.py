#!/usr/bin/env python3
"""
p4_37_fade_mode.py — P4.37: the fade mode (his entries AGAINST a nearby WRB).
==============================================================================
52 of his discovery entries (17%) come within 5 min of a WRB completion but on
the OPPOSITE side. His narration at these: "too much fight in the price action
to stay up at this price level", "failed counter-thrust". FROZEN HYPOTHESIS:
the fade is a FAILED-THRUST trade - a WRB breaks out, price fully retraces its
body shortly after, and he sells the failure.

FADE SIGNAL (frozen): after an RTH 1m WRB completes at bar i, if any bar in
i+1..i+5 CLOSES beyond the WRB's open (bullish WRB: close < its open; bearish:
close > its open - the thrust fully given back), the fade fires at that bar's
close, direction opposite the WRB. One fade per WRB.

Measured: (1) his 52 fade entries - does the failed-thrust pattern precede them?
(2) the signal's direction accuracy (9-bar forward) across ALL firings vs the
54.9% baseline; (3) profit: v9-B exits on fade signals, with/without a news
gate, user-mandated table.

RUN: python3 Tests/P4_entry_determination/p4_37_fade_mode.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies                # noqa: E402
from p4_3_confluence_news import news_sets                # noqa: E402
from p4_31_profit_v9 import wrb_flags, run_leg, ARMS      # noqa: E402
from p4_33_losscuts import month_ctx, row                 # noqa: E402

FADE_BARS = 5


def fade_signals(bars):
    """(fire_bar_index, side, wrb_bar_index) for every failed thrust."""
    isw, wdir, wbb, wbt, wbody = wrb_flags(bars)
    o, c = bars.open.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy()
    sd = bars.session_date.astype(str).to_numpy()
    out = []
    for i in np.flatnonzero(isw):
        if not rth[i]:
            continue
        bull = wdir[i] == "bullish"
        for j in range(i + 1, min(i + 1 + FADE_BARS, len(bars))):
            if sd[j] != sd[i]:
                break
            if (c[j] < o[i]) if bull else (c[j] > o[i]):
                out.append((j, "short" if bull else "long", i))
                break
    return out


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    ev_all = news_sets(repo)["all"]
    p = dict(ARMS["B (momentum ladder)"])
    acc_rows, cover, n_his_fades = [], 0, 0
    frames = {"fade, all": [], "fade + news<=30m": []}
    for month, sym in MONTHS:
        bars, pre, prev, lo, hi = month_ctx(es, month, sym)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy(); o = bars.open.to_numpy()
        sd = bars.session_date.astype(str).to_numpy()
        fades = fade_signals(bars)
        fire_ns = np.array([bts[j] + 60_000_000_000 for j, _, _ in fades], dtype=np.int64)
        # (1) his fades preceded by the pattern?
        smz = sig[sig.month == month]
        comp = smz.comp_ns.to_numpy(np.int64); dirs = smz.direction.to_numpy()
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        for _, t in e_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            want = "bullish" if t.side == "long" else "bearish"
            m = (comp >= en - 5 * 60_000_000_000) & (comp < en)
            if m.any() and not (m & (dirs == want)).any():      # his fade entry
                n_his_fades += 1
                k = (fire_ns >= en - 10 * 60_000_000_000) & (fire_ns <= en + 60_000_000_000)
                sides = [fades[x][1] for x in np.flatnonzero(k)]
                if t.side in sides:
                    cover += 1
        # (2) accuracy + (3) profit
        busy = -1
        for j, side, i in fades:
            if j + 9 < len(bars) and sd[j + 9] == sd[j]:
                fwd = cl[j + 9] - cl[j]
                if fwd != 0:
                    acc_rows.append(((side == "long") == (fwd > 0)))
            fb = j + 1
            if fb >= len(bars) or not bars.rth.iloc[fb] or fb <= busy:
                continue
            cns = int(bts[j]) + 60_000_000_000
            iev = int(np.searchsorted(ev_all, cns, side="right")) - 1
            mins = (cns - ev_all[iev]) / 60e9 if iev >= 0 else np.inf
            uref = prev.get(sd[fb], None)
            fill = o[fb]; long = side == "long"
            px, xi, reason, _ = run_leg(bars, pre, fb, fill, long, 1.0, p, fb, uref)
            tot = (px - fill) if long else (fill - px)
            if reason == "faststop":
                px2, xi2, _, _ = run_leg(bars, pre, xi, px, not long, 1.0, p, xi + 1, uref)
                tot += (px2 - px) if (not long) else (px - px2)
                xi = xi2
            frames["fade, all"].append(tot)
            if mins <= 30:
                frames["fade + news<=30m"].append(tot)
            busy = xi + 5
    acc = np.mean(acc_rows)
    print(f"his fade entries (relaxed def): {n_his_fades}; preceded by a failed-thrust fire "
          f"within 10 min, matching side: {cover} ({cover/max(n_his_fades,1):.0%})")
    print(f"fade-signal direction accuracy (9-bar forward, all firings): {acc:.1%} "
          f"on {len(acc_rows)} (baseline for with-moves was 54.9%)")
    print("\n| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    for name, pnl in frames.items():
        print(row(name + " (v9-B exits)", pnl))
    print("\nREAD: frozen fade definition, search-mode; survivors re-validate later.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
