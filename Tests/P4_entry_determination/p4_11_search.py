#!/usr/bin/env python3
"""
p4_11_search.py — P4.11: parameter SEARCH over all rule variables (discovery months).
======================================================================================
REORIENTATION ON RECORD (user, 2026-11-15): the goal is finding what WORKS. The two
discovery months are the search set - optimize freely here; the reserved years
(2021/2023/2024), used sparingly, are what proves or disproves the result. After a
search, discovery-month numbers are optimistic by construction; expected shrinkage
at validation is normal and the rule is judged THERE.

SEARCH SPACE (every rule variable, not only the ATR multiplier):
  C1 event recency:   signal completed within W minutes of a scheduled event,
                      W in {5, 10, 15, 30, 60}
  C2 zone agreement:  the signal's zone overlaps a same-direction zone on
                      {any of 3m/5m | both 3m and 5m | >=2 of 3/5/10/15m | >=3 of 3/5/10/15m}
  C3 body size:       signal body >= m x (prior session's median WRB body),
                      m in {0.75, 1.0, 1.25, 1.5, 2.0}
  C4 tape speed:      ground covered in the last w minutes >= m x (prior session's
                      median w-minute ground), w in {3, 5, 10}, m in {1.0, 1.25, 1.5, 2.0}
  C5 flow:            5-min aggressor flow (signal direction) > t contracts/sec,
                      t in {0, 0.5, 1.0, 2.0}  (unknown flow = condition false)
  C6 template minute: fixed (on); its own internal windows are a later sweep if wanted
  cutoff k:           1..6 conditions required
OBJECTIVE (declared before the run): maximize F1 - the balance of precision (take
rate among flagged signals) and capture (share of his entries flagged) - REQUIRING
per-month lift > 1.0 in BOTH months (no single-month artifacts). Also reported:
best precision at capture >= 20/30/40/50% (the frontier), and v1/v3 for comparison.

RUN: python3 Tests/P4_entry_determination/p4_11_search.py            (repo root)
     python3 Tests/P4_entry_determination/p4_11_search.py --selftest
OUT: p4_11_features.csv, p4_11_top_configs.csv
"""
import argparse, itertools, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS   # noqa: E402
from p4_2b_zone_mtf import zone_tables                # noqa: E402
from p4_9b_score_v3 import overlap_one                # noqa: E402

TICK = 0.25
W_GRID = (5, 10, 15, 30, 60)
C2_GRID = ("any35", "both35", "ge2of4", "ge3of4")
BODY_M = (0.75, 1.0, 1.25, 1.5, 2.0)
PATH_W = (3, 5, 10)
PATH_M = (1.0, 1.25, 1.5, 2.0)
FLOW_T = (0.0, 0.5, 1.0, 2.0)


def f1(prec, rec):
    return 0.0 if (prec + rec) == 0 or np.isnan(prec) else 2 * prec * rec / (prec + rec)


def path_refs(bars_m, w):
    """Per-bar w-minute ground covered (ticks) + per-session prior-session median."""
    tr = (bars_m.high - bars_m.low).rolling(w).sum() / TICK
    sd = bars_m.session_date.astype(str)
    med = tr.groupby(sd).median()
    sessions = sorted(set(sd))
    ref = {s: float(med.get(sessions[i - 1], np.nan))
           for i, s in enumerate(sessions) if i > 0}
    return tr.to_numpy(), ref


def build(repo):
    df = pd.read_csv(os.path.join(HERE, "p4_9b_score_v3.csv"))
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    parts = []
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        bars_m = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
                    (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
        bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
        zt = zone_tables(bars_m, month)
        sm = df[df.month == month].reset_index(drop=True)
        comp_ns = sm.comp_ns.to_numpy(np.int64)
        for tf in (3, 5, 10, 15):
            z = zt[tf][zt[tf].has_whg.fillna(False)]
            sm[f"ov{tf}"] = overlap_one(sm, z, tf, comp_ns)
        sdmap = bars_m.set_index(pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8)[
            "session_date"].astype(str)
        sess = pd.Series(comp_ns - 60_000_000_000).map(sdmap)
        ib = np.searchsorted(bts, comp_ns - 60_000_000_000)
        ok = (ib < len(bts)) & (bts[np.clip(ib, 0, len(bts) - 1)] == comp_ns - 60_000_000_000)
        for w in PATH_W:
            tr, ref = path_refs(bars_m, w)
            sm[f"path{w}"] = np.where(ok, tr[np.clip(ib, 0, len(bts) - 1)], np.nan)
            sm[f"ref_path{w}"] = sess.map(lambda s: ref.get(s, np.nan)).to_numpy()
        parts.append(sm)
    out = pd.concat(parts, ignore_index=True)
    out.to_csv(os.path.join(HERE, "p4_11_features.csv"), index=False)
    return out


def evaluate(df):
    taken = df.taken.to_numpy(bool)
    month = df.month.to_numpy()
    months = sorted(set(month))
    n_taken = int(taken.sum())
    mins = df.mins_since_all.to_numpy(float)
    body = df.body_tk.to_numpy(float); ref_b = df.ref_body_tk.to_numpy(float)
    flow = df.flow_5m.fillna(-9e9).to_numpy(float)
    c6 = df.c6_template.to_numpy(bool)
    ov = {tf: df[f"ov{tf}"].to_numpy(bool) for tf in (3, 5, 10, 15)}
    c2opt = {"any35": ov[3] | ov[5], "both35": ov[3] & ov[5]}
    nov = ov[3].astype(int) + ov[5].astype(int) + ov[10].astype(int) + ov[15].astype(int)
    c2opt["ge2of4"] = nov >= 2; c2opt["ge3of4"] = nov >= 3
    paths = {w: (df[f"path{w}"].to_numpy(float), df[f"ref_path{w}"].to_numpy(float))
             for w in PATH_W}
    rows = []
    for W, c2k, bm, pw, pm, ft in itertools.product(W_GRID, C2_GRID, BODY_M,
                                                    PATH_W, PATH_M, FLOW_T):
        c1 = (mins >= 0) & (mins <= W)
        c3 = body >= bm * ref_b
        p, rp = paths[pw]
        c4 = p >= pm * rp
        c5 = flow > ft
        score = (c1.astype(np.int8) + c2opt[c2k].astype(np.int8) + c3.astype(np.int8)
                 + c4.astype(np.int8) + c5.astype(np.int8) + c6.astype(np.int8))
        for k in range(2, 7):
            fl = score >= k
            nf = int(fl.sum())
            if nf < 30:          # too few flags to trust
                continue
            prec = taken[fl].mean(); rec = taken[fl].sum() / n_taken
            ok_m = True
            for m in months:
                mm = month == m
                b = taken[mm].mean()
                fm = fl & mm
                if not fm.any() or taken[fm].mean() <= b:
                    ok_m = False; break
            rows.append(dict(W=W, c2=c2k, body_m=bm, path_w=pw, path_m=pm,
                             flow_t=ft, k=k, flagged=nf, precision=prec,
                             capture=rec, f1=f1(prec, rec), both_months=ok_m))
    return pd.DataFrame(rows)


def run(repo):
    df = build(repo)
    base = df.taken.mean()
    print(f"signals={len(df)} taken={int(df.taken.sum())} base={base:.1%}")
    res = evaluate(df)
    res.to_csv(os.path.join(HERE, "p4_11_top_configs.csv"), index=False)
    ok = res[res.both_months].sort_values("f1", ascending=False)
    print(f"configs evaluated: {len(res)} ({res[['W','c2','body_m','path_w','path_m','flow_t']].drop_duplicates().shape[0]} parameter sets x cutoffs); "
          f"passing the both-months requirement: {len(ok)}")
    print(f"\n===== top 15 by F1 (balance of precision and capture), both months positive =====")
    cols = ["W", "c2", "body_m", "path_w", "path_m", "flow_t", "k",
            "flagged", "capture", "precision", "f1"]
    with pd.option_context("display.width", 200):
        print(ok.head(15)[cols].to_string(index=False,
              formatters={"capture": "{:.1%}".format, "precision": "{:.1%}".format,
                          "f1": "{:.3f}".format}))
    print("\n===== the frontier: best precision at each capture floor =====")
    for floor in (0.2, 0.3, 0.4, 0.5):
        c = ok[ok.capture >= floor].sort_values("precision", ascending=False)
        if len(c):
            r = c.iloc[0]
            print(f"  capture >= {floor:.0%}: precision {r.precision:.1%} ({r.precision/base:.1f}x) "
                  f"capture {r.capture:.1%} | W={r.W} c2={r.c2} body x{r.body_m} "
                  f"path{int(r.path_w)}m x{r.path_m} flow>{r.flow_t} k={int(r.k)}")
    print(f"\nreference points: v1 k=4 F1=0.262 (P 19.3% / R 40.8%) | v3 k=4 F1=0.244 (P 16.7% / R 45.3%)")
    print("\nREAD: searched on the discovery months BY DESIGN - these numbers are the")
    print("optimistic in-sample view; the frozen winner goes to the reserved years.")


def selftest():
    print("=== SELF-TEST ===")
    assert abs(f1(0.5, 0.5) - 0.5) < 1e-9 and f1(0.0, 1.0) == 0.0
    print("  F1 OK")
    b = pd.DataFrame(dict(high=[10.0, 11, 12, 13], low=[9.0, 10, 11, 12],
                          session_date=["d1", "d1", "d2", "d2"]))
    tr, ref = path_refs(b, 2)
    assert np.isnan(tr[0]) and abs(tr[1] - 8.0) < 1e-9        # (1+1)/0.25
    assert "d2" in ref and "d1" not in ref and abs(ref["d2"] - 8.0) < 1e-9
    print("  path + prior-session reference OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo)
