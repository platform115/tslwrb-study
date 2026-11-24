#!/usr/bin/env python3
"""
a2_2_measurement.py — A2.2: THE MEASUREMENT TABLE (T-IM41).
Spec: A2_2_SPEC.md (frozen). Harness (truncation recompute + planted-bug
self-test) runs FIRST; the table only builds if it passes.
RUN: python3 Tests/A2_measurement/a2_2_measurement.py           (repo root)
OUT: Data/inputs/a2_features.parquet + printed report.
"""
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
for d in ("P6_imitation_study", "P4_entry_determination", "P5_trade_management"):
    sys.path.insert(0, os.path.join(T, d))
from p6_0_feature_battery import build_ctx, battery          # noqa: E402
from p6_22_s6_1_presence import Resolver                     # noqa: E402
from p6_23_s6_2_interaction import edges_at                  # noqa: E402
from p6_24_s6_3_selectors import interact_edges              # noqa: E402

MONTHS = ["2025-10", "2022-02"]
FAMS = (("REA", 15), ("SQZ", 15), ("GAP", 5), ("SHD", 5))
RNG = np.random.default_rng(113)
N_NULL = 10
FRESH_S = 5


# ---------- harness ----------
def truncate_ctx(C, j):
    """A faithful <=t view of the per-second state (arrays cut at j+1)."""
    C2 = dict(C)
    n = j + 1
    for k in ("secs", "mids", "dif", "burst", "atr10", "Cday", "Rsec",
              "bar_i", "sd_sec"):
        C2[k] = C[k][:n]
    C2["csv"] = C["csv"][:n + 1]
    C2["ctv"] = C["ctv"][:n + 1]
    t_ns = int(C["secs"][j]) * 10**9
    C2["ev"] = C["ev"][C["ev"] <= t_ns]
    ss, sd_, sc = C["sig"]
    m = ss <= C["secs"][j]
    C2["sig"] = (ss[m], sd_[m], sc[m])
    return C2


def battery_bug1(C, t, d):
    """PLANT: mv8 peeks one second ahead."""
    out = battery(C, t, d)
    if out is None:
        return None
    j = int(np.searchsorted(C["secs"], t, "right")) - 1
    k = min(j + 1, len(C["mids"]) - 1)
    out["mv8"] = (C["mids"][k] - C["mids"][max(k - 8, 0)]) / 0.25
    return out


def battery_bug2(C, t, d):
    """PLANT: stall uses 5 seconds beyond t (bar-containing-t style)."""
    out = battery(C, t, d)
    if out is None:
        return None
    j = int(np.searchsorted(C["secs"], t, "right")) - 1
    k = min(j + 5, len(C["mids"]) - 1)
    seg = C["mids"][max(j - 300, 0):k + 1]
    pk = int(np.argmax(seg)) if (d or 1) > 0 else int(np.argmin(seg))
    out["stall_5m_extreme"] = float(k - (max(j - 300, 0) + pk))
    return out


def same(a, b):
    if a is None or b is None:
        return a is b
    for k in a:
        x, y = a[k], b.get(k, np.nan)
        if (isinstance(x, float) and np.isnan(x)
                and isinstance(y, float) and np.isnan(y)):
            continue
        if x != y:
            return False
    return True


def run_harness(C, trade_secs, sides):
    idx = RNG.choice(len(trade_secs), size=min(40, len(trade_secs)),
                     replace=False)
    fails = 0
    caught1 = caught2 = 0
    for i in idx:
        t, d = int(trade_secs[i]), int(sides[i])
        j = int(np.searchsorted(C["secs"], t, "right")) - 1
        if j < 4100 or t - C["secs"][j] > FRESH_S:
            continue
        C2 = truncate_ctx(C, j)
        if not same(battery(C, t, d), battery(C2, t, d)):
            fails += 1
        if not same(battery_bug1(C, t, d), battery_bug1(C2, t, d)):
            caught1 += 1
        if not same(battery_bug2(C, t, d), battery_bug2(C2, t, d)):
            caught2 += 1
    ok = fails == 0 and caught1 > 0 and caught2 > 0
    print(f"HARNESS: honest battery mismatches {fails} (need 0) | "
          f"plant-1 caught at {caught1} moments, plant-2 at {caught2} "
          f"(each needs >=1) -> {'PASS' if ok else 'FAIL'}")
    return ok


# ---------- KME name + surprise ----------
def num(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return np.nan
    s = str(x).strip().replace(",", "")
    m = re.fullmatch(r"(-?\d*\.?\d+)\s*([%KMBT]?)", s)
    if not m:
        return np.nan
    v = float(m.group(1))
    return v * {"": 1, "%": 1, "K": 1e3, "M": 1e6, "B": 1e9,
                "T": 1e12}[m.group(2)]


def kme_lookup(repo):
    cal = pd.read_parquet(os.path.join(repo, "Data/inputs/kme_calendar.parquet"))
    cal = cal.dropna(subset=["ts_utc"]).sort_values("ts_utc")
    # parquet stores microsecond precision; force ns before epoch math
    ts = (pd.to_datetime(cal.ts_utc, utc=True).dt.as_unit("ns")
          .astype("int64").to_numpy() // 10**9)
    ev = cal.event.astype(str).to_numpy()
    act = cal.actual.map(num).to_numpy()
    fc = cal.forecast.map(num).to_numpy()
    return ts, ev, act, fc


def kme_fields(C, kts, kev, kact, kfc, t):
    out = {}
    kk = int(np.searchsorted(C["ev"], t * 10**9, "right")) - 1
    mins = (t * 10**9 - C["ev"][kk]) / 60e9 if kk >= 0 else np.nan
    out["kme_mins_since"] = mins
    out["kme_in45"] = bool(kk >= 0 and mins <= 45)
    out["kme_phase"] = ("0-5" if mins <= 5 else "5-45") if out["kme_in45"] else "none"
    out["kme_event"] = None
    out["kme_surprise"] = np.nan
    out["kme_surprise_sign"] = np.nan
    if kk >= 0:
        esec = C["ev"][kk] // 10**9
        jj = int(np.searchsorted(kts, esec, "right")) - 1
        if jj >= 0 and abs(int(kts[jj]) - int(esec)) <= 1:
            out["kme_event"] = kev[jj]
            if np.isfinite(kact[jj]) and np.isfinite(kfc[jj]):
                s = kact[jj] - kfc[jj]
                out["kme_surprise"] = s
                out["kme_surprise_sign"] = float(np.sign(s))
    return out


# ---------- structure state ----------
def structure_fields(R, sd, t64, side, secs, mids, j):
    out = {}
    px = mids[j]
    for fam, M in FAMS:
        E = interact_edges(R, sd, t64, fam, M, secs, mids, side)
        out[f"{fam}_interact"] = bool(E)
        out[f"{fam}_int_dist"] = float(min(abs(px - e) for e in E)) if E else np.nan
        A = edges_at(R, sd, t64, fam)
        out[f"{fam}_near_dist"] = float(min(abs(px - e) for e in A)) if A else np.nan
    return out


def run(repo="."):
    g = pd.read_parquet(os.path.join(repo, "Data/inputs/a2_ground_truth.parquet"))
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    kts, kev, kact, kfc = kme_lookup(repo)
    rows = []
    for month in MONTHS:
        nxt = "2025-11-01" if month == "2025-10" else "2022-03-01"
        bm = b[(b.ts_event >= f"{month}-01") & (b.ts_event < nxt)
               ].reset_index(drop=True)
        zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
        R = Resolver(bm, zr)
        C = build_ctx(repo, month)
        secs, mids = C["secs"], C["mids"]
        gm = g[g.month == month]
        tsecs = gm.entry_msg_s.to_numpy()
        sds = gm.side.map({"long": 1, "short": -1}).to_numpy()
        if not run_harness(C, tsecs, sds):
            print(f"ABORT {month}: harness failed")
            return
        ent_all = np.sort(tsecs)

        def one(t, d, sd0, who, ep):
            j = int(np.searchsorted(secs, t, "right")) - 1
            fresh = j >= 0 and (t - secs[j]) <= FRESH_S
            row = dict(who=who, episode_id=ep, month=month, sec=t, side=d,
                       session_date=sd0, data_fresh=fresh)
            if fresh and j >= 4100:
                f = battery(C, t, d)
                if f:
                    row.update(f)
                t64 = np.datetime64(int(t), "s")
                row.update(structure_fields(R, sd0, t64, d, secs, mids, j))
                row.update(kme_fields(C, kts, kev, kact, kfc, t))
            return row

        n_fb = 0
        for _, r in gm.iterrows():
            d = 1 if r.side == "long" else -1
            rows.append(one(int(r.entry_msg_s), d, r.session_date, "his",
                            int(r.episode_id)))
            if not r.entry_verified:
                continue
            # matched nulls: same session, same 30-min band, >=10min from
            # any entry; widen to +/-1h around the band if < N_NULL
            t0 = int(r.entry_msg_s)
            band0 = t0 - (t0 % 1800)
            sd_mask = C["sd_sec"] == r.session_date

            def eligible(lo, hi):
                m = sd_mask & (secs >= lo) & (secs < hi)
                cand = secs[m]
                if not len(cand):
                    return cand
                far = np.min(np.abs(cand[:, None] - ent_all[None, :]),
                             axis=1) >= 600
                return cand[far]

            cand = eligible(band0, band0 + 1800)
            if len(cand) < N_NULL:
                cand = eligible(band0 - 3600, band0 + 5400)
                n_fb += 1
            if len(cand) >= N_NULL:
                for t in RNG.choice(cand, size=N_NULL, replace=False):
                    rows.append(one(int(t), d, r.session_date, "null",
                                    int(r.episode_id)))
        print(f"{month}: rows so far {len(rows)}, null fallbacks {n_fb}")
    F = pd.DataFrame(rows)
    out = os.path.join(repo, "Data/inputs/a2_features.parquet")
    F.to_parquet(out, index=False)
    his = F[F.who == "his"]
    nul = F[F.who == "null"]
    print(f"\nwrote {out}: {len(his)} his rows, {len(nul)} null rows, "
          f"{F.shape[1]} columns")
    print(f"his rows with features: {his.data_fresh.sum()}/{len(his)} | "
          f"kme surprise parsed where in-45: "
          f"{his[his.kme_in45 == True].kme_surprise.notna().mean():.0%}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
