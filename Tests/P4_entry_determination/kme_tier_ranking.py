#!/usr/bin/env python3
"""
kme_tier_ranking.py — P4.1b: rank KME event types by REALIZED ES impact; emit tier map.
=======================================================================================
WHY: Perry gives no formal KME list — his stated criterion is "impactful on the S&P 500."
This script IMPLEMENTS that criterion instead of hand-picking a list: rank event types by
the realized ES reaction around their releases. Precedent: announcement-effect event
studies on S&P futures (Andersen, Bollerslev, Diebold & Vega 2003/2007 rank macro
announcements by realized price response; MacKinlay 1997 event-study method). The TIER
CUT below is OUR construction implementing his criterion — flagged in every artifact.

PRE-REGISTERED (before any impact number was seen):
  Population: kme_calendar rows with currency=="USD" and a UTC timestamp,
    EXCLUDING (a) Oct-2025 and Feb-2022 entirely — the discovery months must not
    tune the tier definition (leakage guard); (b) roll-day session dates (CLAUDE.md);
    (c) releases with no bar coverage at t-1 or t+5.
  Event classes: exact event names, with three documented collapses (speeches are a
    class, not individuals): /^FOMC Member .+ Speaks$/ -> "FOMC Member Speaks";
    /^Fed Chair .+/ -> "Fed Chair (any)"; /^President .+ Speaks$/ -> "President Speaks".
  Impact stat per release: |close(t+5m) - close(t-1m)| in ticks, t = release minute
    (floor). Event-type impact = MEDIAN over its releases (robust at small n).
  Baseline: same stat at 10,000 seeded (seed 0) random minutes with NO USD KME within
    +/-30 min, same exclusions. Reported as baseline_median.
  Floor: event types with n < 8 scored releases are UNRANKED (insufficient).
  TIERS (our construction, stated): A if median >= 2.0x baseline_median; B if >= 1.25x;
    else C. The downstream probe grid {A, A+B, all timestamped} is where this choice's
    arbitrariness is controlled — tiers are a labeling, not a hypothesis test.

OUT: kme_event_impact.csv (full ranking) + kme_tiers.csv (event_class -> tier).
RUN: python3 Tests/P4_entry_determination/kme_tier_ranking.py            (from repo root)
     python3 Tests/P4_entry_determination/kme_tier_ranking.py --selftest
"""
import argparse, os, re
import numpy as np
import pandas as pd

TICK = 0.25
POST_MIN, PRE_MIN = 5, 1
N_MIN = 8
B_DRAWS, SEED = 10_000, 0
EXCL = [("2025-10-01", "2025-11-01"), ("2022-02-01", "2022-03-01")]
CLASSES = [(re.compile(r"^FOMC Member .+ Speaks$"), "FOMC Member Speaks"),
           (re.compile(r"^Fed Chair .+"), "Fed Chair (any)"),
           (re.compile(r"^President .+ Speaks$"), "President Speaks")]


def event_class(name: str) -> str:
    for rx, cls in CLASSES:
        if rx.match(name):
            return cls
    return name


def load(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"),
                         columns=["ts_event", "close", "is_roll_day", "session_date"])
    k = pd.read_parquet(os.path.join(repo, "Data/inputs/kme_calendar.parquet"))
    return es, k


def impacts(es: pd.DataFrame, when: pd.Series) -> np.ndarray:
    """|close(t+POST) - close(t-PRE)| in ticks for each ts in `when` (NaN if bars missing)."""
    close = es.set_index("ts_event")["close"]
    t = when.dt.floor("min")
    pre = close.reindex(t - pd.Timedelta(minutes=PRE_MIN)).to_numpy()
    post = close.reindex(t + pd.Timedelta(minutes=POST_MIN)).to_numpy()
    return np.abs(post - pre) / TICK


def run(repo, out_dir):
    es, k = load(repo)
    roll_dates = set(es.loc[es.is_roll_day, "session_date"].unique())
    ev = k[(k.currency == "USD") & k.ts_utc.notna()].copy()
    n0 = len(ev)
    for lo, hi in EXCL:
        ev = ev[~((ev.ts_utc >= pd.Timestamp(lo, tz="UTC")) & (ev.ts_utc < pd.Timestamp(hi, tz="UTC")))]
    n1 = len(ev)
    ev["sdate"] = ev.ts_utc.dt.floor("min").dt.date
    ev = ev[~ev.sdate.astype(str).isin({str(d) for d in roll_dates})]
    print(f"[pop] timestamped USD events: {n0} -> {n1} after discovery-month excl "
          f"-> {len(ev)} after roll-day excl")
    ev["cls"] = ev.event.map(event_class)
    ev["impact_tk"] = impacts(es, ev.ts_utc)
    scored = ev.dropna(subset=["impact_tk"])
    print(f"[pop] scored (bar coverage at t-{PRE_MIN}/t+{POST_MIN}): {len(scored)}")

    # ---- baseline: random no-event minutes ----
    rng = np.random.default_rng(SEED)
    bars = es[~es.is_roll_day].reset_index(drop=True)
    ev_min = ev.ts_utc.dt.floor("min").astype("int64").to_numpy() // 60_000_000_000
    ev_set = set(ev_min)
    guard = 30
    picks, tries = [], 0
    while len(picks) < B_DRAWS and tries < B_DRAWS * 20:
        i = int(rng.integers(0, len(bars))); tries += 1
        m = bars.ts_event.iloc[i].value // 60_000_000_000
        if any((m + d) in ev_set for d in range(-guard, guard + 1)):
            continue
        picks.append(bars.ts_event.iloc[i])
    base = impacts(es, pd.Series(picks))
    base_med = float(np.nanmedian(base))
    print(f"[baseline] {len(picks)} no-event minutes: median |move| = {base_med:.2f} tk "
          f"(mean {np.nanmean(base):.2f})")

    # ---- per-class ranking ----
    g = scored.groupby("cls")["impact_tk"]
    tab = pd.DataFrame({"n": g.size(), "median_tk": g.median(), "mean_tk": g.mean()})
    tab["x_baseline"] = tab.median_tk / base_med
    tab["ranked"] = tab.n >= N_MIN
    def tier(r):
        if not r.ranked: return "unranked"
        return "A" if r.x_baseline >= 2.0 else ("B" if r.x_baseline >= 1.25 else "C")
    tab["tier"] = tab.apply(tier, axis=1)
    tab = tab.sort_values(["ranked", "median_tk"], ascending=[False, False])
    os.makedirs(out_dir, exist_ok=True)
    tab.to_csv(os.path.join(out_dir, "kme_event_impact.csv"))
    tab[tab.ranked][["tier"]].to_csv(os.path.join(out_dir, "kme_tiers.csv"))
    print(f"\n[tiers] A={int((tab.tier=='A').sum())}  B={int((tab.tier=='B').sum())}  "
          f"C={int((tab.tier=='C').sum())}  unranked={int((tab.tier=='unranked').sum())}")
    print("\n===== TOP 25 ranked event classes (median |t-1 -> t+5| move, ticks) =====")
    with pd.option_context("display.width", 120):
        print(tab[tab.ranked].head(25).round(2).to_string())
    print(f"\n[done] wrote kme_event_impact.csv + kme_tiers.csv  (baseline median {base_med:.2f} tk)")


def selftest():
    print("=== SELF-TEST ===")
    ts = pd.date_range("2024-01-02", periods=600, freq="1min", tz="UTC")
    close = np.full(600, 5000.0)
    close[300:] += 2.0                                  # one 8-tick jump at minute 300
    es = pd.DataFrame(dict(ts_event=ts, close=close, is_roll_day=False,
                           session_date=ts.date))
    when = pd.Series([ts[300]])                          # event right at the jump
    v = impacts(es, when)
    print(f"  jump event impact: {v[0]:.1f} tk (expect 8.0)")
    assert abs(v[0] - 8.0) < 1e-9
    quiet = pd.Series([ts[100]])
    v2 = impacts(es, quiet)
    print(f"  quiet impact: {v2[0]:.1f} tk (expect 0.0)"); assert v2[0] == 0.0
    missing = pd.Series([ts[0] - pd.Timedelta(minutes=10)])
    assert np.isnan(impacts(es, missing)[0]); print("  out-of-coverage -> NaN OK")
    assert event_class("FOMC Member Barr Speaks") == "FOMC Member Speaks"
    assert event_class("Non-Farm Employment Change") == "Non-Farm Employment Change"
    print("  event classes OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="Tests/P4_entry_determination")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo, a.out)
