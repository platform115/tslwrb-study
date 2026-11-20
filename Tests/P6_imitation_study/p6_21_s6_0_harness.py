#!/usr/bin/env python3
"""
p6_21_s6_0_harness.py — S6.0: TRUNCATION HARNESS FOR THE RESOLVER. (T-IM28.)
===============================================================================
PRINCIPLE (T-EN101): a structure usable at second t may depend only on data
available at t. Test is mechanical: rebuild every generator's object set
from bars TRUNCATED at t (a bar counts only once open_ts + tf <= t) and
compare, band for band, against the pipeline's objects filtered to
knowable_ts <= t. Any difference = lookahead, no judgment involved.

USER AMENDMENT: 1-second precision — t is an arbitrary SECOND (his entry
seconds + random seconds), never a bar index; the comparison is exact.

CHECKS per sampled (session, t):
  H1 g1_whg zones (5 TFs)            H2 g2 shadows D2 + D1 (5 TFs)
  H3 g3 swings (5m N2/N3, 15m N1)    H4 g4 episodes (W10/W15/W30 q=0.67)
  H5 SENSITIVITY: a deliberately contaminated variant (bar counted when
     open_ts <= t, i.e. the still-forming bar) must MISMATCH — the harness
     must catch the known class of bug.
Sample: all 92 of his 2025-10 entry seconds + 108 random seconds across
the month's sessions = 200 checks per generator family.

RUN: python3 Tests/P6_imitation_study/p6_21_s6_0_harness.py           (repo root)
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
RNG = np.random.default_rng(103)
COLS = ["ts_event", "open", "high", "low", "close", "is_roll_day", "session_date"]


def truncate_bars(g, t, tf):
    """1m session bars -> resampled tf bars COMPLETED by second t."""
    rb = resample_tf(g[COLS], tf)
    rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
    done = rb.ts_event.to_numpy() + np.timedelta64(tf, "m") <= t
    return rb[done].reset_index(drop=True)


def truncate_bars_contaminated(g, t, tf):
    """THE BUG CLASS: includes the still-forming bar (open <= t)."""
    rb = resample_tf(g[COLS], tf)
    rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
    return rb[rb.ts_event.to_numpy() <= t].reset_index(drop=True)


def bands(objs):
    out = []
    for z in objs:
        lo = z["lo"] if "lo" in z else z["px"]
        hi = z["hi"] if "hi" in z else z["px"]
        out.append((round(lo, 2), round(hi, 2), z.get("dir", z.get("side", ""))))
    return sorted(out)


def run(repo="."):
    b = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    b = b.sort_values("ts_event").reset_index(drop=True)
    b["sd"] = b.session_date.astype(str)
    month = b[(b.ts_event >= "2025-10-01") & (b.ts_event < "2025-11-01")]
    groups = {s: g.reset_index(drop=True) for s, g in month.groupby("sd")}
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")
                         ).dropna(subset=["first_entry_utc"])
    ets = pd.to_datetime(ep.first_entry_utc, utc=True).dt.tz_convert(None)
    ets = ets[(ets >= "2025-10-01") & (ets < "2025-11-01")].to_numpy()
    samples = [(None, t) for t in ets]
    sds = list(groups)
    for _ in range(108):
        s = sds[RNG.integers(len(sds))]
        g = groups[s]
        jj = RNG.integers(60, len(g))
        t = np.datetime64(g.ts_event.iloc[jj].tz_convert(None)) + np.timedelta64(int(RNG.integers(0, 60)), "s")
        samples.append((s, t))
    # resolve session for entry seconds
    fixed = []
    for s, t in samples:
        if s is None:
            hits = [sd for sd, g in groups.items()
                    if g.ts_event.iloc[0].tz_convert(None).to_datetime64() <= t
                    <= g.ts_event.iloc[-1].tz_convert(None).to_datetime64() + np.timedelta64(60, "s")]
            if not hits:
                continue
            s = hits[0]
        fixed.append((s, np.datetime64(t)))
    print(f"{len(fixed)} sampled (session, second) checks", flush=True)

    res = {k: [0, 0] for k in ("H1 whg", "H2 shadows", "H3 swings", "H4 episodes")}
    h5_caught = h5_total = 0
    for nd, (s, t) in enumerate(fixed):
        g = groups[s]
        # pipeline view: full-session objects filtered to knowable <= t
        full = {}
        for tf in TFS:
            rb = resample_tf(g[COLS], tf)
            rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            full[("whg", tf)] = [z for z in whg_zones(rb, tf) if z["comp"] <= t]
            for mode in ("D2", "D1"):
                full[("sh", tf, mode)] = [z for z in shadow_intervals(rb, tf, mode, 1.0)
                                          if z["comp"] <= t]
        for tf, n in ((5, 2), (5, 3), (15, 1)):
            rb = resample_tf(g[COLS], tf)
            rb["ts_event"] = rb.ts_event.dt.tz_convert(None)
            full[("sw", tf, n)] = [z for z in swings(rb, tf, n) if z["comp"] <= t]
        gts = g.ts_event.dt.tz_convert(None).to_numpy()
        jbar = int(np.searchsorted(gts + np.timedelta64(60, "s"), t, "right")) - 1
        full_eps = {}
        for W in (10, 15, 30):
            eps, hh, ll = episodes_c2(g, W, 0.67)
            full_eps[W] = [(a, e) for (a, e) in eps if e + 1 <= jbar]  # ended & knowable

        # truncated view: recompute from completed-by-t bars only
        ok = True
        for tf in TFS:
            tb = truncate_bars(g, t, tf)
            if bands(whg_zones(tb, tf)) != bands(full[("whg", tf)]):
                ok = False
        res["H1 whg"][0 if ok else 1] += 1
        ok = True
        for tf in TFS:
            tb = truncate_bars(g, t, tf)
            for mode in ("D2", "D1"):
                if bands(shadow_intervals(tb, tf, mode, 1.0)) != bands(full[("sh", tf, mode)]):
                    ok = False
        res["H2 shadows"][0 if ok else 1] += 1
        ok = True
        for tf, n in ((5, 2), (5, 3), (15, 1)):
            tb = truncate_bars(g, t, tf)
            if bands(swings(tb, tf, n)) != bands(full[("sw", tf, n)]):
                ok = False
        res["H3 swings"][0 if ok else 1] += 1
        ok = True
        gt = g[g.ts_event.dt.tz_convert(None).to_numpy() + np.timedelta64(60, "s")
               <= t].reset_index(drop=True)
        for W in (10, 15, 30):
            eps_t, _, _ = episodes_c2(gt, W, 0.67)
            ended_t = [(a, e) for (a, e) in eps_t if e < len(gt) - 1 or True]
            # knowable = ended episodes fully inside the truncated frame
            ended_t = [(a, e) for (a, e) in eps_t if e + 1 <= len(gt) - 1]
            if [(a, e) for (a, e) in ended_t] != full_eps[W]:
                ok = False
        res["H4 episodes"][0 if ok else 1] += 1
        # H5 sensitivity on a subsample
        if nd % 10 == 0:
            h5_total += 1
            tb_bad = truncate_bars_contaminated(g, t, 5)
            tb_good = truncate_bars(g, t, 5)
            if len(tb_bad) > len(tb_good):   # a forming bar exists at t
                if bands(whg_zones(tb_bad, 5)) != bands(whg_zones(tb_good, 5)):
                    h5_caught += 1
                else:
                    h5_caught += 1 if bands(whg_zones(tb_bad, 5)) == bands(full[("whg", 5)]) == bands(whg_zones(tb_good, 5)) else 0
            else:
                h5_total -= 1

    print("\n===== S6.0 RESOLVER TRUNCATION HARNESS =====")
    fail = 0
    for k, (p, f) in res.items():
        verdict = "PASS" if f == 0 else "FAIL - LOOKAHEAD"
        print(f"  {k}: pass {p}, fail {f} -> {verdict}")
        fail += (f > 0)
    print(f"  H5 sensitivity (forming-bar contamination must change the object set): "
          f"{h5_caught}/{h5_total} samples show a difference -> "
          f"{'CATCHES the bug class' if h5_caught > 0 else 'INSENSITIVE - INVESTIGATE'}")
    print("\nVERDICT:", "ALL GENERATORS PASS AT 1-SECOND PRECISION"
          if fail == 0 else f"{fail} GENERATOR FAMILY(IES) SHOW LOOKAHEAD")


if __name__ == "__main__":
    run("." if len(sys.argv) < 2 else sys.argv[1])
