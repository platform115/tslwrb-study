#!/usr/bin/env python3
"""
p6_1_entry_typology.py — IMITATION STUDY step 1: HIS entries grouped by TYPE.
ONE TRAINING MONTH (user directive). Descriptive, no P&L, no rule-building.
===============================================================================
Every feature is computed from data AT OR BEFORE the entry second
(truncation-harness discipline). His first-entry-per-episode moments only
(adds/re-entries are management decisions, typed later).

FEATURES per entry:
  Tape (per-second mids, all honest):
    mv8   - 8-second move, ticks (burst state)
    mv120 - 2-minute move, ticks
    mv300 - 5-minute move, ticks
    alignment - sign agreement of each with HIS side
  Flow: signed volume toward his side over the last 5 min (contracts/s)
  Clock: minutes from RTH open (or overnight flag); within 45 min AFTER a KME
  Structure (USER'S NEW LEVEL DEFINITION):
    WRB body BORDER BANDS (body_top and body_bottom +/- BAND ticks), 1m/3m/5m:
      - CURRENT-SESSION levels: WRB completed this session before entry
      - VIRGIN levels: completed any earlier time, and price NEVER entered the
        border band between completion and entry
    Feature: tick distance from entry price to nearest qualifying border;
    near-flag at <= 3 and <= 6 ticks.

MOMENTUM STATE (typing axis 1, thresholds stated, descriptive only):
  burst-aligned: |mv8| >= 4 ticks and sign matches his side
  drift-aligned: |mv120| >= 8 ticks matching side, without the burst
  counter:       mv120 >= 8 ticks AGAINST his side (fade entry)
  quiet:         none of the above
Cross-tabbed with border proximity, KME window, session, flow sign.

RUN: python3 Tests/P6_imitation_study/p6_1_entry_typology.py --month 2025-10
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
from p4_2_entry_context import month_bounds             # noqa: E402
from p4_3_confluence_news import news_sets              # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies              # noqa: E402
from p4_2b_zone_mtf import resample                     # noqa: E402
from p4_66_context_ablation import prep                 # noqa: E402

TICK = 0.25
BAND = 3            # border band half-width, ticks (also reported at 6)
KME_WIN = 45 * 60
TFS = (1, 3, 5)
BURST_T, DRIFT_T = 4.0, 8.0


def border_catalog(bars):
    """Per tf: arrays (comp_ns, body_top, body_bottom, session_date)."""
    out = {}
    for tf in TFS:
        rb = bars if tf == 1 else resample(bars, tf)
        w = wrb_bodies(rb)
        comp = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + tf * int(60e9)
        # session date of each WRB, looked up from the source bars
        rb_ts = pd.DatetimeIndex(rb.ts_event).as_unit("ns").asi8
        rb_sd = rb.session_date.astype(str).to_numpy()
        w_ts = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8
        sd = rb_sd[np.searchsorted(rb_ts, w_ts)]
        o = np.argsort(comp)
        out[tf] = (comp[o], w.body_top.to_numpy()[o], w.body_bottom.to_numpy()[o],
                   sd[o])
    return out


def nearest_border(cat, cx, s0_ns, px, sd0, band_ticks):
    """Min tick distance to a qualifying border at entry: current-session
    levels, plus VIRGIN older levels (price never in the band since
    completion). Returns (dist_ticks or inf, kind)."""
    best = np.inf; kind = "-"
    for tf, (comp, top, bot, sd) in cat.items():
        k2 = np.searchsorted(comp, s0_ns)
        for k in range(max(0, k2 - 400), k2):
            cur = sd[k] == sd0
            for border in (top[k], bot[k]):
                d = abs(px - border) / TICK
                if d >= best:
                    continue
                if cur:
                    best, kind = d, f"{tf}m-session"
                    continue
                # virgin check: price never touched the band since completion
                j1 = int(np.searchsorted(cx.bts, comp[k], "right")) - 1
                j2 = int(np.searchsorted(cx.bts, s0_ns, "right")) - 1
                if j2 <= j1 + 1:
                    continue
                hi = cx.h[j1 + 1:j2]; lo = cx.l[j1 + 1:j2]
                b = band_ticks * TICK
                touched = ((lo <= border + b) & (hi >= border - b)).any()
                if not touched:
                    best, kind = d, f"{tf}m-virgin"
    return best, kind


def run(repo, month):
    P = prep(repo, month)
    cx = P["cx"]; bars = cx.bars
    secs, mids = P["secs"], P["mids"]
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds(month)
    e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].copy()
    ev_all = np.asarray(news_sets(repo)["all"], dtype=np.int64)
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
    sv = (f.buyv - f.sellv).to_numpy(float)   # rows align 1:1 with P["secs"]
    csv_ = np.concatenate([[0.0], np.cumsum(sv)])
    cat = border_catalog(bars)
    glbx = (bars.session == "GLOBEX").to_numpy()

    rows = []
    for _, r in e_m.iterrows():
        s0 = int(pd.Timestamp(r.first_entry_utc).value // 10**9)
        side = 1 if r.side == "long" else -1
        j = int(np.searchsorted(secs, s0, "right")) - 1
        if j < 10:
            continue
        px = float(mids[j])

        def mv(back):
            k = int(np.searchsorted(secs, s0 - back))
            return (mids[j] - mids[min(k, j)]) / TICK
        m8, m120, m300 = mv(8), mv(120), mv(300)
        m120s = side * m120            # side-adjusted (+ = with his trade)
        a1 = int(np.searchsorted(secs, s0 - 300))
        a2 = int(np.searchsorted(secs, s0, "right"))
        fl5 = side * (csv_[a2] - csv_[a1]) / 300.0
        ib = int(np.searchsorted(cx.bts, s0 * 10**9, "right")) - 1
        on = bool(glbx[ib])
        mins_open = float(P["mins_rth"][ib]) if (not on and "mins_rth" in P) else np.nan
        kk = np.searchsorted(ev_all, s0 * 10**9, "right") - 1
        kme = bool(kk >= 0 and (s0 * 10**9 - ev_all[kk]) <= KME_WIN * 10**9)
        sd0 = str(P["sd"][ib])
        d3, kind3 = nearest_border(cat, cx, s0 * 10**9, px, sd0, BAND)
        # momentum state
        if abs(m8) >= BURST_T and np.sign(m8) == side:
            state = "burst-aligned"
        elif abs(m120) >= DRIFT_T and np.sign(m120) == side:
            state = "drift-aligned"
        elif m120 * side <= -DRIFT_T:
            state = "counter (fade)"
        else:
            state = "quiet"
        rows.append(dict(state=state, side=side, on=on, mins_open=mins_open,
                         kme=kme, m8=m8, m120=m120, m120s=m120s, m300=m300, fl5=fl5,
                         dist=d3, kind=kind3))
    df = pd.DataFrame(rows)
    n = len(df)
    print(f"===== {month}: {n} first entries (of {len(e_m)} episodes) =====\n")
    print("## Momentum state x structure/context (counts)")
    print("| State | n | share | near border <=3t | <=6t | virgin-near <=6t | in KME window | overnight | median flow toward (c/s) | median m120 toward (t) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for st in ("burst-aligned", "drift-aligned", "counter (fade)", "quiet"):
        g = df[df.state == st]
        if not len(g):
            continue
        vn = g[g.kind.str.contains("virgin") & (g.dist <= 6)]
        print(f"| {st} | {len(g)} | {len(g)/n:.0%} | {(g.dist<=3).mean():.0%} "
              f"| {(g.dist<=6).mean():.0%} | {len(vn)/len(g):.0%} "
              f"| {g.kme.mean():.0%} | {g.on.mean():.0%} "
              f"| {g.fl5.median():+.1f} | {g.m120s.median():+.1f} |")
    # AMBIENT NULL for border proximity: random RTH seconds, same definition
    rng = np.random.default_rng(3)
    rth_sec_idx = np.flatnonzero(P["keep"]) if "keep" in P else None
    amb = rng.choice(rth_sec_idx, size=min(250, len(rth_sec_idx)), replace=False)
    adist = []
    for j in amb:
        s0a = int(secs[j]); iba = int(np.searchsorted(cx.bts, s0a*10**9, "right")) - 1
        da, _ = nearest_border(cat, cx, s0a*10**9, float(mids[j]), str(P["sd"][iba]), BAND)
        adist.append(da)
    adist = np.asarray(adist)
    print("\n## Border proximity overall (his entries) - WITH AMBIENT NULL")
    print(f"within 3 ticks: {(df.dist<=3).mean():.0%} | within 6: "
          f"{(df.dist<=6).mean():.0%} | median distance: "
          f"{df.dist.replace(np.inf, np.nan).median():.1f} ticks")
    print(f"AMBIENT NULL (250 random RTH seconds, same levels): within 3 ticks "
          f"{(adist<=3).mean():.0%} | within 6 {(adist<=6).mean():.0%} | "
          f"median {np.median(adist[np.isfinite(adist)]):.1f} ticks")
    print(f"of near (<=6t) entries, level kind: "
          f"{df[df.dist<=6].kind.value_counts().to_dict()}")
    print("\n## Clock")
    rt = df[~df.on]
    if len(rt):
        print(f"RTH entries {len(rt)} ({len(rt)/n:.0%}); minutes-from-open "
              f"quartiles: {rt.mins_open.quantile([.25,.5,.75]).round(0).tolist()}")
    print(f"overnight entries: {df.on.sum()} ({df.on.mean():.0%}); "
          f"KME-window entries: {df.kme.sum()} ({df.kme.mean():.0%})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--month", default="2025-10")
    a = ap.parse_args()
    run(a.repo, a.month)
