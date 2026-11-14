#!/usr/bin/env python3
"""
p4_2_entry_context.py — P4.2: where were his entries? (descriptive, no conclusions)
====================================================================================
For every trade he took in the two discovery months, measure the surroundings of the
entry moment. DESCRIPTION ONLY — the output nominates what "a signal he could have
seen" means; nothing is judged here.

Per trade (entry time T, first entry price P, side):
  A. Nearest completed 1m WRB before T — same direction as the trade, and any direction:
     minutes since that bar completed; price distance entry-to-its-close (ticks).
  B. Nearest LIVE zone (unfilled WHG) at T, separately on 1m and 5m tables:
     live = formed within the last 2 days and no single bar before T traded through the
     whole zone (high >= top AND low <= bottom). Status: inside / near (<=8 ticks) / far;
     plus pointed-through (zone extends past the entry in the trade's direction),
     zone age (minutes), and minutes between the zone's formation and the nearest news event.
  C. Reference prices at T: distance (ticks) to yesterday's RTH high / low / close,
     today's RTH open, and the nearest 10-point round number.
  D. News: minutes to the nearest scheduled USD event before T and after T, the nearer
     event's name and measured size (median ticks, from kme_event_impact.csv).

Parameters fixed by P4_DESIGN.md: 2-day zone validity, 8-tick "near" (both inherited
from the October zone work, SPEC_06-10), tick = 0.25.

OUT: p4_2_entry_context.parquet + .csv (one row per trade) + printed distributions.
RUN: python3 Tests/P4_entry_determination/p4_2_entry_context.py            (repo root)
     python3 Tests/P4_entry_determination/p4_2_entry_context.py --selftest
"""
import argparse, os
import numpy as np
import pandas as pd

TICK = 0.25
NEAR_TK = 8
ZONE_VALID_DAYS = 2
MONTHS = [("2025-10", "ESZ5"), ("2022-02", "ESH2")]
HERE = os.path.dirname(os.path.abspath(__file__))
WHG_DIR = os.path.join(HERE, "..", "06_trade_flow_exhaustion_CANDIDATE", "06-10_whg_fill")


def month_bounds(month):
    lo = pd.Timestamp(f"{month}-01", tz="UTC")
    return lo, lo + pd.offsets.MonthBegin(1)


# ---------- A. nearest completed WRB before T ----------
def nearest_wrb(wrb_m, T, P, side, same_dir):
    w = wrb_m
    if same_dir:
        want = "bullish" if side == "long" else "bearish"
        w = w[w.direction == want]
    done = w[w.ts_event + pd.Timedelta(seconds=60) <= T]
    if done.empty:
        return np.nan, np.nan
    r = done.iloc[-1]
    mins = (T - (r.ts_event + pd.Timedelta(seconds=60))).total_seconds() / 60
    dist_tk = abs(P - r.close) / TICK
    return mins, dist_tk


# ---------- B. nearest live zone at T ----------
def zone_dead_by(bars, top, bottom, t_formed, T):
    """True if any single bar in (t_formed, T) covers the whole zone."""
    b = bars[(bars.ts_event > t_formed) & (bars.ts_event < T)]
    if b.empty:
        return False
    return bool(((b.high >= top) & (b.low <= bottom)).any())


def nearest_live_zone(whg_m, bars_m, T, P, side, kme_ts, bar_sec=60):
    w = whg_m[(whg_m.ts_event >= T - pd.Timedelta(days=ZONE_VALID_DAYS)) &
              (whg_m.ts_event + pd.Timedelta(seconds=bar_sec) <= T) & whg_m.has_whg]
    best = None
    for _, z in w.iloc[::-1].iterrows():                      # newest first
        if zone_dead_by(bars_m, z.whg_top, z.whg_bottom, z.ts_event, T):
            continue
        if z.whg_bottom <= P <= z.whg_top:
            d = 0.0
        else:
            d = min(abs(P - z.whg_top), abs(P - z.whg_bottom)) / TICK
        if best is None or d < best["dist_tk"]:
            best = dict(dist_tk=d, top=z.whg_top, bottom=z.whg_bottom,
                        formed=z.ts_event, direction=z.direction)
        if best and best["dist_tk"] == 0.0:
            break
    if best is None:
        return dict(zone_status="none", zone_dist_tk=np.nan, zone_age_min=np.nan,
                    zone_pointed=False, zone_form_to_news_min=np.nan)
    status = "inside" if best["dist_tk"] == 0 else ("near" if best["dist_tk"] <= NEAR_TK else "far")
    pointed = (best["top"] >= P) if side == "long" else (best["bottom"] <= P)
    age = (T - best["formed"]).total_seconds() / 60
    if len(kme_ts):
        dmin = np.abs((kme_ts - best["formed"]).dt.total_seconds()) / 60
        form_news = float(np.min(dmin))
    else:
        form_news = np.nan
    return dict(zone_status=status, zone_dist_tk=best["dist_tk"], zone_age_min=age,
                zone_pointed=bool(pointed), zone_form_to_news_min=form_news)


# ---------- C. reference prices ----------
def ref_prices(bars_m, T, P):
    rth = bars_m[bars_m.session == "RTH"]
    today = rth[rth.ts_event <= T]
    out = dict(d_prev_high_tk=np.nan, d_prev_low_tk=np.nan, d_prev_close_tk=np.nan,
               d_open_tk=np.nan)
    if today.empty:
        sd = None
    else:
        sd = today.iloc[-1].session_date
        tod = rth[rth.session_date == sd]
        out["d_open_tk"] = abs(P - tod.iloc[0].open) / TICK
        prev_days = rth[rth.session_date < sd]
        if not prev_days.empty:
            pd_ = prev_days[prev_days.session_date == prev_days.iloc[-1].session_date]
            out["d_prev_high_tk"] = abs(P - pd_.high.max()) / TICK
            out["d_prev_low_tk"] = abs(P - pd_.low.min()) / TICK
            out["d_prev_close_tk"] = abs(P - pd_.iloc[-1].close) / TICK
    out["d_round10_tk"] = abs(P - round(P / 10) * 10) / TICK
    return out


# ---------- D. news proximity ----------
def news_ctx(kme_m, impact, T):
    before = kme_m[kme_m.ts_utc <= T]
    after = kme_m[kme_m.ts_utc > T]
    out = dict(news_before_min=np.nan, news_after_min=np.nan,
               news_nearest="", news_nearest_tk=np.nan)
    ev = None
    if not before.empty:
        r = before.iloc[-1]
        out["news_before_min"] = (T - r.ts_utc).total_seconds() / 60
        ev = r
    if not after.empty:
        r = after.iloc[0]
        out["news_after_min"] = (r.ts_utc - T).total_seconds() / 60
        if ev is None or out["news_after_min"] < out["news_before_min"]:
            ev = r
    if ev is not None:
        out["news_nearest"] = ev.event
        out["news_nearest_tk"] = impact.get(ev.event, np.nan)
    return out


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    wrb = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    kme = pd.read_parquet(os.path.join(repo, "Data/inputs/kme_calendar.parquet"))
    imp = pd.read_csv(os.path.join(HERE, "kme_event_impact.csv"), index_col=0)
    impact = imp.median_tk.to_dict()
    # impact keys are event CLASSES; map raw speech names onto classes
    import re as _re
    def imp_of(name):
        for rx, cls in [(r"^FOMC Member .+ Speaks$", "FOMC Member Speaks"),
                        (r"^Fed Chair .+", "Fed Chair (any)"),
                        (r"^President .+ Speaks$", "President Speaks")]:
            if _re.match(rx, name):
                return impact.get(cls, np.nan)
        return impact.get(name, np.nan)

    rows = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        wrb_m = wrb[(wrb.symbol == sym) & (wrb.timeframe == "1m")].sort_values("ts_event")
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        whg1 = pd.read_parquet(os.path.join(WHG_DIR, f"whg_1m_{month}.parquet")).sort_values("ts_event")
        whg5 = pd.read_parquet(os.path.join(WHG_DIR, f"whg_5m_{month}.parquet")).sort_values("ts_event")
        kme_m = kme[(kme.currency == "USD") & kme.ts_utc.notna() &
                    (kme.ts_utc >= lo - pd.Timedelta(days=2)) & (kme.ts_utc < hi + pd.Timedelta(days=1))
                    ].sort_values("ts_utc")
        kme_ts = kme_m.ts_utc
        print(f"[{month}] trades={len(e)} wrb={len(wrb_m)} bars={len(bars_m)} "
              f"zones 1m/5m={len(whg1)}/{len(whg5)} news={len(kme_m)}")
        for _, t in e.iterrows():
            T, P, side = t.first_entry_utc, float(np.asarray(t.entry_prices).ravel()[0]), t.side
            sd_min, sd_tk = nearest_wrb(wrb_m, T, P, side, same_dir=True)
            ad_min, ad_tk = nearest_wrb(wrb_m, T, P, side, same_dir=False)
            z1 = {f"z1m_{k[5:]}" if k.startswith("zone_") else k: v
                  for k, v in nearest_live_zone(whg1, bars_m, T, P, side, kme_ts).items()}
            z5 = {f"z5m_{k[5:]}" if k.startswith("zone_") else k: v
                  for k, v in nearest_live_zone(whg5, bars_m, T, P, side, kme_ts, bar_sec=300).items()}
            row = dict(month=month, uid=f"{t.source_file}::{t.episode_id}", side=side,
                       entry=T, price=P,
                       wrb_same_min=sd_min, wrb_same_dist_tk=sd_tk,
                       wrb_any_min=ad_min, wrb_any_dist_tk=ad_tk,
                       **z1, **z5, **ref_prices(bars_m, T, P), **news_ctx(kme_m, impact, T))
            row["news_nearest_tk"] = imp_of(row["news_nearest"]) if row["news_nearest"] else np.nan
            rows.append(row)
    df = pd.DataFrame(rows)
    df.to_parquet(os.path.join(HERE, "p4_2_entry_context.parquet"), index=False)
    df.to_csv(os.path.join(HERE, "p4_2_entry_context.csv"), index=False)

    # ---------- printed distributions ----------
    q = lambda s: s.dropna().quantile([.25, .5, .75]).round(1).tolist()
    for month in [m for m, _ in MONTHS] + ["BOTH"]:
        d = df if month == "BOTH" else df[df.month == month]
        print(f"\n===== {month}  (n={len(d)}) =====")
        print(f"minutes since last same-direction WRB completed: p25/med/p75 = {q(d.wrb_same_min)}"
              f"  | within 2 min: {(d.wrb_same_min <= 2).mean():.0%}  within 5: {(d.wrb_same_min <= 5).mean():.0%}"
              f"  within 15: {(d.wrb_same_min <= 15).mean():.0%}")
        print(f"price distance to that WRB's close (ticks):      p25/med/p75 = {q(d.wrb_same_dist_tk)}")
        for tf in ("z1m", "z5m"):
            s = d[f"{tf}_status"].value_counts(normalize=True).round(2).to_dict()
            pt = d.loc[d[f"{tf}_status"] != "none", f"{tf}_pointed"].mean()
            print(f"zone ({tf[1:]}): {s}  | pointed-through where a zone exists: {pt:.0%}"
                  f"  | zone age min med: {d[f'{tf}_age_min'].median():.0f}"
                  f"  | zone-formed-to-news min med: {d[f'{tf}_form_to_news_min'].median():.0f}")
        print(f"ticks to: prev-day high {q(d.d_prev_high_tk)}  low {q(d.d_prev_low_tk)}  "
              f"close {q(d.d_prev_close_tk)}  today's open {q(d.d_open_tk)}  round-10 {q(d.d_round10_tk)}")
        print(f"minutes to news: before {q(d.news_before_min)}  after {q(d.news_after_min)}"
              f"  | entry within 30 min AFTER an event: {(d.news_before_min <= 30).mean():.0%}"
              f"  | nearest-event size (ticks) med: {d.news_nearest_tk.median():.0f}")
    print("\nREAD: description only. These distributions nominate the 'signal he could have "
          "seen' definitions that P4.3 will lock before any taken-vs-skipped comparison runs.")


def selftest():
    print("=== SELF-TEST ===")
    t0 = pd.Timestamp("2025-10-06 13:00", tz="UTC")
    mins = pd.date_range(t0, periods=300, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=mins, open=5000.0, high=5001.0, low=4999.0,
                             close=5000.0, session="RTH",
                             session_date=[d.date() for d in mins]))
    wrb_m = pd.DataFrame(dict(ts_event=[t0 + pd.Timedelta(minutes=10)], symbol="ESZ5",
                              timeframe="1m", direction=["bullish"], close=[5002.0]))
    T = t0 + pd.Timedelta(minutes=16)
    m, d = nearest_wrb(wrb_m, T, 5003.0, "long", True)
    print(f"  WRB: {m:.0f} min since completion (expect 5), {d:.0f} tk away (expect 4)")
    assert m == 5 and d == 4
    m2, _ = nearest_wrb(wrb_m, T, 5003.0, "short", True)
    assert np.isnan(m2); print("  no opposite-direction WRB -> NaN OK")
    whg = pd.DataFrame(dict(ts_event=[t0 + pd.Timedelta(minutes=10)], has_whg=True,
                            whg_top=[5004.0], whg_bottom=[5002.0], direction=["bullish"]))
    z = nearest_live_zone(whg, bars, T, 5003.0, "long", pd.Series([], dtype="datetime64[ns, UTC]"))
    print(f"  zone inside: {z['zone_status']} pointed={z['zone_pointed']}")
    assert z["zone_status"] == "inside" and z["zone_pointed"]
    bars2 = bars.copy()
    bars2.loc[12, ["high", "low"]] = [5005.0, 5001.0]      # one bar covers whole zone -> dead
    z2 = nearest_live_zone(whg, bars2, T, 5003.0, "long", pd.Series([], dtype="datetime64[ns, UTC]"))
    assert z2["zone_status"] == "none"; print("  traded-through zone -> none OK")
    r = ref_prices(bars, T, 5003.0)
    assert r["d_round10_tk"] == 12.0 and r["d_open_tk"] == 12.0
    print(f"  round-10 distance 12 tk OK, open distance 12 tk OK")
    kme_m = pd.DataFrame(dict(ts_utc=[T - pd.Timedelta(minutes=20), T + pd.Timedelta(minutes=40)],
                              event=["CPI m/m", "Minor Thing"]))
    n = news_ctx(kme_m, {"CPI m/m": 72.5}, T)
    assert n["news_before_min"] == 20 and n["news_after_min"] == 40 and n["news_nearest"] == "CPI m/m"
    print(f"  news: 20 min after CPI, next event in 40 min OK")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
