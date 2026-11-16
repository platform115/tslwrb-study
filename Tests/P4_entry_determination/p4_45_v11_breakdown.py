#!/usr/bin/env python3
"""
p4_45_v11_breakdown.py — P4.45: v11 results breakdown table (exit paths x months).
===================================================================================
Re-runs v11 on the four months already run (2025-10, 2022-02 development;
2021-09, 2024-11 validation) with exit-path labeling: which rule actually ended
each trade, including whether a "stop" was the follow-stop or the full 4-pt stop.
GATE: per-month totals must equal the recorded v11 results exactly
(+206.0 / +314.9 ~ pooled +521.0; +57.2; +43.2) - labeling must change nothing.

RUN: python3 Tests/P4_entry_determination/p4_45_v11_breakdown.py          (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS                  # noqa: E402
from p4_31_profit_v9 import wrb_flags                  # noqa: E402
from p4_33_losscuts import month_ctx                   # noqa: E402
from p4_42_v10_oos import score_month, WAIT            # noqa: E402
from p4_43_exit_sharpen import BASE                    # noqa: E402

V11 = {**BASE, "trail": (2.0, 2.5), "early": 1.5}


def run_leg3(bars, pre, fb, fill, long, p, start_j, e_uref=None):
    """run_leg2 logic byte-identical; extra return = which rule bound ('early',
    'full', 'follow', 'be') when the exit was a stop."""
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt, wbody = pre
    n_pt = 0
    best = fill
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session", None
        early = j < fb + p.get("early_bars", 2)
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        src = "early" if early else "full"
        fav_best = (best - fill) if long else (fill - best)
        if p.get("be_at") and fav_best >= p["be_at"]:
            nb = max(stop, fill) if long else min(stop, fill)
            if nb != stop:
                stop, src = nb, "be"
        tr = p.get("trail")
        if tr and fav_best >= tr[0]:
            t = best - tr[1] if long else best + tr[1]
            nb = max(stop, t) if long else min(stop, t)
            if nb != stop:
                stop, src = nb, "follow"
        if (l[j] <= stop if long else h[j] >= stop):
            return stop, j, ("faststop" if early else "stop"), src
        if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            n_pt += 1
            big = p["ladder"] and e_uref and wbody[j] >= 2.0 * e_uref
            if n_pt >= 3 or not big:
                return c[j], j, f"pt{n_pt}", None
        if j >= fb + p.get("time_bars", 9):
            return c[j], j, "time", None
        best = max(best, h[j]) if long else min(best, l[j])
    return c[-1], len(bars) - 1, "eof", None


def leg_label(reason, src):
    if reason == "stop":
        return "follow-stop" if src == "follow" else "full stop"
    if reason in ("pt1", "pt2", "pt3"):
        return "pt exit"
    return reason                       # time, session, faststop, eof


def month_trades(repo, es, month, insample, sym=None):
    if insample:
        sig = pd.read_csv(os.path.join(HERE, "p4_36_all_signals.csv"))
        sig = sig[(sig.month == month) & (sig.score >= 6)]
        bars, _, prev, lo, hi = month_ctx(es, month, sym)
    else:
        sig, bars, _ = score_month(repo, month)
        sig = sig[sig.score >= 6]
    pre = wrb_flags(bars)
    bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
    cl = bars.close.to_numpy(); o = bars.open.to_numpy()
    h, l = bars.high.to_numpy(), bars.low.to_numpy()
    out = []; busy = -1
    for _, r in sig.sort_values("comp_ns").iterrows():
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
        px, xi, reason, src = run_leg3(bars, pre, fb, fill, long, V11, fb + 1, uref)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xi2, r2, s2 = run_leg3(bars, pre, xi, px, not long, V11, xi + 1, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            path = "fast-fail -> reversed -> " + leg_label(r2, s2)
            xi = xi2
        else:
            path = leg_label(reason, src) + " (original leg)"
        out.append(dict(month=month, path=path, pnl=tot))
        busy = xi + 5
    return pd.DataFrame(out)


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    parts = [month_trades(repo, es, m, True, s) for m, s in MONTHS]
    parts += [month_trades(repo, es, m, False) for m in ("2021-09", "2024-11")]
    d = pd.concat(parts, ignore_index=True)
    exp = {"2025-10": None, "2022-02": None, "2021-09": 57.2, "2024-11": 43.2}
    tots = d.groupby("month").pnl.sum()
    assert abs(tots.sum() - (521.0 + 57.2 + 43.2)) < 0.15, f"GATE FAILED: {tots}"
    for m, v in exp.items():
        if v is not None:
            assert abs(tots[m] - v) < 0.05, f"GATE FAILED {m}: {tots[m]:+.1f} != {v:+.1f}"
    print(f"GATE OK: per-month totals match recorded v11 results ({tots.sum():+.1f} overall)\n")
    months = ["2025-10", "2022-02", "2021-09", "2024-11"]
    order = d.groupby("path").pnl.count().sort_values(ascending=False).index
    print("| Exit path | n | Share | Avg | Total | " + " | ".join(months) + " |")
    print("|---|---|---|---|---|" + "---|" * 4)
    for pth in order:
        g = d[d.path == pth]
        cells = []
        for m in months:
            gm = g[g.month == m]
            cells.append(f"{len(gm)} / {gm.pnl.sum():+.0f}" if len(gm) else "-")
        print(f"| {pth} | {len(g)} | {len(g)/len(d):.0%} | {g.pnl.mean():+.2f} | "
              f"{g.pnl.sum():+.1f} | " + " | ".join(cells) + " |")
    print(f"| ALL | {len(d)} | 100% | {d.pnl.mean():+.2f} | {d.pnl.sum():+.1f} | " +
          " | ".join(f"{len(d[d.month==m])} / {d[d.month==m].pnl.sum():+.0f}" for m in months) + " |")
    print("\nNOTE: month cells are n / points. 'follow-stop' = the new profit-protecting")
    print("stop; 'full stop' = the fixed 4-pt stop. A follow-stop hit inside the first")
    print("2 bars still counts as fast-fail (frozen behavior) and triggers the reversal.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
