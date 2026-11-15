#!/usr/bin/env python3
"""
p4_10_direction.py — P4.10: what was price doing before his entries that pointed
the way he traded? (user, 2026-11-15)
==================================================================================
The entry score finds WHEN/WHERE he engages but not WHICH WAY (reaction-WRB
agreement was only 57%). This survey measures, for all 313 taken trades, how
often his chosen side agrees with each trailing, lookahead-free cue:
  momentum:  net price move over the last 5 / 15 / 30 / 60 minutes
             (agree = he traded WITH the move; < 50% means he FADES it)
  last bar:  direction of the last completed 1-minute bar
  flow:      aggressor buy-sell balance over the last 5 minutes (from p4_7 data)
  vwap20:    price above/below the 20-bar rolling volume-weighted average price
  svwap:     price above/below the session-anchored VWAP (standard day-trading ref)
  react dir: the post-event reaction WRB's direction (known ~57%)
  react pos: price above/below the reaction WRB's body at entry, read both ways
All descriptive on taken trades (per the standing frame); the useful cue becomes
a side-selection rule candidate and gets its real test on the reserved years.
Rough 95% noise band at n=313: +/-5.5 points around 50%.

RUN: python3 Tests/P4_entry_determination/p4_10_direction.py            (repo root)
     python3 Tests/P4_entry_determination/p4_10_direction.py --selftest
OUT: p4_10_direction.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS       # noqa: E402
from p4_3_confluence_news import news_sets                # noqa: E402
from p4_5a_taken_anatomy import first_reaction_wrb        # noqa: E402
from p4_7_trailing_flow import load_flow, flow_level      # noqa: E402

TICK = 0.25


def session_vwap(bars_m):
    """Session-anchored VWAP per bar (cumulative within session_date)."""
    sd = bars_m.session_date.astype(str)
    pv_cum = (bars_m.close * bars_m.volume).groupby(sd).cumsum()
    v_cum = bars_m.volume.groupby(sd).cumsum().replace(0, np.nan)
    return (pv_cum / v_cum).to_numpy()


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
        bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
        cl = bars_m.close.to_numpy()
        sv = session_vwap(bars_m)
        vw20 = ((bars_m.close * bars_m.volume).rolling(20).sum() /
                bars_m.volume.rolling(20).sum().replace(0, np.nan)).to_numpy()
        sec, bv, svv, mz = load_flow(repo, month)
        w1m = (wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m")]
               .assign(body_bottom=lambda d: np.minimum(d.open, d.close),
                       body_top=lambda d: np.maximum(d.open, d.close))
               [["ts_event", "direction", "body_bottom", "body_top"]].sort_values("ts_event"))
        for _, t in e.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            P = float(np.asarray(t.entry_prices).ravel()[0])
            is_long = t.side == "long"
            ib = int(np.searchsorted(bts, en - 60_000_000_000, side="right")) - 1
            if ib < 60:
                continue
            r = dict(month=month, side=t.side)
            for k in (5, 15, 30, 60):
                mv = cl[ib] - cl[ib - k]
                r[f"mom_{k}"] = np.nan if mv == 0 else ((mv > 0) == is_long)
            lb = cl[ib] - cl[ib - 1]
            r["last_bar"] = np.nan if lb == 0 else ((lb > 0) == is_long)
            fl = flow_level(sec, bv, svv, mz, en, 300, is_long)
            r["flow_5m"] = np.nan if not np.isfinite(fl) or fl == 0 else (fl > 0)
            r["vwap20"] = np.nan if not np.isfinite(vw20[ib]) or P == vw20[ib] else ((P > vw20[ib]) == is_long)
            r["svwap"] = np.nan if not np.isfinite(sv[ib]) or P == sv[ib] else ((P > sv[ib]) == is_long)
            i_ev = int(np.searchsorted(ev_all, en, side="right")) - 1
            w1 = first_reaction_wrb(w1m, 1, ev_all[i_ev], en) if i_ev >= 0 else None
            if w1 is not None:
                r["react_dir"] = (w1["direction"] == "bullish") == is_long
                if P > w1["top"]:
                    r["react_pos"] = "above"
                elif P < w1["bottom"]:
                    r["react_pos"] = "below"
                else:
                    r["react_pos"] = "inside"
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(HERE, "p4_10_direction.csv"), index=False)

    cues = [("mom_5", "with the last 5-min move"), ("mom_15", "with the last 15-min move"),
            ("mom_30", "with the last 30-min move"), ("mom_60", "with the last 60-min move"),
            ("last_bar", "with the last bar"), ("flow_5m", "with 5-min buy/sell pressure"),
            ("vwap20", "on his side of the 20-bar VWAP"), ("svwap", "on his side of session VWAP"),
            ("react_dir", "with the reaction WRB's direction")]
    print(f"entries measured: {len(df)} (of 313; early-session entries without 60 min of bars dropped)")
    print(f"\n{'cue':38s} {'agree':>7} {'n':>5}   per month")
    for col, name in cues:
        v = df[col].dropna().astype(bool)
        bym = "  ".join(f"{m}:{df[df.month==m][col].dropna().astype(bool).mean():.0%}"
                        for m in df.month.unique())
        print(f"{name:38s} {v.mean():>6.1%} {len(v):>5}   {bym}")
    print("\nposition vs the reaction WRB body at entry, split by his side:")
    sub = df.dropna(subset=["react_pos"])
    for side in ("long", "short"):
        d = sub[sub.side == side]
        print(f"  {side:5s} (n={len(d)}): " +
              "  ".join(f"{k}:{v:.0%}" for k, v in
                        d.react_pos.value_counts(normalize=True).round(2).items()))
    print("\nREAD: >50% = he trades WITH the cue; <50% = he trades AGAINST it. Noise band")
    print("at these n is roughly +/-6 points, so only cues well clear of 50% in BOTH")
    print("months deserve a forward test.")


def selftest():
    print("=== SELF-TEST ===")
    b = pd.DataFrame(dict(close=[10.0, 20.0], volume=[1, 1], session_date=["d", "d"]))
    v = session_vwap(b)
    assert abs(v[0] - 10) < 1e-9 and abs(v[1] - 15) < 1e-9
    b2 = pd.DataFrame(dict(close=[10.0, 20.0], volume=[1, 1], session_date=["d1", "d2"]))
    v2 = session_vwap(b2)
    assert abs(v2[1] - 20) < 1e-9          # resets at the session boundary
    print("  session VWAP cumulative + reset OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
