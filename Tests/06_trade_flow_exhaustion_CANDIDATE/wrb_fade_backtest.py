#!/usr/bin/env python3
"""
wrb_fade_backtest.py — EXPLORATION: fade the 1m WRB with a symmetric 1pt bracket
==================================================================================
RULE (user-specified, coded interpretation):
  On the CLOSE of a 1m WRB (canonical wrb_1m.parquet rows), arm a fade entry in the
  OPPOSITE direction: bullish WRB -> SHORT stop-touch at close - 1 tick; bearish WRB ->
  LONG at close + 1 tick. Fill assumed AT the trigger price on first bar whose range
  touches it. Bracket from entry: target 1.00 pt, stop 1.00 pt, first touch wins.

PRE-REGISTERED MECHANICS (printed, not hidden):
  - Trigger validity: K bars after the WRB close bar; grid K in {1, 3, 10}.
  - One position at a time; signals while in-trade are SKIPPED (counted).
  - Same-bar both-touch = AMBIGUOUS at 1m: reported three ways —
      CONSERVATIVE (stop first)  <- PRIMARY
      OPTIMISTIC   (target first)
      EXCLUDED     (ambiguous trades dropped)
  - Entry bar itself can resolve the bracket (post-touch path unknown -> same ambiguity rule).
  - No bracket resolution by session end -> force-exit at last RTH bar close (counted, PnL at close).
  - Both WRB directions traded. ES tick 0.25. Costs/sizing out of scope (handled separately).

PRECEDENT: fading climactic range expansion is a documented practitioner family (Crabel 1990
range contraction/expansion is the adjacent literature); the 1-tick trigger + symmetric 1pt
bracket is OUR construction — flagged, no precedent claimed for the specific rule.

STATS: win rate (of bracket-resolved trades) + bootstrap 95% CI (seed 0, 10000) + net points
including force-exits. A symmetric bracket is EV~0 under random walk: the finding IS the
win-rate deviation from 0.5. Touch-fill at 1m flatters tight brackets — treat small edges
as fill noise.

RUN (from Tests/06_trade_flow_exhaustion_CANDIDATE, October defaults):
  python3 wrb_fade_backtest.py --config config.toml --wrb wrb_1m.parquet
  python3 wrb_fade_backtest.py --selftest
Feb-2022: add --month 2022-02 --symbol ESH2
"""
import argparse, tomllib
import numpy as np
import pandas as pd

TICK = 0.25
TARGET_PTS = 1.00
STOP_PTS = 1.00
K_GRID = [1, 3, 10]
SEED = 0


def load_bars(config_path, month, symbol):
    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)
    lo = pd.Timestamp(f"{month}-01", tz="UTC")
    hi = lo + pd.offsets.MonthBegin(1)
    es = pd.read_parquet(cfg["paths"]["es_1m_front"],
                         columns=["ts_event", "symbol", "open", "high", "low", "close", "session"])
    es = es[(es.ts_event >= lo) & (es.ts_event < hi) & (es.symbol == symbol)]
    return es.sort_values("ts_event").reset_index(drop=True)


def load_wrbs(wrb_path, month, symbol):
    w = pd.read_parquet(wrb_path)
    lo = pd.Timestamp(f"{month}-01", tz="UTC")
    hi = lo + pd.offsets.MonthBegin(1)
    w = w[(w.ts_event >= lo) & (w.ts_event < hi) & (w.symbol == symbol)]
    if "timeframe" in w.columns:
        w = w[w.timeframe == "1m"]
    return w.sort_values("ts_event").reset_index(drop=True)


def simulate(bars, wrbs, k_bars):
    """Bar-by-bar, one position at a time. Returns trades DataFrame + counters."""
    bars = bars.reset_index(drop=True)
    idx_of = {t: i for i, t in enumerate(bars.ts_event)}
    # per-day last RTH bar index for force-exit
    day = bars.ts_event.dt.tz_convert("America/New_York").dt.date
    rth = bars.session.eq("RTH") if "session" in bars else pd.Series(True, index=bars.index)
    last_rth = {}
    for i in np.flatnonzero(rth.to_numpy()):
        last_rth[day.iloc[i]] = i

    trades, skipped_in_trade, never_triggered, no_bar_match = [], 0, 0, 0
    busy_until = -1  # bar index the current position occupies through

    for _, w in wrbs.iterrows():
        if w.ts_event not in idx_of:
            no_bar_match += 1
            continue
        i0 = idx_of[w.ts_event]              # the WRB bar itself
        if i0 <= busy_until:
            skipped_in_trade += 1
            continue
        side = -1 if w.direction == "bullish" else +1   # fade: bullish -> short
        trig = w.close - TICK if side < 0 else w.close + TICK
        d = day.iloc[i0]
        end_day = last_rth.get(d, i0)

        # --- find trigger touch within K bars after the WRB bar, same day ---
        ent_i = -1
        for j in range(i0 + 1, min(i0 + 1 + k_bars, end_day + 1)):
            b = bars.iloc[j]
            if b.low <= trig <= b.high:
                ent_i = j
                break
        if ent_i < 0:
            never_triggered += 1
            continue

        entry = trig
        tgt = entry - TARGET_PTS if side < 0 else entry + TARGET_PTS
        stp = entry + STOP_PTS if side < 0 else entry - STOP_PTS

        outcome, exit_i = None, None
        for j in range(ent_i, end_day + 1):
            b = bars.iloc[j]
            hit_t = (b.low <= tgt) if side < 0 else (b.high >= tgt)
            hit_s = (b.high >= stp) if side < 0 else (b.low <= stp)
            if hit_t and hit_s:
                outcome, exit_i = "ambiguous", j
                break
            if hit_t:
                outcome, exit_i = "win", j
                break
            if hit_s:
                outcome, exit_i = "loss", j
                break
        if outcome is None:
            j = end_day
            pnl = (entry - bars.iloc[j].close) if side < 0 else (bars.iloc[j].close - entry)
            trades.append(dict(wrb=w.ts_event, dir="short" if side < 0 else "long",
                               entry_bar=ent_i, outcome="force_exit", pnl=float(pnl),
                               hold_bars=j - ent_i))
            busy_until = j
            continue
        pnl = TARGET_PTS if outcome == "win" else (-STOP_PTS if outcome == "loss" else np.nan)
        trades.append(dict(wrb=w.ts_event, dir="short" if side < 0 else "long",
                           entry_bar=ent_i, outcome=outcome, pnl=pnl,
                           hold_bars=exit_i - ent_i))
        busy_until = exit_i

    return pd.DataFrame(trades), dict(skipped_in_trade=skipped_in_trade,
                                      never_triggered=never_triggered,
                                      no_bar_match=no_bar_match)


def boot_ci(wins_bool, seed=SEED, B=10000):
    x = np.asarray(wins_bool, float)
    if len(x) < 5:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    boot = np.array([rng.choice(x, len(x), True).mean() for _ in range(B)])
    return float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def report(tr, counters, k):
    n = len(tr)
    amb = int((tr.outcome == "ambiguous").sum()) if n else 0
    fe = int((tr.outcome == "force_exit").sum()) if n else 0
    print(f"\n========== K={k} bars ==========")
    print(f"  signals -> trades={n} | skipped(in-trade)={counters['skipped_in_trade']} "
          f"| never-triggered={counters['never_triggered']} | no-bar-match={counters['no_bar_match']}")
    if n == 0:
        return
    print(f"  outcomes: win={int((tr.outcome=='win').sum())} loss={int((tr.outcome=='loss').sum())} "
          f"ambiguous={amb} force_exit={fe} | median hold={tr.hold_bars.median():.0f} bars")
    for name, amb_as in (("CONSERVATIVE (amb=loss)  <-PRIMARY", "loss"),
                         ("OPTIMISTIC   (amb=win)", "win"),
                         ("EXCLUDED     (amb dropped)", None)):
        t = tr[tr.outcome != "force_exit"].copy()
        if amb_as is None:
            t = t[t.outcome != "ambiguous"]
            wins = (t.outcome == "win")
        else:
            wins = (t.outcome == "win") | ((t.outcome == "ambiguous") & (amb_as == "win"))
        if len(t) == 0:
            continue
        wr = wins.mean()
        lo, hi = boot_ci(wins.to_numpy())
        pnl_br = wins.sum() * TARGET_PTS - (len(t) - wins.sum()) * STOP_PTS
        fe_pnl = tr.loc[tr.outcome == "force_exit", "pnl"].sum()
        print(f"    {name:34s} n={len(t):4d} win%={wr:.3f} CI[{lo:.3f},{hi:.3f}] "
              f"net={pnl_br + fe_pnl:+.2f} pts (incl force-exit {fe_pnl:+.2f})")
    for dname in ("short", "long"):
        t = tr[(tr["dir"] == dname) & (tr.outcome.isin(["win", "loss", "ambiguous"]))]
        if len(t) < 5:
            continue
        wins = (t.outcome == "win")  # conservative: ambiguous counts as loss
        lo, hi = boot_ci(wins.to_numpy())
        print(f"    by-dir {dname:5s} (conservative)     n={len(t):4d} win%={wins.mean():.3f} CI[{lo:.3f},{hi:.3f}]")


def selftest():
    print("=== SELF-TEST: synthetic bars ===")
    t0 = pd.Timestamp("2025-10-06 14:00", tz="UTC")
    ts = pd.date_range(t0, periods=8, freq="1min", tz="UTC")
    # bar0 = bullish WRB close 5004; bar1 dips to 5003.75 (trigger) then bar2 falls to 5002.5 (target 5003.75-1=5002.75)
    bars = pd.DataFrame(dict(
        ts_event=ts,
        symbol="TEST",
        open=[5000, 5004.00, 5003.5, 5002.9, 5003.0, 5003.0, 5003.0, 5003.0],
        high=[5004, 5004.25, 5003.8, 5003.0, 5003.1, 5003.1, 5003.1, 5003.1],
        low=[4999.5, 5003.75, 5002.5, 5002.8, 5002.9, 5002.9, 5002.9, 5002.9],
        close=[5004, 5004.0, 5002.9, 5002.9, 5003.0, 5003.0, 5003.0, 5003.0],
        session=["RTH"] * 8))
    wrbs = pd.DataFrame(dict(ts_event=[ts[0]], symbol=["TEST"], direction=["bullish"], close=[5004.0]))
    tr, c = simulate(bars, wrbs, k_bars=3)
    assert len(tr) == 1 and tr.iloc[0].outcome in ("win", "ambiguous"), tr
    # trigger 5003.75 touched on bar1; target 5002.75 hit bar2 low 5002.5; bar1 high 5004.25 < stop 5004.75 -> clean win
    assert tr.iloc[0].outcome == "win" and tr.iloc[0].dir == "short" and tr.iloc[0].entry_bar == 1
    print(f"  bullish-WRB fade: short @5003.75, win on bar2  OK")
    # ambiguity: one bar spans both bracket edges
    bars2 = bars.copy()
    bars2.loc[2, ["high", "low"]] = [5005.0, 5002.5]   # bar2 touches stop 5004.75 AND target 5002.75
    tr2, _ = simulate(bars2, wrbs, k_bars=3)
    assert tr2.iloc[0].outcome == "ambiguous"
    print("  both-touch bar -> ambiguous  OK")
    # never triggered: price gaps up and never prints close-0.25 within K
    bars3 = bars.copy()
    for col in ("open", "high", "low", "close"):
        bars3.loc[1:, col] = bars3.loc[1:, col] + 5
    tr3, c3 = simulate(bars3, wrbs, k_bars=3)
    assert len(tr3) == 0 and c3["never_triggered"] == 1
    print("  no-touch within K -> never_triggered  OK")
    # bearish mirror
    wrbs4 = pd.DataFrame(dict(ts_event=[ts[0]], symbol=["TEST"], direction=["bearish"], close=[5000.0]))
    bars4 = bars.copy()
    bars4.loc[1, ["low", "high"]] = [4999.9, 5000.30]   # touch 5000.25 trigger
    bars4.loc[2, ["low", "high"]] = [5000.9, 5001.50]   # target 5001.25 hit, stop 4999.25 not
    tr4, _ = simulate(bars4, wrbs4, k_bars=3)
    assert len(tr4) == 1 and tr4.iloc[0].dir == "long" and tr4.iloc[0].outcome == "win"
    print("  bearish mirror -> long win  OK")
    print("SELF-TEST OK.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config"); ap.add_argument("--wrb")
    ap.add_argument("--month", default="2025-10"); ap.add_argument("--symbol", default="ESZ5")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    if not a.config or not a.wrb:
        raise SystemExit("--config and --wrb required (or --selftest)")
    bars = load_bars(a.config, a.month, a.symbol)
    wrbs = load_wrbs(a.wrb, a.month, a.symbol)
    print(f"[data] {a.symbol} {a.month}: bars={len(bars):,} (RTH {int((bars.session=='RTH').sum()):,}) "
          f"| WRB signals={len(wrbs)} (bull {int((wrbs.direction=='bullish').sum())} / "
          f"bear {int((wrbs.direction=='bearish').sum())})")
    print(f"[rule] fade opposite the WRB: trigger = close -/+ 1 tick, bracket +/-{TARGET_PTS:.2f}pt, "
          f"one position at a time, force-exit at last RTH bar")
    for k in K_GRID:
        tr, counters = simulate(bars, wrbs, k)
        report(tr, counters, k)
    print("\nREAD: PRIMARY = CONSERVATIVE line at each K. Symmetric bracket => random-walk baseline "
          "win% ~0.50 and net ~0; the finding is the deviation, and 1m touch-fills flatter tight "
          "brackets — treat small deviations as fill noise, not edge.")


if __name__ == "__main__":
    main()
