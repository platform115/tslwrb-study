#!/usr/bin/env python3
"""
p4_38_group_stats.py — P4.38: the full ledger per entry group (A / B / C-fade / C-other).
==========================================================================================
For each of his 313 discovery entries, grouped under the relaxed universe
(A = same-direction signal scoring >= 6 in the prior 5 min · B = same-direction
signal under-scored · C-fade = only opposite-direction signal · C-other = no
signal), report BOTH sides in exact ES points:
  HIS side: trades, win rate, avg win / avg loss, total points (points computed
  from his recorded entry/exit prices; exact for 1-in/1-out episodes - the
  per-group subset size is shown)
  OUR side: v9-B exits (reversal included) simulated on those same entries at
  his price/minute/side - trades, win rate, avg win / avg loss, total
  CAUGHT: how many of the group the current mode-A rule flags (A by definition).

RUN: python3 Tests/P4_entry_determination/p4_38_group_stats.py            (repo root)
OUT: p4_38_entry_ledger.csv (per-entry: group, his pts, our pts)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_31_profit_v9 import run_leg, ARMS                 # noqa: E402
from p4_33_losscuts import month_ctx                      # noqa: E402

def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
    p = dict(ARMS["B (momentum ladder)"])
    rows = []
    for month, sym in MONTHS:
        bars, pre, prev, lo, hi = month_ctx(es, month, sym)
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        sd = bars.session_date.astype(str).to_numpy()
        sm = sig[sig.month == month]
        comp = sm.comp_ns.to_numpy(np.int64); dirs = sm.direction.to_numpy()
        sc = sm.score.to_numpy()
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        for _, t in e_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            want = "bullish" if t.side == "long" else "bearish"
            m = (comp >= en - 5 * 60_000_000_000) & (comp < en)
            md = m & (dirs == want)
            if md.any():
                g = "A" if sc[np.flatnonzero(md)].max() >= 6 else "B"
            elif m.any():
                g = "C-fade"
            else:
                g = "C-other"
            # his exact points (1-in/1-out)
            his_pts = np.nan
            if t.n_entries == 1 and t.n_exits == 1:
                P0 = float(np.asarray(t.entry_prices).ravel()[0])
                X0 = float(np.asarray(t.exit_prices).ravel()[0])
                his_pts = (X0 - P0) if t.side == "long" else (P0 - X0)
            # our sim on his entry
            fb = int(np.searchsorted(bts, (en // 60_000_000_000) * 60_000_000_000))
            our = np.nan
            if fb < len(bts) and bars.rth.iloc[min(fb, len(bts) - 1)]:
                P = float(np.asarray(t.entry_prices).ravel()[0])
                long = t.side == "long"
                uref = prev.get(sd[fb], None)
                px, xi, r, _ = run_leg(bars, pre, fb, P, long, 1.0, p, fb + 1, uref)
                our = (px - P) if long else (P - px)
                if r == "faststop":
                    px2, _, _, _ = run_leg(bars, pre, xi, px, not long, 1.0, p, xi + 1, uref)
                    our += (px2 - px) if (not long) else (px - px2)
            rows.append(dict(month=month, group=g, his_win=t.realized_pnl > 0,
                             his_pts=his_pts, our_pts=our))
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(HERE, "p4_38_entry_ledger.csv"), index=False)
    print("| Group | His trades | Caught by rule | HIS: win% / avg win / avg loss / TOTAL pts (exact n) "
          "| OURS same entries: win% / avg win / avg loss / TOTAL |")
    print("|---|---|---|---|---|")
    order = ["A", "B", "C-fade", "C-other"]
    for g in order + ["ALL"]:
        dd = d if g == "ALL" else d[d.group == g]
        hp = dd.his_pts.dropna()
        hw = hp > 0
        op = dd.our_pts.dropna()
        ow = op > 0
        caught = len(dd) if g == "A" else (len(d[d.group == "A"]) if g == "ALL" else 0)
        his = (f"{dd.his_win.mean():.0%} / +{hp[hw].mean():.2f} / {hp[~hw].mean():.2f} / "
               f"{hp.sum():+.1f} (n={len(hp)})")
        ours = (f"{ow.mean():.0%} / +{op[ow].mean():.2f} / {op[~ow].mean():.2f} / {op.sum():+.1f}"
                if len(op) else "-")
        print(f"| {g} | {len(dd)} | {caught} | {his} | {ours} |")
    print("\nNOTE: 'caught' = flagged by the current mode-A rule (score>=6 same-direction")
    print("signal in the prior 5 min). Our side = v9-B exits at his price/minute/side.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
