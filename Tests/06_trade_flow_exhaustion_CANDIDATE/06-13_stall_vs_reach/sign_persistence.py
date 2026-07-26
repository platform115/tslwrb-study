#!/usr/bin/env python3
"""
sign_persistence.py  — Test A (stall-vs-reach diagnostic, Design B exit-anchored matched-elapsed)
=================================================================================================
QUESTION (this conversation): among NON-LOSERS, what is observably different at the moment the
trader exits a trade that stalled short of target (below_target_win, n=29), versus trades that
were still pre-target at that SAME elapsed age and went on to reach pt1 (reach arm, n=47)?

MECHANISM FAMILY A — ORDER-FLOW SIGN PERSISTENCE.
Documented precedent: Lillo & Farmer (2004), "The long memory of the efficient market";
Toth, Palit, Lillo & Farmer (2015). Trade signs are long-memory: same-side aggressor signing
clusters (positive sign autocorrelation, slow decay). A *developing* directional auction keeps
signing the same way; when that directional persistence breaks, the move is petering out.

PRE-REGISTERED HYPOTHESIS (frozen before any real number is seen):
  At the matched exit-age tau, REACH trades show GREATER oriented lag-1 trade-sign autocorrelation
  than STALL trades.  Direction (frozen): per-cut AUC = P(reach rho1 > stall rho1) > 0.5.
  Reported TWO-SIDED (point + 95% CI + which direction; the read is "does CI exclude 0.5").
  On discovery we REPORT; we do not declare a winner or freeze an estimator.

EXPECTED_SIGNAL_SHAPE / what would make it a NEW mechanism vs the already-explored LEVEL channel:
  rho1 is MEAN-REMOVED, so it is (by construction) orthogonal to directional IMBALANCE = mean
  oriented flow (the channel the frozen exhaustion/early-flow candidates already used). If rho1
  separates ONLY where mean-oriented flow also separates (high corr, separation vanishes once you
  condition on it), it is the old level channel re-expressed -> NOT a new mechanism. The diagnostic
  pass reports mean-oriented separation + corr(rho1, mean_oriented) so this is checkable.

CONFOUND_RISK = med. Pre-registered threats + guards:
  (i)  HOLD-TIME proxy (stalls median ~115s, reaches ~310s): NEUTRALIZED by matched-elapsed —
       both arms are read over an identical-span window ending at the SAME age tau, so any feature
       that is a pure function of age/length cannot separate (unit-tested: harness guard -> AUC=0.5).
       Scope honesty: this removes the MARGINAL age effect, not age*X interactions.
  (ii) IMBALANCE conflation: NEUTRALIZED by using mean-removed rho1 + the orthogonality diagnostic.
  (iii) SMALL-SAMPLE BIAS of lag-1 autocorrelation: E[r1] ~ -1/(n-1) under white noise. If STALL
        windows carry fewer trade prints than REACH at matched tau, stall rho1 is biased MORE
        negative -> spuriously inflates AUC(reach>stall). GUARD: report n-per-arm distributions and
        a bias-recentred companion rho1_adj = rho1 + 1/(n-1). If n differs materially or the signal
        only survives on raw (not adj) rho1, treat as an n-asymmetry artifact, not a result.

FEATURE (frozen formula):
  Trade prints only (action=="T"), aggressor side in {"B","A"} (side "N"/null dropped). SIGN ONLY,
  size IGNORED (size = the level/intensity channel, not the sign-memory channel — keeps A orthogonal).
    raw_sign = +1 if side=="B" else -1            # buyer- vs seller-initiated
    oriented = raw_sign * (+1 if long else -1)    # >0 = aggressor WITH the trade direction
  Per window (event-time series of oriented signs s_1..s_n within [ws, we)):
    PRIMARY  rho1 = lag-1 sample autocorrelation of s (mean-removed):
                 m = mean(s); d = s - m
                 rho1 = mean(d[:-1]*d[1:]) / mean(d*d)     # standard biased lag-1 autocorr
                 degenerate rule: if mean(d*d)==0 (all signs identical) -> rho1 = +1.0 (max persistence)
    COMPANION runlen = mean same-sign run length = n / (1 + #sign-changes)   [Handoff's named form;
                 conflates imbalance somewhat -> robustness read, NOT a second primary]
    rho1_adj = rho1 + 1/(n-1)                       # bias-recentred companion (guard iii)
  Validity floor: n >= N_MIN trade prints in window (lag-1 autocorr is noise below this). N_MIN=10
    pre-registered (>=9 pairs); flagged as a judgement call, sensitivity-check deferred.
  Tripwire: flag+exclude any window with inter-print gap > 120s (halt/session) or |mid jump| > 40
    ticks (roll discontinuity). Expected 0 on a single-front-month intraday month.

STATISTIC (Design B = your frozen Design A enumeration, applied to stall-cuts vs reach-peers):
  Each STALL cut at its exit-age tau=hold, window [max(entry, exit-W), exit), W=60s primary.
  Eligible REACH peers = pt1_open_el > tau (still pre-target at age tau), window
  [max(entry, entry+tau-W), entry+tau).  per-cut AUC = P(reach-peer rho1 > stall-cut rho1).
  Cluster bootstrap over the 29 stall cuts (seed 0, 10000). Two-sided.  (Validated: 29 cuts,
  396 peers, median 13 peers/cut, 23/29 cuts have >=8 peers.)

REUSES (imported, never re-implemented): build_groups, S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS,
  INSTRUMENT_ID, column names (trade_flow_exhaustion);  designA_cut_windows,
  designA_peer_windows_for, designA_perCut, cluster_boot_ci, rank_auc (horse_race_spine).

RUN (on your machine, MBP-10 windowed parquet via config):
  python3 sign_persistence.py --config config.toml --wrb /path/to/wrb_1m.parquet
SELF-TEST (no MBP-10 needed; synthetic feature math + harness confound guard):
  python3 sign_persistence.py --selftest --config config.toml --wrb /path/to/wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import (
    build_groups, S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS, INSTRUMENT_ID,
    TS_COL, ACT, SIDE, BID_PX0, ASK_PX0,
)
from horse_race_spine import (
    designA_cut_windows, designA_peer_windows_for, designA_perCut,
    cluster_boot_ci, rank_auc,
)

N_MIN = 10                 # min trade prints per window for a defined rho1 (pre-registered)
W_PRIMARY_S = 60           # Design-A/B trailing window (frozen)


# ---------------------------------------------------------------------------
# 1. PERSISTENCE MATH (pure; unit-testable without any data)
# ---------------------------------------------------------------------------
def persistence_stats(s):
    """s: 1-D array of oriented signs in {+1,-1}. Returns (rho1, runlen).
    rho1 = mean-removed lag-1 sample autocorrelation; +1.0 if the series is constant.
    runlen = mean same-sign run length = n / (1 + #changes)."""
    s = np.asarray(s, float)
    n = len(s)
    if n < 2:
        return np.nan, np.nan
    m = s.mean()
    d = s - m
    denom = float((d * d).mean())
    rho1 = 1.0 if denom == 0.0 else float((d[:-1] * d[1:]).mean() / denom)
    changes = int(np.count_nonzero(s[1:] != s[:-1]))
    runlen = n / (1 + changes)
    return rho1, runlen


# ---------------------------------------------------------------------------
# 2. WINDOWED EXTRACTOR (closes over per-trade arrays from read_trade_signs)
# ---------------------------------------------------------------------------
def make_feature_fns(ts_ns, raw_sign, mid):
    """Build (feat_rho1, feat_runlen, compute) closing over per-trade arrays.
    ts_ns int64 (sorted), raw_sign int8 in {+1,-1}, mid float."""
    def compute(side, ws, we):
        a = np.searchsorted(ts_ns, np.int64(pd.Timestamp(ws).value), "left")
        b = np.searchsorted(ts_ns, np.int64(pd.Timestamp(we).value), "left")
        t = ts_ns[a:b]; rs = raw_sign[a:b]; mz = mid[a:b]
        n = len(t)
        if n < N_MIN:
            return None
        flagged = False
        if n >= 2:
            if (np.diff(t) / 1e9).max() > MAX_GAP_S:
                flagged = True
            if (np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS:
                flagged = True
        s = rs.astype(float) * (1.0 if side == "long" else -1.0)
        rho1, runlen = persistence_stats(s)
        rho1_adj = rho1 + 1.0 / (n - 1) if np.isfinite(rho1) else np.nan
        return dict(rho1=rho1, runlen=runlen, rho1_adj=rho1_adj, n=n,
                    mean_oriented=float(s.mean()), flagged=flagged)

    def feat_rho1(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if d["flagged"] else d["rho1"]), **d}

    def feat_runlen(side, ws, we):
        d = compute(side, ws, we)
        if d is None:
            return None
        return {"value": (np.nan if d["flagged"] else d["runlen"]), **d}

    return feat_rho1, feat_runlen, compute


# ---------------------------------------------------------------------------
# 3. PER-TRADE READER (single streamed pass; sign-only; mid for tripwire)
# ---------------------------------------------------------------------------
def read_trade_signs(windowed, t_min, t_max):
    import pyarrow.parquet as pq, pyarrow as pa
    need = [TS_COL, ACT, SIDE, BID_PX0, ASK_PX0, "instrument_id"]
    pf = pq.ParquetFile(windowed)
    miss = [c for c in need if c not in set(pf.schema_arrow.names)]
    if miss:
        raise SystemExit(f"[schema] missing {miss}")
    tmin = pd.Timestamp(t_min).value; tmax = pd.Timestamp(t_max).value
    TS, RS, MD = [], [], []
    for bt in pf.iter_batches(batch_size=200_000, columns=need):
        ts = bt.column(TS_COL).cast(pa.timestamp("ns")).cast(pa.int64()).to_numpy(zero_copy_only=False)
        m = (ts >= tmin) & (ts < tmax)
        if INSTRUMENT_ID is not None:
            m &= bt.column("instrument_id").to_numpy(zero_copy_only=False) == INSTRUMENT_ID
        m &= bt.column(ACT).to_numpy(zero_copy_only=False) == "T"
        sd = bt.column(SIDE).to_numpy(zero_copy_only=False)
        m &= (sd == "B") | (sd == "A")
        if not m.any():
            continue
        idx = np.flatnonzero(m)
        sdi = sd[idx]
        bp = bt.column(BID_PX0).to_numpy(zero_copy_only=False)[idx]
        ap = bt.column(ASK_PX0).to_numpy(zero_copy_only=False)[idx]
        TS.append(ts[idx])
        RS.append(np.where(sdi == "B", np.int8(1), np.int8(-1)))
        MD.append((bp + ap) / 2.0)
    if not TS:
        raise SystemExit("[read] zero trade prints in range")
    ts_ns = np.concatenate(TS); rs = np.concatenate(RS); mid = np.concatenate(MD)
    order = np.argsort(ts_ns, kind="stable")
    return ts_ns[order], rs[order].astype(np.int8), mid[order]


# ---------------------------------------------------------------------------
# 4. DIAGNOSTIC PASS (tripwire / validity / imbalance-orthogonality) + report
# ---------------------------------------------------------------------------
def diagnostic_pass(stall, reach, compute, W):
    rows = []
    for w in designA_cut_windows(stall, W):
        d = compute(w["side"], w["ws"], w["we"]); 
        if d: rows.append({"arm": "stall", **d})
    for _, st in stall.iterrows():
        for w in designA_peer_windows_for(st, reach, W):
            d = compute(w["side"], w["ws"], w["we"])
            if d: rows.append({"arm": "reach", **d})
    df = pd.DataFrame(rows)
    if df.empty:
        print("[diag] no scored windows"); return df
    print(f"[diag] tripwire-flagged windows: {int(df.flagged.sum())} (expected 0)")
    for arm in ("stall", "reach"):
        a = df[(df.arm == arm) & (~df.flagged)]
        print(f"[diag] {arm:5s}: scored={len(a):4d}  n trade-prints/window "
              f"min={a.n.min():.0f} med={a.n.median():.0f} max={a.n.max():.0f}")
    ok = df[~df.flagged].dropna(subset=["rho1", "mean_oriented"])
    if len(ok) > 5:
        c = np.corrcoef(ok.rho1, ok.mean_oriented)[0, 1]
        print(f"[diag] corr(rho1, mean_oriented) over all windows = {c:+.3f} "
              f"(near 0 => rho1 is NOT just imbalance)")
    return df


def report_two_sided(label, res):
    ci = res["ci"]
    if not np.isfinite(ci["mean"]):
        print(f"  {label}: n cuts scored={res['n_cut_scored']} (<5 valid: uninformative)"); return
    direction = "reach>stall" if ci["mean"] >= 0.5 else "stall>reach"
    strength = ci["mean"] if ci["mean"] >= 0.5 else 1.0 - ci["mean"]
    flag = "CI EXCLUDES 0.5 (separates)" if ci["excludes_half"] else "CI includes 0.5"
    print(f"  {label:14s} per-cut AUC={ci['mean']:.3f}  two-sided={strength:.3f} ({direction})  "
          f"95% CI [{ci['lo']:.3f}, {ci['hi']:.3f}]  cuts={ci['n']}  -> {flag}"
          + ("" if ci["n"] >= 8 else "   [<8 cuts: uninformative]"))


# ---------------------------------------------------------------------------
# 5. MAIN
# ---------------------------------------------------------------------------
def build_arms(config, wrb):
    import tomllib
    with open(config, "rb") as f:
        cfg = tomllib.load(f)
    ep = cfg["paths"]["episodes"]
    windowed = cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")
    g = build_groups(ep, wrb)
    g["is_loser"] = g["realized_pnl"] < 0
    stall = g[(g.group == "failed_trades") & (~g.is_loser)].copy().reset_index(drop=True)
    reach = g[(g.group == "target_reached") & (~g.is_loser)].copy().reset_index(drop=True)
    return stall, reach, windowed


def run(config, wrb, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    print(f"[arms] stall(below_target_win)={len(stall)}  reach(non-loser)={len(reach)}  (expect 29 / 47)")
    W = S(W_PRIMARY_S)
    t_min = min(stall.entry.min() - S(W_PRIMARY_S), reach.entry.min())
    t_max = max(stall.exit.max(), (reach.entry + reach.hold.apply(lambda h: S(h))).max())
    print(f"[read] trade signs in [{t_min}, {t_max}) from {windowed}")
    ts_ns, rs, mid = read_trade_signs(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")
    feat_rho1, feat_runlen, compute = make_feature_fns(ts_ns, rs, mid)

    print("\n--- diagnostic pass (guards) ---")
    diagnostic_pass(stall, reach, compute, W)

    print("\n--- Design B (PRIMARY = rho1; companions = runlen, and rho1 as imbalance check) ---")
    report_two_sided("rho1 [PRIMARY]", designA_perCut(stall, reach, feat_rho1, W, seed=seed))
    report_two_sided("runlen [comp]", designA_perCut(stall, reach, feat_runlen, W, seed=seed))
    # imbalance check: same per-cut design on mean_oriented (the LEVEL channel)
    feat_mo = lambda side, ws, we: (lambda d: None if d is None else
                                    {"value": (np.nan if d["flagged"] else d["mean_oriented"]), **d})(compute(side, ws, we))
    report_two_sided("mean_oriented", designA_perCut(stall, reach, feat_mo, W, seed=seed))
    print("  (read: if rho1 separates but mean_oriented does NOT, rho1 is a new axis; "
          "if both separate and corr is high, rho1 is the level channel re-expressed.)")


def selftest(config, wrb):
    print("=== SELF-TEST 1: persistence math (synthetic) ===")
    cases = {
        "persistent  [+1]*30+[-1]*30": np.r_[np.ones(30), -np.ones(30)],
        "alternating [+1,-1]*30      ": np.tile([1, -1], 30),
        "constant    [+1]*40         ": np.ones(40),
    }
    for name, s in cases.items():
        r, rl = persistence_stats(s)
        print(f"  {name}: rho1={r:+.3f}  runlen={rl:.2f}")
    rng = np.random.default_rng(0)
    s = np.where(rng.random(4000) < 0.8, 1.0, -1.0)  # iid, P(+)=0.8: high imbalance, NO memory
    r, rl = persistence_stats(s)
    print(f"  iid imbalanced (P+=0.8, no memory): mean={s.mean():+.3f}  rho1={r:+.3f} (expect ~0) "
          f"runlen={rl:.2f}")
    assert persistence_stats(np.tile([1, -1], 30))[0] < -0.9
    assert persistence_stats(np.ones(40))[0] == 1.0
    assert abs(r) < 0.06, "rho1 should be ~0 for iid imbalance (orthogonal to level)"
    print("  PASS: rho1 high for runs, -1 for alternation, +1 for constant, ~0 for pure imbalance.\n")

    print("=== SELF-TEST 2: harness confound guard (matched-elapsed neutralizes age) ===")
    stall, reach, _ = build_arms(config, wrb)
    W = S(W_PRIMARY_S)
    # synthetic feature = a pure function of evaluation-age tau (carried on each enumerated window).
    # By construction each peer is evaluated at the cut's tau -> identical value -> per-cut AUC=0.5.
    per_cut = []
    for _, st in stall.iterrows():
        tau = float(st.hold)
        cut_val = tau * 3.14159  # any deterministic f(age)
        peers = designA_peer_windows_for(st, reach, W)
        pv = [pw["tau"] * 3.14159 for pw in peers]
        if pv:
            pv = np.asarray(pv)
            per_cut.append((np.sum(pv > cut_val) + 0.5 * np.sum(pv == cut_val)) / len(pv))
    ci = cluster_boot_ci(per_cut, seed=0)
    print(f"  pure-age feature: per-cut AUC={ci['mean']:.3f}  CI [{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"cuts={ci['n']}  (expect exactly 0.5: age cannot separate under matched-elapsed)")
    assert abs(ci["mean"] - 0.5) < 1e-9, "matched-elapsed should null a pure-age feature"
    print("  PASS: a pure age/length proxy scores exactly 0.5 — hold-time confound is neutralized.")
    print("  (scope: neutralizes the MARGINAL age effect, not age*X interactions.)\n")
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(a.config, a.wrb)
    else:
        run(a.config, a.wrb, seed=a.seed)
