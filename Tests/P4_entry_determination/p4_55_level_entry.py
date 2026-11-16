#!/usr/bin/env python3
"""
p4_55_level_entry.py — P4.55: the LEVEL-BASED entry variant (honest engine,
in-sample development only).
=============================================================================
Built from the T-EN53/56/57 findings, strategy-knowable inputs only:
  SIGNAL     unchanged: frozen v6 score >= 6 at a 1m WRB completion (ungated)
  DIRECTION  unchanged: sign of the last 5-min move
  ENTRY (new) limit order at the nearest LIVE LEVEL on the pullback side of the
             signal close (long: level at/below close; short: at/above), within
             12 ticks; valid 5 bars; price never returns -> no trade; fill at
             the level exactly (no price improvement credited).
             LEVELS (all live-computable, 60-min life):
               - first reaction WRB per KME, body top/bottom: 1m, 5m, 10m
               - every 10m reaction WRB, body top/bottom
               - OUR OWN prior trades' fill and exit prices (his mechanic,
                 translated: the strategy re-enters at its own recent prices)
             VETO: skip if the limit sits within 2 ticks of the running session
             high (he entered there 0/141 times).
  EXITS      v11 stack on the per-second engine (early cut 1.5 + one reversal,
             stop 4.0, follow-stop 2.0/2.5, pt ladder, time 9 bars, session).
IN-SAMPLE (2025-10, 2022-02) ONLY - the validation months stay untouched until
this is frozen. First-pass settings recorded: 12tk max distance, no-improvement
fills, high-side veto only.

RUN: python3 Tests/P4_entry_determination/p4_55_level_entry.py            (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_49_sec_engine import Ctx, leg_sec, V11         # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_53_anchor_sweep import month_anchors           # noqa: E402

TICK = 0.25
WAIT = 5
MAXD_TK = 12
VETO_TK = 2
LIFE_NS = 60 * int(60e9)
LVL_KEYS = ["firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]
EXITS = dict(V11)
REVERSE = True


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    print("| Configuration | Trades | Wins | Losses | Win rate | Avg win / loss | Total | Max DD |")
    print("|---|---|---|---|---|---|---|---|")
    his_rows = []
    pooled = []
    for month, sym in MONTHS:
        cx = Ctx(repo, month, True)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        static = sorted(sum((W[k] for k in LVL_KEYS), []))
        st_t = np.array([t for t, _ in static], dtype=np.int64)
        st_p = np.array([p for _, p in static])
        day_hi = R["today-high"]
        own = []                                   # (avail_ns, price) of our trades
        pnl = []; busy = -1; n_sig = n_armed = 0
        for _, r in cx.sig.sort_values("comp_ns").iterrows():
            cns = int(r.comp_ns)
            ib = int(np.searchsorted(cx.bts, cns - 60_000_000_000))
            if ib >= len(cx.bts) or cx.bts[ib] != cns - 60_000_000_000 or ib < 5:
                continue
            fb0 = ib + 1
            if fb0 >= len(cx.bts) or not cx.rth[fb0] or fb0 <= busy:
                continue
            mv = cx.c[ib] - cx.c[ib - 5]
            if mv == 0:
                continue
            n_sig += 1
            long = mv > 0
            px0 = cx.c[ib]
            # candidate levels, pullback side, within MAXD, live at cns
            a = np.searchsorted(st_t, cns - LIFE_NS)
            b = np.searchsorted(st_t, cns, side="right")
            cand = list(st_p[a:b]) + [p for t0, p in own if t0 <= cns <= t0 + LIFE_NS]
            cand = [L for L in cand
                    if (L <= px0 if long else L >= px0) and abs(px0 - L) / TICK <= MAXD_TK]
            if not cand:
                continue
            L = max(cand) if long else min(cand)   # nearest on the pullback side
            if np.isfinite(day_hi[ib]) and abs(L - day_hi[ib]) / TICK <= VETO_TK:
                continue
            n_armed += 1
            # per-second limit fill, valid through bar fb0+WAIT-1 (RTH only)
            jmax = fb0
            while jmax + 1 < len(cx.bsec) and jmax + 1 < fb0 + WAIT and cx.rth[jmax + 1]:
                jmax += 1
            i = int(np.searchsorted(cx.secs, cx.bsec[fb0]))
            end_s = cx.bsec[jmax] + 60
            fill_s = None
            while i < len(cx.secs) and cx.secs[i] < end_s:
                m = cx.mids[i]
                if (m <= L) if long else (m >= L):
                    fill_s = int(cx.secs[i])
                    break
                i += 1
            if fill_s is None:
                continue
            fb = cx.bar_of(fill_s)
            uref = r.uref if np.isfinite(r.uref) else None
            px, xs, xb, reason = leg_sec(cx, fb, L, fill_s, long, EXITS, uref)
            tot = (px - L) if long else (L - px)
            if REVERSE and reason == "faststop":
                px2, xs2, xb2, _ = leg_sec(cx, xb, px, xs, not long, EXITS, uref)
                tot += (px2 - px) if (not long) else (px - px2)
                xb, xs = xb2, xs2
            pnl.append(tot)
            own.append((int(xs * 1e9) if xs < 1e14 else int(xs), L))
            own.append((int(xs * 1e9) if xs < 1e14 else int(xs), float(px)))
            busy = xb + 5
        a_ = np.asarray(pnl); w = a_ > 0
        eq = np.cumsum(a_); dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(a_) else 0.0
        print(f"| LEVEL ENTRY {month} | {len(a_)} | {int(w.sum())} | {int((~w).sum())} | "
              f"{w.mean():.0%} | +{a_[w].mean():.2f} / {a_[~w].mean():.2f} | {a_.sum():+.1f} | {dd:.1f} |"
              f"  (signals {n_sig}, armed {n_armed}, filled {len(a_)})")
        pooled += pnl
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, True, e_m)
        eA = e_m[g == "A"]
        hw = eA.realized_pnl > 0
        his_rows.append(f"| HIS GROUP A {month} | {len(eA)} | {int(hw.sum())} | {int((~hw).sum())} | "
                        f"{hw.mean():.0%} | +{eA.realized_pnl[hw].mean():.1f} / "
                        f"{eA.realized_pnl[~hw].mean():.1f} (as parsed) | "
                        f"{eA.realized_pnl.sum():+.0f} (as parsed) | - |")
    a_ = np.asarray(pooled); w = a_ > 0
    print(f"| LEVEL ENTRY pooled | {len(a_)} | {int(w.sum())} | {int((~w).sum())} | {w.mean():.0%} | "
          f"+{a_[w].mean():.2f} / {a_[~w].mean():.2f} | {a_.sum():+.1f} | - |")
    print("| v11 honest reference 2025-10 | 206 | 82 | 124 | 40% | +3.37 / -2.36 | -16.8 | 51.0 |")
    print("| v11 honest reference 2022-02 | 204 | 96 | 108 | 47% | +2.74 / -2.26 | +18.6 | 43.0 |")
    for r_ in his_rows:
        print(r_)
    print("\nREAD: in-sample development on the honest engine; validation months untouched.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tight", action="store_true",
                    help="level-coherent exits: stop 1.5 beyond the level at all "
                         "times, NO reversal (default: v11 stack with reversal)")
    a = ap.parse_args()
    if a.tight:
        EXITS = {**V11, "stop": 1.5}
        REVERSE = False
        print("MODE: level-coherent exits (stop 1.5 beyond level, no reversal)\n")
    run(a.repo)
