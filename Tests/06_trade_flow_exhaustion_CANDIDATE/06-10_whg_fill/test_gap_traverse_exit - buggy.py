#!/usr/bin/env python3
"""
test_gap_traverse_exit.py — #3 exit angle: will a gap-arrival trade TRAVERSE or STALL?
-------------------------------------------------------------------------------
Among trades that entered at a live 5m WHG (INSIDE+NEAR, pointed through it), test whether EARLY,
FORWARD, still-open progress into the gap predicts whether the trade completes the traversal (success)
or stalls and gets cut. Population gated by probe_whg_arrival.py (gap-arrival is real, ~34 on 5m).

PRE-REGISTERED LABEL (outcome, measured over full [entry, exit] from 1m bars / true extremes):
  traversed = (max high >= whg_top AND min low <= whg_bottom) before exit  -> SUCCESS arm
  not-traversed = exited first                                              -> CUT arm
(Picked BEFORE seeing outcomes, per discipline: full traversal = success.)

PREDICTORS (early, still-open at τ -> non-circular; late τ would make progress == outcome):
  P1 gap_progress(τ) = fraction of the zone [bottom,top] covered by per-second MID up to min(entry+τ,exit)
  P2 velocity        = time-to-half-coverage (first τ with progress>=0.5) + early progress, traverser vs staller

CIRCULARITY GUARD: progress read at EARLY τ, STILL-OPEN only; within-group spread reported (do some
eventual-traversers show LOW early progress = slow fills -> graded, not the label).

S1-OVERLAP CHECK (the honest "is this just body-progress?"): also compute body_ratio(60s) for these
trades and report corr(gap_progress@60, body_ratio@60). High corr => gap-progress is S1 with a gap-sized
normalizer; low => the concrete gap target adds something prior-bar body did not.

Two-sided. SSD MOUNTED (per-second mid). October ESZ5. n small (~34); discovery. Not financial advice.

RUN (from 06-10_whg_fill/)
  python3 test_gap_traverse_exit.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
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
TAUS = [30, 60, 90, 120, 180]; TAU_PRIMARY = 60
FINE = list(range(15, 181, 15))


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
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
    whgs = [dict(comp_s=int(s5[i] + TF_DUR_5M), fill_s=fill_s(s5, h5, l5, top, bot, i, TF_DUR_5M),
                 top=top, bot=bot, direction=d) for (i, d, bot, top) in identify_whg(b5)]
    W = pd.DataFrame(whgs)

    b1 = load_bars(es1m); s1 = (b1.ts_event.astype("int64") // 1_000_000_000).to_numpy()
    h1 = b1.high.to_numpy(); l1 = b1.low.to_numpy(); o1 = b1.open.to_numpy(); c1 = b1.close.to_numpy()

    def prior_body_max(entry_ts):
        e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
        j = int(np.searchsorted(s1, e_s, "left"))
        return float(np.abs(c1[j-3:j] - o1[j-3:j]).max()) if j >= 3 else np.nan

    t_min = g["entry"].min() - M(5); t_max = g["exit"].max() + M(1)
    print(f"[gap] streaming per-second mid ...")
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)

    def cover_frac(entry_ts, cp_ts, top, bot):
        e = np.int64(pd.Timestamp(entry_ts).value // 1_000_000_000)
        cps = np.int64(pd.Timestamp(cp_ts).value // 1_000_000_000)
        i0 = np.searchsorted(sec, e, "left"); i1 = np.searchsorted(sec, cps, "left")
        if i1 - i0 < 2: return 0.0
        seg = mid[i0:i1]
        lo = max(bot, seg.min()); hi = min(top, seg.max())
        return max(0.0, hi - lo) / (top - bot)

    # build gap-arrival population
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
        if dist > NEAR: continue                          # INSIDE + NEAR only
        toward = (r.side == "long" and ch.top >= ep) or (r.side == "short" and ch.bot <= ep)
        if not toward: continue                           # pointed through the gap only
        top, bot = float(ch.top), float(ch.bot)
        # LABEL: full traversal by exit (1m true extremes)
        i0 = np.searchsorted(s1, e_s, "left"); i1 = np.searchsorted(s1, x_s, "left")
        traversed = bool(i1 > i0 and h1[i0:i1].max() >= top and l1[i0:i1].min() <= bot)
        pbm = prior_body_max(r.entry); sgn = 1.0 if r.side == "long" else -1.0
        rec = dict(uid=r.uid, traversed=traversed, top=top, bot=bot, side=r.side,
                   entry=r.entry, exit=r.exit, entry_price=ep, pbm=pbm)
        for tau in TAUS + FINE:
            cp = min(pd.Timestamp(r.entry) + S(tau), r.exit)
            rec[f"prog_{tau}"] = cover_frac(r.entry, cp, top, bot)
            rec[f"open_{tau}"] = x_s > e_s + tau
        # body_ratio@60 for S1-overlap
        cp60 = min(pd.Timestamp(r.entry) + S(60), r.exit)
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(cp60).value // 1_000_000_000), "right") - 1)
        m60 = mid[i] if i >= 0 else np.nan
        rec["br60"] = (((m60 - ep) * sgn) / pbm) if (pbm and pbm > 0 and not np.isnan(m60)) else np.nan
        rows.append(rec)
    d = pd.DataFrame(rows)
    nt = int(d.traversed.sum()); ns = int((~d.traversed).sum())
    print(f"\n[gap] population: {len(d)} gap-arrival trades (5m INSIDE+NEAR, pointed-through)")
    print(f"      traversed(success)={nt}  stalled(cut)={ns}")
    if ns < 5 or nt < 5:
        print(f"      WARNING: one arm < 5 — too small to read a predictor. Reporting descriptively only.")

    # P1 gap-progress hazard
    print(f"\n  P1 gap-progress(τ) — AUC(traverser progress > staller progress), still-open at τ:")
    print(f"  {'τ(s)':>5} {'AUC':>6} {'trav-open':>9} {'stall-open':>10}")
    for tau in TAUS:
        tv = d[d.traversed & d[f"open_{tau}"]][f"prog_{tau}"].to_numpy()
        sv = d[~d.traversed & d[f"open_{tau}"]][f"prog_{tau}"].to_numpy()
        auc, _, _ = spine.rank_auc(tv, sv) if len(tv) and len(sv) else (np.nan, 0, 0)
        flag = "" if min(len(tv), len(sv)) >= 5 else "  <arm<5>"
        star = "  <<<" if tau == TAU_PRIMARY else ""
        print(f"  {tau:>5} {auc:>6.3f} {len(tv):>9} {len(sv):>10}{flag}{star}")
    # CI + non-circularity + calibration @primary
    tv = d[d.traversed & d[f"open_{TAU_PRIMARY}"]][f"prog_{TAU_PRIMARY}"].to_numpy()
    sv = d[~d.traversed & d[f"open_{TAU_PRIMARY}"]][f"prog_{TAU_PRIMARY}"].to_numpy()
    if len(tv) and len(sv):
        per = [float((np.sum(tv > c) + 0.5 * np.sum(tv == c)) / len(tv)) for c in sv]
        ci = spine.cluster_boot_ci(per, seed=args.seed)
        print(f"\n  @τ={TAU_PRIMARY}s: AUC={ci['mean']:.3f} CI[{ci['lo']:.3f},{ci['hi']:.3f}] "
              f"({'excl' if ci['excludes_half'] else 'incl'} 0.5)")
        sp = lambda a: f"p10={np.percentile(a,10):.2f} p50={np.median(a):.2f} p90={np.percentile(a,90):.2f}"
        print(f"  [non-circularity] traversers progress: {sp(tv)} | stallers: {sp(sv)}")
        print(f"    (traversers showing LOW early progress = slow fills = graded, not the label.)")

    # P2 velocity: time-to-half-coverage
    def t_half(row):
        for tau in FINE:
            if row[f"prog_{tau}"] >= 0.5: return tau
        return np.nan
    d["t_half"] = d.apply(t_half, axis=1)
    th_t = d[d.traversed].t_half.dropna(); th_s = d[~d.traversed].t_half.dropna()
    print(f"\n  P2 velocity — time-to-half-coverage (s): traversers median="
          f"{np.median(th_t) if len(th_t) else float('nan'):.0f} (n reaching 50%={len(th_t)}/{nt}) | "
          f"stallers median={np.median(th_s) if len(th_s) else float('nan'):.0f} (n={len(th_s)}/{ns})")

    # S1 overlap
    dd = d.dropna(subset=["br60", f"prog_{TAU_PRIMARY}"])
    if len(dd) >= 5:
        cc = np.corrcoef(dd[f"prog_{TAU_PRIMARY}"], dd.br60)[0, 1]
        print(f"\n  S1-OVERLAP: corr(gap_progress@60, body_ratio@60) = {cc:+.2f} over {len(dd)} trades")
        print(f"    (~+0.8+ => gap-progress is S1 with a gap normalizer; near 0 => the gap target adds new info.)")

    print(f"\n[gap] READ: does early gap-progress separate eventual traversers from stallers, and is it")
    print(f"  distinct from S1? Watch arm sizes (~{nt}/{ns}); below ~5 per arm this is descriptive only.")


if __name__ == "__main__":
    main()
