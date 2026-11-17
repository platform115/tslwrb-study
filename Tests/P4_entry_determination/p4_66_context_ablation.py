#!/usr/bin/env python3
"""
p4_66_context_ablation.py — P4.66 / Strategy 2: the context conditions as a
variable grid. TRAINING MONTHS ONLY (user rule: 4-month runs need authorization).
=================================================================================
BASE config (the preserved D1-A): D1 burst trigger (99th pct, 120 s clustering),
context = [5-min move >= 30tk toward trade] AND [old score>=6 signal, same
direction, prior 5 min] AND [min_into_sess <= 1050], v11 exits, mid fills.
Variants, one change at a time (user-specified):
  THRUST: 20 / 25 / 35 / 40 ticks; re-expressed as net 5-min move >= k x
    ATR(14 bars) for k=1.5/2.5; replaced by volatility expansion
    ATR(3)/ATR(20) >= 1.5 / 2.0   [definitions recorded below]
  OLD SIGNAL: any direction | none required | score >= 7 | (base: same dir >= 6)
  SESSION TIME: condition dropped | <= 120 min since RTH open | <= 240 min
  TRIGGER: replaced by the momentum-side boundary cross of the signal bar
    (stop order at the signal bar's high if bullish / low if bearish, valid
    5 bars, per-second fill; direction = the signal's own direction)
  D6 trigger with base context, and the D1+D6 union (duplicates within 120 s
    counted once) + overlap share.
DRAWDOWN (new standing definition): worst drop BELOW THE STARTING POINT of the
month, worst month shown - "how far under water does the account go".

RUN: python3 Tests/P4_entry_determination/p4_66_context_ablation.py       (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies             # noqa: E402
from p4_49_sec_engine import leg_sec, V11              # noqa: E402
from p4_60_drawing_board import month_features         # noqa: E402

TICK = 0.25
Q, CLUST = 99.0, 120
WAIT = 5


def prep(repo, month):
    cx, bars, feats, c = month_features(repo, month, True)
    lo, hi = month_bounds(month)
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
    secs = f.sec.to_numpy(np.int64); mids = f.mid.to_numpy(float)
    sv = (f.buyv - f.sellv).to_numpy(float)
    rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
    keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
    i10 = np.searchsorted(secs, secs - 10)
    mv10 = (mids - mids[np.maximum(i10, 0)]) / TICK
    prev20 = (mids[np.maximum(i10, 0)] - mids[np.maximum(np.searchsorted(secs, secs - 30), 0)]) / TICK
    accel = np.abs(mv10) - np.abs(prev20)
    h, l, cl = cx.h, cx.l, cx.c
    pc = np.roll(cl, 1); pc[0] = cl[0]
    tr = np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc))) / TICK
    atr14 = pd.Series(tr).rolling(14).mean().to_numpy()
    atr3 = pd.Series(tr).rolling(3).mean().to_numpy()
    atr20 = pd.Series(tr).rolling(20).mean().to_numpy()
    # minutes since RTH open (RTH bars only)
    sd = cx.sd; rth = cx.rth
    mins_rth = np.full(len(cx.bts), 10**6)
    cur = None; cnt = 0
    for i in range(len(cx.bts)):
        if sd[i] != cur:
            cur = sd[i]; cnt = 0
        if rth[i]:
            mins_rth[i] = cnt; cnt += 1
    w = wrb_bodies(cx.bars[cx.bars.rth].reset_index(drop=True))
    w = w.merge(cx.bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
    w["body"] = (w.close - w.open).abs()
    med = w.groupby(w.session_date.astype(str)).body.median()
    sess = sorted(set(sd))
    prevd = {sx: float(med.get(sess[j - 1], np.nan)) for j, sx in enumerate(sess) if j > 0}
    sg = cx.sig[cx.sig.score >= 6]
    sig_s = sg.comp_ns.to_numpy(np.int64) // 10**9
    sig_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    sig_sc = sg.score.to_numpy()
    oo = np.argsort(sig_s)
    return dict(cx=cx, feats=feats, secs=secs, mids=mids, keep=keep, mv10=mv10,
                accel=accel, atr14=atr14, atr3=atr3, atr20=atr20, mins_rth=mins_rth,
                prevd=prevd, sd=sd, sig_s=sig_s[oo], sig_d=sig_d[oo], sig_sc=sig_sc[oo])


def fires_of(P, which):
    stat = np.abs(P["mv10"]) if which == "D1" else P["accel"]
    sgn = np.sign(P["mv10"])
    thr = np.percentile(stat[P["keep"] & np.isfinite(stat)], Q)
    out = []
    last = -10**18
    for i in np.flatnonzero(P["keep"] & (stat >= thr)):
        if P["secs"][i] - last > CLUST:
            out.append((i, int(sgn[i])))
            last = P["secs"][i]
    return out


def sim(P, fire_list, ctx_fun):
    cx = P["cx"]
    pnl = []
    busy = -1
    cache = {}
    for i, d0 in fire_list:
        if d0 == 0:
            continue
        s0 = int(P["secs"][i])
        ib = int(np.searchsorted(cx.bts, s0 * 10**9)) - 1
        if ib < 60 or not cx.rth[ib] or ib <= busy:
            continue
        if ib not in cache or cache[ib][0] != d0:
            cache[ib] = (d0, P["feats"](ib, d0, s0))
        ft = cache[ib][1]
        a2 = np.searchsorted(P["sig_s"], s0 - 300)
        b2 = np.searchsorted(P["sig_s"], s0, side="right")
        if not ctx_fun(ft, ib, d0, P, a2, b2):
            continue
        fill = float(P["mids"][i]); long = d0 > 0
        uref = P["prevd"].get(P["sd"][ib], None)
        uref = uref if uref and np.isfinite(uref) else None
        px, xs, xb, reason = leg_sec(cx, ib, fill, s0, long, V11, uref)
        tot = (px - fill) if long else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_sec(cx, xb, px, xs, not long, V11, uref)
            tot += (px2 - px) if (not long) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + 5
    return pnl


def sim_confirm(P, ctx_fun):
    """Trigger variant: momentum-side boundary cross of the signal bar."""
    cx = P["cx"]
    pnl = []; busy = -1
    sg = cx.sig[cx.sig.score >= 6].sort_values("comp_ns")
    for _, r in sg.iterrows():
        ib = int(np.searchsorted(cx.bts, int(r.comp_ns) - 60_000_000_000))
        if ib >= len(cx.bts) or cx.bts[ib] != int(r.comp_ns) - 60_000_000_000 or ib < 60:
            continue
        d0 = 1 if r.direction == "bullish" else -1
        fb0 = ib + 1
        if fb0 >= len(cx.bts) or not cx.rth[fb0] or fb0 <= busy:
            continue
        s0 = int(r.comp_ns) // 10**9
        ft = P["feats"](ib, d0, s0)
        if not (ft["ret5m"] >= 30 and ft["min_into_sess"] <= 1050):
            continue
        lvl = cx.h[ib] if d0 > 0 else cx.l[ib]
        jmax = fb0
        while jmax + 1 < len(cx.bsec) and jmax + 1 < fb0 + WAIT and cx.rth[jmax + 1]:
            jmax += 1
        k = int(np.searchsorted(P["secs"], cx.bsec[fb0]))
        end_s = cx.bsec[jmax] + 60
        fill = fill_s = None
        while k < len(P["secs"]) and P["secs"][k] < end_s:
            m = P["mids"][k]
            if (m >= lvl) if d0 > 0 else (m <= lvl):
                fill = max(lvl, m) if d0 > 0 else min(lvl, m)
                fill_s = int(P["secs"][k]); break
            k += 1
        if fill is None:
            continue
        fb = cx.bar_of(fill_s)
        uref = P["prevd"].get(P["sd"][fb], None)
        uref = uref if uref and np.isfinite(uref) else None
        px, xs, xb, reason = leg_sec(cx, fb, fill, fill_s, d0 > 0, V11, uref)
        tot = (px - fill) if d0 > 0 else (fill - px)
        if reason == "faststop":
            px2, xs2, xb2, _ = leg_sec(cx, xb, px, xs, not (d0 > 0), V11, uref)
            tot += (px2 - px) if (d0 <= 0) else (px - px2)
            xb = xb2
        pnl.append(tot)
        busy = xb + 5
    return pnl


def row(name, per_m):
    allp = sum(per_m.values(), [])
    a = np.asarray(allp); wn = a > 0
    dd0 = max((-min(0.0, float(np.min(np.cumsum(p)))) if p else 0.0) for p in per_m.values())
    pm = " / ".join(f"{sum(p):+.0f}" for p in per_m.values())
    aw = f"+{a[wn].mean():.2f}" if wn.any() else "-"
    al = f"{a[~wn].mean():.2f}" if (~wn).any() else "-"
    return (f"| {name} | {len(a)} | {wn.mean():.0%} | {aw} / {al} | "
            f"{a.sum():+.1f} ({pm}) | {dd0:.1f} |")


def run(repo):
    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    base_sig = lambda P, a2, b2, d0: bool((P["sig_d"][a2:b2] == d0).any())

    def CTX(thrust=30, atrk=None, volx=None, sigmode="same", sess=1050, clock=None):
        def f(ft, ib, d0, P, a2, b2):
            if atrk is not None:
                if not (abs(ft["ret5m"]) >= atrk * P["atr14"][ib]):
                    return False
            elif volx is not None:
                if not (P["atr3"][ib] >= volx * P["atr20"][ib]):
                    return False
            else:
                if not (ft["ret5m"] >= thrust):
                    return False
            if sigmode == "same" and not base_sig(P, a2, b2, d0):
                return False
            if sigmode == "any" and not (b2 > a2):
                return False
            if sigmode == "sc7" and not bool(((P["sig_d"][a2:b2] == d0) &
                                              (P["sig_sc"][a2:b2] >= 7)).any()):
                return False
            if clock is not None:
                if not (P["mins_rth"][ib] <= clock):
                    return False
            elif sess is not None and not (ft["min_into_sess"] <= sess):
                return False
            return True
        return f

    variants = [
        ("BASE: thrust 30tk, signal same-dir, early (D1-A)", "D1", CTX()),
        ("thrust 20tk", "D1", CTX(thrust=20)),
        ("thrust 25tk", "D1", CTX(thrust=25)),
        ("thrust 35tk", "D1", CTX(thrust=35)),
        ("thrust 40tk", "D1", CTX(thrust=40)),
        ("thrust as 5-min move >= 1.5x ATR(14)", "D1", CTX(atrk=1.5)),
        ("thrust as 5-min move >= 2.5x ATR(14)", "D1", CTX(atrk=2.5)),
        ("thrust as vol expansion ATR(3)>=1.5x ATR(20)", "D1", CTX(volx=1.5)),
        ("thrust as vol expansion ATR(3)>=2.0x ATR(20)", "D1", CTX(volx=2.0)),
        ("signal: any direction allowed", "D1", CTX(sigmode="any")),
        ("signal: not required at all", "D1", CTX(sigmode="none")),
        ("signal: score >= 7 same-dir", "D1", CTX(sigmode="sc7")),
        ("session-time condition dropped", "D1", CTX(sess=None)),
        ("clock: <= 120 min after RTH open", "D1", CTX(clock=120)),
        ("clock: <= 240 min after RTH open", "D1", CTX(clock=240)),
        ("D6 accel trigger, base context", "D6", CTX()),
    ]
    print("TRAINING MONTHS ONLY (Oct-25 / Feb-22). DD = worst drop below the month's")
    print("starting point, worst month shown. v11 management (sketch), mid fills.\n")
    print("| Variant | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    d1_fires = {m: fires_of(P, "D1") for m, P in Ps.items()}
    d6_fires = {m: fires_of(P, "D6") for m, P in Ps.items()}
    for name, which, ctx in variants:
        fl = d1_fires if which == "D1" else d6_fires
        per_m = {m: sim(Ps[m], fl[m], ctx) for m in Ps}
        print(row(name, per_m))
    per_m = {m: sim_confirm(Ps[m], None) for m in Ps}
    print(row("trigger: momentum-side boundary cross of the signal bar", per_m))
    # D1+D6 union + overlap
    tot_d1 = tot_d6 = tot_shared = 0
    per_m_u = {}
    for m, P in Ps.items():
        c_ = CTX()
        f1 = [(i, d) for (i, d) in d1_fires[m]]
        f6 = [(i, d) for (i, d) in d6_fires[m]]
        s1 = {(int(P["secs"][i]) // CLUST, d) for i, d in f1}
        s6 = {(int(P["secs"][i]) // CLUST, d) for i, d in f6}
        tot_d1 += len(s1); tot_d6 += len(s6); tot_shared += len(s1 & s6)
        merged = sorted(set(f1) | set(f6), key=lambda t: P["secs"][t[0]])
        per_m_u[m] = sim(P, merged, c_)
    print(row("D1+D6 union, base context (within-120s duplicates once)", per_m_u))
    print(f"\nOVERLAP (raw fires, 120s buckets): D1 {tot_d1}, D6 {tot_d6}, shared "
          f"{tot_shared} ({tot_shared/max(min(tot_d1,tot_d6),1):.0%} of the smaller set)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--combos", action="store_true")
    a = ap.parse_args()
    combos(a.repo) if a.combos else run(a.repo)


def combos(repo):
    """The T-EN68 combination rows (previously run via an uncommitted driver)."""
    Ps = {m: prep(repo, m) for m, _ in MONTHS}
    d1 = {m: fires_of(P, "D1") for m, P in Ps.items()}

    def CTX2(thrust, sig, sess):
        def f(ft, ib, d0, P, a2, b2):
            if not (ft["ret5m"] >= thrust):
                return False
            if sig and not bool((P["sig_d"][a2:b2] == d0).any()):
                return False
            if sess is not None and not (ft["min_into_sess"] <= sess):
                return False
            return True
        return f

    print("| Variant | Trades | Win rate | Avg win / loss | Total (per month) | Max below start |")
    print("|---|---|---|---|---|---|")
    for name, t, sg, ss in [
        ("thrust 30, no signal, no session cut", 30, False, None),
        ("thrust 40, no signal, no session cut", 40, False, None),
        ("thrust 40, no signal, early kept", 40, False, 1050),
        ("thrust 50, no signal, no session cut", 50, False, None),
        ("thrust 60, no signal, no session cut", 60, False, None),
        ("thrust 40, signal kept, no session cut", 40, True, None),
    ]:
        per_m = {m: sim(Ps[m], d1[m], CTX2(t, sg, ss)) for m in Ps}
        print(row(name, per_m))
