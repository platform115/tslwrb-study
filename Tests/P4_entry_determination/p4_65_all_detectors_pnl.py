#!/usr/bin/env python3
"""
p4_65_all_detectors_pnl.py — P4.65 / Strategy 2: ALL detectors, same test,
same outputs (precision + managed P&L, all four months).
===========================================================================
User direction: detectors were short-listed by how well they matched HIS
entries, but P&L and imitation proved partially independent (D1-B: 0%
precision in a reserved month, still profitable) - so every known detector
now gets the identical full test:
  trigger: the detector at its own 99th percentile, fires clustered 120 s
  direction: the detector's own sign; for direction-less detectors, the sign
    of the 10-sec move at the fire (FLAGGED as a choice)
  variants: UNGATED, and the common CONTEXT gate frozen from D1-A
    (5-min move >= 30tk toward direction + old score>=6 signal + early session)
  management: v11 exit stack on the per-second engine (acknowledged rough
    sketch), entries at the fire-second mid, 5-bar cooldown
Outputs per detector x variant: trades, his matched, precision, win rate,
avg win/loss, total with per-month breakdown, pooled max drawdown.
Reserved months are spent for this family of configs already (T-EN66).

RUN: python3 Tests/P4_entry_determination/p4_65_all_detectors_pnl.py      (repo root)
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
from p4_61_hot_detectors import detectors              # noqa: E402

TICK = 0.25
Q, CLUST, MATCH_S = 99.0, 120, 120


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    acc = {}
    for month, insample in ALL_MONTHS:
        cx, bars, feats, c = month_features(repo, month, insample)
        lo, hi = month_bounds(month)
        f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
        secs = f.sec.to_numpy(np.int64); mids = f.mid.to_numpy(float)
        bv = f.buyv.to_numpy(float); svv = f.sellv.to_numpy(float)
        rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
        keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
        i10 = np.searchsorted(secs, secs - 10)
        mv10 = (mids - mids[np.maximum(i10, 0)]) / TICK
        D = detectors(secs, mids, bv, svv)
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
        oo = np.argsort(sig_s); sig_s, sig_d = sig_s[oo], sig_d[oo]
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        hs = np.array([pd.Timestamp(x).value // 10**9 for x in e_m.first_entry_utc], dtype=np.int64)
        hd = np.array([1 if s == "long" else -1 for s in e_m.side])
        for dname, (stat, sgn) in D.items():
            st = np.where(np.isfinite(stat), stat, -np.inf)
            thr = np.percentile(st[keep & np.isfinite(stat)], Q)
            fire = keep & (st >= thr)
            fs_i = []; last = -10**18
            for i in np.flatnonzero(fire):
                if secs[i] - last > CLUST:
                    fs_i.append(i); last = secs[i]
            for variant in ("ungated", "context"):
                pnl = []; matched = 0; busy_bar = -1
                for i in fs_i:
                    s0 = int(secs[i])
                    d0 = int(sgn[i]) if sgn is not None else int(np.sign(mv10[i]))
                    if d0 == 0:
                        continue
                    ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
                    if ib < 60 or not cx.rth[ib] or ib <= busy_bar:
                        continue
                    if variant == "context":
                        ft = feats(ib, d0, s0)
                        a2, b2 = np.searchsorted(sig_s, s0 - 300), np.searchsorted(sig_s, s0, side="right")
                        ok = (ft["ret5m"] >= 30 and ft["min_into_sess"] <= 1050
                              and bool((sig_d[a2:b2] == d0).any()))
                        if not ok:
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
                k = (dname, variant)
                a = acc.setdefault(k, dict(pnl=[], matched=0, per_m={}))
                a["pnl"] += pnl
                a["matched"] += matched
                a["per_m"][month] = sum(pnl)
    print("| Detector | Variant | Trades | His matched | Precision | Win rate | "
          "Avg win / loss | Total (per month) | Max DD |")
    print("|---|---|---|---|---|---|---|---|---|")
    for (dname, variant), a in acc.items():
        p_ = np.asarray(a["pnl"]); wn = p_ > 0
        if not len(p_):
            continue
        eq = np.cumsum(p_); dd = float(np.max(np.maximum.accumulate(eq) - eq))
        pm = " / ".join(f"{a['per_m'].get(m, 0):+.0f}" for m, _ in ALL_MONTHS)
        aw = f"+{p_[wn].mean():.2f}" if wn.any() else "-"
        al = f"{p_[~wn].mean():.2f}" if (~wn).any() else "-"
        print(f"| {dname} | {variant} | {len(p_)} | {a['matched']} | "
              f"{a['matched']/len(p_):.0%} | {wn.mean():.0%} | {aw} / {al} | "
              f"{p_.sum():+.1f} ({pm}) | {dd:.1f} |")
    print("\nREAD: month order Oct-25 / Feb-22 / Sep-21 / Nov-24 (first two = where the")
    print("context gate was built). Direction for direction-less detectors = 10s move")
    print("sign at the fire (flagged choice). v11 management acknowledged as a sketch.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
