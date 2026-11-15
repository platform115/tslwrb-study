#!/usr/bin/env python3
"""
p4_28_profit_v7.py — P4.28: profit test under STRATEGY_SPEC_v7 (frozen).
=========================================================================
v7 = v2B/v4B geometry in volatility units (U = prior session's median 1m WRB
body, points): stop 1.6U · fast-fail 0.8U first 2 bars · target 2.3U · WRB
trail · time 9 bars — plus two entry changes: direction requires the 5-min move
AND 5-min pressure to agree (else skip), and 15-min pressure > 4.6 skips
(exhaustion veto). Entry score v6>=6 unchanged. See the spec for derivations.

RUN: python3 Tests/P4_entry_determination/p4_28_profit_v7.py            (repo root)
     python3 Tests/P4_entry_determination/p4_28_profit_v7.py --selftest
OUT: p4_28_trades.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS            # noqa: E402
from p4_3_confluence_news import news_sets                     # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies, first_reaction_wrb  # noqa: E402
from p4_2b_zone_mtf import identify_whg, resample              # noqa: E402
from p4_9b_score_v3 import overlap_one                         # noqa: E402
from p4_7_trailing_flow import load_flow, flow_level           # noqa: E402

TICK = 0.25
STOP_M, EARLY_M, TGT_M = 1.6, 0.8, 2.3
EARLY_BARS = 2
TIME_BARS = 9
COOLDOWN_MIN = 5
K_V6, E_TK, TOL_TK, TRAIL = 6, 24, 4, 120
FLOW15_CAP = 4.6


def wrb_flags(bars):
    o, c = bars.open.to_numpy(), bars.close.to_numpy()
    sd = bars.session_date.astype(str).to_numpy()
    body = np.abs(c - o)
    f = np.zeros(len(bars), bool); d = np.empty(len(bars), object)
    bb = np.minimum(o, c); bt = np.maximum(o, c)
    for i in range(3, len(bars)):
        if (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) and body[i] > 0 and \
           body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]:
            f[i] = True; d[i] = "bullish" if c[i] > o[i] else "bearish"
    return f, d, bb, bt


def simulate_v7(bars, entries):
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy(); sd = bars.session_date.astype(str).to_numpy()
    isw, wdir, wbb, wbt = wrb_flags(bars)
    trades, busy_until = [], -1
    for e in entries:
        fb = e["sig_i"] + 1
        if fb >= len(bars) or not rth[fb] or fb <= busy_until:
            continue
        fill = o[fb]; long = e["side"] == "long"; u = e["u_pts"]
        tgt = fill + TGT_M * u if long else fill - TGT_M * u
        trail = None; trailed = False
        exit_px = exit_i = reason = None
        for j in range(fb, len(bars)):
            if sd[j] != sd[fb] or not rth[j]:
                exit_px, exit_i, reason = c[j - 1], j - 1, "session"; break
            sp = (EARLY_M if j < fb + EARLY_BARS else STOP_M) * u
            base = fill - sp if long else fill + sp
            stop = base if trail is None else (max(base, trail) if long else min(base, trail))
            if (l[j] <= stop if long else h[j] >= stop):
                exit_px, exit_i = stop, j
                reason = "trail" if (trail is not None and stop == trail and
                                     (trail > base if long else trail < base)) else "stop"
                break
            if (h[j] >= tgt if long else l[j] <= tgt):
                exit_px, exit_i, reason = tgt, j, "target"; break
            if j >= fb + TIME_BARS:
                exit_px, exit_i, reason = c[j], j, "time"; break
            if j > fb and isw[j] and ((wdir[j] == "bullish") == long):
                nt = wbb[j] if long else wbt[j]
                trail = nt if trail is None else (max(trail, nt) if long else min(trail, nt))
                trailed = True
        if exit_px is None:
            exit_px, exit_i, reason = c[-1], len(bars) - 1, "eof"
        pnl = (exit_px - fill) if long else (fill - exit_px)
        trades.append(dict(sig_i=e["sig_i"], fill_i=fb, exit_i=exit_i, side=e["side"],
                           fill=fill, exit=exit_px, reason=reason, pnl_pts=pnl,
                           trailed=trailed, ts=bars.ts_event.iloc[fb]))
        busy_until = exit_i + COOLDOWN_MIN
    return pd.DataFrame(trades)


def table_row(name, tr):
    if not len(tr):
        return f"| {name} | 0 | - | - | - |"
    w = tr.pnl_pts > 0
    return (f"| {name} | {len(tr)} | {w.mean():.0%} | +{tr.pnl_pts[w].mean():.2f} / "
            f"{tr.pnl_pts[~w].mean():.2f} | {tr.pnl_pts.sum():+.1f} pts |")


def his_row(e_m, label):
    w = e_m.realized_pnl > 0
    return (f"| HIS {label} | {len(e_m)} | {w.mean():.0%} | +{e_m.realized_pnl[w].mean():.1f} / "
            f"{e_m.realized_pnl[~w].mean():.1f} (as parsed) | {e_m.realized_pnl.sum():+.0f} (as parsed) |")


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev_all = news_sets(repo)["all"]
    all_tr = []
    print("| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                  (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bars["rth"] = bars.session == "RTH"
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy()
        sec, bv, sv, mz = load_flow(repo, month)
        w = wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m") &
                 (wrb1.ts_event >= lo) & (wrb1.ts_event < hi)].sort_values("ts_event")
        zt = {tf: (identify_whg(bars) if tf == 1 else identify_whg(resample(bars, tf)))
              for tf in (1, 3, 5, 10)}
        comp_ns = (pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + 60_000_000_000)
        rng_tk = (bars.high - bars.low) / TICK
        tr5 = rng_tk.rolling(5).sum(); ref5 = tr5.rolling(TRAIL).median().shift(1)
        tr15 = rng_tk.rolling(15).sum(); ref15 = tr15.rolling(TRAIL).median().shift(1)
        lag15 = tr15.shift(5).to_numpy(); ref15l = ref15.shift(5).to_numpy()
        wbody_all = wrb_bodies(bars[bars.rth].reset_index(drop=True)).merge(
            bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
        wbody_all["body"] = (wbody_all.close - wbody_all.open).abs() / TICK
        bmed = wbody_all.groupby(wbody_all.session_date.astype(str)).body.median()
        sessions = sorted(set(bars.session_date.astype(str)))
        prev_ref = {s: float(bmed.get(sessions[i - 1], np.nan))
                    for i, s in enumerate(sessions) if i > 0}
        w1tab = wbody_all.assign(body_bottom=np.minimum(wbody_all.open, wbody_all.close),
                                 body_top=np.maximum(wbody_all.open, wbody_all.close))[
            ["ts_event", "direction", "body_bottom", "body_top"]].sort_values("ts_event")
        w1ts = pd.DatetimeIndex(w1tab.ts_event).as_unit("ns").asi8 + 60_000_000_000
        react = {}
        for k, evns in enumerate(ev_all):
            if not (lo.value - 4 * 86400e9 <= evns < hi.value):
                continue
            m = (w1ts > evns) & (w1ts <= evns + 30 * 60e9)
            if m.any():
                j = int(np.flatnonzero(m)[0])
                react[k] = (int(w1ts[j]), float(w1tab.body_bottom.iloc[j]), float(w1tab.body_top.iloc[j]))
        ov = {tf: overlap_one(w, zt[tf][zt[tf].has_whg.fillna(False)], tf, comp_ns)
              for tf in (3, 5, 10)}
        entries, n_veto, n_dis = [], 0, 0
        for i in range(len(w)):
            cns = int(comp_ns[i]); P = float(w.close.iloc[i])
            ib = int(np.searchsorted(bts, cns - 60_000_000_000))
            if ib >= len(bts) or bts[ib] != cns - 60_000_000_000 or not bars.rth.iloc[ib] or ib < 5:
                continue
            iev = int(np.searchsorted(ev_all, cns, side="right")) - 1
            mins = (cns - ev_all[iev]) / 60e9 if iev >= 0 else np.inf
            is_bull = w.direction.iloc[i] == "bullish"
            fl5 = flow_level(sec, bv, sv, mz, cns, 300, is_bull)
            fl15 = flow_level(sec, bv, sv, mz, cns, 900, is_bull)
            w1 = first_reaction_wrb(w1tab, 1, ev_all[iev], cns) if iev >= 0 else None
            c6 = False
            if iev in react:
                wc, bb, tt = react[iev]
                c6 = wc <= cns <= wc + 30 * 60e9 and bb - TOL_TK * TICK <= P <= tt + TOL_TK * TICK
            pr = prev_ref.get(str(bars.session_date.iloc[ib]), np.nan)
            score = sum([
                mins <= 15,
                bool(ov[3][i] | ov[5][i]),
                np.isfinite(pr) and abs(w.close.iloc[i] - w.open.iloc[i]) / TICK >= 2.0 * pr,
                bool(tr5.iloc[ib] >= 1.5 * ref5.iloc[ib]) if np.isfinite(ref5.iloc[ib]) else False,
                np.isfinite(fl5) and fl5 > 2.0,
                c6,
                bool(w1 and min(abs(P - w1["top"]), abs(P - w1["bottom"])) / TICK <= E_TK),
                bool(ov[10][i]),
                not (np.isfinite(fl15) and fl15 > FLOW15_CAP),
                bool(lag15[ib] > ref15l[ib]) if np.isfinite(ref15l[ib]) else False,
            ])
            if score < K_V6:
                continue
            # v7 entry additions
            if np.isfinite(fl15) and fl15 > FLOW15_CAP:
                n_veto += 1; continue
            mv = cl[ib] - cl[ib - 5]
            # orient pressure by the MOVE's direction for the agreement check
            fl5_move = flow_level(sec, bv, sv, mz, cns, 300, mv > 0) if mv != 0 else np.nan
            if mv == 0 or not np.isfinite(fl5_move) or fl5_move <= 0:
                n_dis += 1; continue
            side = "long" if mv > 0 else "short"
            if not np.isfinite(pr):
                continue
            entries.append(dict(sig_i=ib, side=side, u_pts=pr * TICK))
        tr = simulate_v7(bars, entries)
        tr["month"] = month
        all_tr.append(tr)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        print(table_row(f"v7 {month} (skips: {n_dis} disagree, {n_veto} veto)", tr))
        his_ns = np.sort(pd.DatetimeIndex(e_m.first_entry_utc).as_unit("ns").asi8)
        if len(tr):
            t_ns = pd.DatetimeIndex(tr.ts).as_unit("ns").asi8
            j = np.searchsorted(his_ns, t_ns)
            near = np.minimum(np.abs(his_ns[np.clip(j, 0, len(his_ns) - 1)] - t_ns),
                              np.abs(his_ns[np.clip(j - 1, 0, None)] - t_ns)) / 60e9
            print(table_row(f"v7 {month} imitation (shared moments)", tr[near <= 5]))
        print(his_row(e_m, month))
    allt = pd.concat(all_tr, ignore_index=True)
    allt.to_csv(os.path.join(HERE, "p4_28_trades.csv"), index=False)
    print(table_row("v7 POOLED", allt))
    print(f"\nexit mix: {allt.reason.value_counts().to_dict()}")
    print("reference: v2B +6.2 | v4B +4.5 (both fixed-tick, move-only direction)")
    print("\nREAD: spec v7 frozen before run. Final config re-validates out-of-sample")
    print("before any profitability claim.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=30, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, rth=True, session_date="d1"))
    bars.loc[9, "high"] = 5005.0
    t = simulate_v7(bars, [dict(sig_i=4, side="long", u_pts=2.0)])
    assert t.reason.iloc[0] == "target" and abs(t.pnl_pts.iloc[0] - 4.6) < 1e-9  # 2.3*2.0
    print("=== SELF-TEST ===\n  scaled target 2.3U OK")
    b2 = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                           close=5000.0, rth=True, session_date="d1"))
    b2.loc[5, "low"] = 4998.0        # 2.0 adverse on fill bar; early stop = 0.8*2.0 = 1.6
    t2 = simulate_v7(b2, [dict(sig_i=4, side="long", u_pts=2.0)])
    assert t2.reason.iloc[0] == "stop" and abs(t2.pnl_pts.iloc[0] + 1.6) < 1e-9
    print("  scaled fast-fail 0.8U OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
