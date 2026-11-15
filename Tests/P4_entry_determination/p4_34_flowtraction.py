#!/usr/bin/env python3
"""
p4_34_flowtraction.py — P4.34: flow-based traction cuts (the informed version).
================================================================================
T-EN37 showed price/time traction thresholds trade loss size for win rate at par:
they cannot tell dead stalls from loading ones. Hypothesis (user direction): HE
reads the tape - post-entry aggressor flow is the information that distinguishes
them. Variants, frozen before the run, all on v9-B (reversal kept on the price
fast-fail; flow cuts exit flat; flow unknown -> no cut):
  FT1 at close of bar fill+2: mean oriented flow since the fill <= 0 -> cut
  FT2 same moment: flow <= 0 AND unrealized <= 0 -> cut (live flow excuses a
      stall; dead flow + no progress = dead trade)
  FT3 bars fill+1..fill+4: last-60s oriented flow <= -2 contracts/sec (actively
      against) -> cut
Frames: HIS 313 entries (benchmark -1.71 avg loss at 74% wins) and our entries.

RUN: python3 Tests/P4_entry_determination/p4_34_flowtraction.py            (repo root)
     python3 Tests/P4_entry_determination/p4_34_flowtraction.py --selftest
"""
import argparse, io, contextlib, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_31_profit_v9 import ARMS                          # noqa: E402
from p4_33_losscuts import month_ctx, row                 # noqa: E402
from p4_31_profit_v9 import wrb_flags                     # noqa: E402

EARLY_BARS = 2
TIME_BARS = 9
COOLDOWN_MIN = 5
FT3_THR = -2.0


class Flow:
    def __init__(self, repo, month):
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}.parquet"))
        self.sec = f.sec.to_numpy(np.int64)
        self.cum = np.concatenate([[0], np.cumsum((f.buyv - f.sellv).to_numpy(np.int64))])

    def mean(self, t0_ns, t1_ns, long):
        a = int(np.searchsorted(self.sec, t0_ns // 1_000_000_000))
        b = int(np.searchsorted(self.sec, t1_ns // 1_000_000_000))
        if b <= a:
            return np.nan
        m = (self.cum[b] - self.cum[a]) / (b - a)
        return m if long else -m


def run_leg(bars, pre, fb, fill, long, p, start_j, uref, flow, bts):
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt, wbody = pre
    n_pt = 0
    fill_ns = bts[fb]
    for j in range(start_j, len(bars)):
        if sd[j] != sd[fb] or not rth[j]:
            return c[j - 1], j - 1, "session"
        sp = p["early"] if j < fb + EARLY_BARS else p["stop"]
        stop = fill - sp if long else fill + sp
        if (l[j] <= stop if long else h[j] >= stop):
            return stop, j, ("faststop" if j < fb + EARLY_BARS else "stop")
        if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
            n_pt += 1
            big = p["ladder"] and uref and wbody[j] >= 2.0 * uref
            if n_pt >= 3 or not big:
                return c[j], j, f"pt{n_pt}"
        bar_end = bts[j] + 60_000_000_000
        up = (c[j] - fill) if long else (fill - c[j])
        ft = p.get("ft")
        if ft in (1, 2) and j == fb + 2:
            mf = flow.mean(fill_ns, bar_end, long)
            if np.isfinite(mf) and mf <= 0 and (ft == 1 or up <= 0):
                return c[j], j, "flowcut"
        if ft == 3 and fb + 1 <= j <= fb + 4:
            mf = flow.mean(bar_end - 60_000_000_000, bar_end, long)
            if np.isfinite(mf) and mf <= FT3_THR:
                return c[j], j, "flowcut"
        if j >= fb + TIME_BARS:
            return c[j], j, "time"
    return c[-1], len(bars) - 1, "eof"


VARIANTS = {"v9-B baseline": {}, "FT1 dead-flow@2bars": {"ft": 1},
            "FT2 dead-flow AND flat": {"ft": 2}, "FT3 flow-against": {"ft": 3}}


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    import p4_31_profit_v9 as V9
    with contextlib.redirect_stdout(io.StringIO()):
        A, _ = V9.capture_entries(repo)
    base = dict(ARMS["B (momentum ladder)"])
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    for vname, extra in VARIANTS.items():
        p = dict(base, **extra)
        his_frame, own_frame, ncut = [], [], 0
        for month, sym in MONTHS:
            bars, pre, prev, lo, hi = month_ctx(es, month, sym)
            bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
            sd = bars.session_date.astype(str).to_numpy()
            flow = Flow(repo, month)
            e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
            for _, t in e_m.iterrows():
                en = pd.Timestamp(t.first_entry_utc).value
                fb = int(np.searchsorted(bts, (en // 60_000_000_000) * 60_000_000_000))
                if fb >= len(bts) or not bars.rth.iloc[min(fb, len(bts) - 1)]:
                    continue
                P = float(np.asarray(t.entry_prices).ravel()[0]); long = t.side == "long"
                uref = prev.get(sd[fb], None)
                px, xi, r = run_leg(bars, pre, fb, P, long, p, fb + 1, uref, flow, bts)
                tot = (px - P) if long else (P - px)
                if r == "faststop":
                    px2, _, _ = run_leg(bars, pre, xi, px, not long, p, xi + 1, uref, flow, bts)
                    tot += (px2 - px) if (not long) else (px - px2)
                if r == "flowcut":
                    ncut += 1
                his_frame.append(tot)
            bars2, entries = A[month]
            bts2 = pd.DatetimeIndex(bars2.ts_event).as_unit("ns").asi8
            pre2 = wrb_flags(bars2)
            o2 = bars2.open.to_numpy()
            busy = -1
            for e in entries:
                fb = e["sig_i"] + 1
                if fb >= len(bars2) or not bars2.rth.iloc[fb] or fb <= busy:
                    continue
                fill = o2[fb]; long = e["side"] == "long"
                px, xi, r = run_leg(bars2, pre2, fb, fill, long, p, fb, e.get("uref"), flow, bts2)
                tot = (px - fill) if long else (fill - px)
                if r == "faststop":
                    px2, xi2, _ = run_leg(bars2, pre2, xi, px, not long, p, xi + 1, e.get("uref"), flow, bts2)
                    tot += (px2 - px) if (not long) else (px - px2)
                    xi = xi2
                own_frame.append(tot)
                busy = xi + COOLDOWN_MIN
        print(row(f"{vname} | HIS entries", his_frame))
        print(row(f"{vname} | our entries", own_frame))
    print("| HIS OWN EXITS (benchmark) | 306 | 74% | +6.25 / -1.71 | +1275.8 pts |")
    print("\nREAD: frozen variants, search-mode; a survivor becomes spec v10 and")
    print("re-validates out-of-sample later.")


def selftest():
    class F:
        def __init__(self): pass
    f = Flow.__new__(Flow)
    f.sec = np.arange(1000, 1200, dtype=np.int64)
    f.cum = np.concatenate([[0], np.cumsum(np.full(200, 3, np.int64))])
    m = f.mean(1000 * 10**9, 1060 * 10**9, True)
    assert abs(m - 3.0) < 1e-9 and abs(f.mean(1000 * 10**9, 1060 * 10**9, False) + 3.0) < 1e-9
    print("=== SELF-TEST ===\n  flow prefix-sum mean + orientation OK")
    assert np.isnan(f.mean(500 * 10**9, 600 * 10**9, True))
    print("  out-of-coverage -> NaN (no cut) OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
