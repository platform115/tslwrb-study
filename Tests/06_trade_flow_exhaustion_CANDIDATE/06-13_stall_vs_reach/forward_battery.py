#!/usr/bin/env python3
"""
forward_battery.py  — Design (c): ENTRY-anchored, FORWARD, POOLED  (the predictor frame)
=========================================================================================
WHY: Design (b) (exit-anchored, matched-elapsed) returned 6 nulls + 1 confound-laden positive.
That design was built to STRIP age/duration/regime so it could isolate a confound-free
exit-moment mechanism — which is the wrong question for "recognize a stall EARLY." This script
asks the predictor question instead: in the FIRST tau seconds of a trade, do its features separate
the ones that go on to REACH target (47) from the ones that STALL short but stay green (29)?

KEY DESIGN CHANGES vs (b), each deliberate:
  - ENTRY-anchored, forward window [entry, min(entry+tau, exit)).  (was: exit-anchored, backward)
  - POOLED 47 vs 29 (NOT matched-elapsed) — duration/regime/activity are real-time-observable
    predictors, not confounds to remove. We WANT them to contribute.
  - tau = 30s primary: every trade's hold >= 35s, so the window is full for all 76 trades
    (0 truncation, no length confound). --tau exposes other horizons.
  - Causal: window end = min(entry+tau, exit) never reads past the trade (no lookahead). The
    label (reach/stall) is realized later; we only read the first tau seconds.

PRECEDENT for this frame working: the project's prior `early_flow_confirmation` was entry-forward
oriented flow and separated reach vs non-reach (AUC 0.67 on 52/40). This re-points it at the clean
non-loser 47/29 contrast, alongside the other re-tests.

FEATURES (each a logged trial; discovery = report, Feb = validate). Pure math reused & already
unit-tested in the A/B/C modules — only the ANCHOR and POOLING change here:
  intensity_level  = n_trades / span_s                         [the exit-anchored positive, re-framed]
  flow_level       = mean per-second oriented signed VOLUME    [= early_flow_confirmation feature]
  intensity_slope  = norm_slope(per-second counts)             [intensity.norm_slope]
  ER_abs           = Kaufman efficiency ratio (per-second mid)  [efficiency_ratio.efficiency_ratio]
  hurst            = DFA Hurst of per-trade sign series         [sign_persistence_dfa.dfa_hurst]
  rho1             = lag-1 sign autocorrelation                 [sign_persistence.persistence_stats]
  abs_move_tk      = |net mid move| over window (ticks)         [context: early realized travel]
  session_phase    = minutes since 09:30 ET at ENTRY           [context: when in the session]

PRE-REGISTERED DIRECTIONS (frozen): all reported TWO-SIDED. Only one carries a prior directional
expectation: flow_level reach > stall (building with-trade flow -> develops). The rest are
re-tests with no committed direction; we read which way and whether the CI clears 0.5.

STATISTIC: pooled rank AUC = P(reach value > stall value) over 47 vs 29; two-sample stratified
bootstrap CI (resample each arm independently, seed 0, 10000). Two-sided. (No per-cut clustering:
pooled design, each trade contributes one window.)
  Validity floor: feature defined (>=N_MIN prints; >=2 sec for slope/ER; sign series for hurst).
  Tripwire: per-trade gap>120s or |mid jump|>40 ticks -> flag+exclude.

REUSES: norm_slope (intensity); dfa_hurst (sign_persistence_dfa); persistence_stats, build_arms
  (sign_persistence); efficiency_ratio (efficiency_ratio); S,TICK,MAX_GAP_S,ROLL_JUMP_TICKS,
  INSTRUMENT_ID, col names (trade_flow_exhaustion); rank_auc (horse_race_spine).

RUN:
  python3 forward_battery.py --config config.toml --wrb wrb_1m.parquet
  python3 forward_battery.py --selftest --config config.toml --wrb wrb_1m.parquet
"""

import argparse
import numpy as np
import pandas as pd

from trade_flow_exhaustion import (S, TICK, MAX_GAP_S, ROLL_JUMP_TICKS, INSTRUMENT_ID,
                                   TS_COL, ACT, SIDE, SZ, BID_PX0, ASK_PX0)
from horse_race_spine import rank_auc
from sign_persistence import build_arms, persistence_stats
from sign_persistence_dfa import dfa_hurst
from intensity import norm_slope
from efficiency_ratio import efficiency_ratio

TAU_S = 30
N_MIN = 10


# ---------------------------------------------------------------------------
# reader: per-trade ts, raw_sign, size, mid  (single streamed pass)
# ---------------------------------------------------------------------------
def read_trade_full(windowed, t_min, t_max):
    import pyarrow.parquet as pq, pyarrow as pa
    need = [TS_COL, ACT, SIDE, SZ, BID_PX0, ASK_PX0, "instrument_id"]
    pf = pq.ParquetFile(windowed)
    miss = [c for c in need if c not in set(pf.schema_arrow.names)]
    if miss:
        raise SystemExit(f"[schema] missing {miss}")
    tmin = pd.Timestamp(t_min).value; tmax = pd.Timestamp(t_max).value
    TS, RS, SZv, MD = [], [], [], []
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
        idx = np.flatnonzero(m); sdi = sd[idx]
        TS.append(ts[idx])
        RS.append(np.where(sdi == "B", np.int8(1), np.int8(-1)))
        SZv.append(bt.column(SZ).to_numpy(zero_copy_only=False)[idx].astype("int64"))
        bp = bt.column(BID_PX0).to_numpy(zero_copy_only=False)[idx]
        ap = bt.column(ASK_PX0).to_numpy(zero_copy_only=False)[idx]
        MD.append((bp + ap) / 2.0)
    if not TS:
        raise SystemExit("[read] zero trade prints in range")
    ts_ns = np.concatenate(TS); o = np.argsort(ts_ns, kind="stable")
    return (ts_ns[o], np.concatenate(RS)[o].astype(np.int8),
            np.concatenate(SZv)[o], np.concatenate(MD)[o])


# ---------------------------------------------------------------------------
# per-trade forward-window feature vector
# ---------------------------------------------------------------------------
def window_features(ts_ns, raw_sign, size, mid, side, ws, we):
    ws_ns = np.int64(pd.Timestamp(ws).value); we_ns = np.int64(pd.Timestamp(we).value)
    a = np.searchsorted(ts_ns, ws_ns, "left"); b = np.searchsorted(ts_ns, we_ns, "left")
    t = ts_ns[a:b]; rs = raw_sign[a:b]; sz = size[a:b]; mz = mid[a:b]
    n = len(t); span_s = (we_ns - ws_ns) / 1e9
    if n < N_MIN or span_s < 2:
        return None
    flagged = (n >= 2) and (((np.diff(t) / 1e9).max() > MAX_GAP_S) or
                            ((np.abs(np.diff(mz)) / TICK).max() > ROLL_JUMP_TICKS))
    sgn = 1.0 if side == "long" else -1.0
    k = int(np.ceil(span_s))
    sec_idx = np.minimum(((t - ws_ns) // 1_000_000_000).astype(int), k - 1)
    counts = np.bincount(sec_idx, minlength=k).astype(float)
    buyv = np.bincount(sec_idx, weights=np.where(rs > 0, sz, 0).astype(float), minlength=k)
    sellv = np.bincount(sec_idx, weights=np.where(rs < 0, sz, 0).astype(float), minlength=k)
    oriented_sec = (buyv - sellv) * sgn
    # per-second last mid
    msec = np.full(k, np.nan); msec[sec_idx] = mz
    m_active = msec[~np.isnan(msec)]
    rho1, _ = persistence_stats(rs.astype(float))
    era, _, _ = efficiency_ratio(m_active, side)
    return dict(
        intensity_level=n / span_s,
        flow_level=float(oriented_sec.mean()),
        intensity_slope=norm_slope(counts),
        ER_abs=era,
        hurst=dfa_hurst(rs.astype(float)),
        rho1=rho1,
        abs_move_tk=abs(mz[-1] - mz[0]) / TICK,
        n=n, flagged=flagged,
    )


def two_sample_boot_ci(reach, stall, seed=0, B=10000):
    r = np.asarray(reach, float); s = np.asarray(stall, float)
    r = r[~np.isnan(r)]; s = s[~np.isnan(s)]
    if len(r) < 5 or len(s) < 5:
        return dict(auc=np.nan, lo=np.nan, hi=np.nan, nr=len(r), ns=len(s), excludes_half=False)
    auc, _, _ = rank_auc(r, s)
    rng = np.random.default_rng(seed)
    boot = np.empty(B)
    for i in range(B):
        rb = r[rng.integers(0, len(r), len(r))]; sb = s[rng.integers(0, len(s), len(s))]
        boot[i] = rank_auc(rb, sb)[0]
    lo, hi = float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))
    return dict(auc=float(auc), lo=lo, hi=hi, nr=len(r), ns=len(s),
                excludes_half=(lo > 0.5 or hi < 0.5))


def run(config, wrb, tau=TAU_S, seed=0):
    stall, reach, windowed = build_arms(config, wrb)
    for d in (stall, reach):
        d["tod"] = d.entry.map(lambda t: pd.Timestamp(t).tz_convert("America/New_York"))
        d["session_phase"] = d.tod.map(lambda t: t.hour * 60 + t.minute - (9 * 60 + 30))
    print(f"[arms] stall={len(stall)} reach={len(reach)} | tau={tau}s "
          f"| truncated (hold<tau): stall {int((stall.hold<tau).sum())} reach {int((reach.hold<tau).sum())}")
    t_min = min(stall.entry.min(), reach.entry.min()) - S(2)
    t_max = max((stall.entry + S(tau)).max(), (reach.entry + S(tau)).max())
    print(f"[read] {windowed}")
    ts_ns, rs, sz, mid = read_trade_full(windowed, t_min, t_max)
    print(f"[read] trade prints: {len(ts_ns):,}")

    def feats(df):
        out = []
        for _, r in df.iterrows():
            we = min(r.entry + S(tau), r.exit)
            f = window_features(ts_ns, rs, sz, mid, r.side, r.entry, we)
            if f is None:
                continue
            f["session_phase"] = float(r.session_phase)
            out.append(f)
        return pd.DataFrame(out)

    R, Sd = feats(reach), feats(stall)
    Rok, Sok = R[~R.flagged], Sd[~Sd.flagged]
    print(f"[scored] reach={len(Rok)} stall={len(Sok)}  (tripwire-flagged: "
          f"reach {int(R.flagged.sum())} stall {int(Sd.flagged.sum())})\n")

    FEATS = ["intensity_level", "flow_level", "intensity_slope", "ER_abs",
             "hurst", "rho1", "abs_move_tk", "session_phase"]
    print(f"{'feature':16s}  {'AUC(R>S)':>9s}  {'two-sided':>9s} {'dir':>11s}  {'95% CI':>16s}   flag")
    rows = []
    for f in FEATS:
        ci = two_sample_boot_ci(Rok[f], Sok[f], seed=seed)
        if not np.isfinite(ci["auc"]):
            print(f"{f:16s}  (insufficient valid)"); continue
        ts_ = ci["auc"] if ci["auc"] >= 0.5 else 1 - ci["auc"]
        dirn = "reach>stall" if ci["auc"] >= 0.5 else "stall>reach"
        flag = "** SEPARATES" if ci["excludes_half"] else "  -"
        print(f"{f:16s}  {ci['auc']:9.3f}  {ts_:9.3f} {dirn:>11s}  [{ci['lo']:.3f},{ci['hi']:.3f}]  {flag}")
        rows.append((f, ci))
    print(f"\nmedians (reach vs stall, scored windows):")
    for f in FEATS:
        print(f"  {f:16s} R med={Rok[f].median():+.4f}   S med={Sok[f].median():+.4f}")


def selftest(config, wrb):
    print("=== SELF-TEST: two-sample bootstrap AUC + window assembly ===")
    rng = np.random.default_rng(0)
    a = rng.normal(1, 1, 47); b = rng.normal(0, 1, 29)   # clear separation
    ci = two_sample_boot_ci(a, b, seed=0)
    print(f"  separated arms: AUC={ci['auc']:.3f} CI [{ci['lo']:.3f},{ci['hi']:.3f}] "
          f"excludes_half={ci['excludes_half']}  [expect True]")
    assert ci["excludes_half"] and ci["auc"] > 0.6
    a2 = rng.normal(0, 1, 47); b2 = rng.normal(0, 1, 29)  # no separation
    ci2 = two_sample_boot_ci(a2, b2, seed=0)
    print(f"  identical arms: AUC={ci2['auc']:.3f} CI [{ci2['lo']:.3f},{ci2['hi']:.3f}] "
          f"excludes_half={ci2['excludes_half']}  [expect False]")
    assert not ci2["excludes_half"]
    # window assembly on synthetic per-trade arrays (one 30s window, rising buy flow)
    base = pd.Timestamp("2025-10-06 14:00:00", tz="UTC").value
    ts = np.array([base + int(i * 1e9 * 0.1) for i in range(300)], dtype=np.int64)
    rs = np.where(np.arange(300) % 3 == 0, np.int8(-1), np.int8(1))  # buy-heavy
    sz = np.ones(300, dtype="int64"); mid = 5000 + np.arange(300) * 0.0  # flat mid
    f = window_features(ts, rs, sz, mid, "long", pd.Timestamp(base, tz="UTC"),
                        pd.Timestamp(base + int(30e9), tz="UTC"))
    print(f"  window assembly: n={f['n']} flow_level={f['flow_level']:+.2f} (buy-heavy long -> >0) "
          f"ER_abs={f['ER_abs'] if f['ER_abs']==f['ER_abs'] else 'NaN(flat mid)'}")
    assert f["flow_level"] > 0
    print("SELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--tau", type=int, default=TAU_S); ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest(a.config, a.wrb) if a.selftest else run(a.config, a.wrb, tau=a.tau, seed=a.seed)
