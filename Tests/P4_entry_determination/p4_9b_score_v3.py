#!/usr/bin/env python3
"""
p4_9b_score_v3.py — P4.9b: entry score v3 (repair of v2's two weak conditions).
================================================================================
v2 (p4_9_refine.py) implemented the user's corrections literally and LOST ground:
  * body/tape vs 20-bar ATR: the 20-minute average rises right after news, so the
    conditions turn FALSE exactly at the post-event moments he trades (taken 37%
    vs skipped 40% - slightly backwards).
  * zone on ANY of 3m/5m: true for 81% of all signals - distinguishes little.
v3 keeps the user's intent (small timeframes; no arbitrary pooled numbers) with:
  C2 zone agreement on BOTH the 3m and 5m charts (same direction)
  C3 signal body >= the PRIOR SESSION's median WRB body (is this WRB big by
     yesterday's standard? - trailing, self-calibrating, no picked number,
     computable live, adapts across quiet and wild months)
  C4 last-5-min ground covered >= the prior session's median 5-minute ground
     (is the tape fast by yesterday's standard?)
C1/C5/C6 unchanged. Readout as before. Constructive - reserved years decide.

RUN: python3 Tests/P4_entry_determination/p4_9b_score_v3.py            (repo root)
     python3 Tests/P4_entry_determination/p4_9b_score_v3.py --selftest
OUT: p4_9b_score_v3.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS   # noqa: E402
from p4_2b_zone_mtf import zone_tables                # noqa: E402
from p4_9_refine import readout                       # noqa: E402

TICK = 0.25
V3_COLS = ["c1_kme_born15", "c2_both_small_tf", "c3_body_vs_prev",
           "c4_tape_vs_prev", "c5_flow_with", "c6_template"]


def overlap_one(sig_m, ztf, tf, comp_ns):
    """Signal's zone overlaps a same-direction zone on ONE timeframe's chart
    (correct completion offset for that timeframe; 2-day lookback)."""
    out = np.zeros(len(sig_m), bool)
    has = sig_m.has_whg.fillna(False).to_numpy()
    b_arr, t_arr = sig_m.whg_bottom.to_numpy(), sig_m.whg_top.to_numpy()
    d_arr = sig_m.direction.to_numpy()
    zts = pd.DatetimeIndex(ztf.ts_event).as_unit("ns").asi8
    zb, ztp, zd = ztf.whg_bottom.to_numpy(), ztf.whg_top.to_numpy(), ztf.direction.to_numpy()
    for i, cns in enumerate(comp_ns):
        if not has[i]:
            continue
        m = (zts + tf * 60e9 <= cns) & (zts >= cns - 2 * 86400e9)
        ov = m & ~((ztp < b_arr[i]) | (zb > t_arr[i])) & (zd == d_arr[i])
        out[i] = bool(ov.any())
    return out


def prev_session_ref(bars_m, wrb_m):
    """Per session_date: (median WRB body ticks, median 5-bar ground covered) of the
    PREVIOUS session. Returns dict session_date(str) -> (ref_body, ref_path)."""
    b = bars_m.copy()
    b["tr5"] = (b.high - b.low).rolling(5).sum() / TICK
    path_med = b.groupby(b.session_date.astype(str))["tr5"].median()
    w = wrb_m.copy()
    w["body_tk"] = (np.abs(w.close - w.open)) / TICK
    body_med = w.groupby(w.session_date.astype(str))["body_tk"].median()
    sessions = sorted(set(path_med.index))
    out = {}
    for i, sd in enumerate(sessions):
        if i == 0:
            continue
        prev = sessions[i - 1]
        out[sd] = (float(body_med.get(prev, np.nan)), float(path_med.get(prev, np.nan)))
    return out


def run(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_9_score_v2.csv"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    parts = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        wrb_m = wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m")]
        if "session_date" not in wrb_m.columns:
            bsd = bars_m.set_index("ts_event")["session_date"]
            wrb_m = wrb_m.assign(session_date=wrb_m.ts_event.map(bsd))
        ref = prev_session_ref(bars_m, wrb_m)
        zt = zone_tables(bars_m, month)
        sm = df[df.month == month].reset_index(drop=True)
        comp_ns = sm.comp_ns.to_numpy(np.int64)
        # session of each signal = session of its bar
        bsd = bars_m.set_index(pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8)["session_date"].astype(str)
        sd = pd.Series(comp_ns - 60_000_000_000).map(bsd)
        rb = sd.map(lambda s: ref.get(s, (np.nan, np.nan))[0]).to_numpy()
        rp = sd.map(lambda s: ref.get(s, (np.nan, np.nan))[1]).to_numpy()
        sm["ref_body_tk"], sm["ref_path_tk"] = rb, rp
        z3 = zt[3][zt[3].has_whg.fillna(False)]
        z5 = zt[5][zt[5].has_whg.fillna(False)]
        sm["c2_both_small_tf"] = (overlap_one(sm, z3, 3, comp_ns) &
                                  overlap_one(sm, z5, 5, comp_ns))
        parts.append(sm)
    df = pd.concat(parts, ignore_index=True)
    df["c3_body_vs_prev"] = df.body_tk >= df.ref_body_tk
    df["c4_tape_vs_prev"] = df.en08_path_5m_tk >= df.ref_path_tk
    df["score_v3"] = df[V3_COLS].sum(axis=1)
    df.to_csv(os.path.join(HERE, "p4_9b_score_v3.csv"), index=False)
    print(f"signals={len(df)} taken={int(df.taken.sum())} base={df.taken.mean():.1%}")
    print("condition frequency (share of signals where true):")
    for c in V3_COLS:
        T, K = df[df.taken], df[~df.taken]
        print(f"  {c:18s} all {df[c].mean():5.1%} | taken {T[c].mean():5.1%} | skipped {K[c].mean():5.1%}")
    readout(df, "score_v3", V3_COLS, "SCORE v3 (both-small-TF zones, prior-session references)")
    print("\nREAD: compare v1 (p4_8) / v2 (p4_9) / v3 per month before freezing one for")
    print("validation. Constructed on discovery months - reserved years are the test.")


def selftest():
    print("=== SELF-TEST ===")
    ts = pd.date_range("2025-10-06 13:00", periods=6, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, high=[10.0] * 6, low=[9.0] * 6,
                             close=[9.5] * 6, open=[9.4] * 6,
                             session_date=["d1", "d1", "d1", "d2", "d2", "d2"]))
    wrb = pd.DataFrame(dict(ts_event=ts[:2], open=[9.0, 9.0], close=[10.0, 9.5],
                            session_date=["d1", "d1"]))
    ref = prev_session_ref(bars, wrb)
    assert "d2" in ref and "d1" not in ref
    rb, rp = ref["d2"]
    assert abs(rb - 3.0) < 1e-9, rb        # median WRB body d1 = median(4,2)=3 tk
    print("  prior-session reference OK (d2 reads d1, body median 3 tk)")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
