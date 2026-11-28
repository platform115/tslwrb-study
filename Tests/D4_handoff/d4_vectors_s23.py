#!/usr/bin/env python3
"""
d4_vectors_s23.py — D-4: STRUCTURE VECTORS IN THE TRADINGVIEW
OVERLAP WINDOW (S2/S3 gates after the 1m-history discovery:
TradingView's 1m chart reaches back only to 2025-11-27, so the
October vectors are unreachable there; these replace them for
S2/S3 ONLY, minted from data already held - no purchase).
Sessions (picked by structure activity, April-May 2026 = no roll
weeks, no quarantined months, latest in the rolling window):
  2026-05-07 (sparse), 2026-05-15 (median), 2026-04-06 (busy).
  (2026-04-03 was the raw sparsest but is Good Friday - a short
  holiday session; excluded to keep the bar comparison free of
  feed-calendar noise. Full 1380-bar sessions only.)
DERIVES FROM (R-9 lineage): the v_structure machinery verbatim
from d4_vectors.py.
CONTROL (abort on miss): before minting anything new, the script
rebuilds v_structure_2025-10-15 and asserts byte-identical CSV
content vs the committed vector.
S4-S6 are NOT served by these: per the hybrid decision they verify
on fresh 1s-window vectors after the S4-gate data sliver.
RUN: python3 Tests/D4_handoff/d4_vectors_s23.py          (repo root)
OUT: Tests/D4_handoff/vectors/v_structure_<sd>.csv (3 new sessions)
"""
import io, os, sys
import numpy as np
import pandas as pd

for d in ("Tests/P6_imitation_study", "Tests/P4_entry_determination"):
    sys.path.insert(0, d)
from p6_22_s6_1_presence import Resolver                     # noqa: E402

CONTROL_SD = "2025-10-15"
TARGETS = ["2026-05-07", "2026-04-06", "2026-05-15"]
OUTD = "Tests/D4_handoff/vectors"

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
zr = pd.read_parquet("Data/inputs/his_zone_refs.parquet")


def band_arrays(g, W, q):
    h = g.high.to_numpy(); l = g.low.to_numpy(); n = len(h)
    hs = pd.Series(h).rolling(W).max().to_numpy()
    ls = pd.Series(l).rolling(W).min().to_numpy()
    rng_w = hs - ls
    med = pd.Series(rng_w).shift(1).rolling(60, min_periods=10
                                            ).median().to_numpy()
    active = np.isfinite(rng_w) & np.isfinite(med) & (rng_w <= q * med)
    blo = np.full(n, np.nan); bhi = np.full(n, np.nan)
    run_lo = run_hi = np.nan; in_run = False
    cur_lo = cur_hi = np.nan
    for i in range(n):
        if active[i]:
            s0 = max(0, i - W + 1)
            if not in_run:
                run_lo, run_hi = l[s0:i + 1].min(), h[s0:i + 1].max()
                in_run = True
            else:
                run_lo = min(run_lo, l[i]); run_hi = max(run_hi, h[i])
            cur_lo, cur_hi = run_lo, run_hi
        else:
            in_run = False
        blo[i], bhi[i] = cur_lo, cur_hi
    return blo, bhi


def structure_csv(sd):
    """Verbatim v_structure recording from d4_vectors.py."""
    mo = sd[:7]
    nxt = (pd.Timestamp(mo + "-01") + pd.offsets.MonthBegin(1)
           ).strftime("%Y-%m-%d")
    bm = b[(b.ts_event >= f"{mo}-01") & (b.ts_event < nxt)
           ].reset_index(drop=True)
    R = Resolver(bm, zr)
    g = bm[bm.sd == sd].reset_index(drop=True)
    blo, bhi = band_arrays(g, 20, 0.8)
    rows_s = []
    gts = g.ts_event.dt.tz_convert("America/Chicago")
    for i in range(len(g)):
        t_know = int(g.ts_event.dt.tz_convert(None)
                     .astype("int64").iloc[i] // 10**9) + 120
        sq = {}
        for fam, w in (("sqz10", 10), ("sqz30", 30)):
            eps = [z for z in R._objs(sd, fam)
                   if z["comp"] <= np.datetime64(t_know, "s")]
            if eps:
                z = max(eps, key=lambda q: q["comp"])
                sq[f"{fam}_lo"], sq[f"{fam}_hi"] = z["lo"], z["hi"]
            else:
                sq[f"{fam}_lo"] = sq[f"{fam}_hi"] = None
        rows_s.append(dict(bar_ct=gts.iloc[i].strftime(
            "%Y-%m-%d %H:%M"), w20_lo=round(float(blo[i]), 2)
            if np.isfinite(blo[i]) else None,
            w20_hi=round(float(bhi[i]), 2)
            if np.isfinite(bhi[i]) else None, **sq))
    buf = io.StringIO()
    pd.DataFrame(rows_s).to_csv(buf, index=False)
    return buf.getvalue()


# ---- CONTROL: byte-identical rebuild of the committed October file
want = open(f"{OUTD}/v_structure_{CONTROL_SD}.csv").read()
got = structure_csv(CONTROL_SD)
if want != got:
    print(f"# D4 S23 VECTORS ABORTED - CONTROL FAILED: rebuilt "
          f"v_structure_{CONTROL_SD} differs from the committed file")
    sys.exit(1)
print(f"CONTROL PASS: v_structure_{CONTROL_SD} rebuilt "
      "byte-identical")

for sd in TARGETS:
    out = f"{OUTD}/v_structure_{sd}.csv"
    open(out, "w").write(structure_csv(sd))
    n = sum(1 for _ in open(out)) - 1
    print(f"minted {out} ({n} rows)")
print("D4 S23 VECTORS DONE")
