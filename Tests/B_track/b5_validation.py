#!/usr/bin/env python3
"""
b5_validation.py — B5: one-shot quarantined validation (T-BS06).
Spec: B5_SPEC.md (committed first). Month 2024-11, first touch.
RUN: python3 Tests/B_track/b5_validation.py > Tests/B_track/B5_REPORT.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination"):
    sys.path.insert(0, os.path.join(T, d))
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p6_24_s6_3_selectors import interact_edges              # noqa: E402
from p4_3_confluence_news import news_sets                   # noqa: E402

MONTH, NXT = "2024-11", "2024-12-01"
DISP, ORDER_TTL, DEDUP = 1.25, 300, 300


def m3a(exc, ts):
    peak, tp, mae = 0.0, 0, 0.0
    for i in range(len(exc)):
        mae = min(mae, exc[i])
        if exc[i] > peak:
            peak, tp = exc[i], ts[i]
        if exc[i] <= -3.75:
            return -3.75, i, -mae
        if ts[i] - tp >= 60 or ts[i] >= 480:
            return exc[i], i, -mae
    return (exc[-1], len(exc) - 1, -mae) if len(exc) else (0.0, 0, 0.0)


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= f"{MONTH}-01") & (b.ts_event < NXT)
           ].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    f = pd.read_parquet(os.path.join(
        repo, f"Data/inputs/flow_per_sec_{MONTH}_full.parquet"))
    secs = f.sec.to_numpy(np.int64)
    mids = f.mid.to_numpy(float)
    ev = np.asarray(news_sets(repo)["all"], dtype=np.int64) // 10**9
    evm = ev[(ev >= secs[0]) & (ev <= secs[-1])]
    sd1 = bm.sd.to_numpy()
    bt1 = bm.ts_event.dt.tz_convert(None).astype("int64").to_numpy() // 10**9
    rth = bm.session.eq("RTH").to_numpy()
    roll = bm.is_roll_day.to_numpy()
    nd = bm.sd.nunique()

    # ---- scan + trade in one chronological pass ----
    trades = []
    busy = -10**12
    for es in evm:
        w0, w1 = es + 300, es + 2700
        j0 = int(np.searchsorted(secs, w0))
        j1 = int(np.searchsorted(secs, w1, "right"))
        if j1 - j0 < 60:
            continue
        kb = int(np.searchsorted(bt1, secs[j0], "right")) - 1
        if kb < 0 or not rth[kb] or roll[kb]:
            continue
        sd0 = sd1[kb]
        last_fire = {}
        jj = j0
        while jj < j1:
            t = int(secs[jj])
            E = edges_at(R, sd0, np.datetime64(t, "s"), "SQZ")
            px, prev = mids[jj], mids[jj - 1]
            for e in E:
                d = 1 if (prev <= e < px) else (-1 if (prev >= e > px)
                                                else 0)
                if d == 0:
                    continue
                key = (round(e, 2), d)
                if t - last_fire.get(key, -10**9) <= DEDUP:
                    continue
                last_fire[key] = t
                lvl = e + DISP * d
                j2 = int(np.searchsorted(secs, t + ORDER_TTL, "right"))
                seg = mids[jj:j2]
                hit = np.flatnonzero((seg >= lvl) if d > 0
                                     else (seg <= lvl))
                if not len(hit):
                    continue
                jf = jj + int(hit[0])
                tf = int(secs[jf])
                if tf < busy:
                    continue
                j3 = int(np.searchsorted(secs, tf + 1800, "right"))
                exc = (mids[jf:j3] - lvl) * d
                ts_ = (secs[jf:j3] - tf).astype(int)
                pnl, ix, mae = m3a(exc, ts_)
                busy = int(secs[jf + ix])
                trades.append(dict(tf=tf, d=d, pnl=pnl, mae=mae))
            jj += 1
    tr = pd.DataFrame(trades).sort_values("tf").reset_index(drop=True)

    # ---- his side ----
    ep = pd.read_parquet(os.path.join(repo,
                         "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    ep["m"] = pd.to_datetime(ep.first_entry_utc, utc=True
                             ).dt.strftime("%Y-%m")
    em = ep[ep.m == MONTH].copy()
    em["t_s"] = (pd.to_datetime(em.first_entry_utc, utc=True)
                 .dt.as_unit("ns").astype("int64") // 10**9)
    g2 = []
    for _, r in em.iterrows():
        side = 1 if r.side == "long" else -1
        t = int(r.t_s)
        kk = int(np.searchsorted(ev, t, "right")) - 1
        mins = (t - ev[kk]) / 60.0 if kk >= 0 else np.inf
        if not (5 < mins <= 45):
            continue
        kb = int(np.searchsorted(bt1, t, "right")) - 1
        if kb < 0:
            continue
        E = interact_edges(R, sd1[kb], np.datetime64(t, "s"), "SQZ", 15,
                           secs, mids, side)
        if E:
            g2.append(dict(sec=t, side=side,
                           pnl=float(r.realized_pnl)
                           if pd.notna(r.realized_pnl) else np.nan))
    hg = pd.DataFrame(g2)

    print("# B5 REPORT — ONE-SHOT VALIDATION ON 2024-11 (T-BS06)")
    print("STATUS: CLOSED | 2026-11-25 | Spec: B5_SPEC.md (committed "
          "first) | FIRST touch of the quarantined month")
    print()
    hp = hg.pnl.dropna()
    hw = hp > 0
    print(f"## HIS SIDE ({MONTH}): {len(em)} entries total; G2-like "
          f"(squeeze + news window): {len(hg)}")
    if len(hp):
        print(f"His G2-like results: {hw.mean():.0%} win | "
              f"+{hp[hw].sum():.1f} / {hp[~hw].sum():.1f} | net "
              f"{hp.sum():+.1f} | worst {hp.min():+.2f}")
    print()
    w = tr.pnl > 0
    aw = tr.pnl[w].mean() if w.any() else 0
    al = tr.pnl[~w].mean() if (~w).any() else 0
    eq = tr.pnl.cumsum()
    dd = float((eq.cummax() - eq).max()) if len(tr) else 0.0
    caught = 0
    for _, h in hg.iterrows():
        if ((tr.d == h.side) & (abs(tr.tf - h.sec) <= 300)).any():
            caught += 1
    near = np.zeros(len(tr), bool)
    for _, h in hg.iterrows():
        near |= (np.abs(tr.tf - h.sec) <= 300).to_numpy()
    ex = tr[~near]
    print(f"## OURS (4A d1.25 x M3A, frozen): {len(tr)} trades over "
          f"{nd} sessions ({len(tr)/nd:.1f}/day)")
    print(f"| win rate | points won/lost | net | avg win/loss | worst | "
          f"max MAE | max DD |")
    print(f"|---|---|---|---|---|---|---|")
    print(f"| {w.mean():.0%} | +{tr.pnl[w].sum():.1f} / "
          f"{tr.pnl[~w].sum():.1f} | {tr.pnl.sum():+.1f} | +{aw:.2f} / "
          f"{al:.2f} | {tr.pnl.min():+.2f} | {tr.mae.max():.2f} | "
          f"{dd:.1f} |")
    print()
    print(f"Caught: {caught}/{len(hg)} of his G2-like entries "
          f"({caught/max(1,len(hg)):.0%}; goal 30-50%).")
    print(f"Extras: {len(ex)} trades, net {ex.pnl.sum():+.1f} pts.")
    print()
    passed = tr.pnl.sum() > 0 and ex.pnl.sum() >= 0
    print(f"## VERDICT (pre-stated rule: net > 0 AND extras net >= 0): "
          f"{'PASS' if passed else 'FAIL'}")
    print()
    print("Footer: his 2024-11 labels unaudited (disclosed in spec); "
          "mid-cross stop fills; fees ~0 per J; single position. "
          "Registry: T-BS06.")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
