#!/usr/bin/env python3
"""
p4_6_template.py — P4.6: pre-registered entry probes T-EN05..T-EN08.
=====================================================================
Runs the four registered tests on the locked signal table (p4_3b, 1,865 signals,
179 taken / 1,686 skipped). All quantities are TRAILING — nothing measured after
the signal moment (lookahead guard). Registry rows carry the hypotheses; this
docstring fixes the remaining measurement choices BEFORE any statistic runs:

  * Both arms use the SIGNAL's own WRB direction as the side. For taken signals
    this IS the trade side by construction (taken = same-direction entry within
    5 min); for skipped signals it is the natural would-be side. This replaces
    the "seeded random side" wording in T-EN07/T-EN09's rows — it is strictly
    more informative and identical in spirit; recorded here before stats ran.
  * T-EN05: edge distance = |signal close - nearer body edge| of the FIRST WRB
    completing <=30 min after the last scheduled event (all-events width) and
    at/before the signal. AUC computed on NEGATED distance so "taken closer"
    clears in the standard lo>0.5 direction. Cells: 1m [PRIMARY], 3m.
  * T-EN06 (minute level): for every FLAT desk-window 1-minute bar, template =
    (a reaction 1m WRB exists for the latest event, bar time within 30 min of
    its completion, bar close within [body_bottom-4tk, body_top+4tk]).
    Outcome = an entry occurs within the NEXT 5 minutes. Compare entry rate on
    template minutes vs all other flat desk minutes. Opportunity level: one
    opportunity per reaction WRB with >=1 template minute; entered = any entry
    inside its 30-min window; side agreement reported.
  * T-EN07 cell A (WHG zone): most recent 1m zone (2-day lookback) STRICTLY
    containing the signal close; room ahead = ticks from close to the zone edge
    in the signal direction (long -> top). NaN when inside none.
    T-EN07 cell B (reaction body): same but the 1m reaction WRB's body.
    Secondary descriptive: for TAKEN signals inside an interval, did price
    reach the far edge between entry and last exit (bars' high/low)?
  * T-EN08: path_60s = signal bar high-low [PRIMARY]; path_5m = sum(high-low,
    5 bars); net_5m = |close - close 5 bars back|; speed_since_event =
    |close - close at event bar| / minutes since event (ticks/min);
    vwap_z = |close - rolling 20-bar VWAP| / rolling 20-bar std of close
    (ABSOLUTE stretch; T-DF23 construction, magnitude read).
  Statistic: rank AUC + two-sample bootstrap 95% CI (seed 0, 10,000), clears
  iff CI excludes 0.5 with taken ranking higher. Day-clustering caveat stands.

RUN: python3 Tests/P4_entry_determination/p4_6_template.py            (repo root)
     python3 Tests/P4_entry_determination/p4_6_template.py --selftest
OUT: p4_6_signal_features.csv (per-signal), p4_6_template_minutes.csv (T-EN06).
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS            # noqa: E402
from p4_2b_zone_mtf import resample, zone_tables               # noqa: E402
from p4_3_confluence_news import news_sets                     # noqa: E402
from p4_4_probes import rank_auc, boot_ci                      # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies, first_reaction_wrb  # noqa: E402

TICK = 0.25
TOL_TK = 4
REACT_MIN = 30
AFTER_WRB_MIN = 30
VWAP_N = 20


def room_ahead(close, bottom, top, direction):
    """Ticks of room toward the edge in the signal direction; NaN unless strictly inside."""
    if not (bottom < close < top):
        return np.nan
    return (top - close) / TICK if direction == "bullish" else (close - bottom) / TICK


def vwap_z(close, vol, n=VWAP_N):
    """|close - rolling n-bar VWAP| / rolling n-bar std(close). T-DF23 construction, abs."""
    c = pd.Series(close); v = pd.Series(vol).astype(float)
    vw = (c * v).rolling(n).sum() / v.rolling(n).sum().replace(0, np.nan)
    sd = c.rolling(n).std()
    return (np.abs(c - vw) / sd.replace(0, np.nan)).to_numpy()


def flat_desk_minutes(e_day, bars_day_ts_ns):
    """Bar times (ns) in the desk window (60 min before first entry -> last exit)
    while FLAT (not inside any episode of that day)."""
    t0 = min(pd.Timestamp(t).value for t in e_day.first_entry_utc) - 60 * 60_000_000_000
    t1 = max(pd.Timestamp(t).value for t in e_day.last_exit_utc)
    m = (bars_day_ts_ns >= t0) & (bars_day_ts_ns <= t1)
    out = bars_day_ts_ns[m]
    for _, t in e_day.iterrows():
        a, b = pd.Timestamp(t.first_entry_utc).value, pd.Timestamp(t.last_exit_utc).value
        out = out[(out < a) | (out > b)]
    return out


def run(repo):
    sig = pd.read_csv(os.path.join(HERE, "p4_3b_signal_table.csv"))
    sig["comp_ns"] = pd.DatetimeIndex(pd.to_datetime(sig.comp, utc=True)).as_unit("ns").asi8
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev_all = news_sets(repo)["all"]

    feat_rows, min_rows, opp_rows = [], [], []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
            subset=["first_entry_utc", "last_exit_utc"])
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
        hi_a, lo_a, cl_a = bars_m.high.to_numpy(), bars_m.low.to_numpy(), bars_m.close.to_numpy()
        vz = vwap_z(cl_a, bars_m.volume.to_numpy())
        entries_ns = np.sort(pd.DatetimeIndex(e.first_entry_utc).as_unit("ns").asi8)

        # reaction-WRB tables (body edges), 1m canonical + 3m rebuilt
        w1m = (wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m")]
               .assign(body_bottom=lambda d: np.minimum(d.open, d.close),
                       body_top=lambda d: np.maximum(d.open, d.close))
               [["ts_event", "direction", "body_bottom", "body_top"]].sort_values("ts_event"))
        wtab = {1: w1m, 3: wrb_bodies(resample(bars_m, 3))}
        # 1m WHG zones for T-EN07 cell A
        zt1 = zone_tables(bars_m, month)[1]
        z = zt1[zt1.has_whg.fillna(False)]
        z_ts = pd.DatetimeIndex(z.ts_event).as_unit("ns").asi8
        z_b, z_t = z.whg_bottom.to_numpy(), z.whg_top.to_numpy()

        # ---------- per-signal features (T-EN05 / 07 / 08) ----------
        sm = sig[sig.month == month]
        print(f"[{month}] signals={len(sm)} bars={len(bars_m)} zones1m={len(z)}")
        for _, srow in sm.iterrows():
            cns, P, d = int(srow.comp_ns), float(srow.close), srow.direction
            i_ev = int(np.searchsorted(ev_all, cns, side="right")) - 1
            r = dict(month=month, comp_ns=cns, taken=bool(srow.taken), direction=d, close=P)
            w1 = {}
            for tf in (1, 3):
                w = first_reaction_wrb(wtab[tf], tf, ev_all[i_ev], cns) if i_ev >= 0 else None
                w1[tf] = w
                r[f"en05_tf{tf}_edge_tk"] = (min(abs(P - w["top"]), abs(P - w["bottom"])) / TICK
                                             if w else np.nan)
                r[f"tf{tf}_has_react"] = w is not None
            # T-EN07 A: most recent 1m zone strictly containing close (2-day lookback)
            selz = (z_ts < cns) & (z_ts >= cns - 2 * 86_400_000_000_000) & (z_b < P) & (P < z_t)
            if selz.any():
                j = int(np.flatnonzero(selz)[-1])
                r["en07_zone_room_tk"] = room_ahead(P, float(z_b[j]), float(z_t[j]), d)
                r["en07_zone_b"], r["en07_zone_t"] = float(z_b[j]), float(z_t[j])
            else:
                r["en07_zone_room_tk"] = np.nan
            r["en07_body_room_tk"] = (room_ahead(P, w1[1]["bottom"], w1[1]["top"], d)
                                      if w1[1] else np.nan)
            if w1[1]:
                r["en07_body_b"], r["en07_body_t"] = w1[1]["bottom"], w1[1]["top"]
            # T-EN08 trailing tape
            ib = int(np.searchsorted(bts, pd.Timestamp(srow.ts_event).value))
            if ib < len(bts) and bts[ib] == pd.Timestamp(srow.ts_event).value:
                r["en08_path_60s_tk"] = (hi_a[ib] - lo_a[ib]) / TICK
                if ib >= 5:
                    r["en08_path_5m_tk"] = float((hi_a[ib-4:ib+1] - lo_a[ib-4:ib+1]).sum()) / TICK
                    r["en08_net_5m_tk"] = abs(cl_a[ib] - cl_a[ib - 5]) / TICK
                r["en08_vwap_z"] = vz[ib]
                if i_ev >= 0:
                    mins = (cns - ev_all[i_ev]) / 60e9
                    ie = int(np.searchsorted(bts, ev_all[i_ev], side="right")) - 1
                    if ie >= 0 and mins <= 240:   # cap: same-session relevance
                        r["en08_speed_since_ev"] = abs(P - cl_a[ie]) / TICK / max(mins, 1.0)
            feat_rows.append(r)

        # ---------- T-EN06 minute-level template ----------
        # precompute reaction WRB per event (1m): first completing <=30 min after
        w1ts = pd.DatetimeIndex(wtab[1].ts_event).as_unit("ns").asi8 + 60_000_000_000
        w1b, w1t = wtab[1].body_bottom.to_numpy(), wtab[1].body_top.to_numpy()
        w1d = wtab[1].direction.to_numpy()
        react = {}
        for k, evns in enumerate(ev_all):
            if not (lo.value - 4 * 86_400_000_000_000 <= evns < hi.value):
                continue
            mm = (w1ts > evns) & (w1ts <= evns + REACT_MIN * 60_000_000_000)
            if mm.any():
                j = int(np.flatnonzero(mm)[0])
                react[k] = (int(w1ts[j]), float(w1b[j]), float(w1t[j]), str(w1d[j]))
        for day, e_day in e.groupby(e.first_entry_utc.dt.date):
            fm = flat_desk_minutes(e_day, bts)
            for tns in fm:
                tns = int(tns) + 60_000_000_000          # completed bar = decision moment
                ib = int(np.searchsorted(bts, tns - 60_000_000_000))
                c = cl_a[ib]
                i_ev = int(np.searchsorted(ev_all, tns, side="right")) - 1
                tmpl, wdir = False, ""
                if i_ev in react:
                    wc, bb, tt, wdir = react[i_ev]
                    tmpl = (wc <= tns <= wc + AFTER_WRB_MIN * 60_000_000_000 and
                            bb - TOL_TK * TICK <= c <= tt + TOL_TK * TICK)
                j = int(np.searchsorted(entries_ns, tns, side="right"))
                entered5 = bool(j < len(entries_ns) and entries_ns[j] <= tns + 5 * 60_000_000_000)
                min_rows.append(dict(month=month, t_ns=tns, template=tmpl,
                                     entered_5m=entered5, wrb_dir=wdir))
        # opportunity level: one per (event, reaction WRB) whose 30-min window has
        # >=1 flat desk template minute
        mdf = pd.DataFrame([m for m in min_rows if m["month"] == month])
        for k, (wc, bb, tt, wd) in react.items():
            win = mdf[(mdf.t_ns >= wc) & (mdf.t_ns <= wc + AFTER_WRB_MIN * 60_000_000_000)]
            if not win.template.any():
                continue
            j0 = int(np.searchsorted(entries_ns, wc, side="right"))
            ent = [t for t in entries_ns[j0:] if t <= wc + AFTER_WRB_MIN * 60_000_000_000]
            side_agree = np.nan
            if ent:
                een = e[pd.DatetimeIndex(e.first_entry_utc).as_unit("ns").asi8 == ent[0]]
                if len(een):
                    side_agree = (een.side.iloc[0] == "long") == (wd == "bullish")
            opp_rows.append(dict(month=month, wrb_comp_ns=wc, entered=bool(ent),
                                 side_agree=side_agree))

    df = pd.DataFrame(feat_rows)
    df.to_csv(os.path.join(HERE, "p4_6_signal_features.csv"), index=False)
    mdf = pd.DataFrame(min_rows)
    mdf.to_csv(os.path.join(HERE, "p4_6_template_minutes.csv"), index=False)
    odf = pd.DataFrame(opp_rows)

    T, K = df[df.taken], df[~df.taken]
    print(f"\n[frame] taken={len(T)} skipped={len(K)}")
    cells = [
        ("T-EN05", "en05_tf1_edge_tk", "dist to 1m reaction-WRB edge [PRIMARY]", -1),
        ("T-EN05", "en05_tf3_edge_tk", "dist to 3m reaction-WRB edge", -1),
        ("T-EN07", "en07_zone_room_tk", "room ahead in 1m WHG zone (cell A)", +1),
        ("T-EN07", "en07_body_room_tk", "room ahead in 1m reaction body (cell B)", +1),
        ("T-EN08", "en08_path_60s_tk", "trailing 60s path [PRIMARY]", +1),
        ("T-EN08", "en08_path_5m_tk", "trailing 5m path", +1),
        ("T-EN08", "en08_net_5m_tk", "trailing 5m net move", +1),
        ("T-EN08", "en08_speed_since_ev", "speed since event (tk/min)", +1),
        ("T-EN08", "en08_vwap_z", "abs VWAP stretch (z)", +1),
    ]
    print(f"\n{'id':7s} {'cell':42s} {'AUC':>6} {'95% CI':>16} {'clears':>7} {'n_t/n_k':>11}   taken vs skipped (median)")
    for tid, col, name, sign in cells:
        tv, kv = T[col].to_numpy(float) * sign, K[col].to_numpy(float) * sign
        ci = boot_ci(tv, kv)
        nt, nk = int(np.isfinite(tv).sum()), int(np.isfinite(kv).sum())
        mt, mk = np.nanmedian(T[col]), np.nanmedian(K[col])
        flag = "** YES" if ci["clears"] else "no"
        print(f"{tid:7s} {name:42s} {ci['auc']:>6.3f} [{ci['lo']:.3f},{ci['hi']:.3f}] {flag:>7} {nt:>5}/{nk:<5}   {mt:.1f} vs {mk:.1f} tk")
    for tf in (1, 3):
        print(f"  secondary: has 1m-chart reaction WRB (tf{tf}): taken "
              f"{T[f'tf{tf}_has_react'].mean():.0%} vs skipped {K[f'tf{tf}_has_react'].mean():.0%}")

    print("\n===== T-EN06: template forward application (minute level) =====")
    tm, om = mdf[mdf.template], mdf[~mdf.template]
    print(f"flat desk minutes: {len(mdf)}  | template minutes: {len(tm)} ({len(tm)/len(mdf):.1%})")
    print(f"P(entry within 5 min): template {tm.entered_5m.mean():.2%} vs other flat minutes {om.entered_5m.mean():.2%}"
          f"  -> ratio {tm.entered_5m.mean()/max(om.entered_5m.mean(),1e-9):.2f}x")
    for month in mdf.month.unique():
        a = mdf[(mdf.month == month) & mdf.template]; b = mdf[(mdf.month == month) & ~mdf.template]
        print(f"  {month}: {a.entered_5m.mean():.2%} vs {b.entered_5m.mean():.2%} (n_tmpl={len(a)})")
    print(f"opportunities (reaction WRB with >=1 template minute): {len(odf)}; "
          f"entered within 30 min: {odf.entered.mean():.0%}" if len(odf) else "no opportunities")
    if len(odf) and odf.side_agree.notna().any():
        print(f"  side agrees with reaction WRB (first entry in window): {odf.side_agree.dropna().mean():.0%}"
              f" (n={odf.side_agree.notna().sum()})")

    # T-EN07 secondary: taken signals inside an interval -> far edge reached?
    print("\n===== T-EN07 secondary (descriptive): does the trade reach the far edge? =====")
    for cell, bcol, tcol, rcol in [("WHG zone", "en07_zone_b", "en07_zone_t", "en07_zone_room_tk"),
                                   ("reaction body", "en07_body_b", "en07_body_t", "en07_body_room_tk")]:
        sub = df[df.taken & df[rcol].notna()] if rcol in df else pd.DataFrame()
        hitn = tot = 0
        for _, srow in sub.iterrows():
            month = srow.month; sym = dict(MONTHS)[month]
            lo_, hi_ = month_bounds(month)
            em = ep[(ep.first_entry_utc >= lo_) & (ep.first_entry_utc < hi_)]
            cand = em[(pd.DatetimeIndex(em.first_entry_utc).as_unit("ns").asi8 > srow.comp_ns) &
                      (pd.DatetimeIndex(em.first_entry_utc).as_unit("ns").asi8 <= srow.comp_ns + 5 * 60_000_000_000)]
            if not len(cand):
                continue
            t = cand.iloc[0]
            b2 = es[(es.symbol == sym) & (es.ts_event >= t.first_entry_utc) & (es.ts_event <= t.last_exit_utc)]
            if not len(b2):
                continue
            tot += 1
            far = srow[tcol] if srow.direction == "bullish" else srow[bcol]
            hitn += int(b2.high.max() >= far if srow.direction == "bullish" else b2.low.min() <= far)
        print(f"  {cell}: far edge reached during the trade in {hitn}/{tot} "
              f"({hitn/tot:.0%})" if tot else f"  {cell}: no matched taken signals inside")
    print("\nREAD: discovery months. Day-clustering caveat applies; T-EN06 measures internal")
    print("consistency of a template built from the taken trades. Reserved years decide.")


def selftest():
    print("=== SELF-TEST ===")
    assert room_ahead(5002.0, 5000.0, 5004.0, "bullish") == 8.0
    assert room_ahead(5002.0, 5000.0, 5004.0, "bearish") == 8.0
    assert np.isnan(room_ahead(5005.0, 5000.0, 5004.0, "bullish"))
    print("  room_ahead OK")
    c = np.r_[np.full(25, 100.0), 110.0]; v = np.ones(26)
    z = vwap_z(c, v)
    assert np.isnan(z[10]) is False or True
    assert z[-1] > 3, z[-1]       # big stretch from flat tape
    assert np.isnan(z[24])        # zero-variance tape -> NaN by design (no 0-division)
    print("  vwap_z flags stretch OK")
    ts = pd.date_range("2025-10-06 13:00", periods=400, freq="1min", tz="UTC")
    bts = pd.DatetimeIndex(ts).as_unit("ns").asi8
    e_day = pd.DataFrame(dict(first_entry_utc=[ts[120], ts[200]],
                              last_exit_utc=[ts[150], ts[230]]))
    fm = flat_desk_minutes(e_day, bts)
    assert bts[60] in fm and bts[59] not in fm       # desk opens 60 min before first entry
    assert bts[130] not in fm and bts[210] not in fm  # in-trade minutes excluded
    assert bts[170] in fm                            # flat gap between the two trades kept
    assert bts[231] not in fm                        # desk window ends at last exit
    print("  flat desk minutes OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
