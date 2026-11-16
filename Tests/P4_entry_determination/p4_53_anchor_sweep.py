#!/usr/bin/env python3
"""
p4_53_anchor_sweep.py — P4.53: reverse engineering his GROUP A entry PRICES -
the anchor sweep.
==============================================================================
Think backward from each of his Group A entries (141): catalog every price
level computable from available data at entry time ("anchors"), and measure,
for each anchor type, how often his entry sits within 2 ticks of one - against
the chance rate (every RTH 1-minute close, same months, same anchors). Then a
greedy cover: how many of his entries does the best small set of anchors
jointly explain, and is that union still above chance?
No-lookahead: running levels use completed bars only; windowed levels (WRBs,
his prior trades) exist only after they form.
Anchor catalog (first-pass settings recorded in code):
  his-exit / his-entry: his prior trades' prices, active 60 min after close
  firstWRB-1m/3m/5m/10m/15m: first reaction WRB per KME per chart, body
    top/bottom, active 60 min
  allWRB-10m: every 10m reaction WRB (the P4.51 hint), active 60 min
  zone-3m/5m/10m: WHG zone top/bottom at formation, active 120 min
  today-high/low: running session extreme (through the prior completed bar)
  rth-open: today's RTH opening price
  prev-close/high/low: prior RTH session's close/high/low
  overnight-high/low: this session date's ETH range
  round-5 / round-10: multiples of 5 / 10 points
  vwap: running RTH session VWAP (through the prior completed bar)

RUN: python3 Tests/P4_entry_determination/p4_53_anchor_sweep.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
from p4_2b_zone_mtf import identify_whg, resample      # noqa: E402
import p4_51_kme_levels as p51                         # noqa: E402
from p4_49_sec_engine import Ctx, ALL_MONTHS           # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_52_return_tests import his_prior_levels        # noqa: E402

TICK = 0.25
TOL_TK = 2
LIFE_NS = 60 * int(60e9)
ZONE_LIFE_NS = 120 * int(60e9)


def windowed_hit(points, ts, px, life):
    for t0, p0 in points:
        if t0 <= ts <= t0 + life and abs(px - p0) / TICK <= TOL_TK:
            return True
    return False


def month_anchors(repo, cx, lo, hi, ep):
    """Everything needed to answer: is (ts, px) within 2tk of anchor type X?"""
    ev_all = news_sets(repo)["all"]
    bars = cx.bars
    # windowed WRB levels
    p51.FIRST_ONLY = True
    lv_first = p51.levels_for_month(bars, ev_all, lo, hi)
    p51.FIRST_ONLY = False
    lv_all10 = p51.levels_for_month(bars, ev_all, lo, hi)[10]
    def pts(lv):
        comp, bot, top = lv
        return sorted([(int(c), float(b)) for c, b in zip(comp, bot)] +
                      [(int(c), float(t)) for c, t in zip(comp, top)])
    W = {f"firstWRB-{tf}m": pts(lv_first[tf]) for tf in (1, 3, 5, 10, 15)}
    W["allWRB-10m"] = pts(lv_all10)
    # WHG zone edges
    for tf in (3, 5, 10):
        z = identify_whg(bars if tf == 1 else resample(bars, tf))
        z = z[z.whg_top.notna()]
        comp = pd.DatetimeIndex(z.ts_event).as_unit("ns").asi8 + tf * int(60e9)
        W[f"zone-{tf}m"] = sorted([(int(c), float(b)) for c, b in zip(comp, z.whg_bottom)] +
                                  [(int(c), float(t)) for c, t in zip(comp, z.whg_top)])
    # his prior trade prices
    e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    ex_lv, en_lv = his_prior_levels(e_m)
    W["his-exit"] = ex_lv
    W["his-entry"] = en_lv
    # running session levels, through the PRIOR completed bar (no lookahead)
    sd = bars.session_date.astype(str).to_numpy()
    rth = bars.rth.to_numpy()
    h, l, c, o = bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy(), bars.open.to_numpy()
    v = bars.volume.to_numpy(float)
    n = len(bars)
    run_hi = np.full(n, np.nan); run_lo = np.full(n, np.nan)
    vwap = np.full(n, np.nan); rth_open = np.full(n, np.nan)
    on_hi = np.full(n, np.nan); on_lo = np.full(n, np.nan)
    prev_c = np.full(n, np.nan); prev_h = np.full(n, np.nan); prev_l = np.full(n, np.nan)
    sess_stats = {}
    cur = None
    for i in range(n):
        if sd[i] != cur:
            cur = sd[i]
            hh = ll = np.nan; pv = vv = 0.0; ro = np.nan; oh = ol = np.nan
            dates = sorted(sess_stats)
            pc = sess_stats[dates[-1]] if dates else None
        if pc:
            prev_c[i], prev_h[i], prev_l[i] = pc
        run_hi[i], run_lo[i], vwap[i] = hh, ll, (pv / vv if vv > 0 else np.nan)
        rth_open[i], on_hi[i], on_lo[i] = ro, oh, ol
        if rth[i]:
            hh = h[i] if np.isnan(hh) else max(hh, h[i])
            ll = l[i] if np.isnan(ll) else min(ll, l[i])
            pv += c[i] * v[i]; vv += v[i]
            if np.isnan(ro):
                ro = o[i]
            sess_stats[cur] = (c[i], hh, ll)
        else:
            oh = h[i] if np.isnan(oh) else max(oh, h[i])
            ol = l[i] if np.isnan(ol) else min(ol, l[i])
    R = {"today-high": run_hi, "today-low": run_lo, "rth-open": rth_open,
         "prev-close": prev_c, "prev-high": prev_h, "prev-low": prev_l,
         "overnight-high": on_hi, "overnight-low": on_lo, "vwap": vwap}
    return W, R


def hits_for(W, R, bts, ib, ts, px):
    out = {}
    for k, pts_ in W.items():
        life = ZONE_LIFE_NS if k.startswith("zone") else LIFE_NS
        out[k] = windowed_hit(pts_, ts, px, life)
    for k, arr in R.items():
        out[k] = np.isfinite(arr[ib]) and abs(px - arr[ib]) / TICK <= TOL_TK
    out["round-5"] = abs(px / 5.0 - round(px / 5.0)) * 5.0 / TICK <= TOL_TK
    out["round-10"] = abs(px / 10.0 - round(px / 10.0)) * 10.0 / TICK <= TOL_TK
    return out


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    his_rows, base_rows = [], []
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        for _, t in e_m[g == "A"].iterrows():
            ts = pd.Timestamp(t.first_entry_utc).value
            px = float(np.asarray(t.entry_prices).ravel()[0])
            ib = int(np.searchsorted(cx.bts, ts)) - 1   # last bar started before entry
            his_rows.append(hits_for(W, R, cx.bts, ib, ts, px))
        rthb = cx.bars[cx.bars.rth]
        idx = rthb.index.to_numpy()
        bns = pd.DatetimeIndex(rthb.ts_event).as_unit("ns").asi8 + int(60e9)
        bcl = rthb.close.to_numpy()
        mm = (bns >= lo.value) & (bns < hi.value)
        for ib, ts, px in zip(idx[mm], bns[mm], bcl[mm]):
            base_rows.append(hits_for(W, R, cx.bts, int(ib), int(ts), float(px)))
    H = pd.DataFrame(his_rows); B = pd.DataFrame(base_rows)
    print(f"Universe: his GROUP A entries, n={len(H)}. Chance: {len(B)} RTH minutes.")
    print(f"'Hit' = entry price within {TOL_TK} ticks of a live level of that type.\n")
    print("| Anchor type | His hits | His share | Chance share | He vs chance |")
    print("|---|---|---|---|---|")
    stats = []
    for k in H.columns:
        hs, bs = H[k].mean(), B[k].mean()
        stats.append((k, H[k].sum(), hs, bs, hs / max(bs, 1e-9)))
    for k, n_, hs, bs, r in sorted(stats, key=lambda x: -x[4]):
        print(f"| {k} | {int(n_)} | {hs:.0%} | {bs:.0%} | {r:.2f}x |")
    # greedy cover, judged by ratio of covered share his vs baseline
    print("\nGREEDY COVER - adding the anchor that lifts HIS coverage most each step:")
    print("| Step | Anchor added | His covered | Chance covered | Ratio |")
    print("|---|---|---|---|---|")
    hcov = np.zeros(len(H), bool); bcov = np.zeros(len(B), bool)
    chosen = []
    for step in range(1, 7):
        best = None
        for k in H.columns:
            if k in chosen:
                continue
            gain = (hcov | H[k].to_numpy()).mean() - hcov.mean()
            if best is None or gain > best[1]:
                best = (k, gain)
        k = best[0]; chosen.append(k)
        hcov |= H[k].to_numpy(); bcov |= B[k].to_numpy()
        print(f"| {step} | {k} | {hcov.mean():.0%} | {bcov.mean():.0%} | "
              f"{hcov.mean()/max(bcov.mean(),1e-9):.2f}x |")
    disc = [k for k, n_, hs, bs, r in stats if r >= 2.0]
    hu = np.zeros(len(H), bool); bu = np.zeros(len(B), bool)
    for k in disc:
        hu |= H[k].to_numpy(); bu |= B[k].to_numpy()
    print(f"\nTHE DISCRIMINATING SET (every anchor with ratio >= 2.0): {', '.join(disc)}")
    print("| | His entries at one of these | Chance | Ratio |")
    print("|---|---|---|---|")
    print(f"| union | {int(hu.sum())}/{len(H)} = {hu.mean():.0%} | {bu.mean():.0%} | "
          f"{hu.mean()/max(bu.mean(),1e-9):.2f}x |")
    print("\nREAD: a union that covers his entries AND most minutes explains nothing;")
    print("the Ratio column is the honest judge. Settings first-pass, recorded.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--tol", type=int, default=2)
    a = ap.parse_args()
    TOL_TK = a.tol
    import p4_53_anchor_sweep as _m
    _m.TOL_TK = a.tol
    run(a.repo)
