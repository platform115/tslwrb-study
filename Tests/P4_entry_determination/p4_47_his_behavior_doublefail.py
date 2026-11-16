#!/usr/bin/env python3
"""
p4_47_his_behavior_doublefail.py — P4.47: what HE does and says around our
double fast-fails.
===========================================================================
For each v11 trade (all four run months), look at his record in a window
around our fill (-10 to +15 min):
  - did he enter a trade nearby? same direction as our first leg, or opposite?
  - how many chat messages did he post?
Compared across: double-fails / winning reversals / trades with no fast-fail.
Then dump his messages around every double-fail and every winning reversal to
two text files for qualitative pattern reading.

RUN: python3 Tests/P4_entry_determination/p4_47_his_behavior_doublefail.py  (repo root)
OUT: p4_47_msgs_doublefail.txt, p4_47_msgs_revwin.txt
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_46_doublefail import month_trades              # noqa: E402

W_PRE, W_POST = 10, 15                                 # minutes around our fill


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    parts = [month_trades(repo, es, m, True, s) for m, s in MONTHS]
    parts += [month_trades(repo, es, m, False) for m in ("2021-09", "2024-11")]
    d = pd.concat(parts, ignore_index=True)
    assert abs(d.tot.sum() - 621.5) < 0.15, f"GATE FAILED: {d.tot.sum():+.1f}"
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc"])
    en = pd.DatetimeIndex(ep.first_entry_utc).as_unit("ns").asi8
    esd = ep.side.to_numpy()
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    mts = pd.DatetimeIndex(msg.datetime_utc).as_unit("ns").asi8
    order = np.argsort(mts); mts = mts[order]
    mtx = msg.message.to_numpy()[order]
    mact = msg.trade_action.to_numpy()[order]

    tts = pd.DatetimeIndex(d.ts).as_unit("ns").asi8
    his_entry, his_same, n_msgs = [], [], []
    for i in range(len(d)):
        lo = tts[i] - W_PRE * 60_000_000_000
        hi = tts[i] + W_POST * 60_000_000_000
        m = (en >= lo) & (en <= hi)
        his_entry.append(bool(m.any()))
        if m.any():
            want = "long" if d.side.iloc[i] == "long" else "short"
            his_same.append(bool((esd[m] == want).any()))
        else:
            his_same.append(False)
        a, b = np.searchsorted(mts, lo), np.searchsorted(mts, hi)
        n_msgs.append(b - a)
    d["his_entry"] = his_entry; d["his_same"] = his_same; d["n_msgs"] = n_msgs

    dbl = (d.r2 == "faststop")
    rwin = (d.reason == "faststop") & (d.pnl2 > 0)
    nofail = d.reason != "faststop"
    print("| Around our trade (-10/+15 min) | Double-fails | Winning reversals | No fast-fail |")
    print("|---|---|---|---|")
    for lab, g in [("n", None)]:
        pass
    g1, g2, g3 = d[dbl], d[rwin], d[nofail]
    print(f"| n | {len(g1)} | {len(g2)} | {len(g3)} |")
    print(f"| he entered a trade nearby | {g1.his_entry.mean():.0%} | {g2.his_entry.mean():.0%} | {g3.his_entry.mean():.0%} |")
    print(f"| ...same direction as our first leg | {g1.his_same.mean():.0%} | {g2.his_same.mean():.0%} | {g3.his_same.mean():.0%} |")
    print(f"| avg messages posted in window | {g1.n_msgs.mean():.1f} | {g2.n_msgs.mean():.1f} | {g3.n_msgs.mean():.1f} |")
    print(f"| windows with ZERO messages | {(g1.n_msgs==0).mean():.0%} | {(g2.n_msgs==0).mean():.0%} | {(g3.n_msgs==0).mean():.0%} |")

    for name, mask in [("p4_47_msgs_doublefail.txt", dbl), ("p4_47_msgs_revwin.txt", rwin)]:
        with open(os.path.join(HERE, name), "w") as f:
            for _, r in d[mask].sort_values("ts").iterrows():
                t0 = pd.Timestamp(r.ts)
                lo = t0.value - W_PRE * 60_000_000_000
                hi = t0.value + W_POST * 60_000_000_000
                a, b = np.searchsorted(mts, lo), np.searchsorted(mts, hi)
                f.write(f"\n=== {r.month} {t0} our {r.side} tot {r.tot:+.2f} ===\n")
                for k in range(a, b):
                    dt = pd.Timestamp(mts[k]).strftime("%H:%M")
                    act = f" [{mact[k]}]" if isinstance(mact[k], str) and mact[k] else ""
                    f.write(f"{dt}{act} {str(mtx[k]).strip()[:300]}\n")
        print(f"wrote {name}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
