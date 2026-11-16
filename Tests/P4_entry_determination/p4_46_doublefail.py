#!/usr/bin/env python3
"""
p4_46_doublefail.py — P4.46: pt-reach table + the double fast-fail problem.
============================================================================
A) How many v11 legs see the 1st/2nd/3rd same-direction WRB before exiting.
B) The double fast-fail (24%, -3.00 each): what is observable BEFORE the
   reversal is placed that separates reversals that fail again from reversals
   that go on to win - using only facts available in real time at that moment.
C) The user's side thought, tested directly: reverse a SECOND time after the
   double fail (back to the original direction) - does the third leg pay?
D) In-sample only: do pre-ENTRY features predict which trades will double-fail
   (i.e., could we skip them at selection without losing winners)?
All four run months; gate: totals must match recorded v11 results.

RUN: python3 Tests/P4_entry_determination/p4_46_doublefail.py             (repo root)
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
FEATS = ["mins_since", "flow5", "flow15", "edge_tk", "body_r", "tape_r",
         "lag15_r", "tod", "shadow_r", "contr_n"]


def run_leg4(bars, pre, fb, fill, long, p, start_j, e_uref=None):
    """run_leg3 + returns npt (in-direction WRBs seen) and opp (opposite-direction
    WRB seen during the leg)."""
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt, wbody = pre
    n_pt = 0; opp = False
    best = fill
    mfe = lambda: (best - fill) if long else (fill - best)   # noqa: E731
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session", None, n_pt, opp, mfe()
        early = j < fb + p.get("early_bars", 2)
        sp = p["early"] if early else p["stop"]
        stop = fill - sp if long else fill + sp
        src = "early" if early else "full"
        fav_best = (best - fill) if long else (fill - best)
        tr = p.get("trail")
        if tr and fav_best >= tr[0]:
            t = best - tr[1] if long else best + tr[1]
            nb = max(stop, t) if long else min(stop, t)
            if nb != stop:
                stop, src = nb, "follow"
        if j > fb and isw[j] and ((wdir[j] == "bullish") != long):
            opp = True
        if (l[j] <= stop if long else h[j] >= stop):
            return stop, j, ("faststop" if early else "stop"), src, n_pt, opp, mfe()
        if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            n_pt += 1
            big = p["ladder"] and e_uref and wbody[j] >= 2.0 * e_uref
            if n_pt >= 3 or not big:
                return c[j], j, f"pt{n_pt}", None, n_pt, opp, mfe()
        if j >= fb + p.get("time_bars", 9):
            return c[j], j, "time", None, n_pt, opp, mfe()
        best = max(best, h[j]) if long else min(best, l[j])
    return c[-1], len(bars) - 1, "eof", None, n_pt, opp, mfe()


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
    hrs = pd.DatetimeIndex(bars.ts_event).hour + pd.DatetimeIndex(bars.ts_event).minute / 60
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
        px, xi, reason, src, npt1, opp1, mfe1 = run_leg4(bars, pre, fb, fill, long, V11, fb + 1, uref)
        tot = (px - fill) if long else (fill - px)
        rec = dict(month=month, ts=bars.ts_event.iloc[fb], side="long" if long else "short",
                   pnl1=(px - fill) if long else (fill - px),
                   npt=npt1, opp1=opp1, fail_bar=None, r2=None, npt2=0, pnl2=np.nan,
                   pnl3=np.nan, score=r.score, mv=abs(mv), tod=hrs[fb],
                   wait=fb - fb0 + 1)
        if insample:
            for f in FEATS:
                if f in r:
                    rec[f] = r[f]
        if reason == "faststop":
            rec["fail_bar"] = xi - fb                       # 0 or 1
            px2, xi2, r2, s2, npt2, opp2, mfe2 = run_leg4(bars, pre, xi, px, not long, V11, xi + 1, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            rec["r2"] = r2; rec["npt2"] = npt2; rec["mfe2"] = mfe2
            # favorable extreme ON the leg-2 exit bar (upper bound of what a
            # quick target could have caught; bar order unknown from 1m data)
            rec["mfe2bar"] = (px - l[xi2]) if (not long) else (h[xi2] - px)
            rec["pnl2"] = (px2 - px) if (not long) else (px - px2)
            if r2 == "faststop":                            # C) third leg, both directions
                px3, xi3, r3, _, _, _, _ = run_leg4(bars, pre, xi2, px2, long, V11, xi2 + 1, uref)
                rec["pnl3"] = (px3 - px2) if long else (px2 - px3)
                px4, xi4, r4, _, _, _, _ = run_leg4(bars, pre, xi2, px2, not long, V11, xi2 + 1, uref)
                rec["pnl3s"] = (px4 - px2) if (not long) else (px2 - px4)
            xi = xi2
        rec["reason"] = reason; rec["tot"] = tot
        out.append(rec)
        busy = xi + 5
    return pd.DataFrame(out)


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    parts = [month_trades(repo, es, m, True, s) for m, s in MONTHS]
    parts += [month_trades(repo, es, m, False) for m in ("2021-09", "2024-11")]
    d = pd.concat(parts, ignore_index=True)
    assert abs(d.tot.sum() - 621.5) < 0.15, f"GATE FAILED: {d.tot.sum():+.1f}"
    print(f"GATE OK: total {d.tot.sum():+.1f} matches recorded v11\n")
    months = ["2025-10", "2022-02", "2021-09", "2024-11"]

    print("A) pt-reach table - original legs: how many see the 1st/2nd/3rd")
    print("   same-direction WRB before the trade ends (month cells: n / avg leg pts)\n")
    print("| Reached | n | Share | Avg leg | " + " | ".join(months) + " |")
    print("|---|---|---|---|" + "---|" * 4)
    for k, lab in [(0, "no in-direction WRB"), (1, "pt1"), (2, "pt2"), (3, "pt3")]:
        g = d[d.npt >= k] if k else d[d.npt == 0]
        cells = [f"{len(g[g.month==m])} / {g[g.month==m].pnl1.mean():+.2f}" if len(g[g.month==m]) else "-"
                 for m in months]
        print(f"| {lab} | {len(g)} | {len(g)/len(d):.0%} | {g.pnl1.mean():+.2f} | " + " | ".join(cells) + " |")

    rev = d[d.reason == "faststop"]
    dbl = rev[rev.r2 == "faststop"]
    win = rev[rev.pnl2 > 0]
    print(f"\nB) at the moment of reversal (n={len(rev)}): double-fails (n={len(dbl)}) vs")
    print("   reversals that won (n={}) - facts observable in real time:\n".format(len(win)))
    print("| Observable at reversal | Double-fails | Winning reversals |")
    print("|---|---|---|")
    print(f"| first leg failed on bar 1 (vs 2) | {(dbl.fail_bar==0).mean():.0%} | {(win.fail_bar==0).mean():.0%} |")
    print(f"| opposite-direction WRB formed during first leg | {dbl.opp1.mean():.0%} | {win.opp1.mean():.0%} |")
    print(f"| avg entry score | {dbl.score.mean():.2f} | {win.score.mean():.2f} |")
    print(f"| avg 5-min move at entry (pts) | {dbl.mv.mean():.2f} | {win.mv.mean():.2f} |")
    print(f"| avg bars waited for the confirm fill | {dbl.wait.mean():.2f} | {win.wait.mean():.2f} |")
    print(f"| avg time of day (UTC hour) | {dbl.tod.mean():.1f} | {win.tod.mean():.1f} |")

    print(f"\nC) reverse a SECOND time after the double fail (third leg, original")
    print("   direction, v11 exits, no further reversal):\n")
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    a = dbl.pnl3.dropna().to_numpy(); w = a > 0
    pm = " | ".join(f"{m}: {dbl[dbl.month==m].pnl3.sum():+.0f}" for m in months)
    print(f"| third leg (re-reverse after double fail) | {len(a)} | {w.mean():.0%} | "
          f"+{a[w].mean():.2f} / {a[~w].mean():.2f} | {a.sum():+.1f} ({pm}) |")
    if "pnl3s" in dbl.columns:
        b = dbl.pnl3s.dropna().to_numpy(); wb = b > 0
        pms = " | ".join(f"{m}: {dbl[dbl.month==m].pnl3s.sum():+.0f}" for m in months)
        print(f"| third leg (re-enter SAME dir as the failed reversal) | {len(b)} | {wb.mean():.0%} | "
              f"+{b[wb].mean():.2f} / {b[~wb].mean():.2f} | {b.sum():+.1f} ({pms}) |")
    print(f"| status quo (exit after double fail) | {len(a)} | - | - | +0.0 |")

    ins = d[d.month.isin([m for m, _ in MONTHS])]
    if "flow5" in ins.columns:
        from p4_4_probes import rank_auc, boot_ci
        tgt = ins.r2 == "faststop"
        print(f"\nD) in-sample only: do pre-ENTRY features predict the double-fail?")
        print(f"   (double-fails n={int(tgt.sum())} vs all other trades n={int((~tgt).sum())};")
        print("   * = confidence interval excludes 0.5)\n")
        for f in FEATS + ["score", "mv", "wait", "tod"]:
            if f not in ins.columns:
                continue
            a_t = ins.loc[tgt, f].astype(float).dropna()
            a_k = ins.loc[~tgt, f].astype(float).dropna()
            if len(a_t) < 20:
                continue
            auc = rank_auc(a_t, a_k)
            ci = boot_ci(a_t, a_k) if auc > 0.5 else boot_ci(-a_t, -a_k)
            star = "*" if ci["clears"] else " "
            print(f"  {f:12s} AUC {auc:.3f}{star} [{ci['lo']:.3f},{ci['hi']:.3f}]")
    print("\nREAD: B and D are evidence; any gate built from them is a new spec change")
    print("to test in the development months first, like every other change.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
