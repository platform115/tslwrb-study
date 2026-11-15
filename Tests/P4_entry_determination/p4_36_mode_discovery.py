#!/usr/bin/env python3
"""
p4_36_mode_discovery.py — P4.36: (1) relaxed signal definition, (2) his words per mode.
========================================================================================
1. RELAXED DEFINITION (user-approved fix): a signal is ANY RTH 1m WRB completion -
   the flat-at-completion / desk-window requirements are dropped (position state is
   the strategy loop's business, as the profit sims already treat it). Every
   completion is scored with the frozen v6 conditions. Then his 313 entries are
   re-decomposed: matched+flagged / matched-underscored / unmatched.
2. HIS WORDS PER MODE: his non-trade messages in the 15 min before each entry,
   grouped by mode (A news-burst flagged / B underscored / C-fade / C-other);
   distinctive tokens per mode vs mode A, plus verbatim samples - looking for the
   quiet mode's name in his own vocabulary.

RUN: python3 Tests/P4_entry_determination/p4_36_mode_discovery.py            (repo root)
OUT: p4_36_all_signals.csv (every scored RTH completion, both months)
"""
import argparse, os, sys
from collections import Counter
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds, MONTHS            # noqa: E402
from p4_3_confluence_news import news_sets                     # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies, first_reaction_wrb  # noqa: E402
from p4_2b_zone_mtf import identify_whg, resample              # noqa: E402
from p4_9b_score_v3 import overlap_one                         # noqa: E402
from p4_7_trailing_flow import load_flow, flow_level           # noqa: E402
from p4_17_chat_alignment import tokens                        # noqa: E402

TICK = 0.25
E_TK, TOL_TK, TRAIL, FLOW15_CAP = 24, 4, 120, 4.6


def score_all_completions(repo, month, sym):
    """Every RTH 1m WRB completion in the month, scored with the frozen v6 conditions."""
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    wrb1 = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_1m.parquet"))
    ev_all = news_sets(repo)["all"]
    lo, hi = month_bounds(month)
    bars = es[(es.symbol == sym) & (es.ts_event >= lo - pd.Timedelta(days=4)) &
              (es.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
    bars["rth"] = bars.session == "RTH"
    bts = pd.DatetimeIndex(bars.ts_event).as_unit("ns").asi8
    sec, bv, sv, mz = load_flow(repo, month)
    w = wrb1[(wrb1.symbol == sym) & (wrb1.timeframe == "1m") &
             (wrb1.ts_event >= lo) & (wrb1.ts_event < hi)].sort_values("ts_event").reset_index(drop=True)
    zt = {tf: (identify_whg(bars) if tf == 1 else identify_whg(resample(bars, tf)))
          for tf in (3, 5, 10)}
    comp_ns = (pd.DatetimeIndex(w.ts_event).as_unit("ns").asi8 + 60_000_000_000)
    rng_tk = (bars.high - bars.low) / TICK
    tr5 = rng_tk.rolling(5).sum(); ref5 = tr5.rolling(TRAIL).median().shift(1)
    tr15 = rng_tk.rolling(15).sum(); ref15 = tr15.rolling(TRAIL).median().shift(1)
    lag15 = tr15.shift(5).to_numpy(); ref15l = ref15.shift(5).to_numpy()
    wball = wrb_bodies(bars[bars.rth].reset_index(drop=True)).merge(
        bars[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
    wball["body"] = (wball.close - wball.open).abs()
    med = wball.groupby(wball.session_date.astype(str)).body.median()
    sessions = sorted(set(bars.session_date.astype(str)))
    prev = {sx: float(med.get(sessions[i - 1], np.nan)) for i, sx in enumerate(sessions) if i > 0}
    w1tab = wball.assign(body_bottom=np.minimum(wball.open, wball.close),
                         body_top=np.maximum(wball.open, wball.close))[
        ["ts_event", "direction", "body_bottom", "body_top"]].sort_values("ts_event")
    w1ts = pd.DatetimeIndex(w1tab.ts_event).as_unit("ns").asi8 + 60_000_000_000
    react = {}
    for k, evns in enumerate(ev_all):
        if not (lo.value - 4 * 86400e9 <= evns < hi.value):
            continue
        m = (w1ts > evns) & (w1ts <= evns + 30 * 60e9)
        if m.any():
            j = int(np.flatnonzero(m)[0])
            react[k] = (int(w1ts[j]), float(w1tab.body_bottom.iloc[j]), float(w1tab.body_top.iloc[j]))
    ov = {tf: overlap_one(w, zt[tf][zt[tf].has_whg.fillna(False)], tf, comp_ns) for tf in (3, 5, 10)}
    sd = bars.session_date.astype(str).to_numpy()
    rows = []
    for i in range(len(w)):
        cns = int(comp_ns[i]); P = float(w.close.iloc[i])
        ib = int(np.searchsorted(bts, cns - 60_000_000_000))
        if ib >= len(bts) or bts[ib] != cns - 60_000_000_000 or not bars.rth.iloc[ib] or ib < 5:
            continue
        iev = int(np.searchsorted(ev_all, cns, side="right")) - 1
        mins = (cns - ev_all[iev]) / 60e9 if iev >= 0 else np.inf
        is_bull = w.direction.iloc[i] == "bullish"
        fl5 = flow_level(sec, bv, sv, mz, cns, 300, is_bull)
        fl15 = flow_level(sec, bv, sv, mz, cns, 900, is_bull)
        w1 = first_reaction_wrb(w1tab, 1, ev_all[iev], cns) if iev >= 0 else None
        c6 = False
        if iev in react:
            wc, bb, tt = react[iev]
            c6 = wc <= cns <= wc + 30 * 60e9 and bb - TOL_TK * TICK <= P <= tt + TOL_TK * TICK
        pr = prev.get(sd[ib], np.nan)
        score = sum([
            mins <= 15,
            bool(ov[3][i] | ov[5][i]),
            np.isfinite(pr) and abs(w.close.iloc[i] - w.open.iloc[i]) / TICK >= 2.0 * pr,
            bool(tr5.iloc[ib] >= 1.5 * ref5.iloc[ib]) if np.isfinite(ref5.iloc[ib]) else False,
            np.isfinite(fl5) and fl5 > 2.0,
            c6,
            bool(w1 and min(abs(P - w1["top"]), abs(P - w1["bottom"])) / TICK <= E_TK),
            bool(ov[10][i]),
            not (np.isfinite(fl15) and fl15 > FLOW15_CAP),
            bool(lag15[ib] > ref15l[ib]) if np.isfinite(ref15l[ib]) else False,
        ])
        rows.append(dict(month=month, comp_ns=cns, direction=w.direction.iloc[i], score=score, c1_news=bool(mins <= 15), uref=pr * TICK if np.isfinite(pr) else np.nan))
    return pd.DataFrame(rows)


def run(repo):
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet")).dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    nt = msg[msg.trade_action.fillna("") == ""].copy()
    nt["ns"] = pd.DatetimeIndex(nt.datetime_utc).as_unit("ns").asi8
    nt = nt.sort_values("ns")
    allsig = pd.concat([score_all_completions(repo, m, s) for m, s in MONTHS], ignore_index=True)
    allsig.to_csv(os.path.join(HERE, "p4_36_all_signals.csv"), index=False)
    print(f"relaxed universe: {len(allsig)} RTH WRB completions scored "
          f"(flagged >=6: {(allsig.score >= 6).sum()})")

    groups = Counter(); words = {g: Counter() for g in ("A", "B", "Cfade", "Cother")}
    nmsg = Counter(); samples = {g: [] for g in words}
    for month, sym in MONTHS:
        lo, hi = month_bounds(month)
        sm = allsig[allsig.month == month]
        comp = sm.comp_ns.to_numpy(np.int64); dirs = sm.direction.to_numpy()
        scores = sm.score.to_numpy()
        e_m = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)]
        for _, t in e_m.iterrows():
            en = pd.Timestamp(t.first_entry_utc).value
            want = "bullish" if t.side == "long" else "bearish"
            m = (comp >= en - 5 * 60_000_000_000) & (comp < en)
            md = m & (dirs == want)
            if md.any():
                g = "A" if scores[np.flatnonzero(md)].max() >= 6 else "B"
            elif m.any():
                g = "Cfade"
            else:
                g = "Cother"
            groups[g] += 1
            w = nt[(nt.ns >= en - 15 * 60_000_000_000) & (nt.ns < en)]
            nmsg[g] += len(w)
            for s in w.message:
                words[g].update(tokens(s))
            if len(w) and len(samples[g]) < 8:
                samples[g].append(f"[{str(w.datetime_utc.iloc[-1])[:16]}] {str(w.message.iloc[-1])[:110]}")
    n = sum(groups.values())
    print(f"\n=== RELAXED decomposition of his {n} entries ===")
    for g in ("A", "B", "Cfade", "Cother"):
        print(f"  {g:6s}: {groups[g]:4d} ({groups[g]/n:.0%})   [{nmsg[g]} pre-entry messages]")
    totA = sum(words["A"].values())
    for g in ("B", "Cfade", "Cother"):
        tot = sum(words[g].values())
        if not tot: continue
        sc = sorted(((c / tot) / ((words["A"][w_] + 1) / max(totA, 1)), w_, c)
                    for w_, c in words[g].items() if c >= 6)
        print(f"\n[{g}] words over-represented vs mode A (word, count, ratio):")
        for r, w_, c in sc[::-1][:10]:
            print(f"    {w_:16s} {c:4d}  {r:4.1f}x")
        print(f"[{g}] sample last-messages before these entries:")
        for s_ in samples[g][:5]:
            print(f"    {s_}")
    print("\nREAD: search-mode. The relaxed universe feeds the side-plan test next.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
