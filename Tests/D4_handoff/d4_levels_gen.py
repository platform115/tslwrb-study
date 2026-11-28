#!/usr/bin/env python3
"""
d4_levels_gen.py — D-4: the DAILY LEVEL LIST feed for the Pine port.
Emits ready-to-paste Pine v6 array code for a session-date range.
DERIVES FROM (R-9 lineage): the certified lf level machinery
(g26_remint_gen.py copy, identical to d8_prep.py which passed the
row-identical rebuild control).
CONTROL (runs every time): the generated 2022-05 lists must equal
the committed blind lists (Tests/D8_judgment/blind_levels_2022-05.csv)
exactly. Abort on mismatch.
RUN: python3 Tests/D4_handoff/d4_levels_gen.py 2025-10-01 2025-10-31
  -> prints the Pine block for sessions in [start, end] to stdout.
FORWARD USE: needs Data/inputs/es_1m_front.parquet and s4_objects
to cover [start - 60 sessions, end]. If they do not, the script
says so and stops (the forward-data gap is a known decision point).
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets                   # noqa: E402

GRID = 0.25

b = pd.read_parquet("Data/inputs/es_1m_front.parquet")
b = b.sort_values("ts_event").reset_index(drop=True)
b["sd"] = b.session_date.astype(str)
days_all = sorted(b[~b.is_roll_day].sd.unique())
day_ix = {d: i for i, d in enumerate(days_all)}
closes = b[~b.is_roll_day].groupby("sd").close.last(
    ).reindex(days_all).to_numpy()
ev_all = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9

rows = []
so = pd.read_parquet("Data/inputs/s4_objects.parquet",
                     columns=["generator", "band_lo", "band_hi",
                              "session_date", "knowable_ts"])
so = so[so.generator.isin(["g2_shadow_d2", "g1_whg", "g3_swing"])]
so["sd"] = so.session_date.astype(str)
ks = so.knowable_ts.astype("datetime64[ns]").astype("int64") // 10**9
kk2 = np.searchsorted(ev_all, ks.to_numpy(), "right") - 1
so["newsborn"] = (ks.to_numpy() - ev_all[np.maximum(kk2, 0)]) <= 2700
wrb_day = {}
for tfm, tfs in (("5min", 300), ("15min", 900)):
    for sd, g in b[~b.is_roll_day].groupby("sd"):
        r = g.set_index("ts_event").resample(tfm).agg(
            {"open": "first", "close": "last"}).dropna()
        body = (r.close - r.open).abs().to_numpy()
        pm = pd.Series(body).shift(1).rolling(3).max().to_numpy()
        w_ = body > pm
        comp = (r.index.astype("int64").to_numpy() // 10**9 + tfs)[w_]
        for c_, o, cl_ in zip(comp, r.open.to_numpy()[w_],
                              r.close.to_numpy()[w_]):
            wrb_day.setdefault(sd, []).append(
                (int(c_), float(max(o, cl_))))
            wrb_day.setdefault(sd, []).append(
                (int(c_), float(min(o, cl_))))
for col in ("band_lo", "band_hi"):
    rows.append(so[["sd", col, "newsborn"]].dropna()
                .rename(columns={col: "px"}))
for sd, lst in wrb_day.items():
    rows.append(pd.DataFrame({"sd": sd,
                              "px": [p for _, p in lst],
                              "newsborn": False}))
EV = pd.concat(rows, ignore_index=True)
EV["px"] = (EV.px * 4).round() / 4
EV = EV.drop_duplicates(["sd", "px"])
EV["di"] = EV.sd.map(day_ix); EV = EV.dropna(subset=["di"])
EV["di"] = EV.di.astype(int)
Vpx, Vdi, Vnb = EV.px.to_numpy(), EV.di.to_numpy(), EV.newsborn.to_numpy()


def density_levels(px, di, nb, tol, m):
    if not len(px):
        return []
    gp = np.round(px / GRID).astype(np.int64)
    lo, hi = gp.min(), gp.max()
    width = int(round(tol / GRID))
    order = np.argsort(gp)
    gs, ds, nbs = gp[order], di[order], nb[order]
    uniq = np.arange(lo, hi + 1); score = np.zeros(len(uniq))
    for k, g0 in enumerate(uniq):
        a = np.searchsorted(gs, g0 - width)
        b2 = np.searchsorted(gs, g0 + width, "right")
        if b2 > a:
            score[k] = len(set(ds[a:b2])) + (1.0 if nbs[a:b2].any()
                                             else 0.0)
    out, taken = [], np.zeros(len(uniq), bool)
    for k in np.argsort(-score):
        if score[k] < m or taken[k]:
            continue
        out.append(float(uniq[k] * GRID))
        taken[max(0, k - 2 * width):k + 2 * width + 1] = True
    return out


lv_cache = {}
def lf(di):
    if di not in lv_cache:
        msk = (Vdi >= di - 60) & (Vdi < di)
        out = []
        for p in density_levels(Vpx[msk], Vdi[msk], Vnb[msk], 2.0, 4):
            sel = np.abs(Vpx[msk] - p) <= 2.0
            last_mem = int(Vdi[msk][sel].max())
            cseg = closes[last_mem + 1:di]
            if not (len(cseg) and (np.abs(cseg - p) > 5.0).all()):
                out.append(p)
        lv_cache[di] = out
    return lv_cache[di]


# ---- CONTROL: must reproduce the committed 2022-05 blind lists ----
blind = pd.read_csv("Tests/D8_judgment/blind_levels_2022-05.csv")
for sd, g in blind.groupby("session_date"):
    want = sorted(g.level.tolist())
    got = sorted(lf(day_ix[sd]))
    if want != got:
        print(f"# D4 LEVELS ABORTED - CONTROL FAILED on {sd}")
        sys.exit(1)
print("// CONTROL PASS: 2022-05 committed blind lists reproduced "
      "exactly", file=sys.stderr)

# ---- emit the Pine block for the requested range ----
if len(sys.argv) != 3:
    print("usage: d4_levels_gen.py YYYY-MM-DD YYYY-MM-DD",
          file=sys.stderr)
    sys.exit(2)
lo, hi = sys.argv[1], sys.argv[2]
sds = [d for d in days_all if lo <= d <= hi]
if not sds:
    print("# no sessions in range (or data does not cover it - "
          "the forward-data gap)", file=sys.stderr)
    sys.exit(2)
dates, starts, flat = [], [], []
for sd in sds:
    starts.append(len(flat))
    dates.append(sd.replace("-", ""))
    flat.extend(lf(day_ix[sd]))
starts.append(len(flat))
print("// ==== D4 LEVEL LIST (generated %s..%s; paste whole block,"
      " never edit) ====" % (lo, hi))
print("var int[]   d4_lvl_dates = array.from(%s)"
      % ", ".join(dates))
print("var int[]   d4_lvl_start = array.from(%s)"
      % ", ".join(str(s) for s in starts))
print("var float[] d4_lvl_px    = array.from(%s)"
      % ", ".join(f"{p:.2f}" for p in flat))
print("// lookup: for session date D (yyyymmdd int), its levels are"
      " d4_lvl_px[start[i] .. start[i+1]-1] where"
      " d4_lvl_dates[i] == D")
