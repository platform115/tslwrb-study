#!/usr/bin/env python3
"""
trade_flow_exhaustion.py  — Test 06 / Round 1  (Phase B: realized trade-flow channel)
-------------------------------------------------------------------------------
Question: does aggressor volume IN THE TRADE'S DIRECTION dry up before adverse trades?
"Exhaustion" = oriented signed trade-flow weak / negative over the window. This is the REALIZED-TRADE
channel (action=="T", aggressor side, size) — orthogonal to the resting-book features in 03/04/05,
which all came back null. OFI-family (Cont, Kukanov, Stoikov 2014, "The price impact of order book
events"). Close edit of refill_resiliency.py (same reader of action/side/size).

ROUND 1 population: 16 actual losers (realized_pnl < 0) vs 47 non-loser target_reached.
  WHY 47 not 52: 5 of the 16 losers sit INSIDE target_reached (tagged pt1 then gave it back to a
  loss). Comparing 16-vs-52 would put those 5 on BOTH sides of the AUC (compared to themselves),
  inflating it. The 5 stay in the LOSER arm; they are removed from the COMPARISON arm. -> 16 vs 47.
  (Round 2, later, is 52 target_reached vs 40 failed_trades — those are disjoint, no de-dupe; same
  frozen feature params + firing/validity rules carry over.)

Feature (FROZEN, pre-registered before any flow number was seen):
  per second:  signed_flow = buy_vol(side=="B") - sell_vol(side=="A")        (aggressor-signed, int64)
               oriented    = signed_flow * (+1 long / -1 short)              (>0 = pressure WITH trade)
  per window:  LEVEL = mean(oriented per-second flow)            [PRIMARY — robust at n=16]
               SLOPE = OLS(oriented flow on elapsed seconds)     [SECONDARY — the literal "fade"]
  Pre-registered direction (both): AUC(reached oriented > loser oriented).  (losers = weaker flow)

Firing (FROZEN) for the freeze-worthiness rule:
  a trade FIRES the exhaustion flag if window oriented LEVEL < 0 (net flow against the trade).
  Report loser fire-rate, reached fire-rate, and AUC on the fired subset.
  FLOOR: a high AUC counts as a freeze candidate only on >= 8 VALID firings (valid = window has a
  defined feature, i.e. >=1 sec for level / >=2 sec for slope). Below 8 valid -> "uninformative,
  n too low", NOT a number to freeze. Windows < 2s report NaN (never a one-snapshot value).

Windows (= 05, per-second, anchor = pt1 reached / floor(exit) otherwise):
  A1 pre-entry [entry-180s, entry) ; A2 in-trade [max(entry,anchor-180s), anchor) ;
  B no-floor [anchor-180s, anchor) with pre_entry_frac stratification.
Tripwire: gap>120s or mid-jump>40 ticks -> flag+exclude (Oct ESZ5 expected 0). Design A (in-trade
tau, W=60s) on the decision-point reading. AUC + cluster-bootstrap CI (seed 0). Deterministic,
memory-safe single streamed pass. Relies on CURRENT_STATE conventions.

    python3 trade_flow_exhaustion.py --config config.toml --wrb /path/to/wrb_1m.parquet
"""

import argparse, tomllib
import numpy as np, pandas as pd

INSTRUMENT_ID = 294973
TS_COL = "ts_event"; ACT = "action"; SIDE = "side"; SZ = "size"
BID_PX0, ASK_PX0 = "bid_px_00", "ask_px_00"
WRB_TF, MONTH, SYMBOL = "1m", "2025-10", "ESZ5"
WINDOW_S = 180; TICK = 0.25
MAX_GAP_S = 120; ROLL_JUMP_TICKS = 40
M = lambda n: pd.Timedelta(minutes=n); S = lambda n: pd.Timedelta(seconds=n)
floor_min = lambda t: t.floor("min")


def load_paths(c):
    with open(c, "rb") as f:
        cfg = tomllib.load(f)
    return cfg["paths"]["episodes"], cfg.get("run", {}).get("resolved", {}).get("windowed_parquet")


def build_groups(episodes_path, wrb_path):
    """Reading B grouping + realized_pnl + three windows. Round-1 arms derived in main()."""
    lo = pd.Timestamp(f"{MONTH}-01"); hi = lo + pd.offsets.MonthBegin(1)
    ep = pd.read_parquet(episodes_path); ep["td"] = pd.to_datetime(ep["trading_date"])
    o = ep[(ep["td"] >= lo) & (ep["td"] < hi)].copy().reset_index(drop=True)
    w = pd.read_parquet(wrb_path)
    w = w[(w["ts_event"] >= lo.tz_localize("UTC")) & (w["ts_event"] < hi.tz_localize("UTC"))].copy()
    if "timeframe" in w.columns:
        w = w[w["timeframe"] == WRB_TF]
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
        a1_s, a1_e = entry - S(WINDOW_S), entry
        a2_s, a2_e = max(entry, anchor - S(WINDOW_S)), anchor
        b_s, b_e = anchor - S(WINDOW_S), anchor
        pre = max(0.0, WINDOW_S - (anchor - entry).total_seconds())
        rows.append(dict(
            uid=f"{r['source_file']}::{r['episode_id']}", side=side, entry=entry, exit=exit_,
            group="target_reached" if reached else "failed_trades", realized_pnl=r["realized_pnl"],
            hold=hold, pt1_open_el=((pt1 - entry).total_seconds() if reached else np.nan),
            is_entry_bar_pt1=bool(reached and pt1 == emin),
            a1_s=a1_s, a1_e=a1_e, a2_s=a2_s, a2_e=a2_e, b_s=b_s, b_e=b_e, pre_entry_frac=pre / WINDOW_S))
    return pd.DataFrame(rows)


def read_per_second(windowed, t_min, t_max):
    """Per-second arrays: sec, oriented-able signed flow components (buyv, sellv summed per second),
    and mid (last per second). Memory-safe single streamed pass. ~256k rows/month."""
    import pyarrow.parquet as pq, pyarrow as pa
    need = [TS_COL, ACT, SIDE, SZ, BID_PX0, ASK_PX0, "instrument_id"]
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
        act = b.column(ACT).to_numpy(zero_copy_only=False)[idx]
        sd = b.column(SIDE).to_numpy(zero_copy_only=False)[idx]
        sz = b.column(SZ).to_numpy(zero_copy_only=False)[idx].astype("int64")
        bp = b.column(BID_PX0).to_numpy(zero_copy_only=False)[idx]
        ap = b.column(ASK_PX0).to_numpy(zero_copy_only=False)[idx]
        is_t = act == "T"
        buyv = np.where(is_t & (sd == "B"), sz, 0)     # buy-aggressor volume
        sellv = np.where(is_t & (sd == "A"), sz, 0)    # sell-aggressor volume
        d = {"sec": ts[idx] // 1_000_000_000, "buyv": buyv, "sellv": sellv, "mid": (bp + ap) / 2}
        df = pd.DataFrame(d)
        agg = df.groupby("sec").agg(buyv=("buyv", "sum"), sellv=("sellv", "sum"), mid=("mid", "last"))
        parts.append(agg)
    if not parts:
        raise SystemExit("[read] zero rows in range")
    out = pd.concat(parts).groupby(level=0).agg(buyv=("buyv", "sum"), sellv=("sellv", "sum"),
                                                mid=("mid", "last")).sort_index()
    return (out.index.to_numpy(), out["buyv"].to_numpy().astype("int64"),
            out["sellv"].to_numpy().astype("int64"), out["mid"].to_numpy())


def score(sec, buyv, sellv, mid, ws, we, side, tick=TICK):
    """Returns (level, slope, n, mid_chg, flagged). oriented signed flow = (buyv-sellv)*sign."""
    a = np.searchsorted(sec, np.int64(pd.Timestamp(ws).value // 1_000_000_000), "left")
    b = np.searchsorted(sec, np.int64(pd.Timestamp(we).value // 1_000_000_000), "left")
    s = sec[a:b]; bv = buyv[a:b]; sv = sellv[a:b]; mz = mid[a:b]
    n = len(s)
    if n < 1:
        return np.nan, np.nan, 0, np.nan, False
    flagged = False
    if n >= 2:
        if np.diff(s).max() > MAX_GAP_S:
            flagged = True
        if (np.abs(np.diff(mz)) / tick).max() > ROLL_JUMP_TICKS:
            flagged = True
    sgn = 1.0 if side == "long" else -1.0
    y = (bv - sv).astype(float) * sgn
    level = float(np.mean(y))
    if n >= 2:
        x = (s - s[0]).astype(float); vx = x.var()
        slope = float(np.cov(x, y)[0, 1] / vx) if vx > 0 else 0.0
    else:
        slope = np.nan
    mid_chg = float((mz[-1] - mz[0]) * sgn) if n >= 2 else np.nan
    return level, slope, n, mid_chg, flagged


def auc_pair(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan, len(a), len(b)
    gt = (a[:, None] > b[None, :]).sum() + 0.5 * (a[:, None] == b[None, :]).sum()
    return gt / (len(a) * len(b)), len(a), len(b)


def cluster_boot_ci(per_cut, seed=0, B=10000):
    pc = np.asarray(per_cut, float); pc = pc[~np.isnan(pc)]
    if len(pc) < 5:
        return np.nan, np.nan, np.nan, len(pc)
    rng = np.random.default_rng(seed)
    boot = np.array([rng.choice(pc, len(pc), True).mean() for _ in range(B)])
    return float(pc.mean()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)), len(pc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--designA-window-seconds", type=int, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="trade_flow_exhaustion_results.csv")
    args = ap.parse_args()

    ep_path, windowed = load_paths(args.config)
    g = build_groups(ep_path, args.wrb)

    # ---- Round-1 arms: 16 losers vs 47 non-loser reached ----
    g["is_loser"] = g["realized_pnl"] < 0
    losers = g[g.is_loser].copy()
    reached_nonloser = g[(g.group == "target_reached") & (~g.is_loser)].copy()
    print(f"[build] losers={len(losers)} (in reached={int((losers.group=='target_reached').sum())}, "
          f"in failed={int((losers.group=='failed_trades').sum())}) | "
          f"comparison non-loser reached={len(reached_nonloser)}")
    assert len(losers) == 16 and len(reached_nonloser) == 47, "ROUND-1 ARM DRIFT"

    arms = pd.concat([losers.assign(arm="loser"), reached_nonloser.assign(arm="reached")])

    Wd = S(args.designA_window_seconds)
    t_min = arms["a1_s"].min(); t_max = max(arms["a2_e"].max(), arms["b_e"].max())
    print(f"[read] streaming per-second trade flow in [{t_min}, {t_max}) ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[read] per-second rows: {len(sec):,} ({len(sec)/3600:.1f} grid-hours)")

    for tag in ["a1", "a2", "b"]:
        lv, sl, nn, mc, fl = [], [], [], [], []
        for _, r in arms.iterrows():
            level, slope, n, midc, flag = score(sec, buyv, sellv, mid, r[f"{tag}_s"], r[f"{tag}_e"], r.side)
            lv.append(level); sl.append(slope); nn.append(n); mc.append(midc); fl.append(flag)
        arms[f"{tag}_level"] = lv; arms[f"{tag}_slope"] = sl
        arms[f"{tag}_n"] = nn; arms[f"{tag}_midchg"] = mc; arms[f"{tag}_flag"] = fl

    nflag = int(arms[["a1_flag", "a2_flag", "b_flag"]].to_numpy().sum())
    print(f"[tripwire] flagged windows: {nflag} (expected 0)")
    chk = arms.dropna(subset=["b_level", "b_midchg"])
    if len(chk) > 5:
        cc = np.corrcoef(chk["b_level"], chk["b_midchg"])[0, 1]
        print(f"[selfcheck] corr(mean oriented flow, oriented mid change) over B = {cc:+.3f} (expect >0)")

    def report(win, stat):
        d = arms[~arms[f"{win}_flag"]]
        r = d.loc[d.arm == "reached", f"{win}_{stat}"]
        l = d.loc[d.arm == "loser", f"{win}_{stat}"]
        auc, nr, nl = auc_pair(r, l)
        # valid-n note for floor rule
        print(f"  {stat:6s} AUC(reached>loser)={auc:.3f}  (reached n={nr}, loser n={nl})  "
              f"med R={np.nanmedian(r):+.1f} L={np.nanmedian(l):+.1f}")

    print(f"\n===== ROUND 1: 16 losers vs 47 non-loser reached =====")
    for win, name in [("a1", "A1 pre-entry"), ("a2", "A2 in-trade run-up"), ("b", "B decision-point(no-floor)")]:
        print(f"\n-- {name} --")
        report(win, "level"); report(win, "slope")

    # ---- FIRING (oriented level < 0) + floor-8-on-valid rule ----
    print(f"\n===== FIRING: exhaustion flag = oriented LEVEL < 0  (freeze rule: >=8 VALID loser firings) =====")
    for win, name in [("a1", "A1"), ("a2", "A2"), ("b", "B")]:
        d = arms[~arms[f"{win}_flag"]]
        L = d[d.arm == "loser"]; R = d[d.arm == "reached"]
        Lv = L.dropna(subset=[f"{win}_level"]); Rv = R.dropna(subset=[f"{win}_level"])
        l_fire = int((Lv[f"{win}_level"] < 0).sum()); r_fire = int((Rv[f"{win}_level"] < 0).sum())
        print(f"  {name}: loser fires {l_fire}/{len(Lv)} valid | reached fires {r_fire}/{len(Rv)} valid", end="")
        if l_fire >= 8:
            # AUC on fired subset (fired losers vs fired reached) — only if floor met
            lf = Lv.loc[Lv[f"{win}_level"] < 0, f"{win}_level"]
            rf = Rv.loc[Rv[f"{win}_level"] < 0, f"{win}_level"]
            auc, _, _ = auc_pair(rf, lf)
            print(f"  -> >=8: AUC on fired subset = {auc:.3f}")
        else:
            print(f"  -> <8 valid loser firings: UNINFORMATIVE, do not freeze")

    # ---- Design A (in-trade tau) on decision-point, level ----
    print(f"\n===== CONTROL Design A (cut-time-matched, in-trade tau, W={args.designA_window_seconds}s, level) =====")
    R = reached_nonloser
    per_cut = []
    for _, f in losers.iterrows():
        cut = f["exit"]
        cv, _, _, _, cflag = score(sec, buyv, sellv, mid, max(f.entry, cut - Wd), cut, f.side)
        if np.isnan(cv) or cflag:
            continue
        peers = R[R.pt1_open_el > f.hold]
        pv = []
        for _, rr in peers.iterrows():
            anc = rr.entry + S(f.hold)
            v, _, _, _, pflag = score(sec, buyv, sellv, mid, max(rr.entry, anc - Wd), anc, rr.side)
            if not np.isnan(v) and not pflag:
                pv.append(v)
        if pv:
            pv = np.array(pv)
            per_cut.append((np.sum(pv > cv) + 0.5 * np.sum(pv == cv)) / len(pv))
    m, lo, hi, npc = cluster_boot_ci(per_cut, args.seed)
    print(f"  AUC(per-cut, {npc}) = P(peer flow > loser flow) = {m:.3f}  95% CI [{lo:.3f}, {hi:.3f}]"
          + ("" if npc >= 8 else "   (<8 cuts: uninformative)"))

    # ---- B composition check ----
    print(f"\n===== B composition check: stratify by pre_entry_frac (median split) =====")
    med = arms["pre_entry_frac"].median()
    for lab, mask in [("LOW (<=med)", arms.pre_entry_frac <= med), ("HIGH (>med)", arms.pre_entry_frac > med)]:
        d = arms[mask & ~arms.b_flag]
        auc, nr, nl = auc_pair(d.loc[d.arm == "reached", "b_level"], d.loc[d.arm == "loser", "b_level"])
        print(f"  {lab:12s} B level AUC={auc:.3f} (reached {nr}, loser {nl})")
    print("  NOTE: signal only in HIGH stratum = composition artifact.")

    arms.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
