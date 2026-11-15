#!/usr/bin/env python3
"""
p4_12_variants_search.py — P4.12: same-day (trailing) size references + extended search.
=========================================================================================
USER (2026-11-15): define "big bar" and "fast tape" against references from the
CURRENT day's tape before the signal — pre-session (overnight) bars are fine, no
session anchoring. All references are trailing windows ending just before the signal:

  BIG BAR variants (body in ticks vs):
    prev      m x prior session's median WRB body            (the v4 incumbent)
    twrb      m x median body of the LAST 20 WRBs completed  (trailing, crosses sessions)
    tbar      m x mean bar range of the trailing 120 bars    (trailing 2 hours)
    rank30/60 body is the largest of the last 30 / 60 bars   (rank-based, no multiplier)
  FAST TAPE variants (w-minute ground covered vs), w in {3,5,10}:
    prev      m x prior session's median w-minute ground      (incumbent)
    tmed      m x median w-minute ground of the trailing 120 bars
    rank      current w-minute ground is the largest of the last 60 bars
Multipliers m in {0.75, 1.0, 1.25, 1.5, 2.0} (body) / {1.0, 1.25, 1.5, 2.0} (tape).
Other dimensions as in p4_11 (event window, zone form, flow threshold, cutoff).
Objective unchanged and declared: max F1, >=30 flagged. Search set = discovery
months by design; reserved years judge. Also writes the WIDE per-signal feature
table (continuous ratios included) used by p4_13 (tree) and p4_14 (clusters).

RUN: python3 Tests/P4_entry_determination/p4_12_variants_search.py            (repo root)
     python3 Tests/P4_entry_determination/p4_12_variants_search.py --selftest
OUT: p4_12_features.csv, p4_12_top_configs.csv
"""
import argparse, itertools, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS   # noqa: E402
from p4_11_search import f1                           # noqa: E402

TICK = 0.25
BODY_M = (0.75, 1.0, 1.25, 1.5, 2.0)
PATH_M = (1.0, 1.25, 1.5, 2.0)
PATH_W = (3, 5, 10)
W_GRID = (5, 10, 15, 30, 60)
C2_GRID = ("any35", "both35", "ge2of4", "ge3of4")
FLOW_T = (0.0, 0.5, 1.0, 2.0)
TRAIL_BARS = 120
TRAIL_WRBS = 20


def trailing_refs(bars_m, wrb_m, comp_ns):
    """Per-signal trailing references (no session anchoring; overnight bars count):
    twrb_med (median body of last TRAIL_WRBS WRBs), tbar_mean (mean range of last
    TRAIL_BARS bars), tmed_path{w} (median rolling-w ground of last TRAIL_BARS bars),
    maxbody30/60 (largest body among the prior 30/60 bars), maxpath60_{w}."""
    bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
    rng = (bars_m.high - bars_m.low) / TICK
    body = (bars_m.close - bars_m.open).abs() / TICK
    tbar = rng.rolling(TRAIL_BARS).mean().shift(1).to_numpy()
    mx30 = body.rolling(30).max().shift(1).to_numpy()
    mx60 = body.rolling(60).max().shift(1).to_numpy()
    wts = pd.DatetimeIndex(wrb_m.ts_event).as_unit("ns").asi8 + 60_000_000_000
    wbody = ((wrb_m.close - wrb_m.open).abs() / TICK).to_numpy()
    out = {k: np.full(len(comp_ns), np.nan) for k in
           ["twrb_med", "tbar_mean", "maxbody30", "maxbody60"]}
    paths = {}
    for w in PATH_W:
        tr = rng.rolling(w).sum()
        paths[w] = (tr.to_numpy(),
                    tr.rolling(TRAIL_BARS).median().shift(1).to_numpy(),
                    tr.rolling(60).max().shift(1).to_numpy())
        out[f"tmed_path{w}"] = np.full(len(comp_ns), np.nan)
        out[f"maxpath60_{w}"] = np.full(len(comp_ns), np.nan)
    ib = np.searchsorted(bts, comp_ns - 60_000_000_000)
    ok = (ib < len(bts)) & (bts[np.clip(ib, 0, len(bts) - 1)] == comp_ns - 60_000_000_000)
    for i, cns in enumerate(comp_ns):
        if not ok[i]:
            continue
        j = ib[i]
        out["tbar_mean"][i] = tbar[j]
        out["maxbody30"][i] = mx30[j]
        out["maxbody60"][i] = mx60[j]
        for w in PATH_W:
            out[f"tmed_path{w}"][i] = paths[w][1][j]
            out[f"maxpath60_{w}"][i] = paths[w][2][j]
        k = int(np.searchsorted(wts, cns)) - 1          # last WRB completed BEFORE this signal
        if k + 1 >= TRAIL_WRBS:
            out["twrb_med"][i] = float(np.median(wbody[k - TRAIL_WRBS + 1:k + 1]))
    return out


def build(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_11_features.csv"))
    f6 = pd.read_csv(os.path.join(HERE, "p4_6_signal_features.csv"))
    f7 = pd.read_csv(os.path.join(HERE, "p4_7_trailing_flow.csv"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    df = df.merge(f6[["comp_ns", "en05_tf1_edge_tk", "en08_vwap_z", "en08_net_5m_tk",
                      "tf1_has_react"]], on="comp_ns", how="left")
    parts = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        wrb_m = wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m")].sort_values("ts_event")
        sm = df[df.month == month].reset_index(drop=True)
        comp_ns = sm.comp_ns.to_numpy(np.int64)
        for k, v in trailing_refs(bars_m, wrb_m, comp_ns).items():
            sm[k] = v
        b = f7[f7.month == month].reset_index(drop=True)
        assert len(b) == len(sm) and (b.taken.to_numpy() == sm.taken.to_numpy()).all()
        sm["flow_15m"] = b.flow_15m.to_numpy()
        parts.append(sm)
    out = pd.concat(parts, ignore_index=True)
    # continuous ratios for the tree/clusters
    out["body_r_prev"] = out.body_tk / out.ref_body_tk
    out["body_r_twrb"] = out.body_tk / out.twrb_med
    out["body_r_tbar"] = out.body_tk / out.tbar_mean
    for w in PATH_W:
        out[f"path{w}_r_prev"] = out[f"path{w}"] / out[f"ref_path{w}"]
        out[f"path{w}_r_tmed"] = out[f"path{w}"] / out[f"tmed_path{w}"]
    out.to_csv(os.path.join(HERE, "p4_12_features.csv"), index=False)
    return out


def evaluate(df):
    taken = df.taken.to_numpy(bool); n_taken = int(taken.sum())
    mins = df.mins_since_all.to_numpy(float)
    flow = df.flow_5m.fillna(-9e9).to_numpy(float)
    c6 = df.c6_template.to_numpy(bool)
    ov = {tf: df[f"ov{tf}"].to_numpy(bool) for tf in (3, 5, 10, 15)}
    nov = sum(ov[t].astype(int) for t in ov)
    c2opt = {"any35": ov[3] | ov[5], "both35": ov[3] & ov[5],
             "ge2of4": nov >= 2, "ge3of4": nov >= 3}
    body = df.body_tk.to_numpy(float)
    body_opts = {}
    for name, ref in [("prev", df.ref_body_tk), ("twrb", df.twrb_med), ("tbar", df.tbar_mean)]:
        r = ref.to_numpy(float)
        for m in BODY_M:
            body_opts[f"{name}_x{m}"] = body >= m * r
    body_opts["rank30"] = body >= df.maxbody30.to_numpy(float)
    body_opts["rank60"] = body >= df.maxbody60.to_numpy(float)
    path_opts = {}
    for w in PATH_W:
        p = df[f"path{w}"].to_numpy(float)
        for name, ref in [("prev", df[f"ref_path{w}"]), ("tmed", df[f"tmed_path{w}"])]:
            r = ref.to_numpy(float)
            for m in PATH_M:
                path_opts[f"{name}{w}_x{m}"] = p >= m * r
        path_opts[f"rank{w}"] = p >= df[f"maxpath60_{w}"].to_numpy(float)
    flow_opts = {f">{t}": flow > t for t in FLOW_T}
    c1_opts = {W: (mins >= 0) & (mins <= W) for W in W_GRID}
    rows = []
    for (W, c1), (c2k, c2v), (bk, bv), (pk, pv), (fk, fv) in itertools.product(
            c1_opts.items(), c2opt.items(), body_opts.items(),
            path_opts.items(), flow_opts.items()):
        score = (c1.astype(np.int8) + c2v.astype(np.int8) + bv.astype(np.int8)
                 + pv.astype(np.int8) + fv.astype(np.int8) + c6.astype(np.int8))
        for k in range(2, 7):
            fl = score >= k
            nf = int(fl.sum())
            if nf < 30:
                continue
            prec = taken[fl].mean(); rec = taken[fl].sum() / n_taken
            rows.append(dict(W=W, c2=c2k, body=bk, path=pk, flow=fk, k=k,
                             flagged=nf, precision=prec, capture=rec,
                             f1=f1(prec, rec)))
    return pd.DataFrame(rows)


def run(repo):
    df = build(repo)
    base = df.taken.mean()
    print(f"signals={len(df)} taken={int(df.taken.sum())} base={base:.1%}")
    res = evaluate(df)
    res.to_csv(os.path.join(HERE, "p4_12_top_configs.csv"), index=False)
    ok = res.sort_values("f1", ascending=False)
    nsets = res[["W", "c2", "body", "path", "flow"]].drop_duplicates().shape[0]
    print(f"configs evaluated: {len(res)} rows ({nsets} parameter sets x cutoffs)")
    print("\n===== top 15 by F1 (same declared objective as p4_11) =====")
    cols = ["W", "c2", "body", "path", "flow", "k", "flagged", "capture", "precision", "f1"]
    print(ok.head(15)[cols].to_string(index=False,
          formatters={"capture": "{:.1%}".format, "precision": "{:.1%}".format,
                      "f1": "{:.3f}".format}))
    print("\n===== best per big-bar reference family (is any same-day variant better?) =====")
    ok2 = ok.copy(); ok2["bfam"] = ok2.body.str.split("_").str[0]
    for fam, g in ok2.groupby("bfam"):
        r = g.iloc[0]
        print(f"  {fam:7s}: best F1 {r.f1:.3f} (P {r.precision:.1%} / R {r.capture:.1%})"
              f"  [{r.body}, {r.path}, W={r.W}, flow{r.flow}, k={int(r.k)}]")
    print("\n===== frontier =====")
    for floor in (0.2, 0.3, 0.4, 0.5):
        c = ok[ok.capture >= floor].sort_values("precision", ascending=False)
        if len(c):
            r = c.iloc[0]
            print(f"  capture >= {floor:.0%}: precision {r.precision:.1%} ({r.precision/base:.1f}x)"
                  f" at {r.capture:.1%} | body={r.body} path={r.path} W={r.W} flow{r.flow} k={int(r.k)}")
    print(f"\nreference: p4_11 best F1 0.266 (prev-session references only)")
    print("READ: search set by design; reserved years judge the winner.")


def selftest():
    print("=== SELF-TEST ===")
    ts = pd.date_range("2025-10-06 10:00", periods=200, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, close=5000.5,
                             high=5001.0, low=5000.0))
    wrb = pd.DataFrame(dict(ts_event=ts[:25], open=5000.0, close=[5001.0 + i * 0.25 for i in range(25)]))
    comp = np.array([ts[150].value + 60_000_000_000], dtype=np.int64)
    # signal bar = index 151 (bar open ts[151]) -> comp = ts[151]+60s? use ts[150]+60 = ts[151] open ... compute:
    comp = np.array([pd.Timestamp(ts[151]).value + 60_000_000_000], dtype=np.int64)
    r = trailing_refs(bars, wrb, comp)
    assert abs(r["tbar_mean"][0] - 4.0) < 1e-9           # every bar range = 1.0 pt = 4 tk
    assert np.isfinite(r["twrb_med"][0])                 # 25 WRBs before -> median of last 20
    exp = np.median([abs(5001.0 + i * 0.25 - 5000.0) / TICK for i in range(5, 25)])
    assert abs(r["twrb_med"][0] - exp) < 1e-9, (r["twrb_med"][0], exp)
    assert abs(r["maxbody30"][0] - 2.0) < 1e-9           # all bodies 0.5 pt = 2 tk
    print("  trailing references OK (bar mean, last-20-WRB median, 30-bar max)")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
