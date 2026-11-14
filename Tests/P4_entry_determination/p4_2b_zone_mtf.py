#!/usr/bin/env python3
"""
p4_2b_zone_mtf.py — P4.2b: zones across his actual timeframe stack (1/3/5/10/15 min),
entries vs a random-moment baseline. DESCRIPTION ONLY.
=====================================================================================
WHY: user (2026-11-14): the trader alternates between 1, 3, 5, 10 and 15-minute charts
for zones. Two timeframes was too narrow. Also, "inside some zone" was near-universal
at 1m, so this script adds the missing yardstick: the SAME measurement at random
flat moments inside his desk window. Entries only mean something relative to that.

WHAT:
  - Builds zone (WHG) tables for 3m/10m/15m by resampling the committed 1m bars
    (session-safe: bars never span a session date; same identification rules as the
    1m/5m builder, which follow WRB_Definition.txt: body strictly > each of the prior
    3 bodies, all 4 bars in one session, zone = body-gap beyond the prior 3 bodies'
    extreme, zone exists only if the close clears that extreme).
  - For each of the 313 discovery-month entries AND for 2,000 seeded random minutes
    per month (inside the 60-min desk window, not during one of his trades): nearest
    zone per timeframe (any fill state, 2-day lookback) -> position / fill state / age.
  - CONVENTION (recorded in P4_DESIGN): fill state for every zone timeframe is judged
    on completed 1-minute bars (the strictest reading of "a bar's range covers the
    whole zone"). All measures are backward-looking only -> usable in a live signal.

OUT: printed comparison table + p4_2b_zone_mtf.csv (per-row detail for both groups).
RUN: python3 Tests/P4_entry_determination/p4_2b_zone_mtf.py            (repo root)
     python3 Tests/P4_entry_determination/p4_2b_zone_mtf.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import nearest_live_zone, month_bounds, MONTHS, WHG_DIR  # noqa: E402

TFS = [1, 3, 5, 10, 15]          # minutes — his actual chart stack (user statement)
N_BASE = 2000
SEED = 0
PAD_MIN = 60


def resample(bars_1m: pd.DataFrame, tf_min: int) -> pd.DataFrame:
    """1m -> tf bars, start-stamped, never spanning a session date."""
    b = bars_1m.sort_values("ts_event").copy()
    b["bin"] = b.ts_event.dt.floor(f"{tf_min}min")
    g = b.groupby(["session_date", "bin"], sort=True)
    out = g.agg(open=("open", "first"), high=("high", "max"),
                low=("low", "min"), close=("close", "last")).reset_index()
    return out.rename(columns={"bin": "ts_event"}).sort_values("ts_event").reset_index(drop=True)


def identify_whg(df: pd.DataFrame) -> pd.DataFrame:
    """Same rules as build_whg_series.py / WRB_Definition.txt."""
    o = df.open.to_numpy(); c = df.close.to_numpy()
    sd = df.session_date.astype(str).to_numpy()
    body = np.abs(c - o); n = len(df)
    rows = []
    for i in range(3, n):
        if not (sd[i] == sd[i - 1] == sd[i - 2] == sd[i - 3]) or body[i] <= 0:
            continue
        if not (body[i] > body[i - 1] and body[i] > body[i - 2] and body[i] > body[i - 3]):
            continue
        if c[i] > o[i]:
            pbh = max(o[i - 1], c[i - 1], o[i - 2], c[i - 2], o[i - 3], c[i - 3])
            if c[i] > pbh:
                rows.append((df.ts_event.iloc[i], "bullish", pbh, c[i]))
        else:
            pbl = min(o[i - 1], c[i - 1], o[i - 2], c[i - 2], o[i - 3], c[i - 3])
            if c[i] < pbl:
                rows.append((df.ts_event.iloc[i], "bearish", c[i], pbl))
    w = pd.DataFrame(rows, columns=["ts_event", "direction", "whg_bottom", "whg_top"])
    w["has_whg"] = True
    return w


def zone_tables(bars_m: pd.DataFrame, month: str) -> dict:
    """{tf_min: whg table}; 1m and 5m come from the committed builders' tables."""
    out = {}
    for tf in TFS:
        if tf in (1, 5):
            t = pd.read_parquet(os.path.join(WHG_DIR, f"whg_{tf}m_{month}.parquet"))
        else:
            t = identify_whg(resample(bars_m, tf))
        out[tf] = t.sort_values("ts_event")
    return out


def sample_baseline(ep_m: pd.DataFrame, rng) -> list:
    """Random minutes inside [first entry - PAD, last exit] per day, not during a trade."""
    days = ep_m.assign(day=ep_m.first_entry_utc.dt.date).groupby("day").agg(
        t0=("first_entry_utc", "min"), t1=("last_exit_utc", "max"))
    days["t0"] = days.t0 - pd.Timedelta(minutes=PAD_MIN)
    spans = [(r.t0.value // 60_000_000_000, r.t1.value // 60_000_000_000) for r in days.itertuples()]
    weights = np.array([b - a for a, b in spans], float)
    iv = list(zip(ep_m.first_entry_utc.to_numpy(), ep_m.last_exit_utc.to_numpy()))
    picks = []
    while len(picks) < N_BASE:
        k = rng.choice(len(spans), p=weights / weights.sum())
        m = int(rng.integers(spans[k][0], spans[k][1] + 1))
        t = pd.Timestamp(m * 60_000_000_000, tz="UTC")
        if any((t >= s) and (t <= e) for s, e in iv):
            continue
        picks.append(t)
    return picks


def measure(points, zt, bars_m, close_at):
    rows = []
    for T, P in points:
        r = {"t": T, "price": P}
        for tf in TFS:
            z = nearest_live_zone(zt[tf], bars_m, T, P, "long", pd.Series([], dtype="datetime64[ns, UTC]"),
                                  bar_sec=tf * 60)
            r[f"tf{tf}_status"] = z["zone_status"]; r[f"tf{tf}_fill"] = z["zone_fill"]
            r[f"tf{tf}_age"] = z["zone_age_min"]
        rows.append(r)
    return pd.DataFrame(rows)


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    rng = np.random.default_rng(SEED)
    ent_all, base_all = [], []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        zt = zone_tables(bars_m, month)
        print(f"[{month}] zones per tf: " + "  ".join(f"{tf}m={len(zt[tf])}" for tf in TFS))
        close_at = bars_m.set_index("ts_event")["close"]
        ents = [(t.first_entry_utc, float(np.asarray(t.entry_prices).ravel()[0])) for _, t in e.iterrows()]
        E = measure(ents, zt, bars_m, close_at); E["group"] = "entry"; E["month"] = month
        bts = sample_baseline(e, rng)
        bps = close_at.reindex(pd.DatetimeIndex(bts).floor("min"), method="ffill").to_numpy()
        B = measure(list(zip(bts, bps)), zt, bars_m, close_at); B["group"] = "baseline"; B["month"] = month
        ent_all.append(E); base_all.append(B)
    df = pd.concat(ent_all + base_all, ignore_index=True)
    df.to_csv(os.path.join(HERE, "p4_2b_zone_mtf.csv"), index=False)

    print("\n===== ENTRIES vs RANDOM FLAT MOMENTS (both months pooled) =====")
    print(f"{'tf':>4} | {'--- inside-or-near % ---':^25} | {'--- fill state at zone (inside/near) ---':^52} | {'age med (min)':^16}")
    print(f"{'':>4} | {'entries':>10} {'baseline':>10}    | {'entries unf/part/fill':>25} {'baseline unf/part/fill':>25} | {'entr':>7} {'base':>7}")
    for tf in TFS:
        e = df[df.group == "entry"]; b = df[df.group == "baseline"]
        def stats(d):
            at = d[d[f"tf{tf}_status"].isin(["inside", "near"])]
            share = len(at) / len(d) if len(d) else np.nan
            f = at[f"tf{tf}_fill"].value_counts(normalize=True)
            trip = "/".join(f"{f.get(k, 0):.0%}" for k in ("unfilled", "partial", "filled"))
            return share, trip, d[f"tf{tf}_age"].median()
        es_, et, ea = stats(e); bs_, bt, ba = stats(b)
        print(f"{tf:>3}m | {es_:>9.0%} {bs_:>9.0%}    | {et:>25} {bt:>25} | {ea:>7.0f} {ba:>7.0f}")
    print("\nREAD: description. The signal-relevant quantity is the GAP between the entry")
    print("column and the baseline column on the same row - zone presence or fill state is")
    print("only worth building into a strategy signal where those columns differ.")


def selftest():
    print("=== SELF-TEST ===")
    ts = pd.date_range("2025-10-06 13:00", periods=60, freq="1min", tz="UTC")
    b = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                          close=5000.0, session_date=[d.date() for d in ts]))
    # four 15m bins: three flat (doji priors are legal) then a 10-pt body in the last
    b.loc[b.index[59], "close"] = 5010.0
    b.loc[b.index[59], "high"] = 5010.0
    r15 = resample(b, 15)
    assert len(r15) == 4 and abs(r15.iloc[3].close - 5010.0) < 1e-9
    w = identify_whg(r15)
    assert len(w) == 1 and w.iloc[0].direction == "bullish", w
    print(f"  15m resample + WRB zone found: [{w.iloc[0].whg_bottom}, {w.iloc[0].whg_top}] OK")
    r3 = resample(b, 3)
    assert len(r3) == 20
    print("  3m resample bar count OK")
    # session boundary never crossed
    two = b.copy()
    two.loc[two.index[:30], "session_date"] = pd.Timestamp("2025-10-05").date()
    rr = resample(two, 15)
    assert rr.groupby("session_date").size().tolist() == [2, 2], rr
    print("  session seam splits bins OK")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
