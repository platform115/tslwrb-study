#!/usr/bin/env python3
"""
p6_17_s4_emit.py — S4 STEP 1: OBJECT EMISSION. (T-IM24.)
===============================================================================
Runs the S3-adopted generators (plus the recorded rivals, for S4
arbitration) over every session that carries at least one of his structure
references, and writes ONE objects table.

Generators emitted:
  g1_whg        hidden gaps, TFs 1/2/3/5/15 (S2 definition, roll-excluded)
  g2_shadow_d2  shadow intervals D2 (adopted provisional), full range +
                wick sub-range kept
  g2_shadow_d1  rival: D1 r=1.0
  g3_swing      reaction swings 5m N=2 (adopted) + 5m N=3 + 15m N=1 (siblings)
  g4_c2         contraction episodes W=15 q=0.67 and W=30 q=0.67 (episode
                band at episode END; knowable_ts = episode end + 1 bar)
Schema: object_id | generator | tf | param | dir_side | band_lo | band_hi |
        sub_lo | sub_hi | knowable_ts (UTC ns) | session_date
Output: Data/inputs/s4_objects.parquet (gitignored; checksum recorded).

RUN: python3 Tests/P6_imitation_study/p6_17_s4_emit.py                (repo root)
"""
import os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p6_12_g1_hidden_gap import resample_tf, whg_zones     # noqa: E402
from p6_14_g2_shadow import shadow_intervals               # noqa: E402
from p6_15_g3_reaction import swings                       # noqa: E402
from p6_16_g4_contraction import episodes_c2               # noqa: E402

TFS = (1, 2, 3, 5, 15)


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    zr = pd.read_parquet(os.path.join(repo, "Data/inputs/his_zone_refs.parquet"))
    ref_sess = set()
    ts1 = b.ts_event.dt.tz_convert(None).to_numpy()
    sd_arr = b.sd.to_numpy()
    for t in pd.to_datetime(zr.ts_utc, utc=True).dt.tz_convert(None):
        j = np.searchsorted(ts1, np.datetime64(t), "right") - 1
        if j >= 0:
            ref_sess.add(sd_arr[j])
    sess_list = list(dict.fromkeys(sd_arr))
    # include 5 prior sessions of each (lookback parity with S3)
    needed = set()
    for s in ref_sess:
        si = sess_list.index(s)
        needed |= {sess_list[si - k] for k in range(5) if si - k >= 0}
    print(f"sessions: {len(ref_sess)} referenced, {len(needed)} with lookback", flush=True)

    rows = []
    cols = ["ts_event", "open", "high", "low", "close", "is_roll_day", "session_date"]
    for nd, (s, g) in enumerate(b.groupby("sd")):
        if s not in needed:
            continue
        g = g.reset_index(drop=True)
        rbs = {}
        for tf in TFS:
            rb = resample_tf(g[cols], tf)
            rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            rbs[tf] = rb
        for tf in TFS:
            for z in whg_zones(rbs[tf], tf):
                rows.append(("g1_whg", tf, "", z["dir"], z["lo"], z["hi"],
                             np.nan, np.nan, z["comp"], s))
            for mode, name, r in (("D2", "g2_shadow_d2", 0), ("D1", "g2_shadow_d1", 1.0)):
                for z in shadow_intervals(rbs[tf], tf, mode, r):
                    rows.append((name, tf, mode, z["dir"], z["lo"], z["hi"],
                                 z["sh_lo"], z["sh_hi"], z["comp"], s))
        for tf, n in ((5, 2), (5, 3), (15, 1)):
            for z in swings(rbs[tf], tf, n):
                rows.append(("g3_swing", tf, f"N{n}", z["side"], z["px"], z["px"],
                             np.nan, np.nan, z["comp"], s))
        gts = g.ts_event.dt.tz_convert(None).to_numpy()
        for W, q in ((15, 0.67), (30, 0.67)):
            eps, h, l = episodes_c2(g, W, q)
            for (a, e) in eps:
                if e + 1 >= len(gts):
                    continue
                a0 = max(0, a - W + 1)
                rows.append(("g4_c2", 1, f"W{W}", "", float(l[a0:e+1].min()),
                             float(h[a0:e+1].max()), np.nan, np.nan,
                             gts[e + 1], s))
        if nd % 200 == 0:
            print(f"  {nd} groups done, {len(rows)} objects", flush=True)

    df = pd.DataFrame(rows, columns=["generator", "tf", "param", "dir_side",
                                     "band_lo", "band_hi", "sub_lo", "sub_hi",
                                     "knowable_ts", "session_date"])
    df["object_id"] = np.arange(len(df))
    out = os.path.join(repo, "Data/inputs/s4_objects.parquet")
    df.to_parquet(out)
    print(f"\nEMITTED {len(df)} objects -> {out}")
    print(df.generator.value_counts().to_string())
    return df


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
