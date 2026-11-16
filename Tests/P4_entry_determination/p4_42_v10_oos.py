#!/usr/bin/env python3
"""
p4_42_v10_oos.py — P4.42: spec v10 OUT-OF-SAMPLE on a reserved month (one shot).
=================================================================================
Runs the frozen v10 (ungated score>=6, confirmation entry, v9-B exits with one
reversal) on a month never used in any profit development. Only 2021-09 and
2024-11 have the full-month per-second flow the 10-condition score needs.
Construction identical to discovery: WRB and zone tables rebuilt from bars
(rebuild proven exact against the canonical tables - T-EN23 gates); prior-session
references, calendar, flow per the frozen definitions. Recorded as-is.

RUN: python3 Tests/P4_entry_determination/p4_42_v10_oos.py --month 2021-09
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies, first_reaction_wrb  # noqa: E402
from p4_2b_zone_mtf import identify_whg, resample      # noqa: E402
from p4_9b_score_v3 import overlap_one                 # noqa: E402
from p4_7_trailing_flow import flow_level              # noqa: E402
from p4_31_profit_v9 import wrb_flags, run_leg, ARMS   # noqa: E402

TICK = 0.25
E_TK, TOL_TK, TRAIL, FLOW15_CAP = 24, 4, 120, 4.6
WAIT = 5


def load_flow_any(repo, month):
    for suffix in ("", "_full"):
        path = os.path.join(repo, f"Data/inputs/flow_per_sec_{month}{suffix}.parquet")
        if os.path.exists(path):
            f = pd.read_parquet(path)
            return (f.sec.to_numpy(np.int64), f.buyv.to_numpy(np.int64),
                    f.sellv.to_numpy(np.int64), f.mid.to_numpy(float))
    raise SystemExit(f"no flow file for {month}")


def score_month(repo, month):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    ev_all = news_sets(repo)["all"]
    lo, hi = month_bounds(month)
    sym = es[(es.ts_event >= lo) & (es.ts_event < hi)].symbol.mode().iloc[0]
    bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
              (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
    bars["rth"] = bars.session == "RTH"
    bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
    sec, bv, sv, mz = load_flow_any(repo, month)
    # WRB signal table rebuilt from bars (gate-proven exact vs canonical)
    w = wrb_bodies(bars[bars.rth].reset_index(drop=True))
    w = w[(w.ts_event >= lo) & (w.ts_event < hi)].reset_index(drop=True)
    w = w.merge(bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
    z1 = identify_whg(bars)
    w = w.merge(z1[["ts_event", "whg_top", "whg_bottom"]], on="ts_event", how="left")
    w["has_whg"] = w.whg_top.notna()
    zt = {1: z1, 3: identify_whg(resample(bars, 3)), 5: identify_whg(resample(bars, 5)),
          10: identify_whg(resample(bars, 10))}
    comp_ns = (pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + 60_000_000_000)
    rng_tk = (bars.high - bars.low) / TICK
    tr5 = rng_tk.rolling(5).sum(); ref5 = tr5.rolling(TRAIL).median().shift(1)
    tr15 = rng_tk.rolling(15).sum(); ref15 = tr15.rolling(TRAIL).median().shift(1)
    lag15 = tr15.shift(5).to_numpy(); ref15l = ref15.shift(5).to_numpy()
    wball = w.copy(); wball["body"] = (wball.close - wball.open).abs()
    med = wball.groupby(wball.session_date.astype(str)).body.median()
    sessions = sorted(set(bars.session_date.astype(str)))
    prev = {sx: float(med.get(sessions[i - 1], np.nan)) for i, sx in enumerate(sessions) if i > 0}
    w1tab = wball.assign(body_bottom=np.minimum(wball.open, wball.close),
                         body_top=np.maximum(wball.open, wball.close))[
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
    ov = {tf: overlap_one(w, zt[tf][zt[tf].has_whg.fillna(False)], tf, comp_ns) for tf in (3, 5, 10)}
    sd = bars.session_date.astype(str).to_numpy()
    rows = []
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
        pr = prev.get(sd[ib], np.nan)
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
        rows.append(dict(comp_ns=cns, score=score, direction=w.direction.iloc[i],
                         uref=pr * TICK if np.isfinite(pr) else np.nan))
    return pd.DataFrame(rows), bars, sym


def run(repo, month):
    sig, bars, sym = score_month(repo, month)
    print(f"[{month}] {sym}: {len(sig)} RTH WRB completions, flagged>=6: {(sig.score >= 6).sum()}")
    bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
    cl = bars.close.to_numpy(); o = bars.open.to_numpy()
    h, l = bars.high.to_numpy(), bars.low.to_numpy()
    pre = wrb_flags(bars)
    p = dict(ARMS["B (momentum ladder)"])
    pnl = []; busy = -1
    for _, r in sig[sig.score >= 6].sort_values("comp_ns").iterrows():
        ib = int(np.searchsorted(bts, int(r.comp_ns) - 60_000_000_000))
        if ib >= len(bts) or bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 5:
            continue
        fb0 = ib + 1
        if fb0 >= len(bts) or not bars.rth.iloc[fb0] or fb0 <= busy:
            continue
        mv = cl[ib] - cl[ib - 5]
        if mv == 0:
            continue
        long = mv > 0
        uref = r.uref if np.isfinite(r.uref) else None
        lvl = h[ib] if long else l[ib]
        fb = None
        for j in range(fb0, min(fb0 + WAIT, len(bars))):
            if not bars.rth.iloc[j]:
                break
            if (h[j] >= lvl) if long else (l[j] <= lvl):
                fb = j
                fill = max(lvl, o[j]) if long else min(lvl, o[j])
                break
        if fb is None:
            continue
        px, xi, reason, _ = run_leg(bars, pre, fb, fill, long, 1.0, p, fb + 1, uref)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xi2, _, _ = run_leg(bars, pre, xi, px, not long, 1.0, p, xi + 1, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            xi = xi2
        pnl.append(tot)
        busy = xi + 5
    a = np.asarray(pnl); w = a > 0
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    lo, hi = month_bounds(month)
    e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
    hw = e_m.realized_pnl > 0
    print("\n| Configuration | Trades | Win rate | Avg win / loss | Total |")
    print("|---|---|---|---|---|")
    print(f"| v10 {month} (OUT-OF-SAMPLE) | {len(a)} | {w.mean():.0%} | "
          f"+{a[w].mean():.2f} / {a[~w].mean():.2f} | {a.sum():+.1f} pts |")
    print(f"| HIS {month} | {len(e_m)} | {hw.mean():.0%} | +{e_m.realized_pnl[hw].mean():.1f} / "
          f"{e_m.realized_pnl[~hw].mean():.1f} (as parsed) | {e_m.realized_pnl.sum():+.0f} (as parsed) |")
    print("\nREAD: one-shot look, recorded as-is, no retuning against it.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--month", required=True)
    a = ap.parse_args()
    run(a.repo, a.month)
