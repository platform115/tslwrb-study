#!/usr/bin/env python3
"""
p4_52_return_tests.py — P4.52: two sharper entry tests on his GROUP A trades.
==============================================================================
TEST 1 (the approach, not the distance): a RETURN happens when price moves at
least 8 ticks away from a level and then comes back to within 2 ticks of it.
Levels = body top/bottom of the FIRST reaction WRB per KME per chart (1m, 3m,
5m), active 60 min (as P4.51). Question: do his A entries happen AT returns
more than chance - and when they do, does price then bounce or break?
TEST 2 (his own prior-trade levels): levels = HIS previous trades' exit prices
and entry prices (each active 60 min after that trade closes). Question: are
his A entries placed at his own earlier prices ("the WRB pt1 of my recent
trade") more than chance?
Baseline in both: every RTH 1-minute bar in the same months, same level sets.
Universe: his GROUP A trades only (141). Detection on 1m closes (deterministic).

RUN: python3 Tests/P4_entry_determination/p4_52_return_tests.py           (repo root)
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
import p4_51_kme_levels as p51                         # noqa: E402
from p4_49_sec_engine import Ctx, ALL_MONTHS           # noqa: E402
from p4_50_his_overlap import groups_for               # noqa: E402

TICK = 0.25
AWAY_TK, NEAR_TK = 8, 2        # return = moved >= 8tk away, back to <= 2tk
LIFE_NS = 60 * int(60e9)
ENTRY_TOL_NS = 3 * 60_000_000_000   # his entry within +/-3 min of the return bar
BREAK_TK, HORIZON = 4, 15      # outcome: +/-4tk through/away within 15 bars


def detect_returns(bars, levels):
    """All return events: (bar_ns, level_px, approach_side, outcome).
    approach_side=+1 means price was ABOVE the level and came down to it.
    outcome: 'bounce' (rejects >=4tk back toward approach side), 'break'
    (crosses >=4tk through), or 'neither' within 15 bars."""
    rth = bars[bars.rth]
    bns = pd.DatetimeIndex(rth.ts_event).as_unit("ns").asi8 + int(60e9)  # close time
    cl = rth.close.to_numpy()
    out = []
    comp, bot, top = levels
    for k in range(len(comp)):
        for L in (bot[k], top[k]):
            a = np.searchsorted(bns, comp[k])
            b = np.searchsorted(bns, comp[k] + LIFE_NS)
            armed = 0
            for i in range(a, b):
                d = (cl[i] - L) / TICK
                if abs(d) >= AWAY_TK:
                    armed = 1 if d > 0 else -1
                elif armed and abs(d) <= NEAR_TK:
                    end = min(i + 1 + HORIZON, len(cl))
                    seg = (cl[i + 1:end] - L) / TICK
                    bounce = (seg * armed >= BREAK_TK).any() if len(seg) else False
                    brk = (seg * armed <= -BREAK_TK).any() if len(seg) else False
                    if bounce and brk:
                        first_b = np.argmax(seg * armed >= BREAK_TK)
                        first_k = np.argmax(seg * armed <= -BREAK_TK)
                        oc = "bounce" if first_b < first_k else "break"
                    else:
                        oc = "bounce" if bounce else ("break" if brk else "neither")
                    out.append((int(bns[i]), float(L), armed, oc))
                    armed = 0
    return out


def his_prior_levels(e_m):
    """(available_from_ns, price) for each of his trades' exit and entry prices."""
    ex, en = [], []
    for _, t in e_m.iterrows():
        done = pd.Timestamp(t.last_exit_utc).value
        for p in np.asarray(t.exit_prices).ravel():
            ex.append((done, float(p)))
        for p in np.asarray(t.entry_prices).ravel():
            en.append((done, float(p)))
    return sorted(ex), sorted(en)


def near_any(points, ts, px, tol_tk, min_age_ns=0):
    for t0, p0 in points:
        if t0 + min_age_ns <= ts <= t0 + LIFE_NS and abs(px - p0) / TICK <= tol_tk:
            return True
    return False


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    ev_all = news_sets(repo)["all"]
    p51.FIRST_ONLY = True
    t1 = dict(his=0, hisn=0, base=0, basen=0, oc_all={}, oc_his={}, side_right=0, side_n=0)
    t2 = {"exit prices": [0, 0, 0, 0], "entry prices": [0, 0, 0, 0],
          "exit prices, level 10-60 min old": [0, 0, 0, 0],
          "entry prices, level 10-60 min old": [0, 0, 0, 0]}  # his_hit, his_n, base_hit, base_n
    for month, insample in ALL_MONTHS:
        cx = Ctx(repo, month, insample)
        lo, hi = month_bounds(month)
        lv = p51.levels_for_month(cx.bars, ev_all, lo, hi)
        levels135 = (np.concatenate([lv[tf][0] for tf in (1, 3, 5)]),
                     np.concatenate([lv[tf][1] for tf in (1, 3, 5)]),
                     np.concatenate([lv[tf][2] for tf in (1, 3, 5)]))
        rets = detect_returns(cx.bars, levels135)
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
        g = groups_for(repo, month, insample, e_m)
        eA = e_m[g == "A"]
        # TEST 1: his A entries at returns
        rts = np.array([r[0] for r in rets], dtype=np.int64)
        rpx = np.array([r[1] for r in rets])
        for _, t in eA.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            px = float(np.asarray(t.entry_prices).ravel()[0])
            m = (np.abs(rts - en) <= ENTRY_TOL_NS) & (np.abs(px - rpx) / TICK <= NEAR_TK)
            t1["hisn"] += 1
            if m.any():
                t1["his"] += 1
                r = rets[int(np.flatnonzero(m)[0])]
                t1["oc_his"][r[3]] = t1["oc_his"].get(r[3], 0) + 1
                # his side vs what happened: bounce in approach dir = fade-side wins
                went = {"bounce": r[2], "break": -r[2], "neither": 0}[r[3]]
                his_side = 1 if t.side == "long" else -1
                if went:
                    t1["side_n"] += 1
                    t1["side_right"] += int(went == his_side)
        for r in rets:
            t1["oc_all"][r[3]] = t1["oc_all"].get(r[3], 0) + 1
        rthb = cx.bars[cx.bars.rth]
        bns = pd.DatetimeIndex(rthb.ts_event).as_unit("ns").asi8 + int(60e9)
        bcl = rthb.close.to_numpy()
        mm = (bns >= lo.value) & (bns < hi.value)
        for ts, px in zip(bns[mm], bcl[mm]):
            m = (np.abs(rts - ts) <= ENTRY_TOL_NS) & (np.abs(px - rpx) / TICK <= NEAR_TK)
            t1["basen"] += 1
            t1["base"] += int(m.any())
        # TEST 2: his prior-trade price levels
        ex_lv, en_lv = his_prior_levels(e_m)
        AGE = 10 * 60_000_000_000
        for name, pts, age in [("exit prices", ex_lv, 0), ("entry prices", en_lv, 0),
                               ("exit prices, level 10-60 min old", ex_lv, AGE),
                               ("entry prices, level 10-60 min old", en_lv, AGE)]:
            for _, t in eA.iterrows():
                ts = pd.Timestamp(t.first_entry_utc).value
                px = float(np.asarray(t.entry_prices).ravel()[0])
                t2[name][1] += 1
                t2[name][0] += int(near_any(pts, ts, px, NEAR_TK, age))
            for ts, px in zip(bns[mm], bcl[mm]):
                t2[name][3] += 1
                t2[name][2] += int(near_any(pts, int(ts), px, NEAR_TK, age))

    print("TEST 1 - entries at RETURNS to a first-reaction-WRB level (1m/3m/5m)")
    print("A return = price moved >= 8 ticks from the level, came back to <= 2 ticks.")
    print("'At a return' = within 3 min of one and within 2 ticks of its level.\n")
    hr = t1["his"] / t1["hisn"]; br = t1["base"] / t1["basen"]
    print("| Who | At a return | Out of | Share | vs chance |")
    print("|---|---|---|---|---|")
    print(f"| His A entries | {t1['his']} | {t1['hisn']} | {hr:.0%} | {hr/br:.2f}x |")
    print(f"| Any RTH minute (chance) | {t1['base']} | {t1['basen']} | {br:.0%} | 1.00x |")
    n_all = sum(t1["oc_all"].values()); n_his = sum(t1["oc_his"].values())
    print("\nWhat happens after a return (next 15 bars):")
    print("| Outcome | All returns | Returns he entered at |")
    print("|---|---|---|")
    for oc in ("bounce", "break", "neither"):
        a = t1["oc_all"].get(oc, 0); h = t1["oc_his"].get(oc, 0)
        print(f"| {oc} | {a} ({a/max(n_all,1):.0%}) | {h} ({h/max(n_his,1):.0%}) |")
    if t1["side_n"]:
        print(f"\nWhen the return resolved, his side matched the resolution "
              f"{t1['side_right']}/{t1['side_n']} = {t1['side_right']/t1['side_n']:.0%}")

    print("\nTEST 2 - entries at HIS OWN previous trades' prices (active 60 min")
    print("after that trade closed; 'at' = within 2 ticks).\n")
    print("| Level set | His A entries at one | Share | Chance share | vs chance |")
    print("|---|---|---|---|---|")
    for name, (hh, hn, bh, bn) in t2.items():
        print(f"| his prior {name} | {hh}/{hn} | {hh/hn:.0%} | {bh/bn:.0%} | "
              f"{(hh/hn)/max(bh/bn,1e-9):.2f}x |")
    print("\nREAD: settings (8tk away, 2tk near, 60 min life) are first-pass, recorded.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
