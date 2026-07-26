#!/usr/bin/env python3
"""
efficiency_ratio.py  — Test C (price-path geometry, stall-exit vs reach, Design B)
==================================================================================
MECHANISM FAMILY C — KAUFMAN EFFICIENCY RATIO (Perry Kaufman, "Trading Systems and Methods";
the trend/noise core of the Kaufman Adaptive Moving Average). Pure PRICE-PATH geometry: no flow,
no sign, no trade count. ER = |net price change| / sum|step-to-step changes| in [0,1]:
  ER -> 1 : clean, straight, efficient directional move (trending).
  ER -> 0 : choppy back-and-forth that nets nowhere (ranging).

WHY ER NOW: the six prior reads in the exit-local window (sign, sign-memory x2, flow level,
intensity slope, impact) are all null on Design B; the only separating thing (raw activity / net
move) was a higher-energy/volatile-regime gap, NOT a mechanism. ER is SCALE-FREE (a ratio in
[0,1]), so it is NOT confounded by stall windows being busier/more volatile — it isolates path
SHAPE from path SIZE. That is the specific value of this probe given what impact.py showed.

PRE-REGISTERED (frozen before any real number):
  PRIMARY  ER_abs = |mid[end]-mid[start]| / sum|diff(mid_per_second)|   (standard Kaufman, [0,1]).
           Direction (frozen): per-cut AUC = P(reach ER_abs > stall ER_abs) > 0.5  (reaches trend
           efficiently toward target; stalls chop). Two-sided. On discovery we REPORT.
  COMPANION ER_ori = (mid[end]-mid[start])*sgn / sum|diff|   in [-1,1]  (signed: is the efficient
           move WITH the trade? reach expected > stall). Not a 2nd primary.
  HONEST TENSION (not peeked): impact.py showed stalls have MORE net travel (7 vs 3 ticks). If
  stall paths are not proportionally choppier, ER could favor STALLS — the two-sided read catches it.
  ER is direction-agnostic for ER_abs (efficiency is a path property, like Hurst was).

  Logged TRIAL (feeds Deflated-Sharpe N). A positive carries to the Feb holdout, not a candidate here.

FEATURE (frozen formula), per Design-B window [ws, we), on PER-SECOND mid (last (bid+ask)/2 each
second; per-second, NOT per-trade, to suppress bid-ask bounce):
    m = per-second mid series within [ws, we), k points
    net  = m[-1] - m[0]
    path = sum(|diff(m)|)
    ER_abs = |net| / path     (NaN if path == 0: a flat 60s window carries no shape info)
    ER_ori = net * (+1 long / -1 short) / path
  Validity floor: k >= N_MIN_SEC seconds of mid (pre-registered; non-binding, windows span >=35s busy).
  Tripwire: per-second gap > 120s or |mid jump| > 40 ticks -> flag+exclude (same as A/B).

STATISTIC: Design B (frozen) — stall cuts at exit-age tau, reach peers pt1_open_el>tau, W=60s,
  per-cut AUC, cluster bootstrap over 29 cuts (seed 0, 10000), two-sided.

REUSES: read_per_second, S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS (trade_flow_exhaustion);
  designA_perCut, designA_cut_windows, designA_peer_windows_for (horse_race_spine);
  build_arms, W_PRIMARY_S, report_two_sided (sign_persistence).

RUN:
  python3 efficiency_ratio.py --config config.toml --wrb wrb_1m.parquet
  python3 efficiency_ratio.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import read_per_second, S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS
from horse_race_spine import designA_perCut, designA_cut_windows, designA_peer_windows_for
from sign_persistence import build_arms, W_PRIMARY_S, report_two_sided

N_MIN_SEC = 10


# ---------------------------------------------------------------------------
# pure ER math (unit-testable)
# ---------------------------------------------------------------------------
def efficiency_ratio(m, side):
    """m: per-second mid series. Returns (ER_abs, ER_ori, path_ticks). NaN if path==0 or k<2."""
    m = np.asarray(m, float)
    if len(m) < 2:
        return np.nan, np.nan, np.nan
    net = m[-1] - m[0]
    path = float(np.abs(np.diff(m)).sum())
    if path == 0.0:
        return np.nan, np.nan, 0.0
    sgn = 1.0 if side == "long" else -1.0
    return abs(net) / path, (net * sgn) / path, path / TICK


# ---------------------------------------------------------------------------
# windowed extractor (closes over per-second arrays)
# ---------------------------------------------------------------------------
def make_er_features(sec, mid):
    def compute(side, ws, we):
        a = np.searchsorted(sec, np.int64(pd.Timestamp(ws).value // 1_000_000_000), "left")
        b = np.searchsorted(sec, np.int64(pd.Timestamp(we).value // 1_000_000_000), "left")
        s = sec[a:b]; m = mid[a:b]
        k = len(s)
        if k < N_MIN_SEC:
            return None
        flagged = False
        if k >= 2:
            if np.diff(s).max() > MAX_GAP_S:
                flagged = True
            if (np.abs(np.diff(m)) / TICK).max() > ROLL_JUMP_TICKS:
                flagged = True
        era, ero, path = efficiency_ratio(m, side)
        return dict(ER_abs=era, ER_ori=ero, path_tk=path, k=k, flagged=flagged)

    def feat_abs(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if (d["flagged"] or not np.isfinite(d["ER_abs"])) else d["ER_abs"]), **d}

    def feat_ori(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if (d["flagged"] or not np.isfinite(d["ER_ori"])) else d["ER_ori"]), **d}

    return feat_abs, feat_ori, compute


def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    print(f"[arms] stall={len(stall)}  reach={len(reach)}  (expect 29 / 47)")
    W = S(W_PRIMARY_S)
    t_min = min(stall.entry.min() - S(W_PRIMARY_S), reach.entry.min())
    t_max = max(stall.exit.max(), (reach.entry + reach.hold.apply(lambda h: S(h))).max())
    print(f"[read] per-second mid in [{t_min}, {t_max}) from {windowed}")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[read] per-second rows: {len(sec):,}")

    feat_abs, feat_ori, compute = make_er_features(sec, mid)

    print("\n--- diagnostic: path shape per arm ---")
    rows = []
    for w in designA_cut_windows(stall, W):
        d = compute(w["side"], w["ws"], w["we"])
        if d: rows.append({"arm": "stall", **d})
    for _, st in stall.iterrows():
        for w in designA_peer_windows_for(st, reach, W):
            d = compute(w["side"], w["ws"], w["we"])
            if d: rows.append({"arm": "reach", **d})
    df = pd.DataFrame(rows)
    print(f"[diag] tripwire-flagged: {int(df.flagged.sum())} | scored {len(df)} | "
          f"ER NaN: {int((~np.isfinite(df.ER_abs)).sum())}")
    for arm in ("stall", "reach"):
        a = df[(df.arm == arm) & ~df.flagged & np.isfinite(df.ER_abs)]
        print(f"[diag] {arm:5s}: ER_abs med={a.ER_abs.median():.3f} (IQR {a.ER_abs.quantile(.25):.3f}.."
              f"{a.ER_abs.quantile(.75):.3f})  ER_ori med={a.ER_ori.median():+.3f}  "
              f"path med={a.path_tk.median():.1f}tk  sec/win med={a.k.median():.0f}")

    print("\n--- Design B ---")
    report_two_sided("ER_abs [PRIMARY]", designA_perCut(stall, reach, feat_abs, W, seed=seed))
    report_two_sided("ER_ori [comp]", designA_perCut(stall, reach, feat_ori, W, seed=seed))


def selftest(config, wrb):
    print("=== SELF-TEST: Kaufman efficiency ratio (synthetic per-second mid paths) ===")
    cases = [
        ("straight up  [0..5]      ", np.array([0, 1, 2, 3, 4, 5.]), "long", 1.00),
        ("pure chop    [0,1,0,1,0,1]", np.array([0, 1, 0, 1, 0, 1.]), "long", 0.20),
        ("V net-zero   [5,3,1,3,5]  ", np.array([5, 3, 1, 3, 5.]), "long", 0.00),
        ("partial      [0,2,1,3]    ", np.array([0, 2, 1, 3.]), "long", 0.60),
    ]
    for name, m, side, want in cases:
        era, ero, path = efficiency_ratio(m, side)
        ok = abs(era - want) < 1e-9
        print(f"  {name}: ER_abs={era:.3f} (want {want:.2f})  ER_ori={ero:+.3f}  [{'PASS' if ok else 'CHECK'}]")
        assert ok
    # orientation: a clean DOWN move is efficient & WITH-trade for a short (ER_ori>0)
    era, ero, _ = efficiency_ratio(np.array([5, 4, 3, 2, 1.]), "short")
    print(f"  short, clean down [5..1]: ER_abs={era:.3f} ER_ori={ero:+.3f} (ori>0 = with-trade)")
    assert era == 1.0 and ero > 0
    # same down move is adverse for a long (ER_ori<0)
    era, ero, _ = efficiency_ratio(np.array([5, 4, 3, 2, 1.]), "long")
    assert ero < 0
    assert np.isnan(efficiency_ratio(np.array([3, 3, 3, 3.]), "long")[0])  # flat -> NaN
    print("  PASS: ER=1 straight, 0.2 chop, 0 net-zero, 0.6 partial; orientation correct; flat->NaN.")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
