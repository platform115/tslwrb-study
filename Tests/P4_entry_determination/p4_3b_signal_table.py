#!/usr/bin/env python3
"""
p4_3b_signal_table.py — P4.3: the taken-vs-skipped signal table (definitions locked).
======================================================================================
LOCKED DEFINITIONS (P4_DESIGN.md, user-approved 2026-11-14):
  SIGNAL  = a 1m WRB completing (bar start + 60s) during the desk window (60 min
            before the day's first entry -> last exit) while he is FLAT.
  TAKEN   = one of his entries, with side matching the WRB's direction, occurs within
            5 minutes after completion (15-minute flag kept as cross-check).
  Entries matching no signal are counted and reported, never silently dropped.

FEATURES per signal (all computable live - backward-looking only):
  body_tk            WRB body in ticks
  kme_born_{W}_{w}   completed 0..W min after a scheduled event (W in 5/15/30;
                     w = all events / >=20-tick movers). "Same bar" counts.
  mins_since_all / mins_since_ge20   minutes from last event to completion
  n_htf_overlap      of his higher timeframes (3/5/10/15m): how many have a zone,
                     formed in the prior 2 days before the signal, whose price range
                     overlaps this signal's own zone (fill state NOT checked - recorded
                     convention; ambience lesson applies, the comparison decides)
  n_htf_overlap_dir  same, zone direction matching the signal's
  at_kme_level       signal price inside/near (<=8tk) an OLDER (>=30 min) KME-born
                     zone (>=20tk events, W=30, any timeframe) - the trader's
                     "those levels stay interesting" claim, directly
  tod_ct             hour of day (Chicago time)

OUT: p4_3b_signal_table.csv (every signal, both months) + descriptive readout.
RUN: python3 Tests/P4_entry_determination/p4_3b_signal_table.py            (repo root)
     python3 Tests/P4_entry_determination/p4_3b_signal_table.py --selftest
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS  # noqa: E402
from p4_2b_zone_mtf import zone_tables  # noqa: E402
from p4_3_confluence_news import news_sets  # noqa: E402

TICK = 0.25
PAD_MIN = 60
MATCH_MIN = 5
MATCH_MIN_ALT = 15
BORN_W = [5, 15, 30]
NEAR_TK = 8
HTF = [3, 5, 10, 15]
LEVEL_MIN_AGE_MIN = 30


def _ns(x):
    return pd.DatetimeIndex(x).as_unit("ns").asi8


def build_signals(wrb_m, ep_m):
    """Desk-window, flat 1m WRB signals with taken flags."""
    e = ep_m.assign(day=ep_m.first_entry_utc.dt.date)
    dw = e.groupby("day").agg(t0=("first_entry_utc", "min"), t1=("last_exit_utc", "max"))
    dw["t0"] = dw.t0 - pd.Timedelta(minutes=PAD_MIN)
    s = wrb_m.copy()
    s["comp"] = s.ts_event + pd.Timedelta(seconds=60)
    day = s.comp.dt.date
    t0 = day.map(dw.t0); t1 = day.map(dw.t1)
    s = s[t0.notna() & (s.comp >= t0) & (s.comp <= t1)]
    iv = list(zip(_ns(ep_m.first_entry_utc), _ns(ep_m.last_exit_utc)))
    cn = _ns(s.comp)
    flat = np.ones(len(s), bool)
    for a, b in iv:
        flat &= ~((cn >= a) & (cn <= b))
    s = s[flat].copy()
    # taken flags: same-side entry within MATCH after completion
    for lab, mins in [("taken", MATCH_MIN), ("taken15", MATCH_MIN_ALT)]:
        fl = np.zeros(len(s), bool)
        cn2 = _ns(s.comp); dirs = s.direction.to_numpy()
        for _, t in ep_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            want = "bullish" if t.side == "long" else "bearish"
            fl |= (dirs == want) & (cn2 < en) & (en - cn2 <= mins * 60e9)
        s[lab] = fl
    # entry-side match rate (entries explained by a signal)
    matched_entries = 0
    for _, t in ep_m.iterrows():
        en = pd.Timestamp(t.first_entry_utc).value
        want = "bullish" if t.side == "long" else "bearish"
        if (((_ns(wrb_m.ts_event) + int(60e9)) < en) &
                ((en - (_ns(wrb_m.ts_event) + int(60e9))) <= MATCH_MIN * 60e9) &
                (wrb_m.direction.to_numpy() == want)).any():
            matched_entries += 1
    return s, matched_entries


def add_features(s, ev, zt, kme_level_zones):
    comp_ns = _ns(s.comp)
    s["body_tk"] = s.body_size / TICK
    for wname, arr in ev.items():
        key = "all" if wname == "all" else "ge20"
        if wname == ">=45tk":
            continue
        idx = np.searchsorted(arr, comp_ns, side="right") - 1
        mins = np.where(idx >= 0, (comp_ns - arr[np.clip(idx, 0, None)]) / 60e9, np.nan)
        s[f"mins_since_{key}"] = mins
        for W in BORN_W:
            s[f"kme_born_{W}_{key}"] = (mins >= 0) & (mins <= W)
    # signal-level higher-timeframe zone overlap
    n_ov = np.zeros(len(s), int); n_ovd = np.zeros(len(s), int)
    has = s.has_whg.fillna(False).to_numpy()
    b_arr = s.whg_bottom.to_numpy(); t_arr = s.whg_top.to_numpy()
    dir_arr = s.direction.to_numpy()
    zcache = {tf: (_ns(zt[tf].ts_event), zt[tf].whg_bottom.to_numpy(),
                   zt[tf].whg_top.to_numpy(), zt[tf].direction.to_numpy()) for tf in HTF}
    for i, cns in enumerate(comp_ns):
        if not has[i]:
            continue
        for tf in HTF:
            zts, zb, ztp, zd = zcache[tf]
            m = (zts + tf * 60e9 <= cns) & (zts >= cns - 2 * 86400e9)
            if not m.any():
                continue
            ov = m & ~((ztp < b_arr[i]) | (zb > t_arr[i]))
            if ov.any():
                n_ov[i] += 1
                if (ov & (zd == dir_arr[i])).any():
                    n_ovd[i] += 1
    s["n_htf_overlap"] = n_ov; s["n_htf_overlap_dir"] = n_ovd
    # at an OLDER KME-born level (>=20tk, W=30, any tf)
    kz_ts, kz_b, kz_t = kme_level_zones
    at = np.zeros(len(s), bool)
    px = s.close.to_numpy()
    for i, cns in enumerate(comp_ns):
        m = (kz_ts <= cns - LEVEL_MIN_AGE_MIN * 60e9) & (kz_ts >= cns - 2 * 86400e9)
        if not m.any():
            continue
        d = np.where(px[i] < kz_b[m], kz_b[m] - px[i],
                     np.where(px[i] > kz_t[m], px[i] - kz_t[m], 0.0)) / TICK
        at[i] = bool((d <= NEAR_TK).any())
    s["at_kme_level"] = at
    s["tod_ct"] = s.comp.dt.tz_convert("America/Chicago").dt.hour
    return s


def kme_born_zone_list(zt, ev_ge20):
    """All KME-born zones (W=30, >=20tk) across every timeframe -> (ts_ns, bottom, top)."""
    ts, bo, tp = [], [], []
    for tf, t in zt.items():
        z = t[t.has_whg.fillna(False)]
        zc = _ns(z.ts_event) + tf * int(60e9)
        idx = np.searchsorted(ev_ge20, zc, side="right") - 1
        mins = np.where(idx >= 0, (zc - ev_ge20[np.clip(idx, 0, None)]) / 60e9, np.nan)
        m = (mins >= 0) & (mins <= 30)
        ts.append(_ns(z.ts_event)[m]); bo.append(z.whg_bottom.to_numpy()[m]); tp.append(z.whg_top.to_numpy()[m])
    return np.concatenate(ts), np.concatenate(bo), np.concatenate(tp)


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev = news_sets(repo)
    frames = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        wrb_m = wrb[(wrb.symbol == sym) & (wrb.timeframe == "1m")].sort_values("ts_event")
        wrb_m = wrb_m[(wrb_m.ts_event >= lo) & (wrb_m.ts_event < hi)]
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        zt = zone_tables(bars_m, month)
        s, me = build_signals(wrb_m, e)
        s = add_features(s, ev, zt, kme_born_zone_list(zt, ev[">=20tk"]))
        s["month"] = month
        print(f"[{month}] signals={len(s)} taken={int(s.taken.sum())} taken15={int(s.taken15.sum())} "
              f"| entries matched by a signal: {me}/{len(e)} ({me/len(e):.0%})")
        frames.append(s)
    df = pd.concat(frames, ignore_index=True)
    keep = [c for c in df.columns if c not in ("prior_body_max", "is_roll_day", "session",
                                               "volume", "open", "high", "low", "session_date",
                                               "whg_size", "whg_fill_status", "timeframe", "symbol")]
    df[keep].to_csv(os.path.join(HERE, "p4_3b_signal_table.csv"), index=False)

    T = df[df.taken]; K = df[~df.taken]
    print(f"\n===== TAKEN (n={len(T)}) vs SKIPPED (n={len(K)}) — both months =====")
    print(f"{'feature':34s} {'taken':>10} {'skipped':>10}")
    def line(name, tv, kv, pct=False):
        f = (lambda v: f"{v:.0%}") if pct else (lambda v: f"{v:.2f}")
        print(f"{name:34s} {f(tv):>10} {f(kv):>10}")
    line("WRB body (ticks, median)", T.body_tk.median(), K.body_tk.median())
    line("has own zone", T.has_whg.mean(), K.has_whg.mean(), pct=True)
    for key in ("all", "ge20"):
        for W in BORN_W:
            line(f"KME-born <= {W} min ({key})", T[f"kme_born_{W}_{key}"].mean(),
                 K[f"kme_born_{W}_{key}"].mean(), pct=True)
    line("mins since event (ge20, median)", T.mins_since_ge20.median(), K.mins_since_ge20.median())
    line("higher-TF zone overlap (mean 0-4)", T.n_htf_overlap.mean(), K.n_htf_overlap.mean())
    line("  same-direction overlap (mean)", T.n_htf_overlap_dir.mean(), K.n_htf_overlap_dir.mean())
    line("at older KME-born level", T.at_kme_level.mean(), K.at_kme_level.mean(), pct=True)
    print("\nby month (taken vs skipped, KME-born <=30 ge20 / at_kme_level):")
    for m in df.month.unique():
        d = df[df.month == m]; t_, k_ = d[d.taken], d[~d.taken]
        print(f"  {m}: born30 {t_.kme_born_30_ge20.mean():.0%} vs {k_.kme_born_30_ge20.mean():.0%}"
              f" | at_level {t_.at_kme_level.mean():.0%} vs {k_.at_kme_level.mean():.0%}")
    print("\nREAD: descriptive splits. Formal tests (AUC + confidence intervals, registry rows)")
    print("run next, only on features showing daylight here. taken15 column kept as cross-check.")


def selftest():
    print("=== SELF-TEST ===")
    lo = pd.Timestamp("2025-10-06 14:00", tz="UTC")
    wrb_m = pd.DataFrame(dict(
        ts_event=[lo, lo + pd.Timedelta(minutes=10), lo + pd.Timedelta(minutes=20)],
        direction=["bullish", "bullish", "bearish"], body_size=[2.0, 1.0, 1.0],
        has_whg=[True, False, False], whg_bottom=[5000.0, np.nan, np.nan],
        whg_top=[5002.0, np.nan, np.nan], close=[5002.0, 5001.0, 5000.0]))
    ep_m = pd.DataFrame(dict(
        first_entry_utc=[lo + pd.Timedelta(minutes=4), lo + pd.Timedelta(minutes=30)],
        last_exit_utc=[lo + pd.Timedelta(minutes=8), lo + pd.Timedelta(minutes=35)],
        side=["long", "long"]))
    s, me = build_signals(wrb_m, ep_m)
    # desk window 13:04 -> 14:35. Signal 1 completes 14:01 flat, long entry 14:04 within 5 min -> taken.
    # Signals completing 14:11 / 14:21 fall between trades (flat) but match no entry within 5 min.
    assert len(s) == 3 and s.taken.tolist() == [True, False, False], s[["comp", "taken"]]
    assert me == 1   # second entry (14:30) has no same-direction completion within 5 min before it
    print("  signal building + taken matching OK")
    ev = {"all": np.array([(lo - pd.Timedelta(minutes=3)).value]),
          ">=20tk": np.array([(lo - pd.Timedelta(minutes=3)).value]),
          ">=45tk": np.array([], dtype=np.int64)}
    zt = {tf: pd.DataFrame(dict(ts_event=pd.DatetimeIndex([lo - pd.Timedelta(hours=1)]),
                                has_whg=[True], whg_bottom=[5001.0], whg_top=[5003.0],
                                direction=["bullish"])) for tf in HTF}
    kz = kme_born_zone_list(zt, ev[">=20tk"])
    s2 = add_features(s, ev, zt, kz)
    r = s2.iloc[0]
    assert r.kme_born_5_all and r.kme_born_5_ge20          # completed 4 min after event
    assert r.n_htf_overlap == 4 and r.n_htf_overlap_dir == 4   # [5000,5002] overlaps [5001,5003] on all 4
    assert not r.at_kme_level                               # htf zones only 60 min old but formed 57m AFTER.. wait
    print(f"  features: born5={r.kme_born_5_ge20} overlap={r.n_htf_overlap} at_level={r.at_kme_level} OK")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
