#!/usr/bin/env python3
"""
test_gap_capture_v2.py — WHG-capture trades, REBUILT with correct directional traversal label
-------------------------------------------------------------------------------
SUPERSEDES test_gap_traverse_exit.py, which had a LABEL BUG: it used both-edges coverage
(max_high>=top AND min_low<=bottom), so a long entering near the bottom and running UP never re-satisfied
min_low<=bottom -> traversal massively under-counted (false 6/34). All conclusions from that script
(AUC, velocity, +0.00 S1 corr) are INVALID. This uses the correct DIRECTIONAL far-edge label.

SCOPE: these ~34 trades were entered to CAPTURE WHG action — a specific setup. S1/S2 are GENERAL exit
signals (derived across all trades), not WHG-specific. So WHG trades are analyzed as their OWN
population here, NOT pooled into 16/47 or 52/40, and NOT assumed to behave like S1/S2 trades. The
relationship to S1 is reported as an OPEN check, not an assumption.

LABEL (directional, 1m TRUE extremes over [entry,exit]):
  traversal_frac = (max_high - whg_bottom)/(whg_top-whg_bottom)  [long]   ; symmetric for short.
  traversed (binary) = traversal_frac >= 1.0 (far edge reached). extension = traversal_frac (>1 = ran past).

PART A: binary traverse vs not (we expect ~29 vs ~5 -> non-traversers described, predictor n-limited).
PART B: among TRAVERSERS, what early/forward signal separates big-runs (eventual reached) from
  stall-at-gap (eventual failed)? Predictors: early gap-progress(tau) + velocity (time-to-half), still-open.
S1 CHECK: corr(gap_progress@60, body_ratio@60) and corr(extension, body_ratio@60) — open, not assumed.
OVERLAP: how many WHG-capture trades fall in the existing loser/reached sets (separation diagnostic).

Two-sided. SSD MOUNTED (per-second mid). October ESZ5. SMALL n (~34; traverser-failed arm ~8) — most
reads are descriptive/suggestive, holdout-pending. Not financial advice.

RUN (from 06-10_whg_fill/)
  python3 test_gap_capture_v2.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end ---

import argparse, tomllib
import numpy as np, pandas as pd

import horse_race_spine as spine
from trade_flow_exhaustion import build_groups, read_per_second, S, M

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
TF_DUR_5M = 300; WIN_S = 2 * 86400; NEAR = 8 * 0.25
TAUS = [30, 60, 90, 120]; TAU_PRIMARY = 60; FINE = list(range(15, 181, 15))


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["run"]["resolved"]["windowed_parquet"], cfg["paths"]["es_1m_front"], cfg["paths"]["es_5m_front"]


def load_bars(path):
    d = pd.read_parquet(path, columns=["ts_event", "instrument_id", "open", "high", "low", "close", "session_date"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    return d.sort_values("ts_event").reset_index(drop=True)


def identify_whg(df):
    o = df.open.to_numpy(); c = df.close.to_numpy()
    sd = df.session_date.astype(str).to_numpy(); body = np.abs(c - o); n = len(df); out = []
    for i in range(3, n):
        if not (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]) or body[i] <= 0:
            continue
        if not (body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]):
            continue
        if c[i] > o[i]:
            pbh = max(max(o[i-1], c[i-1]), max(o[i-2], c[i-2]), max(o[i-3], c[i-3]))
            if c[i] > pbh: out.append((i, "bullish", pbh, c[i]))
        elif c[i] < o[i]:
            pbl = min(min(o[i-1], c[i-1]), min(o[i-2], c[i-2]), min(o[i-3], c[i-3]))
            if c[i] < pbl: out.append((i, "bearish", c[i], pbl))
    return out


def fill_s(bsec, bhi, blo, top, bot, idx, dur):
    hi = bhi[idx+1:]; lo = blo[idx+1:]; ss = bsec[idx+1:]
    if len(hi) == 0: return np.inf
    both = (np.maximum.accumulate(hi) >= top) & (np.minimum.accumulate(lo) <= bot)
    k = int(np.argmax(both)) if both.any() else -1
    return float(ss[k] + dur) if k >= 0 else np.inf


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    g, windowed, es1m, es5m = load(args.config, args.wrb)

    b5 = load_bars(es5m); s5 = (b5.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    h5 = b5.high.to_numpy(); l5 = b5.low.to_numpy()
    W = pd.DataFrame([dict(comp_s=int(s5[i] + TF_DUR_5M), fill_s=fill_s(s5, h5, l5, top, bot, i, TF_DUR_5M),
                           top=top, bot=bot) for (i, d, bot, top) in identify_whg(b5)])
    b1 = load_bars(es1m); s1 = (b1.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    h1 = b1.high.to_numpy(); l1 = b1.low.to_numpy(); o1 = b1.open.to_numpy(); c1 = b1.close.to_numpy()

    def prior_body_max(entry_ts):
        e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
        j = int(np.searchsorted(s1, e_s, "left"))
        return float(np.abs(c1[j-3:j] - o1[j-3:j]).max()) if j >= 3 else np.nan

    print("[gap2] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, g["entry"].min() - M(5), g["exit"].max() + M(1))

    def mid_prog(entry_ts, cp_ts, top, bot, side):
        e = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
        cps = np.int64(pd.Timestamp(cp_ts).value // 1_000_000_000)
        i0 = np.searchsorted(sec, e, "left"); i1 = np.searchsorted(sec, cps, "left")
        if i1 - i0 < 2: return 0.0
        seg = mid[i0:i1]; zone = top - bot
        return ((seg.max() - bot) / zone) if side == "long" else ((top - seg.min()) / zone)

    rows = []
    for _, r in g.iterrows():
        e_s = int(pd.Timestamp(r.entry).value // 1_000_000_000); ep = r.entry_price
        x_s = int(pd.Timestamp(r.exit).value // 1_000_000_000)
        live = W[(W.comp_s <= e_s) & (W.comp_s >= e_s - WIN_S) & (W.fill_s > e_s)]
        if len(live) == 0: continue
        d_in = (live.bot <= ep) & (ep <= live.top)
        if d_in.any():
            ch = live[d_in].iloc[int(live[d_in].comp_s.values.argmax())]; dist = 0.0
        else:
            bot_a = live.bot.to_numpy(); top_a = live.top.to_numpy()
            dd = np.where(ep < bot_a, bot_a - ep, np.where(ep > top_a, ep - top_a, 0.0))
            j = int(np.argmin(dd)); dist = float(dd[j]); ch = live.iloc[j]
        if dist > NEAR: continue
        if not ((r.side == "long" and ch.top >= ep) or (r.side == "short" and ch.bot <= ep)): continue
        top, bot = float(ch.top), float(ch.bot); zone = top - bot
        i0 = np.searchsorted(s1, e_s, "left"); i1 = np.searchsorted(s1, x_s, "left")
        if i1 <= i0: continue
        frac = ((h1[i0:i1].max() - bot) / zone) if r.side == "long" else ((top - l1[i0:i1].min()) / zone)
        pbm = prior_body_max(r.entry); sgn = 1.0 if r.side == "long" else -1.0
        rec = dict(uid=r.uid, group=r.group, is_loser=bool(r.is_loser), side=r.side,
                   hold=round(r.hold), traversal_frac=max(0.0, frac), traversed=(frac >= 1.0))
        for tau in TAUS + FINE:
            cp = min(pd.Timestamp(r.entry) + S(tau), r.exit)
            rec[f"prog_{tau}"] = mid_prog(r.entry, cp, top, bot, r.side)
            rec[f"open_{tau}"] = x_s > e_s + tau
        cp60 = min(pd.Timestamp(r.entry) + S(60), r.exit)
        ii = int(np.searchsorted(sec, np.int64(pd.Timestamp(cp60).value // 1_000_000_000), "right") - 1)
        m60 = mid[ii] if ii >= 0 else np.nan
        rec["br60"] = (((m60 - ep) * sgn) / pbm) if (pbm and pbm > 0 and not np.isnan(m60)) else np.nan
        rows.append(rec)
    d = pd.DataFrame(rows)

    nT = int(d.traversed.sum()); nN = int((~d.traversed).sum())
    print(f"\n[gap2] WHG-capture population: {len(d)}  | traversed(far edge)={nT}  not={nN}")
    print(f"  OVERLAP with existing sets: losers={int(d.is_loser.sum())}  "
          f"reached={int((d.group=='target_reached').sum())}  failed={int((d.group=='failed_trades').sum())}")

    # ---- PART A: binary traverse ----
    print(f"\n  === PART A: traverse vs not ===")
    if nN:
        nt = d[~d.traversed]
        print(f"  non-traversers (n={nN}): hold(s)={list(nt.hold)} group={list(nt.group)} "
              f"frac={[round(f,2) for f in nt.traversal_frac]}")
    print(f"  (predictor for 'will it traverse' is n-limited at {nN} non-traversers; descriptive only)")

    # ---- PART B: among TRAVERSERS, big-run (reached) vs stall (failed) ----
    print(f"\n  === PART B: among traversers, reached(big-run) vs failed(stall) ===")
    tv = d[d.traversed]
    reached = tv[tv.group == "target_reached"]; failed = tv[tv.group == "failed_trades"]
    print(f"  traversers: reached={len(reached)}  failed={len(failed)}")
    print(f"  extension (traversal_frac) by group: reached median={reached.traversal_frac.median():.2f} "
          f"| failed median={failed.traversal_frac.median():.2f}")
    print(f"  early gap-progress AUC(reached > failed), still-open at τ:")
    for tau in TAUS:
        rv = reached[reached[f"open_{tau}"]][f"prog_{tau}"].to_numpy()
        fv = failed[failed[f"open_{tau}"]][f"prog_{tau}"].to_numpy()
        auc, _, _ = spine.rank_auc(rv, fv) if len(rv) and len(fv) else (np.nan, 0, 0)
        flag = "" if min(len(rv), len(fv)) >= 5 else "  <arm<5>"
        star = "  <<<" if tau == TAU_PRIMARY else ""
        print(f"    τ={tau:>3}s AUC={auc:.3f}  reached-open={len(rv)} failed-open={len(fv)}{flag}{star}")
    rv = reached[reached[f"open_{TAU_PRIMARY}"]][f"prog_{TAU_PRIMARY}"].to_numpy()
    fv = failed[failed[f"open_{TAU_PRIMARY}"]][f"prog_{TAU_PRIMARY}"].to_numpy()
    if len(rv) and len(fv):
        per = [float((np.sum(rv > c) + 0.5 * np.sum(rv == c)) / len(rv)) for c in fv]
        ci = spine.cluster_boot_ci(per, seed=args.seed)
        print(f"    @τ={TAU_PRIMARY}s CI[{ci['lo']:.3f},{ci['hi']:.3f}] ({'excl' if ci['excludes_half'] else 'incl'} 0.5)")
        sp = lambda a: f"p10={np.percentile(a,10):.2f} p50={np.median(a):.2f} p90={np.percentile(a,90):.2f}"
        print(f"    [non-circularity] reached early-prog: {sp(rv)} | failed: {sp(fv)}")

    # velocity
    def t_half(row):
        for tau in FINE:
            if row[f"prog_{tau}"] >= 0.5: return tau
        return np.nan
    tv = tv.copy(); tv["t_half"] = tv.apply(t_half, axis=1)
    rh = tv[tv.group == "target_reached"].t_half.dropna(); fh = tv[tv.group == "failed_trades"].t_half.dropna()
    print(f"  velocity time-to-half(s): reached median={np.median(rh) if len(rh) else float('nan'):.0f} "
          f"| failed median={np.median(fh) if len(fh) else float('nan'):.0f}")

    # ---- S1 check (open) ----
    dd = d.dropna(subset=["br60", f"prog_{TAU_PRIMARY}"])
    if len(dd) >= 5:
        c1c = np.corrcoef(dd[f"prog_{TAU_PRIMARY}"], dd.br60)[0, 1]
        c2c = np.corrcoef(dd.traversal_frac, dd.br60)[0, 1]
        print(f"\n  === S1 CHECK (open question, not assumed) ===")
        print(f"  corr(gap_progress@60, body_ratio@60) = {c1c:+.2f}")
        print(f"  corr(extension(traversal_frac), body_ratio@60) = {c2c:+.2f}")
        print(f"    (~+0.8 => the WHG signal is body-progress in disguise; near 0 => distinct on these trades)")

    print(f"\n[gap2] READ: Part A nearly all traverse (~{nT}/{len(d)}). Part B is the real question — does")
    print(f"  early progress separate big-runs from stalls AMONG traversers? n is small (failed~{len(failed)});")
    print(f"  treat as suggestive + a holdout target, not established. S1 corr decides if it's distinct.")


if __name__ == "__main__":
    main()
