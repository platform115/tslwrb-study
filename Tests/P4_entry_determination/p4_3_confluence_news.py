#!/usr/bin/env python3
"""
p4_3_confluence_news.py — P4.3 prep: the three factors that must beat the baseline.
====================================================================================
User priority (2026-11-14): cross-timeframe zone agreement ("confluence") and zones
formed around meaningful news are the factors to be thorough on. This script measures
both — plus the overdue baseline check on WRB timing — for all 313 entries AND the
same 4,000 random flat desk-window moments used in p4_2b. DESCRIPTION ONLY: the
signal-worthy quantity is always the entries-vs-baseline gap.

MEASURES per point (entry or random moment):
  1. TIMING: minutes since the last 1m WRB completed — any direction for both groups;
     trade-direction for entries vs a seeded random direction for baseline moments
     (markets are two-sided; a random side is the fair stand-in).
  2. CONFLUENCE: of his five chart timeframes (1/3/5/10/15m), on how many is the point
     INSIDE a zone (0-5)? And on how many inside a zone whose direction matches the
     trade side (baseline: the seeded random side)?
  3. NEWS-FORMED ZONES: for the nearest zone on each timeframe, minutes between its
     formation and the nearest news event, and whether it formed within 30 minutes
     AFTER an event — at the three approved news widths:
     ALL scheduled USD events · events >=20 ticks median move · >=45 ticks (jobs/CPI/Fed).

RUN: python3 Tests/P4_entry_determination/p4_3_confluence_news.py            (repo root)
     python3 Tests/P4_entry_determination/p4_3_confluence_news.py --selftest
OUT: p4_3_confluence_news.csv + printed comparison tables.
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import nearest_live_zone, month_bounds, MONTHS  # noqa: E402
from p4_2b_zone_mtf import zone_tables, sample_baseline, TFS  # noqa: E402

SEED = 0
AFTER_MIN = 30          # "formed after news" window (descriptive; grid later if probed)
WIDTH_TK = {"all": 0.0, ">=20tk": 20.0, ">=45tk": 45.0}


def mins_since_completion(wrb_ts_completion_ns: np.ndarray, T) -> float:
    """Minutes since the last WRB completion at/before T (NaN if none)."""
    t = np.int64(pd.Timestamp(T).value)
    i = np.searchsorted(wrb_ts_completion_ns, t, side="right") - 1
    return (t - wrb_ts_completion_ns[i]) / 60e9 if i >= 0 else np.nan


def news_sets(repo):
    kme = pd.read_parquet(os.path.join(repo, "Data/inputs/kme_calendar.parquet"))
    imp = pd.read_csv(os.path.join(HERE, "kme_event_impact.csv"), index_col=0)
    import re
    def size_of(name):
        for rx, cls in [(r"^FOMC Member .+ Speaks$", "FOMC Member Speaks"),
                        (r"^Fed Chair .+", "Fed Chair (any)"),
                        (r"^President .+ Speaks$", "President Speaks")]:
            if re.match(rx, str(name)):
                name = cls; break
        return imp.median_tk.get(name, np.nan)
    k = kme[(kme.currency == "USD") & kme.ts_utc.notna()].copy()
    k["size_tk"] = k.event.map(size_of)
    out = {}
    for w, thr in WIDTH_TK.items():
        sel = k if thr == 0 else k[k.size_tk >= thr]
        out[w] = np.sort(pd.DatetimeIndex(sel.ts_utc).as_unit("ns").asi8)   # force ns (parquet stores us)
    return out


def formed_after_news(formed_ns: float, ev_ns: np.ndarray) -> tuple:
    """(minutes to nearest event either side, formed within AFTER_MIN after an event?)"""
    if not len(ev_ns) or not np.isfinite(formed_ns):
        return np.nan, False
    i = np.searchsorted(ev_ns, formed_ns)
    cands = []
    if i > 0: cands.append(formed_ns - ev_ns[i - 1])          # event before formation
    if i < len(ev_ns): cands.append(ev_ns[i] - formed_ns)     # event after formation
    nearest = min(cands) / 60e9
    after = (i > 0) and ((formed_ns - ev_ns[i - 1]) / 60e9 <= AFTER_MIN)
    return nearest, after


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev = news_sets(repo)
    rng = np.random.default_rng(SEED)
    rows = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        zt = zone_tables(bars_m, month)
        w1 = wrb[(wrb.symbol == sym) & (wrb.timeframe == "1m")].sort_values("ts_event")
        comp = {"any": (w1.ts_event.astype("int64") + 60_000_000_000).to_numpy()}
        for d in ("bullish", "bearish"):
            comp[d] = (w1[w1.direction == d].ts_event.astype("int64") + 60_000_000_000).to_numpy()
        close_at = bars_m.set_index("ts_event")["close"]

        pts = [(t.first_entry_utc, float(np.asarray(t.entry_prices).ravel()[0]),
                "entry", t.side) for _, t in e.iterrows()]
        bts = sample_baseline(e, rng)
        bps = close_at.reindex(pd.DatetimeIndex(bts).floor("min"), method="ffill").to_numpy()
        bsides = rng.choice(["long", "short"], size=len(bts))
        pts += [(t, p, "baseline", sd) for t, p, sd in zip(bts, bps, bsides)]
        print(f"[{month}] points: {len(e)} entries + {len(bts)} baseline")

        for T, P, grp, side in pts:
            want = "bullish" if side == "long" else "bearish"
            r = dict(month=month, group=grp, t=T, side=side,
                     m_any=mins_since_completion(comp["any"], T),
                     m_dir=mins_since_completion(comp[want], T))
            n_in = n_dir = 0
            for tf in TFS:
                z = nearest_live_zone(zt[tf], bars_m, T, P, side,
                                      pd.Series([], dtype="datetime64[ns, UTC]"), bar_sec=tf * 60)
                inside = z["zone_status"] == "inside"
                n_in += int(inside)
                n_dir += int(inside and z["zone_dir"] == want)
                formed_ns = (pd.Timestamp(T).value - z["zone_age_min"] * 60e9
                             if np.isfinite(z["zone_age_min"]) else np.nan)
                for w in WIDTH_TK:
                    near, aft = formed_after_news(formed_ns, ev[w])
                    r[f"tf{tf}_news_{w}_min"] = near
                    r[f"tf{tf}_formed_after_{w}"] = aft
            r["n_inside"] = n_in; r["n_inside_dir"] = n_dir
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "p4_3_confluence_news.csv"), index=False)

    E = df[df.group == "entry"]; B = df[df.group == "baseline"]
    q = lambda s: s.dropna().quantile([.25, .5, .75]).round(1).tolist()
    print("\n===== 1. TIMING: minutes since last 1m WRB completed =====")
    print(f"  any direction  — entries {q(E.m_any)}  baseline {q(B.m_any)}"
          f"  | within 5 min: {(E.m_any <= 5).mean():.0%} vs {(B.m_any <= 5).mean():.0%}")
    print(f"  with direction — entries {q(E.m_dir)}  baseline(random side) {q(B.m_dir)}"
          f"  | within 5 min: {(E.m_dir <= 5).mean():.0%} vs {(B.m_dir <= 5).mean():.0%}"
          f"  | within 2 min: {(E.m_dir <= 2).mean():.0%} vs {(B.m_dir <= 2).mean():.0%}")

    print("\n===== 2. CONFLUENCE: on how many of the 5 timeframes is the point inside a zone? =====")
    for name, col in [("inside any zone", "n_inside"), ("inside, direction matches", "n_inside_dir")]:
        ed = E[col].value_counts(normalize=True).sort_index()
        bd = B[col].value_counts(normalize=True).sort_index()
        line = "  ".join(f"{k}:{ed.get(k, 0):.0%}/{bd.get(k, 0):.0%}" for k in range(6))
        print(f"  {name:28s} (entries/baseline)  {line}   mean {E[col].mean():.2f} vs {B[col].mean():.2f}")

    print(f"\n===== 3. NEWS-FORMED ZONES: share whose nearest zone formed within {AFTER_MIN} min AFTER an event =====")
    print(f"{'tf':>4} | " + " | ".join(f"{w:^15}" for w in WIDTH_TK))
    print(f"{'':>4} | " + " | ".join(f"{'entr':>6} {'base':>6}  " for _ in WIDTH_TK))
    for tf in TFS:
        cells = []
        for w in WIDTH_TK:
            cells.append(f"{E[f'tf{tf}_formed_after_{w}'].mean():>6.0%} {B[f'tf{tf}_formed_after_{w}'].mean():>6.0%}  ")
        print(f"{tf:>3}m | " + " | ".join(cells))
    print("\nREAD: description. A factor earns a place in the taken-vs-skipped probes only "
          "where the entry and baseline columns differ meaningfully on the same row.")


def selftest():
    print("=== SELF-TEST ===")
    comp = np.array([pd.Timestamp("2025-10-06 14:00", tz="UTC").value + 60_000_000_000], dtype=np.int64)
    m = mins_since_completion(comp, pd.Timestamp("2025-10-06 14:06", tz="UTC"))
    assert m == 5.0, m; print("  minutes since completion = 5 OK")
    assert np.isnan(mins_since_completion(comp, pd.Timestamp("2025-10-06 13:00", tz="UTC")))
    print("  before any completion -> NaN OK")
    ev = np.array([pd.Timestamp("2025-10-06 12:30", tz="UTC").value], dtype=np.int64)
    f = pd.Timestamp("2025-10-06 12:50", tz="UTC").value
    near, aft = formed_after_news(float(f), ev)
    assert near == 20 and aft, (near, aft); print("  zone formed 20 min after event -> flagged OK")
    f2 = pd.Timestamp("2025-10-06 12:10", tz="UTC").value
    near2, aft2 = formed_after_news(float(f2), ev)
    assert near2 == 20 and not aft2; print("  zone formed BEFORE event -> not flagged OK")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
