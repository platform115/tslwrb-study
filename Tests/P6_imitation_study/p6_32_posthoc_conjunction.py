#!/usr/bin/env python3
"""
p6_32_posthoc_conjunction.py — POST-HOC: interaction AND drift state. (T-IM39.)
One declared cell (flagged post-hoc): REA-interaction (15 min, direction-
aligned) AND active-drift state B6/S90/M1 (bursts5>=6, silence<=90s,
aligned mv60>=1t), NO signal requirement. Second variant M2 reported for
range. Scored: uncaught-catch (57), all-catch (92), fires/day.
RUN: python3 Tests/P6_imitation_study/p6_32_posthoc_conjunction.py     (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
T = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(T, "P4_entry_determination"))
sys.path.insert(0, os.path.join(T, "P5_trade_management"))
from p6_0_feature_battery import build_ctx
from p6_22_s6_1_presence import Resolver
from p6_24_s6_3_selectors import interact_edges
from p4_2_entry_context import month_bounds

DEDUP = 300
TICK = 0.25


def run(repo="."):
    C = build_ctx(repo, "2025-10")
    secs, mids = C["secs"], C["mids"]
    cb = np.concatenate([[0], np.cumsum(C["burst"].astype(np.int64))])
    i300 = np.searchsorted(secs, secs - 300)
    bursts5 = cb[np.arange(len(secs)) + 1] - cb[i300]
    lastb = np.full(len(secs), -1e12); lb = -1e12
    for i in range(len(secs)):
        if C["burst"][i]:
            lb = secs[i]
        lastb[i] = lb
    silence = secs - lastb
    i60 = np.searchsorted(secs, secs - 60)
    mv60 = (mids - mids[np.maximum(i60, 0)]) / TICK

    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    bm = b[(b.ts_event >= "2025-10-01") & (b.ts_event < "2025-11-01")].reset_index(drop=True)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    R = Resolver(bm, zr)
    sd1 = bm.sd.to_numpy(); bt1 = bm.ts_event.dt.tz_convert(None).to_numpy()

    def sec_sd(t):
        j = np.searchsorted(bt1, np.datetime64(t), "right") - 1
        return sd1[j] if j >= 0 else None

    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    lo, hi = month_bounds("2025-10")
    em = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].reset_index(drop=True)
    D = pd.read_parquet(os.path.join(repo, "Data/inputs/s6_selectors_final.parquet"))
    v1 = D["V1 rea&sig"].to_numpy()
    ndays = len(set(sd1))

    for M in (1, 2):
        cu = ca = 0
        for i, (_, r) in enumerate(em.iterrows()):
            t = np.datetime64(pd.Timestamp(r.first_entry_utc).tz_convert(None))
            d = 1 if r.side == "long" else -1
            j = int(np.searchsorted(secs, t.astype("datetime64[s]").astype(np.int64), "right")) - 1
            if j < 4000:
                continue
            st = (bursts5[j] >= 6) and (silence[j] <= 90) and (d * mv60[j] >= M)
            if not st:
                continue
            sd0 = sec_sd(t)
            if sd0 and interact_edges(R, sd0, t, "REA", 15, secs, mids, d):
                ca += 1
                if not v1[i]:
                    cu += 1
        fires = 0
        g30 = np.arange(4000, len(secs), 30)
        for d in (1, -1):
            st = (bursts5[g30] >= 6) & (silence[g30] <= 90) & (d * mv60[g30] >= M)
            idx = g30[st]
            last = -1e12
            for j in idx:
                t = np.datetime64(int(secs[j]), "s")
                if secs[j] - last <= DEDUP:
                    continue
                sd0 = sec_sd(t)
                if sd0 and interact_edges(R, sd0, t, "REA", 15, secs, mids, d):
                    fires += 1; last = secs[j]
        print(f"interaction & drift(B6/S90/M{M}): uncaught {cu}/57 ({cu/57:.0%}) "
              f"| all {ca}/92 | fires/day {fires/ndays:.0f}")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
