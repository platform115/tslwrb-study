#!/usr/bin/env python3
"""
p4_64_oos_gates.py — P4.64 / Strategy 2 (pre-v1): the frontier gates on the
reserved months (user-authorized side track) + Strategy 1 management on top.
=============================================================================
Gates FROZEN from the in-sample frontier (T-EN65), applied unchanged:
  D1-A (the half-trusted row): D1 burst + 5-min move >= 30tk + old signal
       (score >= 6, same dir, prior 5 min) + first ~2/3 of session
  D1-B (the optimistic row):   D1 burst + 5-min move >= 40tk + old signal
       + day range so far < 150tk + first ~2/3 of session
  D4-A: D4 flow-run >= its 99th pct + old score >= 7 + day range < 200tk
For every month (training as reference, reserved as the test):
  1. gate precision: fires taken, his entries matched (120 s, same dir),
     share of fires that are his
  2. full Strategy 1 / v11 trade management on the gated fires (enter at the
     fire second's mid, burst direction; v11 exit stack on the per-second
     engine incl. one reversal) - the mandated results table + max drawdown,
     with HIS month rows (all his entries, as parsed).
KNOWN NON-NORMALIZED KNOB (flagged): day-range and move thresholds are in
ticks, not scaled to regime volatility - OOS shrinkage may partly be scale.

RUN: python3 Tests/P4_entry_determination/p4_64_oos_gates.py              (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies             # noqa: E402
from p4_49_sec_engine import leg_sec, V11, ALL_MONTHS  # noqa: E402
from p4_60_drawing_board import month_features         # noqa: E402

TICK = 0.25
Q, CLUST, MATCH_S = 99.0, 120, 120


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    print("| Configuration | Fires taken | His matched | Precision | Trades | Win rate | Avg win / loss | Total | Max DD |")
    print("|---|---|---|---|---|---|---|---|---|")
    his_rows = []
    for month, insample in ALL_MONTHS:
        cx, bars, feats, c = month_features(repo, month, insample)
        lo, hi = month_bounds(month)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64); mids = f.mid.to_numpy(float)
        sv = (f.buyv - f.sellv).to_numpy(float)
        rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
        keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        i10 = np.searchsorted(secs, secs - 10)
        mv10 = (mids - mids[np.maximum(i10, 0)]) / TICK
        runl = np.zeros(len(secs)); cur = 0; last_sign = 0
        for i in range(len(secs)):
            s = np.sign(sv[i])
            if s != 0 and s == last_sign:
                cur += 1
            elif s != 0:
                cur = 1; last_sign = s
            runl[i] = cur * (last_sign if last_sign else 0)
        # prior-session median WRB body (for the pt-ladder hold rule)
        w = wrb_bodies(bars[bars.rth].reset_index(drop=True))
        w = w.merge(bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
        w["body"] = (w.close - w.open).abs()
        med = w.groupby(w.session_date.astype(str)).body.median()
        sess = sorted(set(bars.session_date.astype(str)))
        prev = {sx: float(med.get(sess[j - 1], np.nan)) for j, sx in enumerate(sess) if j > 0}
        sd = bars.session_date.astype(str).to_numpy()
        sg = cx.sig[cx.sig.score >= 6]
        sig_s = sg.comp_ns.to_numpy(np.int64) // 10**9
        sig_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
        sig_sc = sg.score.to_numpy()
        oo = np.argsort(sig_s); sig_s, sig_d, sig_sc = sig_s[oo], sig_d[oo], sig_sc[oo]
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])
        for uni, stat, sgn, gates in [
            ("D1", np.abs(mv10), np.sign(mv10), {
                "A (ret5m>=30, old signal, early)":
                    lambda ft, osc: ft["ret5m"] >= 30 and osc >= 6 and ft["min_into_sess"] <= 1050,
                "B (ret5m>=40, old signal, rng<150, early)":
                    lambda ft, osc: ft["ret5m"] >= 40 and osc >= 6 and ft["day_rng_tk"] < 150
                    and ft["min_into_sess"] <= 1050}),
            ("D4", np.abs(runl), np.sign(runl), {
                "A (old score>=7, rng<200)":
                    lambda ft, osc: osc >= 7 and ft["day_rng_tk"] < 200}),
        ]:
            thr = np.percentile(stat[keep & np.isfinite(stat)], Q)
            fire = keep & (stat >= thr)
            fs_i = []; last = -10**18
            for i in np.flatnonzero(fire):
                if secs[i] - last > CLUST:
                    fs_i.append(i); last = secs[i]
            for gname, gfun in gates.items():
                pnl = []; matched = 0; busy_bar = -1
                for i in fs_i:
                    s0 = int(secs[i]); d0 = int(sgn[i])
                    if d0 == 0:
                        continue
                    ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
                    if ib < 60 or not cx.rth[ib] or ib <= busy_bar:
                        continue
                    ft = feats(ib, d0, s0)
                    a2, b2 = np.searchsorted(sig_s, s0 - 300), np.searchsorted(sig_s, s0, side="right")
                    m = sig_d[a2:b2] == d0
                    osc = float(sig_sc[a2:b2][m].max()) if m.any() else 0.0
                    if not gfun(ft, osc):
                        continue
                    if ((np.abs(hs - s0) <= MATCH_S) & (hd == d0)).any():
                        matched += 1
                    fill = float(mids[i]); long = d0 > 0
                    uref = prev.get(sd[ib], None)
                    uref = uref if uref and np.isfinite(uref) else None
                    px, xs, xb, reason = leg_sec(cx, ib, fill, s0, long, V11, uref)
                    tot = (px - fill) if long else (fill - px)
                    if reason == "faststop":
                        px2, xs2, xb2, _ = leg_sec(cx, xb, px, xs, not long, V11, uref)
                        tot += (px2 - px) if (not long) else (px - px2)
                        xb = xb2
                    pnl.append(tot)
                    busy_bar = xb + 5
                a = np.asarray(pnl); wn = a > 0
                eq = np.cumsum(a); dd = float(np.max(np.maximum.accumulate(eq) - eq)) if len(a) else 0.0
                tag = "TRAIN" if insample else "RESERVED"
                aw = f"+{a[wn].mean():.2f}" if wn.any() else "-"
                al = f"{a[~wn].mean():.2f}" if (~wn).any() else "-"
                print(f"| {uni}-{gname[:1]} {month} ({tag}) | {len(a)} | {matched} | "
                      f"{matched/max(len(a),1):.0%} | {len(a)} | "
                      f"{wn.mean():.0%} | {aw} / {al} | {a.sum():+.1f} | {dd:.1f} |")
        hw = e_m.realized_pnl > 0
        his_rows.append(f"| HIS {month} (all entries, as parsed) | - | - | - | {len(e_m)} | "
                        f"{hw.mean():.0%} | +{e_m.realized_pnl[hw].mean():.1f} / "
                        f"{e_m.realized_pnl[~hw].mean():.1f} | {e_m.realized_pnl.sum():+.0f} | - |")
    for r in his_rows:
        print(r)
    print("\nREAD: gates frozen from in-sample (T-EN65); reserved months are the test.")
    print("Entries at the fire-second mid; v11 exit stack, per-second engine.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
