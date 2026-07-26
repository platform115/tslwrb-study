#!/usr/bin/env python3
"""
intensity.py  — Test B (arrival-intensity: stall-exit vs reach-at-matched-age, Design B)
========================================================================================
MECHANISM FAMILY B — TRADE-ARRIVAL INTENSITY. Event-timing only: NO sign, NO size (so it is
genuinely distinct from the three flow-derived A-channel nulls: sign / level-of-flow / sign-memory).
Reduced-form observable of a self-exciting (Hawkes) arrival process — we measure the RATE and its
within-window TREND, NOT a fitted Hawkes kernel (per-trade kernel fitting at this n would overfit;
HANDOFF guidance). References: Hawkes (1971) self-exciting point processes; effort-vs-result is the
practitioner framing (Wyckoff) — measurable content is the rate/slope below, not the vocabulary.

TWO FEATURES, DIFFERENT EPISTEMIC STATUS:
  LEVEL = trades per second over the window.
     ** PEEKED **: Test A's diagnostic already showed stalls busier at matched age (1356 vs 796
     prints/window). So LEVEL's direction is known going in. The in-sample AUC here is DESCRIPTIVE
     QUANTIFICATION, NOT a discovery — capped at a HOLDOUT hypothesis regardless of CI. Reported
     two-sided. Pre-registered (peeked) direction: stall > reach (effort-vs-result: churn, no progress).
  SLOPE = within-window trend of the per-second rate, normalized to the window's mean rate
     (fractional change/sec). ** CLEAN / UNSEEN **: the within-window trend was never observed.
     PRIMARY discovery statistic. Pre-registered direction (frozen before any number):
        reach > stall  (reaches: rate stable/rising = move developing; stalls: rate decaying =
        move dying out under churn).  per-cut AUC = P(reach slope > stall slope), two-sided.

INTERPRETIVE CAVEATS (frozen, read before trusting SLOPE):
  - Endpoint asymmetry: the STALL window ends at his actual EXIT (an event); the REACH window ends
    at an arbitrary matched age. Activity often clusters around any decision/event, so a stall-slope
    effect may reflect "activity changes near an exit" rather than "stalls specifically decay."
    Exit-anchored design cannot fully separate these — report, do not over-claim.
  - A spike INTO his exit would show as stall slope > 0 (rising), REVERSING the pre-registered
    direction. Two-sided reporting will catch that; it is itself an interesting finding if it occurs.
  - SLOPE is level-normalized, so the peeked LEVEL difference does not mechanically drive it.

FEATURE (frozen formulas), per Design-B window [ws, we), span k = (we-ws) seconds:
    n      = trade prints in window (action=="T")
    LEVEL  = n / span_s                                   # trades/sec
    counts = per-second trade counts, c_0..c_{k-1} (bincount of floor((t-ws)/1s))
    SLOPE  = ( Cov(sec_index, counts) / Var(sec_index) ) / mean(counts)   # fractional rate change/sec
             (requires k>=2 and mean(counts)>0 else NaN)
  Validity floor: n >= N_MIN_INT and span_s >= MIN_SPAN_S (both pre-registered; non-binding here —
    diagnostic showed min n=101, min span 35s).
  Tripwire: gap>120s or |mid jump|>40 ticks -> flag+exclude (same as A).

STATISTIC: Design B (frozen) — stall cuts at exit-age tau, reach peers pt1_open_el>tau, W=60s,
  per-cut AUC, cluster bootstrap over 29 cuts (seed 0, 10000), two-sided.

REUSES: read_trade_signs, build_arms, W_PRIMARY_S, report_two_sided (sign_persistence);
  designA_perCut (horse_race_spine); S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS (trade_flow_exhaustion).

RUN:
  python3 intensity.py --config config.toml --wrb wrb_1m.parquet
  python3 intensity.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS
from horse_race_spine import designA_perCut, designA_cut_windows, designA_peer_windows_for
from sign_persistence import read_trade_signs, build_arms, W_PRIMARY_S, report_two_sided

N_MIN_INT = 10
MIN_SPAN_S = 10.0


# ---------------------------------------------------------------------------
# pure slope math (unit-testable)
# ---------------------------------------------------------------------------
def norm_slope(counts):
    """Fractional change in per-second rate per second = OLS slope / mean. NaN if undefined."""
    counts = np.asarray(counts, float)
    k = len(counts)
    if k < 2:
        return np.nan
    mu = counts.mean()
    if mu <= 0:
        return np.nan
    x = np.arange(k, dtype=float)
    vx = x.var()
    if vx == 0:
        return np.nan
    slope = np.cov(x, counts)[0, 1] / vx
    return float(slope / mu)


# ---------------------------------------------------------------------------
# windowed extractor (closes over per-trade arrays; uses ts + mid only)
# ---------------------------------------------------------------------------
def make_intensity_features(ts_ns, mid):
    def compute(side, ws, we):
        ws_ns = np.int64(pd.Timestamp(ws).value); we_ns = np.int64(pd.Timestamp(we).value)
        a = np.searchsorted(ts_ns, ws_ns, "left")
        b = np.searchsorted(ts_ns, we_ns, "left")
        t = ts_ns[a:b]; mz = mid[a:b]
        n = len(t)
        span_s = (we_ns - ws_ns) / 1e9
        if n < N_MIN_INT or span_s < MIN_SPAN_S:
            return None
        flagged = False
        if n >= 2:
            if (np.diff(t) / 1e9).max() > MAX_GAP_S:
                flagged = True
            if (np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS:
                flagged = True
        level = n / span_s
        k = int(np.ceil(span_s))
        sec_idx = np.minimum(((t - ws_ns) // 1_000_000_000).astype(int), k - 1)
        counts = np.bincount(sec_idx, minlength=k).astype(float)
        slope = norm_slope(counts)
        return dict(level=level, slope=slope, n=n, span_s=span_s, flagged=flagged)

    def feat_level(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if d["flagged"] else d["level"]), **d}

    def feat_slope(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if (d["flagged"] or not np.isfinite(d["slope"])) else d["slope"]), **d}

    return feat_level, feat_slope, compute


def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    print(f"[arms] stall={len(stall)}  reach={len(reach)}  (expect 29 / 47)")
    W = S(W_PRIMARY_S)
    t_min = min(stall.entry.min() - S(W_PRIMARY_S), reach.entry.min())
    t_max = max(stall.exit.max(), (reach.entry + reach.hold.apply(lambda h: S(h))).max())
    print(f"[read] trade signs in [{t_min}, {t_max}) from {windowed}")
    ts_ns, rs, mid = read_trade_signs(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")

    feat_level, feat_slope, compute = make_intensity_features(ts_ns, mid)

    print("\n--- diagnostic: per-arm level + slope spread (validity) ---")
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
          f"slope NaN: {int((~np.isfinite(df.slope)).sum())}")
    for arm in ("stall", "reach"):
        a = df[(df.arm == arm) & ~df.flagged]
        print(f"[diag] {arm:5s}: level/sec med={a.level.median():.2f}  "
              f"slope med={a.slope.median():+.4f} (IQR {a.slope.quantile(.25):+.4f}..{a.slope.quantile(.75):+.4f})")

    print("\n--- Design B ---")
    print("  [LEVEL is PEEKED -> descriptive/holdout-only, not a discovery result]")
    report_two_sided("intensity LEVEL", designA_perCut(stall, reach, feat_level, W, seed=seed))
    print("  [SLOPE is the CLEAN discovery test]")
    report_two_sided("intensity SLOPE [PRIMARY]", designA_perCut(stall, reach, feat_slope, W, seed=seed))


def selftest(config, wrb):
    print("=== SELF-TEST: normalized intensity slope (synthetic per-second counts) ===")
    cases = [
        ("rising  [1,2,3,4,5,6]", np.array([1, 2, 3, 4, 5, 6.]), +1),
        ("decaying[6,5,4,3,2,1]", np.array([6, 5, 4, 3, 2, 1.]), -1),
        ("flat    [3,3,3,3,3,3]", np.array([3, 3, 3, 3, 3, 3.]), 0),
    ]
    for name, c, sgn in cases:
        s = norm_slope(c)
        ok = (sgn > 0 and s > 0.05) or (sgn < 0 and s < -0.05) or (sgn == 0 and abs(s) < 1e-9)
        print(f"  {name}: slope={s:+.4f}  [{'PASS' if ok else 'CHECK'}]")
        assert ok
    assert np.isnan(norm_slope(np.array([5.])))         # k<2 -> NaN
    assert np.isnan(norm_slope(np.array([0., 0., 0.])))  # mean 0 -> NaN
    print("  PASS: slope +/- with rate trend, 0 for flat, NaN for degenerate.")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
