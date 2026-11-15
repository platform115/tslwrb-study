#!/usr/bin/env python3
"""
p4_20_validation.py — P4.20: VALIDATION of the frozen entry rules on reserved months.
======================================================================================
Runs the FROZEN protocol (P4_DESIGN.md) on one reserved month. Nothing here is
tunable: rule settings come from the freezes (v5 T-EN14, v6 T-EN22), the
no-pressure cutoffs were fixed on discovery data before any reserved month was
touched (v5-noflow: 2 of 5 · v6-noflow: 4 of 8), and the WRB reconstruction was
proven exact against the canonical tables on both discovery months (0 diff).

Per month: signals rebuilt with the LOCKED definition (desk-window flat RTH 1m WRB
completions; taken = same-direction entry within 5 min; roll-day sessions
excluded), both no-pressure rules scored, lift = flagged precision / base with a
bootstrap 95% CI (seed 0, 10,000), read on ALL signals and PRESENT-ONLY (chat).
Direction rule (follow the last 5-min move) read on the month's entries.
PASS criteria live at the pooled level (protocol step 4); single months report
numbers with CIs and small-n caveats.

RUN: python3 Tests/P4_entry_determination/p4_20_validation.py --month 2021-09
     python3 Tests/P4_entry_determination/p4_20_validation.py --selftest
OUT: p4_20_signals_<month>.csv
"""
import argparse, os, sys
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from p4_2_entry_context import month_bounds            # noqa: E402
from p4_3_confluence_news import news_sets             # noqa: E402
from p4_5a_taken_anatomy import wrb_bodies, first_reaction_wrb  # noqa: E402
from p4_2b_zone_mtf import identify_whg, resample      # noqa: E402
from p4_9b_score_v3 import overlap_one                 # noqa: E402
from p4_17_chat_alignment import mins_since_prev       # noqa: E402

TICK = 0.25
SEED, B = 0, 10_000
K_V5NF, K_V6NF = 2, 4          # fixed on discovery BEFORE any reserved month
E_TK = 24                      # v6 freeze
TOL_TK = 4
TRAIL = 120


def build_signals(ep_m, wrb_m, bars_m):
    """Locked signal definition: desk-window flat RTH WRB completions; taken =
    same-direction entry within 5 min. Roll-day sessions excluded."""
    roll_days = set(bars_m.loc[bars_m.get("is_roll_day", pd.Series(False, index=bars_m.index)).fillna(False), "session_date"].astype(str))
    wts = pd.DatetimeIndex(wrb_m.ts_event).as_unit("ns").asi8
    rows = []
    for day, e_day in ep_m.groupby(ep_m.first_entry_utc.dt.date):
        t0 = min(pd.Timestamp(t).value for t in e_day.first_entry_utc) - 3600 * int(1e9)
        t1 = max(pd.Timestamp(t).value for t in e_day.last_exit_utc)
        spans = [(pd.Timestamp(r.first_entry_utc).value, pd.Timestamp(r.last_exit_utc).value)
                 for _, r in e_day.iterrows()]
        ent = sorted((pd.Timestamp(r.first_entry_utc).value, r.side) for _, r in e_day.iterrows())
        for i, wns in enumerate(wts):
            comp = wns + 60 * int(1e9)
            if not (t0 <= comp <= t1):
                continue
            if any(a <= comp <= b for a, b in spans):
                continue
            w = wrb_m.iloc[i]
            if str(w.session_date) in roll_days:
                continue
            tk = False
            for ens, side in ent:
                if comp < ens <= comp + 5 * 60 * int(1e9):
                    tk = (side == "long") == (w.direction == "bullish")
                    if tk:
                        break
            rows.append(dict(ts_event=w.ts_event, comp_ns=comp, direction=w.direction,
                             close=float(w.close), body_tk=abs(w.close - w.open) / TICK,
                             session_date=str(w.session_date), taken=bool(tk)))
    return pd.DataFrame(rows)


def lift_ci(taken, flagged, seed=SEED, nb=B):
    rng = np.random.default_rng(seed)
    n = len(taken); out = np.empty(nb)
    base = taken.mean(); lift = taken[flagged].mean() / base if flagged.any() else np.nan
    for b in range(nb):
        i = rng.integers(0, n, n)
        t, f = taken[i], flagged[i]
        out[b] = t[f].mean() / t.mean() if f.any() and t.mean() > 0 else np.nan
    return lift, float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


def run(repo, month):
    es = pd.read_parquet(os.path.join(repo, "Data/inputs/es_1m_front.parquet"))
    ep = pd.read_parquet(os.path.join(repo, "Data/inputs/tsl_episodes_clean.parquet"))
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    msg_ns = np.sort(pd.DatetimeIndex(msg.datetime_utc).as_unit("ns").asi8)
    ev_all = news_sets(repo)["all"]
    lo, hi = month_bounds(month)
    e = ep[(ep.first_entry_utc >= lo) & (ep.first_entry_utc < hi)].dropna(
        subset=["first_entry_utc", "last_exit_utc"])
    bars_all = es[(es.ts_event >= lo - pd.Timedelta(days=4)) & (es.ts_event < hi)]
    sym = bars_all[(bars_all.ts_event >= lo)].symbol.mode().iloc[0]
    bars_m = bars_all[bars_all.symbol == sym].sort_values("ts_event").reset_index(drop=True)
    print(f"[{month}] symbol={sym} bars={len(bars_m)} episodes={len(e)} "
          f"(gate: episodes>0 and bars>5000: {'PASS' if len(e) > 0 and len(bars_m) > 5000 else 'FAIL'})")
    wrb_rth = wrb_bodies(bars_m[bars_m.session == "RTH"].reset_index(drop=True))
    wrb_rth = wrb_rth.merge(
        bars_m[["ts_event", "open", "close", "session_date"]], on="ts_event", how="left")
    sig = build_signals(e, wrb_rth, bars_m)
    print(f"signals={len(sig)} taken={int(sig.taken.sum())} base={sig.taken.mean():.1%}")

    # features (identical constructions to the freezes)
    bts = pd.DatetimeIndex(bars_m.ts_event).as_unit("ns").asi8
    rng_tk = (bars_m.high - bars_m.low) / TICK
    tr5 = rng_tk.rolling(5).sum(); ref5 = tr5.rolling(TRAIL).median().shift(1)
    tr15 = rng_tk.rolling(15).sum(); ref15 = tr15.rolling(TRAIL).median().shift(1)
    lag15 = tr15.shift(5).to_numpy(); ref15l = ref15.shift(5).to_numpy()
    wbody = wrb_rth.assign(body=lambda d: (d.close - d.open).abs() / TICK)
    body_med = wbody.groupby(wbody.session_date.astype(str)).body.median()
    sessions = sorted(set(bars_m.session_date.astype(str)))
    prev_ref = {s: float(body_med.get(sessions[i - 1], np.nan))
                for i, s in enumerate(sessions) if i > 0}
    # zones rebuilt from bars (gated vs canonical tables on both discovery months:
    # 0 missing, <=2 extra boundary rows per ~5,000 - construction equivalent)
    zt = {tf: (identify_whg(bars_m) if tf == 1 else identify_whg(resample(bars_m, tf)))
          for tf in (1, 3, 5, 10)}
    z1 = zt[1]
    sig = sig.merge(z1[["ts_event", "has_whg", "whg_top", "whg_bottom"]], on="ts_event", how="left")
    comp_ns = sig.comp_ns.to_numpy(np.int64)
    ovs = {}
    for tf in (3, 5, 10):
        z = zt[tf][zt[tf].has_whg.fillna(False)]
        ovs[tf] = overlap_one(sig, z, tf, comp_ns)
    # reaction WRB machinery (1m RTH table)
    w1tab = wrb_rth.rename(columns={})[["ts_event", "direction"]].assign(
        body_bottom=np.minimum(wrb_rth.open, wrb_rth.close),
        body_top=np.maximum(wrb_rth.open, wrb_rth.close)).sort_values("ts_event")
    w1ts = pd.DatetimeIndex(w1tab.ts_event).as_unit("ns").asi8 + 60 * int(1e9)
    react = {}
    for k, evns in enumerate(ev_all):
        if not (lo.value - 4 * 86400 * int(1e9) <= evns < hi.value):
            continue
        m = (w1ts > evns) & (w1ts <= evns + 30 * 60 * int(1e9))
        if m.any():
            j = int(np.flatnonzero(m)[0])
            react[k] = (int(w1ts[j]), float(w1tab.body_bottom.iloc[j]), float(w1tab.body_top.iloc[j]))
    c1 = np.zeros(len(sig), bool); c6 = np.zeros(len(sig), bool); c7 = np.zeros(len(sig), bool)
    c3 = np.zeros(len(sig), bool); c4 = np.zeros(len(sig), bool); c10 = np.zeros(len(sig), bool)
    ib = np.searchsorted(bts, comp_ns - 60 * int(1e9))
    ok = (ib < len(bts)) & (bts[np.clip(ib, 0, len(bts) - 1)] == comp_ns - 60 * int(1e9))
    for i in range(len(sig)):
        cns = int(comp_ns[i]); P = sig.close.iloc[i]
        iev = int(np.searchsorted(ev_all, cns, side="right")) - 1
        mins = (cns - ev_all[iev]) / 60e9 if iev >= 0 else np.inf
        c1[i] = mins <= 15
        if iev in react:
            wc, bb, tt = react[iev]
            c6[i] = (wc <= cns <= wc + 30 * 60 * int(1e9) and
                     bb - TOL_TK * TICK <= P <= tt + TOL_TK * TICK)
        w1 = first_reaction_wrb(w1tab, 1, ev_all[iev], cns) if iev >= 0 else None
        if w1:
            c7[i] = min(abs(P - w1["top"]), abs(P - w1["bottom"])) / TICK <= E_TK
        ref = prev_ref.get(sig.session_date.iloc[i], np.nan)
        c3[i] = np.isfinite(ref) and sig.body_tk.iloc[i] >= 2.0 * ref
        if ok[i]:
            j = ib[i]
            c4[i] = tr5.iloc[j] >= 1.5 * ref5.iloc[j] if np.isfinite(ref5.iloc[j]) else False
            c10[i] = lag15[j] > ref15l[j] if np.isfinite(ref15l[j]) else False
    sig["v5nf"] = c1.astype(int) + ovs[3].astype(int) * 0  # placeholder, replaced below
    c2 = ovs[3] | ovs[5]
    sig["v5nf"] = c1.astype(int) + c2.astype(int) + c3.astype(int) + c4.astype(int) + c6.astype(int)
    sig["v6nf"] = sig.v5nf + c7.astype(int) + ovs[10].astype(int) + c10.astype(int)
    sig["present30"] = np.array([mins_since_prev(msg_ns, int(t)) for t in comp_ns]) <= 30
    sig.to_csv(os.path.join(HERE, f"p4_20_signals_{month}.csv"), index=False)

    taken = sig.taken.to_numpy(bool)
    print(f"\n===== {month}: frozen rules, no-pressure versions =====")
    for name, sc, k in [("v5-noflow >= 2 of 5", sig.v5nf.to_numpy(), K_V5NF),
                        ("v6-noflow >= 4 of 8", sig.v6nf.to_numpy(), K_V6NF)]:
        for frame, m in [("all signals ", np.ones(len(sig), bool)),
                         ("present-only", sig.present30.to_numpy())]:
            t, fl = taken[m], (sc >= k)[m]
            if not fl.any() or t.mean() == 0:
                print(f"  {name} | {frame}: no flags/trades"); continue
            lf, lo_, hi_ = lift_ci(t, fl)
            print(f"  {name} | {frame}: base {t.mean():5.1%}  flags {int(fl.sum()):4d}  "
                  f"captures {t[fl].sum()/t.sum():5.1%}  precision {t[fl].mean():5.1%}  "
                  f"lift {lf:.2f}x [{lo_:.2f},{hi_:.2f}]")
    # direction rule on the month's entries
    cl = bars_m.close.to_numpy()
    agree = []
    for _, t in e.iterrows():
        en = pd.Timestamp(t.first_entry_utc).value
        j = int(np.searchsorted(bts, en - 60 * int(1e9), side="right")) - 1
        if j < 5:
            continue
        mv = cl[j] - cl[j - 5]
        if mv != 0:
            agree.append((mv > 0) == (t.side == "long"))
    a = np.array(agree)
    se = a.std(ddof=1) / np.sqrt(len(a)) if len(a) > 1 else np.nan
    print(f"\ndirection rule (follow last 5-min move): agrees {a.mean():.1%} of {len(a)} entries"
          f" (rough 95% band +/-{1.96*se:.1%})")
    print("\nREAD: one-shot look under the frozen protocol; PASS is judged pooled, these")
    print("are per-month numbers with small-n caveats. No re-tuning follows from this.")


def selftest():
    ts = pd.date_range("2021-09-07 13:30", periods=200, freq="1min", tz="UTC")
    bars = pd.DataFrame(dict(ts_event=ts, open=5000.0, high=5000.5, low=4999.5,
                             close=5000.0, session_date="2021-09-07", session="RTH"))
    bars.loc[50, ["close", "high"]] = [5004.0, 5004.0]
    w = wrb_bodies(bars).merge(bars[["ts_event", "open", "close", "session_date"]],
                               on="ts_event", how="left")
    ep_m = pd.DataFrame(dict(first_entry_utc=[ts[52]], last_exit_utc=[ts[80]], side=["long"]))
    s = build_signals(ep_m, w, bars)
    assert len(s) == 1 and bool(s.taken.iloc[0])      # WRB completes 51, entry 52 same-dir
    print("=== SELF-TEST ===\n  signal construction + taken label OK")
    ep2 = pd.DataFrame(dict(first_entry_utc=[ts[52]], last_exit_utc=[ts[80]], side=["short"]))
    s2 = build_signals(ep2, w, bars)
    assert len(s2) == 1 and not bool(s2.taken.iloc[0])
    print("  opposite-side entry -> not taken OK\nSELF-TEST OK.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--month")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    selftest() if a.selftest else run(a.repo, a.month)
