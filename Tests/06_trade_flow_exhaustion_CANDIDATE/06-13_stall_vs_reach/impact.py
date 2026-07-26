#!/usr/bin/env python3
"""
impact.py  — Test B dig: PRICE MOVE PER TRADE (effort-vs-result), stall-exit vs reach (Design B)
================================================================================================
PURPOSE: the intensity-LEVEL finding (stalls ~2x trades/sec at matched exit-age; per-cut AUC 0.244,
two-sided 0.756) is real but PEEKED and partly time-of-day confounded (stalls cluster at the busy
open + close; U-shaped activity). This dig asks the MECHANISM question that LEVEL alone cannot:
does all that extra trading actually MOVE price? If stalls trade 2x but price travels the same or
less, that is ABSORPTION (churn, no progress) — a documented, behaviorally-meaningful stall
signature. If price travel scales with trade count, the level gap is "just busy" and collapses to a
timing pattern.

WHY THIS IS NOT JUST THE LEVEL FINDING RE-RUN, AND IS TOD-ROBUST: it is a RATIO (move / trades).
At busy times BOTH the numerator (|price move|) and denominator (trade count) inflate, so the
U-shaped time-of-day activity that confounds raw rate largely cancels in the ratio. And the
direction is genuinely UNSEEN: we know stall trade-COUNT (peeked) but not stall |price move|.

DOCUMENTED PRECEDENT: Amihud (2002) illiquidity = |return| / volume (price impact per unit
activity); Kyle (1985) lambda (price impact of order flow). "Effort vs result" is the practitioner
framing (Wyckoff) — the measurable content is the Amihud/Kyle ratio, not the vocabulary.

PRE-REGISTERED (frozen before any real number):
  PRIMARY  impact_abs = |net mid displacement over window, ticks| / n_trades.
           Direction (frozen): per-cut AUC = P(reach impact_abs > stall impact_abs) > 0.5
           (stalls = low move-per-trade = absorption). Two-sided. On discovery we REPORT.
  COMPANION impact_ori = (oriented net displacement, ticks) / n_trades  [signed; is the move WITH
           the trade? reach expected > stall, possibly stall ~0/negative]. Not a 2nd primary.
  NOTE this is a logged TRIAL on the level finding's mechanism (feeds the Deflated-Sharpe N). A
  positive carries the COMBINED hypothesis "high activity + low impact = absorption" to the Feb
  holdout — it is not a candidate on October.

FEATURE (frozen formula), per Design-B window [ws, we), trade prints only (action=="T"):
    n          = trade prints in window
    net_ticks  = (mid_at_last_print - mid_at_first_print) / TICK         # signed
    impact_abs = |net_ticks| / n                                          # PRIMARY (Amihud-style)
    impact_ori = net_ticks * (+1 if long else -1) / n                     # COMPANION (signed)
  Result = NET displacement (not path length): a volatile-but-went-nowhere window has small net
  displacement -> correctly reads as absorption regardless of intra-window wiggle/volatility.
  Validity floor: n >= N_MIN_IMP (pre-registered; non-binding, min n was 101).
  Tripwire: gap>120s or |mid jump|>40 ticks -> flag+exclude (same as A/B).

STATISTIC: Design B (frozen) — stall cuts at exit-age tau, reach peers pt1_open_el>tau, W=60s,
  per-cut AUC, cluster bootstrap over 29 cuts (seed 0, 10000), two-sided.

REUSES: read_trade_signs, build_arms, W_PRIMARY_S, report_two_sided (sign_persistence);
  designA_perCut, designA_cut_windows, designA_peer_windows_for (horse_race_spine);
  S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS (trade_flow_exhaustion).

RUN:
  python3 impact.py --config config.toml --wrb wrb_1m.parquet
  python3 impact.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS
from horse_race_spine import designA_perCut, designA_cut_windows, designA_peer_windows_for
from sign_persistence import read_trade_signs, build_arms, W_PRIMARY_S, report_two_sided

N_MIN_IMP = 10


# ---------------------------------------------------------------------------
# pure impact math (unit-testable)
# ---------------------------------------------------------------------------
def impact_stats(mid_first, mid_last, n, side, tick=TICK):
    """Returns (impact_abs, impact_ori, net_ticks). NaN if n<1."""
    if n < 1:
        return np.nan, np.nan, np.nan
    net_ticks = (mid_last - mid_first) / tick
    sgn = 1.0 if side == "long" else -1.0
    return abs(net_ticks) / n, (net_ticks * sgn) / n, net_ticks


# ---------------------------------------------------------------------------
# windowed extractor (closes over per-trade arrays)
# ---------------------------------------------------------------------------
def make_impact_features(ts_ns, mid):
    def compute(side, ws, we):
        a = np.searchsorted(ts_ns, np.int64(pd.Timestamp(ws).value), "left")
        b = np.searchsorted(ts_ns, np.int64(pd.Timestamp(we).value), "left")
        t = ts_ns[a:b]; mz = mid[a:b]
        n = len(t)
        if n < N_MIN_IMP:
            return None
        flagged = False
        if n >= 2:
            if (np.diff(t) / 1e9).max() > MAX_GAP_S:
                flagged = True
            if (np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS:
                flagged = True
        ia, io, net = impact_stats(mz[0], mz[-1], n, side)
        return dict(impact_abs=ia, impact_ori=io, net_ticks=net, n=n, flagged=flagged)

    def feat_abs(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if d["flagged"] else d["impact_abs"]), **d}

    def feat_ori(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if d["flagged"] else d["impact_ori"]), **d}

    return feat_abs, feat_ori, compute


def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    print(f"[arms] stall={len(stall)}  reach={len(reach)}  (expect 29 / 47)")
    W = S(W_PRIMARY_S)
    t_min = min(stall.entry.min() - S(W_PRIMARY_S), reach.entry.min())
    t_max = max(stall.exit.max(), (reach.entry + reach.hold.apply(lambda h: S(h))).max())
    print(f"[read] trade signs in [{t_min}, {t_max}) from {windowed}")
    ts_ns, rs, mid = read_trade_signs(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")

    feat_abs, feat_ori, compute = make_impact_features(ts_ns, mid)

    print("\n--- diagnostic: effort vs result, per arm (THIS is the mechanism, read it directly) ---")
    rows = []
    for w in designA_cut_windows(stall, W):
        d = compute(w["side"], w["ws"], w["we"])
        if d: rows.append({"arm": "stall", **d})
    for _, st in stall.iterrows():
        for w in designA_peer_windows_for(st, reach, W):
            d = compute(w["side"], w["ws"], w["we"])
            if d: rows.append({"arm": "reach", **d})
    df = pd.DataFrame(rows)
    print(f"[diag] tripwire-flagged: {int(df.flagged.sum())} | scored {len(df)}")
    for arm in ("stall", "reach"):
        a = df[(df.arm == arm) & ~df.flagged]
        print(f"[diag] {arm:5s}: n/win med={a.n.median():.0f}  |net move| med={a.net_ticks.abs().median():.2f}tk  "
              f"impact_abs med={a.impact_abs.median():.4f}  impact_ori med={a.impact_ori.median():+.4f}")

    print("\n--- Design B ---")
    report_two_sided("impact_abs [PRIMARY]", designA_perCut(stall, reach, feat_abs, W, seed=seed))
    report_two_sided("impact_ori [comp]", designA_perCut(stall, reach, feat_ori, W, seed=seed))


def selftest(config, wrb):
    print("=== SELF-TEST: impact math (effort vs result) ===")
    # same 5-tick net move, but 2x trades -> half the impact (absorption signature)
    ia1, io1, net1 = impact_stats(5000.0, 5000.0 + 5 * TICK, 50, "long")
    ia2, io2, net2 = impact_stats(5000.0, 5000.0 + 5 * TICK, 100, "long")
    print(f"  +5tk over 50 trades : impact_abs={ia1:.4f} impact_ori={io1:+.4f} net={net1:+.1f}tk")
    print(f"  +5tk over 100 trades: impact_abs={ia2:.4f} impact_ori={io2:+.4f} net={net2:+.1f}tk  (half -> absorption)")
    assert abs(ia1 - 0.1) < 1e-9 and abs(ia2 - 0.05) < 1e-9
    # short side: a downward move is FAVORABLE (oriented positive)
    ia3, io3, net3 = impact_stats(5000.0, 5000.0 - 4 * TICK, 40, "short")
    print(f"  short, -4tk over 40 : impact_abs={ia3:.4f} impact_ori={io3:+.4f} net={net3:+.1f}tk  (ori>0: with-trade)")
    assert io3 > 0 and abs(ia3 - 0.1) < 1e-9
    # adverse move reads oriented-negative even though |impact| is the same
    ia4, io4, net4 = impact_stats(5000.0, 5000.0 - 4 * TICK, 40, "long")
    print(f"  long,  -4tk over 40 : impact_abs={ia4:.4f} impact_ori={io4:+.4f} net={net4:+.1f}tk  (ori<0: adverse)")
    assert io4 < 0 and abs(ia4 - ia3) < 1e-9
    print("  PASS: more trades for same move -> lower impact (absorption); orientation correct; "
          "|impact| direction-agnostic.")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
