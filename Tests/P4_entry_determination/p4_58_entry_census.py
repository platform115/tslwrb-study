#!/usr/bin/env python3
"""
p4_58_entry_census.py — P4.58: the entry replication census (his GROUP A,
primary two months ONLY).
===========================================================================
For each of his Group A entries in 2025-10 and 2022-02 (n=97), test every
entry method we have. CAUGHT = the method produces an entry within 120 s of
his, same direction, price within the tolerance (4 and 8 ticks reported;
"close, not exact").
Methods (strategy-knowable unless marked):
  SIGNAL   enter at market at the score>=6 completion itself (close price)
  CONFIRM  v10/v11 confirmation stop entry, honest per-second fills
  TRIGGER  level-touch + 10s burst, gated by the signal window (P4.57;
           reaction-WRB levels; M=2 ticks, V=50 contracts)
  TRIG+HIS same trigger with his own prior trade prices added (DESCRIPTIVE
           upper bound - a live strategy cannot know his trades)
Output: per-method catch counts, the union of knowable methods, and the
uncaught remainder listed entry by entry for hand classification.
Validation months untouched.

RUN: python3 Tests/P4_entry_determination/p4_58_entry_census.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import MONTHS, month_bounds    # noqa: E402
from p4_49_sec_engine import Ctx, simulate, V11        # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402
from p4_53_anchor_sweep import month_anchors           # noqa: E402

TICK = 0.25
LIFE_NS = 60 * int(60e9)
MATCH_S = 120
TOLS = (4, 8)
TOUCH_TK, TOUCH_WIN, M_TK, V_CT = 1, 45, 2, 50
KNOWABLE = ["firstWRB-1m", "firstWRB-5m", "firstWRB-10m", "allWRB-10m"]
UPPER = KNOWABLE + ["his-exit", "his-entry"]


def trigger_fires(cx, W, keys, lo, hi, repo, month):
    f = pd.read_parquet(os.path.join(repo, f"Data/inputs/flow_per_sec_{month}_full.parquet"))
    secs = f.sec.to_numpy(np.int64)
    mids = f.mid.to_numpy(float)
    sv = (f.buyv - f.sellv).to_numpy(float)
    csv_ = np.concatenate([[0.0], np.cumsum(sv)])
    rb = pd.DatetimeIndex(cx.bars[cx.bars.rth].ts_event).as_unit("ns").asi8 // 10**9
    keep = np.isin(secs // 60 * 60, rb) & (secs >= lo.value // 10**9) & (secs < hi.value // 10**9)
    pts = sorted(sum((W[k] for k in keys), []))
    lt = np.array([t for t, _ in pts], dtype=np.int64)
    lp = np.array([p for _, p in pts])
    near = np.zeros(len(secs), bool)
    for i in np.flatnonzero(keep):
        s_ns = secs[i] * 10**9
        a, b = np.searchsorted(lt, s_ns - LIFE_NS), np.searchsorted(lt, s_ns, side="right")
        if b > a and np.abs(mids[i] - lp[a:b]).min() / TICK <= TOUCH_TK:
            near[i] = True
    last_touch = np.full(len(secs), -10**18, dtype=np.int64)
    lts = -10**18
    for i in range(len(secs)):
        if near[i]:
            lts = secs[i]
        last_touch[i] = lts
    i10 = np.searchsorted(secs, secs - 10)
    mv10 = mids - mids[np.maximum(i10, 0)]
    vol10 = csv_[np.arange(1, len(secs) + 1)] - csv_[i10]
    d = np.sign(mv10)
    sg = cx.sig[cx.sig.score >= 6]
    sig_s = sg.comp_ns.to_numpy(np.int64) // 10**9
    sig_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
    o = np.argsort(sig_s); sig_s, sig_d = sig_s[o], sig_d[o]
    fire = keep & (secs - last_touch <= TOUCH_WIN) & (np.abs(mv10) / TICK >= M_TK) \
           & (np.abs(vol10) >= V_CT) & (np.sign(vol10) == d) & (d != 0)
    out_s, out_d, out_p = [], [], []
    last = -10**18
    for i in np.flatnonzero(fire):
        if secs[i] - last <= MATCH_S:
            continue
        a, b = np.searchsorted(sig_s, secs[i] - 300), np.searchsorted(sig_s, secs[i], side="right")
        if not (sig_d[a:b] == d[i]).any():
            continue
        out_s.append(secs[i]); out_d.append(int(d[i])); out_p.append(mids[i])
        last = secs[i]
    return np.array(out_s, dtype=np.int64), np.array(out_d), np.array(out_p)


def caught(his_s, his_d, his_p, es, ed, epx, tol_tk):
    out = np.zeros(len(his_s), bool)
    for j in range(len(his_s)):
        m = (np.abs(es - his_s[j]) <= MATCH_S) & (ed == his_d[j]) \
            & (np.abs(epx - his_p[j]) / TICK <= tol_tk)
        out[j] = bool(m.any())
    return out


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    ev = None
    allA = {"n": 0}
    marks = {k: [] for k in ("SIGNAL", "CONFIRM", "TRIGGER", "TRIG+HIS")}
    rows = []
    for month, sym in MONTHS:
        cx = Ctx(repo, month, True)
        lo, hi = month_bounds(month)
        W, R = month_anchors(repo, cx, lo, hi, ep)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, True, e_m)
        eA = e_m[g == "A"].reset_index(drop=True)
        his_s = np.array([pd.Timestamp(x).value // 10**9 for x in eA.first_entry_utc], dtype=np.int64)
        his_d = np.array([1 if s == "long" else -1 for s in eA.side])
        his_p = np.array([float(np.asarray(x).ravel()[0]) for x in eA.entry_prices])
        allA["n"] += len(eA)
        # SIGNAL: market at every score>=6 completion
        sg = cx.sig[cx.sig.score >= 6]
        s_s = sg.comp_ns.to_numpy(np.int64) // 10**9
        s_d = np.where(sg.direction.to_numpy() == "bullish", 1, -1)
        ibs = np.searchsorted(cx.bts, sg.comp_ns.to_numpy(np.int64) - 60_000_000_000)
        s_p = cx.c[np.clip(ibs, 0, len(cx.c) - 1)]
        # CONFIRM: v11 per-second fills
        coll = []
        simulate(cx, V11, coll)
        c_s = np.array([t["ts"].value // 10**9 for t in coll], dtype=np.int64)
        c_d = np.array([1 if t["side"] == "long" else -1 for t in coll])
        c_p = np.array([t["fill"] for t in coll])
        # TRIGGER / TRIG+HIS
        t_s, t_d, t_p = trigger_fires(cx, W, KNOWABLE, lo, hi, repo, month)
        u_s, u_d, u_p = trigger_fires(cx, W, UPPER, lo, hi, repo, month)
        per = {"SIGNAL": (s_s, s_d, s_p), "CONFIRM": (c_s, c_d, c_p),
               "TRIGGER": (t_s, t_d, t_p), "TRIG+HIS": (u_s, u_d, u_p)}
        month_marks = {}
        for k, (es, ed, epx) in per.items():
            month_marks[k] = {tol: caught(his_s, his_d, his_p, es, ed, epx, tol) for tol in TOLS}
            marks[k].append(month_marks[k])
        for j in range(len(eA)):
            rows.append(dict(month=month, ts=pd.Timestamp(int(his_s[j]), unit="s", tz="UTC"),
                             side=eA.side.iloc[j], px=his_p[j], pnl=eA.realized_pnl.iloc[j],
                             **{k: bool(month_marks[k][8][j]) for k in per}))
    d = pd.DataFrame(rows)
    print(f"Universe: his GROUP A entries, primary two months, n={len(d)}.")
    print(f"CAUGHT = our entry within {MATCH_S}s, same direction, price within tolerance.\n")
    print("| Method | Within 4 ticks | Within 8 ticks | Live-tradable? |")
    print("|---|---|---|---|")
    live = {"SIGNAL": "yes", "CONFIRM": "yes", "TRIGGER": "yes",
            "TRIG+HIS": "NO - needs his trades"}
    for k in marks:
        c4 = sum(m[4].sum() for m in marks[k]); c8 = sum(m[8].sum() for m in marks[k])
        print(f"| {k} | {c4}/{len(d)} = {c4/len(d):.0%} | {c8}/{len(d)} = {c8/len(d):.0%} | {live[k]} |")
    un = d[["SIGNAL", "CONFIRM", "TRIGGER"]].any(axis=1)
    print(f"| UNION of live-tradable | - | {int(un.sum())}/{len(d)} = {un.mean():.0%} | yes |")
    rest = d[~un]
    print(f"\nNOT YET REPLICABLE (8tk): {len(rest)} entries - the work list:")
    print("| # | Month | Time (UTC) | Side | Price | His pnl |")
    print("|---|---|---|---|---|---|")
    for i, (_, r) in enumerate(rest.iterrows(), 1):
        print(f"| {i} | {r.month} | {r.ts.strftime('%m-%d %H:%M:%S')} | {r.side} | {r.px} | {r.pnl:+.1f} |")
    d.to_csv(os.path.join(HERE, "p4_58_census.csv"), index=False)
    print("\nOUT: p4_58_census.csv (per-entry method flags)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
