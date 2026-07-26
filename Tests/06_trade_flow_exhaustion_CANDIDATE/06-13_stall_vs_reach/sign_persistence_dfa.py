#!/usr/bin/env python3
"""
sign_persistence_dfa.py  — Test A, TRIAL 2 (faithful long-memory estimator)
===========================================================================
WHY THIS EXISTS: Test A trial 1 (sign_persistence.py, lag-1 oriented autocorrelation `rho1`) was
NULL on Design B (per-cut AUC 0.542, CI [0.426,0.657]). lag-1 only probes the shortest horizon;
the DOCUMENTED Lillo & Farmer (2004) mechanism is the SLOW POWER-LAW DECAY of the sign ACF across
many lags, C(l) ~ l^-gamma, gamma<1  <=>  Hurst H = 1 - gamma/2 > 0.5. The faithful estimator of H
is DFA (Peng et al. 1994, "Mosaic organization of DNA nucleotides"; standard for sign-series long
memory). Windows here carry ~100-2700 prints, so DFA is well-powered per window (the HANDOFF
"don't fit Hurst" warning was about n=16 TRADES, not per-window prints).

TRIAL DISCIPLINE: this is the SAME 29 cuts as trial 1. It is a 2nd operationalization of ONE idea
(sign-memory), logged as its own registry trial (feeds the Deflated-Sharpe N). A positive here is
NOT a fresh discovery — it is one of two reads of the same hypothesis and must go to the Feb holdout.

PRE-REGISTERED (frozen before any real number):
  PRIMARY = H (Hurst via DFA-1) of the trade-sign series within each Design-B window.
  Direction (frozen): per-cut AUC = P(reach H > stall H) > 0.5  (reaches = more clustered/persistent
  order flow; stalls = more random). Reported TWO-SIDED. On discovery we REPORT, not declare.
  NOTE: H is invariant to global sign flip -> direction-agnostic (faithful: long memory is a
  property of the sign series itself, not of with-trade orientation). We compute on RAW signs.

FEATURE (frozen formula):
  Trade prints only (action=="T"), raw_sign = +1 (side B) / -1 (side A). x = raw_sign series in
  event order within [ws, we).  DFA-1:
    profile  y = cumsum(x - mean(x))
    scales   log-spaced ints in [MIN_SCALE, n//4], >=4 distinct scales required
    for each scale s: split y into floor(n/s) non-overlapping segments; linear-detrend each;
                      F(s) = rms over segments of the per-segment rms residual
    H = OLS slope of log F(s) on log s
  Validity floor: n >= N_MIN_DFA trade prints (need room for >=4 scales). N_MIN_DFA=50
    (pre-registered; diagnostic confirms it excludes 0 windows since min n was 101).
  Tripwire: same as trial 1 (gap>120s or |mid jump|>40 ticks -> flag+exclude).
  Companion carried for continuity: lag-1 `rho1` from trial 1 (expected ~null, side-by-side only).

STATISTIC: Design B (frozen) — stall cuts at exit-age tau, reach peers pt1_open_el>tau, W=60s,
  per-cut AUC P(reach>stall), cluster bootstrap over 29 cuts (seed 0, 10000), two-sided.

REUSES (imported, not re-implemented): read_trade_signs, build_arms, W_PRIMARY_S, N_MIN,
  make_feature_fns (for the rho1 continuity line) from sign_persistence; designA_perCut,
  cluster_boot_ci from horse_race_spine; S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS from trade_flow_exhaustion.

RUN:
  python3 sign_persistence_dfa.py --config config.toml --wrb wrb_1m.parquet
  python3 sign_persistence_dfa.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS
from horse_race_spine import designA_perCut, cluster_boot_ci
from sign_persistence import (
    read_trade_signs, build_arms, make_feature_fns, W_PRIMARY_S,
    report_two_sided, diagnostic_pass,
)

N_MIN_DFA = 50
MIN_SCALE = 4


# ---------------------------------------------------------------------------
# DFA-1 Hurst (pure; unit-testable)
# ---------------------------------------------------------------------------
def dfa_hurst(x, min_scale=MIN_SCALE, n_scales=14):
    x = np.asarray(x, float)
    n = len(x)
    if n < 4 * min_scale:
        return np.nan
    y = np.cumsum(x - x.mean())               # integrated profile
    max_scale = n // 4
    if max_scale < min_scale * 2:
        return np.nan
    scales = np.unique(np.floor(
        np.logspace(np.log10(min_scale), np.log10(max_scale), n_scales)).astype(int))
    scales = scales[scales >= min_scale]
    if len(scales) < 4:
        return np.nan
    F = []
    for s in scales:
        nseg = n // s
        if nseg < 1:
            F.append(np.nan); continue
        t = np.arange(s)
        resid_sq = []
        for v in range(nseg):
            seg = y[v * s:(v + 1) * s]
            c = np.polyfit(t, seg, 1)
            resid_sq.append(np.mean((seg - np.polyval(c, t)) ** 2))
        F.append(np.sqrt(np.mean(resid_sq)))
    F = np.asarray(F)
    good = np.isfinite(F) & (F > 0)
    if good.sum() < 4:
        return np.nan
    return float(np.polyfit(np.log(scales[good]), np.log(F[good]), 1)[0])


# ---------------------------------------------------------------------------
# Windowed Hurst feature (closes over per-trade arrays)
# ---------------------------------------------------------------------------
def make_hurst_feature(ts_ns, raw_sign, mid):
    def compute(side, ws, we):
        a = np.searchsorted(ts_ns, np.int64(pd.Timestamp(ws).value), "left")
        b = np.searchsorted(ts_ns, np.int64(pd.Timestamp(we).value), "left")
        t = ts_ns[a:b]; rs = raw_sign[a:b]; mz = mid[a:b]
        n = len(t)
        if n < N_MIN_DFA:
            return None
        flagged = False
        if n >= 2:
            if (np.diff(t) / 1e9).max() > MAX_GAP_S:
                flagged = True
            if (np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS:
                flagged = True
        H = dfa_hurst(rs.astype(float))         # direction-agnostic: raw signs
        return dict(H=H, n=n, mean_oriented=float((rs.astype(float) *
                    (1.0 if side == "long" else -1.0)).mean()), flagged=flagged)

    def feat_H(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if (d["flagged"] or not np.isfinite(d["H"])) else d["H"]), **d}

    return feat_H, compute


# ---------------------------------------------------------------------------
def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    print(f"[arms] stall={len(stall)}  reach={len(reach)}  (expect 29 / 47)")
    W = S(W_PRIMARY_S)
    t_min = min(stall.entry.min() - S(W_PRIMARY_S), reach.entry.min())
    t_max = max(stall.exit.max(), (reach.entry + reach.hold.apply(lambda h: S(h))).max())
    print(f"[read] trade signs in [{t_min}, {t_max}) from {windowed}")
    ts_ns, rs, mid = read_trade_signs(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")

    feat_H, compute_H = make_hurst_feature(ts_ns, rs, mid)
    feat_rho1, _, _ = make_feature_fns(ts_ns, rs, mid)

    print("\n--- diagnostic: per-arm Hurst spread + n (validity) ---")
    rows = []
    from horse_race_spine import designA_cut_windows, designA_peer_windows_for
    for w in designA_cut_windows(stall, W):
        d = compute_H(w["side"], w["ws"], w["we"])
        if d: rows.append({"arm": "stall", **d})
    for _, st in stall.iterrows():
        for w in designA_peer_windows_for(st, reach, W):
            d = compute_H(w["side"], w["ws"], w["we"])
            if d: rows.append({"arm": "reach", **d})
    df = pd.DataFrame(rows)
    print(f"[diag] tripwire-flagged: {int(df.flagged.sum())} | scored {len(df)} windows "
          f"(any H NaN: {int((~np.isfinite(df.H)).sum())})")
    for arm in ("stall", "reach"):
        a = df[(df.arm == arm) & ~df.flagged & np.isfinite(df.H)]
        print(f"[diag] {arm:5s}: H med={a.H.median():+.3f} (IQR {a.H.quantile(.25):+.3f}..{a.H.quantile(.75):+.3f})"
              f"  n/window med={a.n.median():.0f}")

    print("\n--- Design B (PRIMARY = Hurst H via DFA; rho1 carried from trial 1) ---")
    report_two_sided("Hurst H [PRIMARY]", designA_perCut(stall, reach, feat_H, W, seed=seed))
    report_two_sided("rho1 (trial 1)", designA_perCut(stall, reach, feat_rho1, W, seed=seed))


def selftest(config, wrb):
    print("=== SELF-TEST: DFA Hurst on synthetic sign series ===")
    rng = np.random.default_rng(0)
    iid = np.where(rng.random(2000) < 0.5, 1.0, -1.0)
    alt = np.tile([1.0, -1.0], 1000)
    # persistent: long runs (Markov chain with high stay-probability)
    p_stay = 0.95; s = [1.0]
    for _ in range(1999):
        s.append(s[-1] if rng.random() < p_stay else -s[-1])
    persist = np.asarray(s)
    for name, x, lo, hi in [
        ("iid white   (expect ~0.5)", iid, 0.40, 0.60),
        ("alternating (expect <0.5)", alt, 0.0, 0.45),
        ("long runs   (expect >0.5)", persist, 0.60, 1.05),
    ]:
        H = dfa_hurst(x)
        ok = lo <= H <= hi
        print(f"  {name}: H={H:+.3f}  [{'PASS' if ok else 'CHECK'}]")
        assert ok, f"{name}: H={H} outside [{lo},{hi}]"
    # global sign flip invariance
    H1 = dfa_hurst(persist); H2 = dfa_hurst(-persist)
    print(f"  sign-flip invariance: H(x)={H1:+.3f}  H(-x)={H2:+.3f}  (equal => direction-agnostic)")
    assert abs(H1 - H2) < 1e-9
    print("SELF-TEST OK: DFA reads persistence (white~0.5, anti<0.5, runs>0.5), flip-invariant.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
