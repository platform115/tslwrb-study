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
def nearest_live_zone(whg_m, bars_m, T, P, side, kme_ts, bar_sec=60):
    """Nearest zone formed in the last ZONE_VALID_DAYS, REGARDLESS of fill status
    (user-confirmed 2026-11-14: he sometimes trades zones already filled, so fill
    state is recorded, never used as a filter). Fill state at T, canonical per
    WRB_Definition.txt 1.5: filled = ONE bar's range covers the whole zone;
    partial = price entered the zone (incl. top+bottom touched in different bars);
    unfilled = untouched. Judged on completed 1m bars after the zone's bar completes."""
    w = whg_m[(whg_m.ts_event >= T - pd.Timedelta(days=ZONE_VALID_DAYS)) &
              (whg_m.ts_event + pd.Timedelta(seconds=bar_sec) <= T) & whg_m.has_whg]
    if w.empty:
        return dict(zone_status="none", zone_fill="", zone_dist_tk=np.nan, zone_age_min=np.nan,
                    zone_pointed=False, zone_form_to_news_min=np.nan, zone_dir="")
    top = w.whg_top.to_numpy(); bot = w.whg_bottom.to_numpy()
    dist = np.where(P < bot, bot - P, np.where(P > top, P - top, 0.0)) / TICK
    j = int(np.flatnonzero(dist == dist.min())[-1])        # nearest; tie -> newest
    z = w.iloc[j]
    b = bars_m[(bars_m.ts_event >= z.ts_event + pd.Timedelta(seconds=bar_sec)) &
               (bars_m.ts_event + pd.Timedelta(seconds=60) <= T)]
    if len(b) and bool(((b.high >= z.whg_top) & (b.low <= z.whg_bottom)).any()):
        fill = "filled"
    elif len(b) and bool(((b.high >= z.whg_bottom) & (b.low <= z.whg_top)).any()):
        fill = "partial"
    else:
        fill = "unfilled"
    status = "inside" if dist[j] == 0 else ("near" if dist[j] <= NEAR_TK else "far")
    pointed = (z.whg_top >= P) if side == "long" else (z.whg_bottom <= P)
    age = (T - z.ts_event).total_seconds() / 60
    if len(kme_ts):
        form_news = float(np.min(np.abs((kme_ts - z.ts_event).dt.total_seconds()) / 60))
    else:
        form_news = np.nan
    return dict(zone_status=status, zone_fill=fill, zone_dist_tk=float(dist[j]), zone_age_min=age,
                zone_pointed=bool(pointed), zone_form_to_news_min=form_news,
                zone_dir=str(z.direction))


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
            at_zone = d[d[f"{tf}_status"].isin(["inside", "near"])]
            f = at_zone[f"{tf}_fill"].value_counts(normalize=True).round(2).to_dict()
            pt = d.loc[d[f"{tf}_status"] != "none", f"{tf}_pointed"].mean()
            print(f"zone ({tf[1:]}): position {s}")
            print(f"   fill state when at a zone (inside/near, n={len(at_zone)}): {f}"
                  f"  | pointed-through: {pt:.0%}  | age min med: {d[f'{tf}_age_min'].median():.0f}"
                  f"  | formed-to-news min med: {d[f'{tf}_form_to_news_min'].median():.0f}")
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
    print(f"  zone inside: {z['zone_status']} fill={z['zone_fill']} pointed={z['zone_pointed']}")
    assert z["zone_status"] == "inside" and z["zone_fill"] == "unfilled" and z["zone_pointed"]
    bars2 = bars.copy()
    bars2.loc[12, ["high", "low"]] = [5005.0, 5001.0]      # one bar sweeps whole zone
    z2 = nearest_live_zone(whg, bars2, T, 5003.0, "long", pd.Series([], dtype="datetime64[ns, UTC]"))
    assert z2["zone_status"] == "inside" and z2["zone_fill"] == "filled"
    print("  single-bar sweep -> still nearest, fill=filled OK")
    bars3 = bars.copy()
    bars3.loc[12, ["high", "low"]] = [5005.0, 5003.5]      # touches top only
    bars3.loc[13, ["high", "low"]] = [5003.0, 5001.0]      # later bar touches bottom only
    z3 = nearest_live_zone(whg, bars3, T, 5003.0, "long", pd.Series([], dtype="datetime64[ns, UTC]"))
    assert z3["zone_fill"] == "partial"
    print("  top+bottom in DIFFERENT bars -> partial (letter of the definition) OK")
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
