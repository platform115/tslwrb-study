#!/usr/bin/env python3
"""
p4_5a_taken_anatomy.py — P4.5a: anatomy of the TAKEN trades' KME -> WRB -> level chain.
========================================================================================
Trader-stated mechanism #2 (user, 2026-11-14): a KME occurs, a WRB forms at/after it,
and the TOP and BOTTOM of that WRB's body become the price levels where his interest
concentrates. This script reconstructs that chain for every trade he entered in the
two discovery months, and maps WHERE his entry price sat relative to those edges.

TAKEN-ONLY BY DESIGN: this builds the template. No baseline here - the template gets
applied to matching-but-not-entered situations in the next step, which is the test.

Per entry (all 313, not only signal-matched ones):
  KME     = last scheduled USD event before entry (all-events width, standing decision)
  gap     = minutes from that event to entry
  W1(tf)  = the FIRST WRB on timeframe tf (1m canonical; 5m, 15m rebuilt from bars)
            completing within 30 min after the event and before the entry
            ("the reaction bar"). May not exist.
  For each existing W1: body_top = max(open, close), body_bottom = min(open, close);
  entry price classified vs the body: above / AT-top / inside / AT-bottom / below,
  with "AT" tolerance on a grid of 2 / 4 / 8 ticks; signed tick distances kept.
  Also: W1 direction vs trade side (same / opposite).

OUT: p4_5a_taken_anatomy.csv + printed distributions (the template).
RUN: python3 Tests/P4_entry_determination/p4_5a_taken_anatomy.py            (repo root)
     python3 Tests/P4_entry_determination/p4_5a_taken_anatomy.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS  # noqa: E402
from p4_2b_zone_mtf import resample  # noqa: E402
from p4_3_confluence_news import news_sets  # noqa: E402

TICK = 0.25
REACT_MIN = 30          # WRB must complete within this many minutes after the event
TOLS = [2, 4, 8]        # "AT the edge" tolerance grid, ticks
TFS_ANAT = [1, 5, 15]


def wrb_bodies(bars: pd.DataFrame) -> pd.DataFrame:
    """All WRBs (body strictly > each of prior 3 bodies, one session, no doji) with
    OHLC body edges — zone NOT required (differs from the WHG tables on purpose)."""
    o = bars.open.to_numpy(); c = bars.close.to_numpy()
    sd = bars.session_date.astype(str).to_numpy()
    body = np.abs(c - o); rows = []
    for i in range(3, len(bars)):
        if not (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) or body[i] <= 0:
            continue
        if body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]:
            rows.append((bars.ts_event.iloc[i], "bullish" if c[i] > o[i] else "bearish",
                         min(o[i], c[i]), max(o[i], c[i])))
    return pd.DataFrame(rows, columns=["ts_event", "direction", "body_bottom", "body_top"])


def first_reaction_wrb(w: pd.DataFrame, tf_min: int, ev_ns: int, entry_ns: int):
    """First WRB on this table completing in (event, event+REACT_MIN] and before entry."""
    comp = pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + tf_min * int(60e9)
    m = (comp > ev_ns) & (comp <= ev_ns + REACT_MIN * int(60e9)) & (comp <= entry_ns)
    if not m.any():
        return None
    i = int(np.flatnonzero(m)[0])
    return dict(direction=w.direction.iloc[i], bottom=float(w.body_bottom.iloc[i]),
                top=float(w.body_top.iloc[i]),
                comp_to_entry_min=(entry_ns - comp[i]) / 60e9)


def classify(P, bottom, top, tol_tk):
    d_top = (P - top) / TICK; d_bot = (P - bottom) / TICK
    if abs(d_top) <= tol_tk:
        return "AT-top"
    if abs(d_bot) <= tol_tk:
        return "AT-bottom"
    if P > top:
        return "above"
    if P < bottom:
        return "below"
    return "inside"


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev_all = news_sets(repo)["all"]
    rows = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        wtab = {1: wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m")]
                      .rename(columns={"whg_bottom": "_x"})  # keep canonical, body edges from o/c
                      .assign(body_bottom=lambda d: np.minimum(d.open, d.close),
                              body_top=lambda d: np.maximum(d.open, d.close))
                      [["ts_event", "direction", "body_bottom", "body_top"]]
                      .sort_values("ts_event")}
        for tf in (5, 15):
            wtab[tf] = wrb_bodies(resample(bars_m, tf))
        print(f"[{month}] entries={len(e)} WRBs 1m/5m/15m="
              f"{len(wtab[1])}/{len(wtab[5])}/{len(wtab[15])}")
        for _, t in e.iterrows():
            T = t.first_entry_utc; P = float(np.asarray(t.entry_prices).ravel()[0])
            en = pd.Timestamp(T).value
            i = int(np.searchsorted(ev_all, en, side="right")) - 1
            r = dict(month=month, uid=f"{t.source_file}::{t.episode_id}", side=t.side,
                     entry=T, price=P,
                     gap_kme_min=(en - ev_all[i]) / 60e9 if i >= 0 else np.nan)
            for tf in TFS_ANAT:
                w1 = first_reaction_wrb(wtab[tf], tf, ev_all[i], en) if i >= 0 else None
                if w1 is None:
                    r[f"tf{tf}_has_react"] = False
                    continue
                r[f"tf{tf}_has_react"] = True
                r[f"tf{tf}_dir_same"] = (w1["direction"] == "bullish") == (t.side == "long")
                r[f"tf{tf}_d_top_tk"] = (P - w1["top"]) / TICK
                r[f"tf{tf}_d_bot_tk"] = (P - w1["bottom"]) / TICK
                r[f"tf{tf}_min_edge_tk"] = min(abs(r[f"tf{tf}_d_top_tk"]), abs(r[f"tf{tf}_d_bot_tk"]))
                r[f"tf{tf}_wrb_to_entry_min"] = w1["comp_to_entry_min"]
                for tol in TOLS:
                    r[f"tf{tf}_loc_tol{tol}"] = classify(P, w1["bottom"], w1["top"], tol)
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "p4_5a_taken_anatomy.csv"), index=False)

    q = lambda s: s.dropna().quantile([.25, .5, .75]).round(1).tolist()
    print(f"\n===== TEMPLATE: the {len(df)} taken trades =====")
    print(f"minutes from last event to entry: p25/med/p75 = {q(df.gap_kme_min)}"
          f" | entry within 30 min of an event: {(df.gap_kme_min <= 30).mean():.0%}"
          f" | within 60: {(df.gap_kme_min <= 60).mean():.0%}")
    for tf in TFS_ANAT:
        has = df[df[f"tf{tf}_has_react"] == True]  # noqa: E712
        print(f"\n--- {tf}m reaction WRB (formed <=30 min after the event, before entry) ---")
        print(f"exists for {len(has)}/{len(df)} entries ({len(has)/len(df):.0%})")
        if not len(has):
            continue
        print(f"  trade side matches reaction-WRB direction: {has[f'tf{tf}_dir_same'].mean():.0%}")
        print(f"  minutes from that WRB's completion to entry: {q(has[f'tf{tf}_wrb_to_entry_min'])}")
        print(f"  distance to nearest body edge (ticks): {q(has[f'tf{tf}_min_edge_tk'])}")
        for tol in TOLS:
            loc = has[f"tf{tf}_loc_tol{tol}"].value_counts(normalize=True).round(2).to_dict()
            print(f"  position vs body (tol {tol} tk): {loc}")
    print("\nREAD: taken-only template by design - no baseline here. The next step applies")
    print("this template to matching moments he did NOT enter; only that comparison (and")
    print("the reserved years) says whether the template has selective power.")


def selftest():
    print("=== SELF-TEST ===")
    ts = pd.date_range("2025-10-06 13:00", periods=40, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, session_date=[d.date() for d in ts]))
    bars.loc[10, ["close", "high"]] = [5004.0, 5004.0]     # WRB bar at minute 10
    w = wrb_bodies(bars)
    assert len(w) == 1 and w.iloc[0].body_top == 5004.0 and w.iloc[0].body_bottom == 5000.0
    print("  WRB body edges OK")
    ev = pd.Timestamp("2025-10-06 13:08", tz="UTC").value
    entry = pd.Timestamp("2025-10-06 13:20", tz="UTC").value
    w1 = first_reaction_wrb(w, 1, ev, entry)
    assert w1 is not None and w1["comp_to_entry_min"] == 9.0
    print("  reaction WRB found (completes 13:11, entry 13:20 -> 9 min) OK")
    assert first_reaction_wrb(w, 1, ev, pd.Timestamp("2025-10-06 13:10", tz="UTC").value) is None
    print("  entry before WRB completion -> no reaction bar OK")
    assert classify(5004.5, 5000.0, 5004.0, 4) == "AT-top"
    assert classify(5000.2, 5000.0, 5004.0, 2) == "AT-bottom"
    assert classify(5002.0, 5000.0, 5004.0, 2) == "inside"
    assert classify(5006.0, 5000.0, 5004.0, 2) == "above"
    print("  edge classification OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
