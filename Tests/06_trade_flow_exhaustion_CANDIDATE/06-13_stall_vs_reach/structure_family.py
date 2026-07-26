#!/usr/bin/env python3
"""
structure_family.py  — flow-STRUCTURE family at the justified primary window (120s survivors)
=============================================================================================
WHY: across the conversation the only leakage-free early lead was HURST (sign-memory persistence),
clearing the survivors control at W=120s (0.657, CI [0.507,0.795]) and reach>stall at all 8 reads.
The whole STRUCTURE/DIRECTION family leaned the same way at 120s survivors (flow_level 0.568,
rho1 0.598, ER 0.600) while MAGNITUDE features were flat. Lesson set:
  (1) 30s under-powered structural features (hurst 0.607@60 -> 0.657@120); ~120s is the right horizon.
  (2) capped = whole-life stall signature (answers nothing early); survivors = clean early read.
  (3) live axis = "how organized/persistent is the early flow", not "how much".
  (4) scale-free measures (hurst, ER) behaved best.

PRIMARY WINDOW (pre-registered, FIXED — not shopped): W=120s, SURVIVORS-only (both arms read full
[entry, entry+120s], no exit-capping). The 60/180/300 + capped columns print for DIRECTION-
CONSISTENCY context only; the decision read is 120s-survivors. (Fixing this is what keeps re-testing
from becoming window-fishing.)

NEW / GAP-FILL FEATURES:
  flow_consistency [NEW, the candidate] = |sum_s oriented_flow_s| / sum_s |oriented_flow_s|, in [0,1].
     = Kaufman Efficiency Ratio applied to the CUMULATIVE signed-flow path (since cumsum diffs are
     the per-second flows). Documented composition: Kaufman ER + signed order flow (OFI; Cont,
     Kukanov, Stoikov 2014). Scale-free (lesson 4), directional+structural (lesson 3). High = flow
     accumulates steadily one way (organized, developing); low = sloshes both ways (disorganized).
     Pre-registered direction: reach > stall.
  impact [GAP-FILL] = |net mid move ticks| / n_trades, entry-forward. Only ever tested exit-anchored
     before (null there); never entry-forward. Two-sided (no committed direction).

CARRIED (reproduce prior sweep numbers; here for apples-to-apples in ONE table, NOT new trials):
  flow_level (mean oriented per-second flow), hurst (DFA sign memory), rho1 (lag-1 sign autocorr),
  ER_abs (Kaufman ER on per-second mid).

CAVEAT (frozen): flow_consistency is CORRELATED with flow_level / hurst / rho1 / ER — it UNIFIES
the axis, it does not independently confirm it. It earns "candidate" only if it CLEARS the 120s
survivors control with consistent cross-window direction (the bar hurst met). Three correlated
leaners are not three confirmations.

POOLED 47 vs 29, two-sample bootstrap (seed 0), two-sided. Discovery = report; Feb = validate.
This is the LAST in-sample structural probe; the persistence axis (hurst + whatever clears here)
then goes to Feb rather than spawning a further estimator.

REUSES (unchanged, unit-tested): read_trade_full, two_sample_boot_ci, build_arms (forward_battery);
  dfa_hurst (sign_persistence_dfa); persistence_stats (sign_persistence); efficiency_ratio
  (efficiency_ratio); S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS (trade_flow_exhaustion).

RUN:  python3 structure_family.py --config config.toml --wrb wrb_1m.parquet
      python3 structure_family.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS
from forward_battery import read_trade_full, two_sample_boot_ci, build_arms
from sign_persistence_dfa import dfa_hurst
from sign_persistence import persistence_stats
from efficiency_ratio import efficiency_ratio

WINDOWS = [60, 120, 180, 300]
PRIMARY_W = 120
N_MIN = 10
SURV_FLOOR = 8
FEATS = ["flow_consistency", "flow_level", "hurst", "rho1", "ER_abs", "impact"]
NEW = {"flow_consistency", "impact"}


def flow_consistency(oriented_sec):
    """Kaufman ER on cumulative signed flow = |sum| / sum|.|. [0,1]. NaN if no flow."""
    x = np.asarray(oriented_sec, float)
    den = np.abs(x).sum()
    if den == 0:
        return np.nan
    return abs(x.sum()) / den


def window_struct(ts_ns, raw_sign, size, mid, side, ws, we):
    ws_ns = np.int64(pd.Timestamp(ws).value); we_ns = np.int64(pd.Timestamp(we).value)
    a = np.searchsorted(ts_ns, ws_ns, "left"); b = np.searchsorted(ts_ns, we_ns, "left")
    t = ts_ns[a:b]; rs = raw_sign[a:b]; sz = size[a:b]; mz = mid[a:b]
    n = len(t); span = (we_ns - ws_ns) / 1e9
    if n < N_MIN or span < 2:
        return None
    flagged = (n >= 2) and (((np.diff(t) / 1e9).max() > MAX_GAP_S) or
                            ((np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS))
    sgn = 1.0 if side == "long" else -1.0
    k = int(np.ceil(span))
    sec_idx = np.minimum(((t - ws_ns) // 1_000_000_000).astype(int), k - 1)
    buyv = np.bincount(sec_idx, weights=np.where(rs > 0, sz, 0).astype(float), minlength=k)
    sellv = np.bincount(sec_idx, weights=np.where(rs < 0, sz, 0).astype(float), minlength=k)
    oriented_sec = (buyv - sellv) * sgn
    msec = np.full(k, np.nan); msec[sec_idx] = mz
    m_active = msec[~np.isnan(msec)]
    rho1, _ = persistence_stats(rs.astype(float))
    era, _, _ = efficiency_ratio(m_active, side)
    return dict(
        flow_consistency=flow_consistency(oriented_sec),
        flow_level=float(oriented_sec.mean()),
        hurst=dfa_hurst(rs.astype(float)),
        rho1=rho1,
        ER_abs=era,
        impact=abs(mz[-1] - mz[0]) / TICK / n,
        flagged=flagged,
    )


def collect(df, ts_ns, rs, sz, mid, W, survivors_only):
    rows = []
    for _, r in df.iterrows():
        if survivors_only:
            if r.hold < W:
                continue
            we = r.entry + S(W)
        else:
            we = min(r.entry + S(W), r.exit)
        f = window_struct(ts_ns, rs, sz, mid, r.side, r.entry, we)
        if f is None or f["flagged"]:
            continue
        rows.append(f)
    return pd.DataFrame(rows)


def report(R, Sd, seed, only=None):
    for f in FEATS:
        if only and f not in only:
            continue
        ci = two_sample_boot_ci(R[f], Sd[f], seed=seed)
        if not np.isfinite(ci["auc"]):
            print(f"       {f:17s} (insufficient)"); continue
        mark = "**" if ci["excludes_half"] else "  "
        tag = " [NEW]" if f in NEW else ""
        print(f"   {mark} {f:17s} AUC={ci['auc']:.3f}  CI[{ci['lo']:.3f},{ci['hi']:.3f}]"
              f"  Rmed={R[f].median():+.3f} Smed={Sd[f].median():+.3f}{tag}")


def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    print(f"[arms] stall={len(stall)} reach={len(reach)}")
    t_min = min(stall.entry.min(), reach.entry.min()) - S(2)
    t_max = max((stall.entry + S(max(WINDOWS))).max(), (reach.entry + S(max(WINDOWS))).max())
    print(f"[read] {windowed}")
    ts_ns, rs, sz, mid = read_trade_full(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")

    for W in WINDOWS:
        primary = (W == PRIMARY_W)
        print(f"\n========== W={W}s{'  <<< PRIMARY' if primary else ''} ==========")
        Rs = collect(reach, ts_ns, rs, sz, mid, W, True)
        Ss = collect(stall, ts_ns, rs, sz, mid, W, True)
        if len(Ss) >= SURV_FLOOR:
            print(f"  SURVIVORS (clean) reach n={len(Rs)} stall n={len(Ss)}"
                  f"{'   *** decision read ***' if primary else ''}")
            report(Rs, Ss, seed)
        else:
            print(f"  SURVIVORS stall n={len(Ss)} < {SURV_FLOOR}: UNINFORMATIVE (artifact-prone)")
        # capped shown only as context for the new features (full population)
        Rc = collect(reach, ts_ns, rs, sz, mid, W, False)
        Sc = collect(stall, ts_ns, rs, sz, mid, W, False)
        print(f"  capped (context only) reach n={len(Rc)} stall n={len(Sc)}")
        report(Rc, Sc, seed, only=NEW)
    print(f"\nDECISION READ = W={PRIMARY_W}s survivors. flow_consistency is a candidate ONLY if it "
          f"clears there with consistent cross-W direction (the bar hurst met). It is correlated "
          f"with the family -> corroborates, does not independently confirm.")


def selftest(config, wrb):
    print("=== SELF-TEST: flow_consistency (Kaufman ER on cumulative signed flow) ===")
    for name, x, want in [
        ("all one way   [5,5,5,5]   ", np.array([5, 5, 5, 5.]), 1.0),
        ("balanced slosh[5,-5,5,-5]  ", np.array([5, -5, 5, -5.]), 0.0),
        ("net +4 of 6   [3,1,-1,1]   ", np.array([3, 1, -1, 1.]), 4 / 6),
    ]:
        fc = flow_consistency(x)
        ok = abs(fc - want) < 1e-9
        print(f"  {name}: fc={fc:.3f} (want {want:.3f})  [{'PASS' if ok else 'CHECK'}]")
        assert ok
    assert np.isnan(flow_consistency(np.zeros(5)))
    print("  PASS: 1 organized, 0 sloshing, partial correct, NaN if no flow.")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, seed=a.seed)
