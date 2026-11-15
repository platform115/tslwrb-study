#!/usr/bin/env python3
"""
p4_22_profit_test.py — P4.22: PROFIT TEST under STRATEGY_SPEC_v1 (frozen).
===========================================================================
RUN HEADER (values the spec required computing before the run):
  time stop = 3 one-minute bars after the fill bar (his median hold 2.8 min,
  rounded to bar granularity; discovery-months median 2.1).
SPEC RESOLUTIONS recorded here (deterministic, fixed before first run):
  * Signal universe: ALL RTH (08:30-15:00 CT) 1m WRB completions in the month -
    not his desk windows. Position state (one at a time + 5-min cooldown) is the
    only availability constraint.
  * Fill: open of the bar after the signal bar. Force-flat at the session's last
    RTH bar close.
  * Far-edge target: the 1m reaction-WRB body's far edge in the trade direction
    (top for longs, bottom for shorts); if none exists, the signal's own zone's
    far edge; if the "far" edge is not at least 1 tick beyond the fill, fallback
    to fixed 2 points. Comparison arm: fixed 2 points for every trade.
  * Stop 2.5 points adverse. Same-bar stop+target touch -> STOP first
    (conservative standard).
  * Direction: sign of (close[signal bar] - close[5 bars earlier]); flat -> skip.
  * Discovery-month flow caveat: per-second flow exists only inside his trade
    windows (the committed windowed reductions), so outside them the two flow
    conditions score as the freeze dictates (c5 false, c9 passes) - the system
    is effectively concentrated where flow is known. The full-month files being
    built on the user's Mac lift this for 2021-09/2024-11 later.
Readings: STANDALONE (all system trades) and IMITATION (system trades at the
minutes he also entered; simulated exits vs HIS realized results, sign-level -
his pnl units are as parsed from chat, so sign/median comparisons, not sums).

RUN: python3 Tests/P4_entry_determination/p4_22_profit_test.py            (repo root)
     python3 Tests/P4_entry_determination/p4_22_profit_test.py --selftest
OUT: p4_22_trades.csv
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
STOP_PTS = 2.5
FIXED_TGT = 2.0
TIME_BARS = 3          # run header: median hold 2.8 min -> 3 bars
COOLDOWN_MIN = 5
K_V6 = 6
E_TK = 24
TOL_TK = 4
TRAIL = 120


def simulate(bars, entries):
    """entries: list of dicts(sig_i, side, target_px or None). Returns trades.
    bars: DataFrame with open/high/low/close, rth flag, session_date."""
    o, h, l, c = bars.open.to_numpy(), bars.high.to_numpy(), bars.low.to_numpy(), bars.close.to_numpy()
    rth = bars.rth.to_numpy()
    sd = bars.session_date.astype(str).to_numpy()
    trades = []
    busy_until = -1
    for e in entries:
        fb = e["sig_i"] + 1                       # fill bar
        if fb >= len(bars) or not rth[fb] or fb <= busy_until:
            continue
        fill = o[fb]
        long = e["side"] == "long"
        stop = fill - STOP_PTS if long else fill + STOP_PTS
        tgt = e["target_px"]
        if tgt is None or (long and tgt < fill + TICK) or (not long and tgt > fill - TICK):
            tgt = fill + FIXED_TGT if long else fill - FIXED_TGT
        exit_px = exit_i = reason = None
        for j in range(fb, len(bars)):
            if sd[j] != sd[fb] or not rth[j]:                      # session ended
                exit_px, exit_i, reason = c[j - 1], j - 1, "session"
                break
            hit_s = l[j] <= stop if long else h[j] >= stop
            hit_t = h[j] >= tgt if long else l[j] <= tgt
            if hit_s:                                              # stop first (conservative)
                exit_px, exit_i, reason = stop, j, "stop"
                break
            if hit_t:
                exit_px, exit_i, reason = tgt, j, "target"
                break
            if j >= fb + TIME_BARS:
                exit_px, exit_i, reason = c[j], j, "time"
                break
        if exit_px is None:
            exit_px, exit_i, reason = c[len(bars) - 1], len(bars) - 1, "eof"
        pnl = (exit_px - fill) if long else (fill - exit_px)
        trades.append(dict(sig_i=e["sig_i"], fill_i=fb, exit_i=exit_i, side=e["side"],
                           fill=fill, exit=exit_px, reason=reason, pnl_pts=pnl,
                           ts=bars.ts_event.iloc[fb], target_kind=e.get("kind", "?")))
        busy_until = exit_i + COOLDOWN_MIN
    return pd.DataFrame(trades)


def summarize(tr, label):
    if not len(tr):
        print(f"  {label}: no trades"); return
    w = tr.pnl_pts > 0
    eq = tr.pnl_pts.cumsum()
    dd = (eq - eq.cummax()).min()
    print(f"  {label}: trades {len(tr)} | win {w.mean():.0%} | avg win {tr.pnl_pts[w].mean():+.2f} "
          f"avg loss {tr.pnl_pts[~w].mean():+.2f} | TOTAL {tr.pnl_pts.sum():+.1f} pts | "
          f"worst stretch {dd:+.1f} pts | exits: {tr.reason.value_counts().to_dict()}")


def run(repo):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev_all = news_sets(repo)["all"]
    all_tr = {}
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                  (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bars["rth"] = bars.session == "RTH"
        bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
        cl = bars.close.to_numpy()
        sec, bv, sv, mz = load_flow(repo, month)
        # signal universe: every RTH WRB completion in the month
        w = wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m") &
                 (wrb1.ts_event >= lo) & (wrb1.ts_event < hi)].sort_values("ts_event")
        zt = {tf: (identify_whg(bars) if tf == 1 else identify_whg(resample(bars, tf)))
              for tf in (1, 3, 5, 10)}
        # canonical wrb_1m already carries has_whg / whg_top / whg_bottom
        comp_ns = (pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + 60_000_000_000)
        # trailing references
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
        entries = []
        for i in range(len(w)):
            cns = int(comp_ns[i]); P = float(w.close.iloc[i])
            ib = int(np.searchsorted(bts, cns - 60_000_000_000))
            if ib >= len(bts) or bts[ib] != cns - 60_000_000_000 or not bars.rth.iloc[ib]:
                continue
            iev = int(np.searchsorted(ev_all, cns, side="right")) - 1
            mins = (cns - ev_all[iev]) / 60e9 if iev >= 0 else np.inf
            fl5 = flow_level(sec, bv, sv, mz, cns, 300, w.direction.iloc[i] == "bullish")
            fl15 = flow_level(sec, bv, sv, mz, cns, 900, w.direction.iloc[i] == "bullish")
            w1 = first_reaction_wrb(w1tab, 1, ev_all[iev], cns) if iev >= 0 else None
            c6 = False
            if iev in react:
                wc, bb, tt = react[iev]
                c6 = wc <= cns <= wc + 30 * 60e9 and bb - TOL_TK * TICK <= P <= tt + TOL_TK * TICK
            pr = prev_ref.get(str(w.session_date.iloc[i]) if "session_date" in w else
                              str(bars.session_date.iloc[ib]), np.nan)
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
                not (np.isfinite(fl15) and fl15 > 4.6),
                bool(lag15[ib] > ref15l[ib]) if np.isfinite(ref15l[ib]) else False,
            ])
            if score < K_V6 or ib < 5:
                continue
            mv = cl[ib] - cl[ib - 5]
            if mv == 0:
                continue
            side = "long" if mv > 0 else "short"
            tgt = kind = None
            if w1:
                tgt = w1["top"] if side == "long" else w1["bottom"]; kind = "react-edge"
            elif w.has_whg.iloc[i]:
                tgt = float(w.whg_top.iloc[i]) if side == "long" else float(w.whg_bottom.iloc[i]); kind = "zone-edge"
            entries.append(dict(sig_i=ib, side=side, target_px=tgt, kind=kind or "fixed"))
        print(f"\n[{month}] signal universe scored; system entries attempted: {len(entries)}")
        tr = simulate(bars, entries)
        tr["month"] = month
        all_tr[month] = tr
        # fixed-target comparison arm
        tr_fx = simulate(bars, [dict(e, target_px=None) for e in entries]); tr_fx["month"] = month
        print(f"===== {month} STANDALONE =====")
        summarize(tr, "far-edge target")
        summarize(tr_fx, "fixed 2pt target")
        # imitation frame
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        his_ns = np.sort(pd.DatetimeIndex(e_m.first_entry_utc).as_unit("ns").asi8)
        if len(tr):
            t_ns = pd.DatetimeIndex(tr.ts).as_unit("ns").asi8
            j = np.searchsorted(his_ns, t_ns)
            near = np.minimum(np.abs(his_ns[np.clip(j, 0, len(his_ns) - 1)] - t_ns),
                              np.abs(his_ns[np.clip(j - 1, 0, None)] - t_ns)) / 60e9
            tr["his_trade_nearby"] = near <= 5
            im = tr[tr.his_trade_nearby]
            print(f"===== {month} IMITATION =====")
            print(f"  system trades within 5 min of one of his entries: {len(im)}/{len(tr)}"
                  f" ({len(im)/len(tr):.0%}); share of his {len(e_m)} entries covered: "
                  f"{min(len(im), len(e_m))/len(e_m):.0%} (upper bound)")
            summarize(im, "system on shared moments")
            his_w = (e_m.realized_pnl > 0)
            print(f"  HIS results that month (episode table): {len(e_m)} trades, "
                  f"win {his_w.mean():.0%}, median pnl sign-basis (units as parsed)")
    allt = pd.concat(all_tr.values(), ignore_index=True)
    allt.to_csv(os.path.join(HERE, "p4_22_trades.csv"), index=False)
    print("\n===== POOLED STANDALONE (far-edge) ====="); summarize(allt, "both months")
    print("\nREAD: spec v1, first trial of the assembled exit stack. No profit bar was")
    print("pre-registered; this is the honest readout. Variants come as spec v2+.")


def selftest():
    ts = pd.date_range("2025-10-06 14:00", periods=30, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, rth=True, session_date="d1"))
    bars.loc[6, ["high"]] = 5003.0        # target hit on bar 6
    tr = simulate(bars, [dict(sig_i=4, side="long", target_px=5002.5, kind="t")])
    assert len(tr) == 1 and tr.reason.iloc[0] == "target" and abs(tr.pnl_pts.iloc[0] - 2.5) < 1e-9
    print("=== SELF-TEST ===\n  target exit OK")
    bars2 = bars.copy(); bars2.loc[6, ["high", "low"]] = [5003.0, 4997.0]
    tr2 = simulate(bars2, [dict(sig_i=4, side="long", target_px=5002.5, kind="t")])
    assert tr2.reason.iloc[0] == "stop" and abs(tr2.pnl_pts.iloc[0] + 2.5) < 1e-9
    print("  same-bar stop+target -> stop first (conservative) OK")
    bars3 = bars.copy()
    tr3 = simulate(bars3, [dict(sig_i=4, side="long", target_px=5010.0, kind="t")])
    assert tr3.reason.iloc[0] == "time" and tr3.exit_i.iloc[0] == 8   # fill bar 5 + 3
    print("  time stop at 3 bars OK")
    tr4 = simulate(bars, [dict(sig_i=4, side="long", target_px=5002.5, kind="t"),
                          dict(sig_i=7, side="long", target_px=5002.5, kind="t")])
    assert len(tr4) == 1, "cooldown must block the second entry"
    print("  cooldown blocks re-entry OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
