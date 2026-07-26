#!/usr/bin/env python3
"""
book_points_against_trade.py  — Test 05  (Phase B: directional book signal)
-------------------------------------------------------------------------------
Question: does the population-oriented book direction (bid-heavy = up; oriented +1 long / -1 short)
point AGAINST the trade more, or more strongly, for non-runners (failed_trades) than for runners
(target_reached)?  "points against" = negative oriented imbalance.

This is a close edit of Test 03 (queue_imbalance_slope.py). What is REUSED unchanged:
  - grouping (Reading B inclusive pt1 -> 52 target_reached / 40 failed_trades),
  - the memory-safe per-batch streamed reader (downsampled to one snapshot per second),
  - pure-numpy AUC + cluster-bootstrap CI,
  - Design A cut-time-matched control.
What is NEW / different from 03 (this is why 05 is not a rerun):
  - DEPTH: L1 primary (population says L1 carries the signal; 03 used diluted L1-10). L1-5 ride-along.
  - STATISTIC: per-second oriented LEVEL is primary (population-supported); OLS slope is secondary
    (03's spent statistic, here at the untested L1 depth so we can see if 03's slope-null was the
    depth or the slope).
  - THREE pre-registered windows, per the design agreed before coding:
      A1  pre-entry context   [entry-180s, entry)         fixed 180s, identical both groups.
      A2  in-trade run-up     [max(entry, anchor-180s), anchor)   entry-floored, anchor excluded.
      B   decision-point      [anchor-180s, anchor)        NO entry floor (live-screen feature).
    anchor = pt1 bar (reached) / floor(exit) (failed), as in 03/04.

Pre-registered directions (all): AUC(reached feature > failed feature).
  level: reached should be LESS against (higher oriented) than failed.
  slope: reached oriented imbalance should hold up / rise vs failed fading.

CONFOUND CONTROL (measured before coding):
  B's window is back-anchored with no floor, so its pre-entry FRACTION differs by group
  (reached ~0.73 vs failed ~0.58; AUC of the fraction alone = 0.621, in the pre-registered
  direction). So B reports pre_entry_frac per trade and prints the AUC STRATIFIED by a median
  split on pre_entry_frac. A B result that only appears in the high-fraction stratum is the
  composition artifact, not a book signal. B is exploratory-with-caveat by construction.

  A1 Design A: collapses to PRIMARY (fixed-length pre-entry window -> no elapsed-time/survivorship
  confound to control; every reached trade is an eligible peer; per-cut AUC == pooled AUC). We
  therefore report A1 PRIMARY and add a cluster-bootstrap CI over the 40 failed as the only thing
  "Design A" contributes pre-entry. Real Design A (in-trade tau) runs on the decision-point reading.

TRIPWIRE: any feature window whose in-window per-second snapshots contain a gap > MAX_GAP_S
(session/maintenance break) or a mid jump > ROLL_JUMP_TICKS (roll basis) is FLAGGED and excluded
from that feature. For October ESZ5 (single front month, intraday episodes) this is expected to
flag zero windows; it is a data-integrity tripwire, not a constraint.

Relies on CURRENT_STATE conventions (open-stamp; WRB+60s; MBP-10 schema; ESZ5; sizes uint32->int64;
imbalance orientation +1 long / -1 short). Deterministic. Memory-safe (single streamed pass,
per-second downsample -> ~256k rows for the whole month).

    python3 book_points_against_trade.py --config config.toml --wrb /path/to/wrb_1m.parquet
"""

import argparse, tomllib
import numpy as np, pandas as pd

INSTRUMENT_ID = 294973
TS_COL = "ts_event"
BID_SZ = [f"bid_sz_0{i}" for i in range(10)]
ASK_SZ = [f"ask_sz_0{i}" for i in range(10)]
BID_PX0, ASK_PX0 = "bid_px_00", "ask_px_00"
WRB_TIMEFRAME, MONTH, SYMBOL = "1m", "2025-10", "ESZ5"
WINDOW_S = 180                      # pre-registered feature window (3 min), per design
TICK = 0.25
MAX_GAP_S = 120                    # tripwire: gap between consecutive in-window seconds (session/halt)
ROLL_JUMP_TICKS = 40              # tripwire: per-second mid jump that big => roll/discontinuity
M = lambda n: pd.Timedelta(minutes=n)
S = lambda n: pd.Timedelta(seconds=n)
floor_min = lambda t: t.floor("min")


def load_paths(c):
    with open(c, "rb") as f:
        cfg = tomllib.load(f)
    return cfg["paths"]["episodes"], cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")


# ---------------------------------------------------------------------------
# Grouping + window construction (= CURRENT_STATE; Reading B inclusive pt1).
# Three windows per trade. anchor = pt1 (reached) / floor(exit) (failed).
# ---------------------------------------------------------------------------
def build_groups(episodes_path, wrb_path):
    lo = pd.Timestamp(f"{MONTH}-01"); hi = lo + pd.offsets.MonthBegin(1)
    ep = pd.read_parquet(episodes_path); ep["td"] = pd.to_datetime(ep["trading_date"])
    o = ep[(ep["td"] >= lo) & (ep["td"] < hi)].copy().reset_index(drop=True)
    w = pd.read_parquet(wrb_path)
    w = w[(w["ts_event"] >= lo.tz_localize("UTC")) & (w["ts_event"] < hi.tz_localize("UTC"))].copy()
    if "timeframe" in w.columns:
        w = w[w["timeframe"] == WRB_TIMEFRAME]
    w = w[w["symbol"] == SYMBOL].sort_values("ts_event")
    rows = []
    for _, r in o.iterrows():
        side, entry, exit_ = r["side"], r["first_entry_utc"], r["last_exit_utc"]
        emin = floor_min(entry); want = "bullish" if side == "long" else "bearish"
        cand = w[(w["direction"] == want) & (w["ts_event"] >= emin)]
        pt1 = cand.iloc[0]["ts_event"] if len(cand) else pd.NaT
        reached = (len(cand) > 0) and (exit_ >= pt1 + M(1))
        anchor = pt1 if reached else floor_min(exit_)
        hold = (exit_ - entry).total_seconds()
        # three windows
        a1_s, a1_e = entry - S(WINDOW_S), entry                       # pre-entry, fixed 180s
        a2_s, a2_e = max(entry, anchor - S(WINDOW_S)), anchor          # in-trade run-up, entry-floored
        b_s,  b_e  = anchor - S(WINDOW_S), anchor                      # no-floor decision-point
        pre_entry_s = max(0.0, WINDOW_S - (anchor - entry).total_seconds())   # how much of B is pre-entry
        rows.append(dict(
            uid=f"{r['source_file']}::{r['episode_id']}", side=side, entry=entry, exit=exit_,
            group="target_reached" if reached else "failed_trades",
            hold=hold, pt1_open_el=((pt1 - entry).total_seconds() if reached else np.nan),
            is_entry_bar_pt1=bool(reached and pt1 == emin),
            a1_s=a1_s, a1_e=a1_e, a2_s=a2_s, a2_e=a2_e, b_s=b_s, b_e=b_e,
            pre_entry_frac=pre_entry_s / WINDOW_S))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Reader: single streamed pass, downsample to one snapshot per second.
# Returns per-second arrays: sec (int64), imb_L1, imb_L5, mid.  ~256k rows / month.
# (Per-second matches the population diagnostic convention and is memory-trivial.)
# ---------------------------------------------------------------------------
def read_per_second(windowed, t_min, t_max):
    import pyarrow.parquet as pq, pyarrow as pa
    need = [TS_COL, BID_PX0, ASK_PX0, "instrument_id"] + BID_SZ[:5] + ASK_SZ[:5]
    pf = pq.ParquetFile(windowed)
    miss = [c for c in need if c not in set(pf.schema_arrow.names)]
    if miss:
        raise SystemExit(f"[schema] missing {miss}")
    tmin_ns = pd.Timestamp(t_min).value; tmax_ns = pd.Timestamp(t_max).value
    parts = []
    for b in pf.iter_batches(batch_size=200_000, columns=need):
        ts = b.column(TS_COL).cast(pa.timestamp("ns")).cast(pa.int64()).to_numpy(zero_copy_only=False)
        m = (ts >= tmin_ns) & (ts < tmax_ns)
        if INSTRUMENT_ID is not None:
            m &= b.column("instrument_id").to_numpy(zero_copy_only=False) == INSTRUMENT_ID
        if not m.any():
            continue
        idx = np.flatnonzero(m)
        b0 = b.column(BID_SZ[0]).to_numpy(zero_copy_only=False)[idx].astype("int64")
        a0 = b.column(ASK_SZ[0]).to_numpy(zero_copy_only=False)[idx].astype("int64")
        b5 = np.zeros(len(idx), "int64"); a5 = np.zeros(len(idx), "int64")
        for c in BID_SZ[:5]: b5 += b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64")
        for c in ASK_SZ[:5]: a5 += b.column(c).to_numpy(zero_copy_only=False)[idx].astype("int64")
        bp = b.column(BID_PX0).to_numpy(zero_copy_only=False)[idx]
        ap = b.column(ASK_PX0).to_numpy(zero_copy_only=False)[idx]
        t1 = b0 + a0; t5 = b5 + a5
        d = {"sec": ts[idx] // 1_000_000_000,
             "imb_L1": np.where(t1 > 0, (b0 - a0) / np.where(t1 > 0, t1, 1), np.nan),
             "imb_L5": np.where(t5 > 0, (b5 - a5) / np.where(t5 > 0, t5, 1), np.nan),
             "mid": (bp + ap) / 2}
        parts.append(pd.DataFrame(d).groupby("sec").last())
    if not parts:
        raise SystemExit("[read] zero snapshots in range")
    out = pd.concat(parts).groupby(level=0).last().sort_index()
    return (out.index.to_numpy(),
            out["imb_L1"].to_numpy(), out["imb_L5"].to_numpy(), out["mid"].to_numpy())


# ---------------------------------------------------------------------------
# Feature scoring on one window.  Returns (level, slope, n, mid_chg, flagged).
# oriented = imb * (+1 long / -1 short).  level = mean; slope = OLS on elapsed sec.
# ---------------------------------------------------------------------------
def score(sec, imb, mid, ws, we, side, tick=TICK):
    a = np.searchsorted(sec, np.int64(pd.Timestamp(ws).value // 1_000_000_000), "left")
    b = np.searchsorted(sec, np.int64(pd.Timestamp(we).value // 1_000_000_000), "left")
    s = sec[a:b]; y_raw = imb[a:b]; mz = mid[a:b]
    ok = ~np.isnan(y_raw)
    s, y_raw, mz = s[ok], y_raw[ok], mz[ok]
    n = len(s)
    if n < 1:
        return np.nan, np.nan, 0, np.nan, False
    flagged = False
    if n >= 2:
        gaps = np.diff(s)
        if gaps.max() > MAX_GAP_S:
            flagged = True
        if (np.abs(np.diff(mz)) / tick).max() > ROLL_JUMP_TICKS:
            flagged = True
    sgn = 1.0 if side == "long" else -1.0
    y = y_raw * sgn
    level = float(np.mean(y))
    if n >= 2:
        x = (s - s[0]).astype(float)
        vx = x.var()
        slope = float(np.cov(x, y)[0, 1] / vx) if vx > 0 else 0.0
    else:
        slope = np.nan
    mid_chg = float((mz[-1] - mz[0]) * sgn) if n >= 2 else np.nan
    return level, slope, n, mid_chg, flagged


def auc_pair(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan, 0, 0
    gt = (a[:, None] > b[None, :]).sum() + 0.5 * (a[:, None] == b[None, :]).sum()
    return gt / (len(a) * len(b)), len(a), len(b)


def cluster_boot_ci(per_cut, seed=0, B=10000):
    per_cut = np.asarray(per_cut, float); per_cut = per_cut[~np.isnan(per_cut)]
    if len(per_cut) < 5:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    boot = np.array([rng.choice(per_cut, len(per_cut), True).mean() for _ in range(B)])
    return float(per_cut.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--wrb", required=True)
    ap.add_argument("--designA-window-seconds", type=int, default=60)   # 03/04 trailing W
    ap.add_argument("--depth", choices=["L1", "L5"], default="L1")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="book_points_against_trade_results.csv")
    args = ap.parse_args()

    ep_path, windowed = load_paths(args.config)
    g = build_groups(ep_path, args.wrb)
    print(f"[build] target_reached={int((g.group=='target_reached').sum())} "
          f"failed_trades={int((g.group=='failed_trades').sum())} | "
          f"entry-bar-pt1={int(g.is_entry_bar_pt1.sum())}")

    # global read range: earliest A1 start .. latest anchor (B/A2 end). + DesignA peer reach.
    Wd = S(args.designA_window_seconds)
    t_min = g["a1_s"].min()
    t_max = max(g["a2_e"].max(), g["b_e"].max())
    # DesignA peers reach to peer.entry + tau; bounded by t_max already (peers are reached trades).
    print(f"[read] streaming per-second book in [{t_min}, {t_max}) ...")
    sec, imbL1, imbL5, mid = read_per_second(windowed, t_min, t_max)
    print(f"[read] per-second snapshots: {len(sec):,} ({len(sec)/3600:.1f} grid-hours)")
    imb = imbL1 if args.depth == "L1" else imbL5

    # ---- score the three PRIMARY windows per trade ----
    for tag in ["a1", "a2", "b"]:
        lv, sl, nn, mc, fl = [], [], [], [], []
        for _, r in g.iterrows():
            ws, we = r[f"{tag}_s"], r[f"{tag}_e"]
            level, slope, n, midc, flag = score(sec, imb, mid, ws, we, r.side)
            lv.append(level); sl.append(slope); nn.append(n); mc.append(midc); fl.append(flag)
        g[f"{tag}_level"] = lv; g[f"{tag}_slope"] = sl
        g[f"{tag}_n"] = nn; g[f"{tag}_midchg"] = mc; g[f"{tag}_flag"] = fl

    nflag = int(g[["a1_flag", "a2_flag", "b_flag"]].to_numpy().sum())
    print(f"[tripwire] windows flagged (gap>{MAX_GAP_S}s or mid jump>{ROLL_JUMP_TICKS} ticks): "
          f"{nflag}  (expected 0 for Oct ESZ5)")

    # ---- orientation self-check on B (mean oriented level vs oriented mid change) ----
    chk = g.dropna(subset=["b_level", "b_midchg"])
    if len(chk) > 5:
        cc = np.corrcoef(chk["b_level"], chk["b_midchg"])[0, 1]
        print(f"[selfcheck] corr(mean oriented L1 level, oriented mid change) over B = {cc:+.3f}  "
              f"(expect >0; population L1 sign is +1)")

    def report(col, label, exclude_flag):
        d = g.copy()
        if exclude_flag:
            d = d[~d[f"{col.split('_')[0]}_flag"]]
        rA = d.loc[d.group == "target_reached", col]
        fA = d.loc[d.group == "failed_trades", col]
        auc, nr, nf = auc_pair(rA, fA)
        print(f"  {label:28s} AUC(reached>failed)={auc:.3f}  "
              f"(reached {nr}, failed {nf})  med R={np.nanmedian(rA):+.3f} F={np.nanmedian(fA):+.3f}")

    print(f"\n===== PRIMARY 52/40  (depth={args.depth})  level = primary, slope = secondary =====")
    for win, name in [("a1", "A1 pre-entry"), ("a2", "A2 in-trade run-up"), ("b", "B decision-point(no-floor)")]:
        print(f"\n-- {name} --")
        report(f"{win}_level", "level", True)
        report(f"{win}_slope", "slope", True)
        # excl entry-bar-pt1 (the 22)
        d2 = g[~g.is_entry_bar_pt1]
        for stat in ["level", "slope"]:
            rA = d2.loc[d2.group == "target_reached", f"{win}_{stat}"]
            fA = d2.loc[d2.group == "failed_trades", f"{win}_{stat}"]
            auc, nr, nf = auc_pair(rA, fA)
            print(f"  {stat+' (excl-22)':28s} AUC={auc:.3f}  (reached {nr}, failed {nf})")

    # ---- A1 cluster-bootstrap CI (the only thing 'Design A' adds pre-entry) ----
    F = g[g.group == "failed_trades"]; R = g[g.group == "target_reached"]
    per_cut_a1 = []
    rl = R["a1_level"].to_numpy()
    for _, f in F.iterrows():
        fv = f["a1_level"]
        if np.isnan(fv):
            continue
        rr = rl[~np.isnan(rl)]
        per_cut_a1.append((np.sum(rr > fv) + 0.5 * np.sum(rr == fv)) / len(rr))
    m, lo, hi = cluster_boot_ci(per_cut_a1, args.seed)
    print(f"\n-- A1 'Design A' == PRIMARY (fixed pre-entry window) -> point est coincides; CI added --")
    print(f"  A1 level AUC = {m:.3f}  95% CI [{lo:.3f}, {hi:.3f}]  (cluster-bootstrap over {len(per_cut_a1)} failed)")

    # ---- Real Design A: cut-time-matched in-trade tau, trailing W, on oriented LEVEL ----
    print(f"\n===== CONTROL Design A (cut-time-matched, in-trade tau, W={args.designA_window_seconds}s, level) =====")
    per_cut = []
    for _, f in F.iterrows():
        cut = f["exit"]
        cv, _, cn, _, cflag = score(sec, imb, mid, max(f.entry, cut - Wd), cut, f.side)
        if np.isnan(cv) or cflag:
            continue
        peers = R[R.pt1_open_el > f.hold]
        pv = []
        for _, rr in peers.iterrows():
            anc = rr.entry + S(f.hold)
            v, _, pn, _, pflag = score(sec, imb, mid, max(rr.entry, anc - Wd), anc, rr.side)
            if not np.isnan(v) and not pflag:
                pv.append(v)
        if pv:
            pv = np.array(pv)
            per_cut.append((np.sum(pv > cv) + 0.5 * np.sum(pv == cv)) / len(pv))
    m, lo, hi = cluster_boot_ci(per_cut, args.seed)
    print(f"  AUC(per-cut, {len(per_cut)}) = P(peer level > cut level) = {m:.3f}  95% CI [{lo:.3f}, {hi:.3f}]")

    # ---- B stratified by pre_entry_frac (composition-artifact check) ----
    print(f"\n===== B composition check: stratify by pre_entry_frac (median split) =====")
    med = g["pre_entry_frac"].median()
    print(f"  pre_entry_frac median={med:.2f}  (reached mean={R.pre_entry_frac.mean():.2f}, "
          f"failed mean={F.pre_entry_frac.mean():.2f})")
    for lab, mask in [("LOW pre-entry (<=med)", g.pre_entry_frac <= med),
                      ("HIGH pre-entry (>med)", g.pre_entry_frac > med)]:
        d = g[mask & ~g.b_flag]
        rA = d.loc[d.group == "target_reached", "b_level"]
        fA = d.loc[d.group == "failed_trades", "b_level"]
        auc, nr, nf = auc_pair(rA, fA)
        print(f"  {lab:24s} B level AUC={auc:.3f}  (reached {nr}, failed {nf})")
    print("  NOTE: a B signal present ONLY in the HIGH stratum is the composition artifact, not book direction.")

    g.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
