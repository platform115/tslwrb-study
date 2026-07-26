#!/usr/bin/env python3
"""
test_signal_redundancy.py — do Signal 1 (body-progress) and Signal 2 (adverse stop) overlap?
-------------------------------------------------------------------------------
The guide claims the two exit signals are COMPLEMENTARY (forward "not building" vs reactive "went
against me"). Untested. If they flag the SAME losers at the SAME time, they are one signal twice
(redundant) and "use both" buys nothing. If they catch DIFFERENT losers, or S1 fires earlier on shared
ones, they are a genuine two-part system. This settles it on the 16 losers.

PER LOSER, compute (per-second mid):
  br60         = body_ratio at entry+60s (Signal 1 read; NaN if cut before 60s -> S1 cannot fire)
  adv60        = adverse excursion (pts) by 60s (Signal 2 reading AT 60s)
  max_adv      = max adverse over [entry, exit] (Signal 2's eventual trigger)
  s2_fire_s    = first second adverse crosses the S2 zone (else NaN)
FLAGS (indicative zones from the guide; threshold-robustness also reported):
  S1 flag = open at 60s AND br60 < 0.5
  S2 flag = max_adv >= 2.5 pts
CROSS-TAB: both / S1-only / S2-only / neither / S1-NA (cut before 60s; S2-territory only).
COMPLEMENTARITY EVIDENCE:
  - S1-only or S2-only losers > 0  => catch different trades.
  - losers with S1 flag at 60s but adv60 < 2.5 (S2 not yet) that LATER hit max_adv>=2.5
    => S1 gave EARLIER warning on a trade S2 only caught later (temporal complementarity).
  - corr(br60, max_adv): strongly negative => redundant (low body <-> high adverse, same trades).

Deterministic. Read-only. 16 losers, October, descriptive. Not financial advice.

RUN (from its subfolder inside the 06 folder; SSD must be mounted)
  python3 test_signal_redundancy.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import numpy as np, pandas as pd

from trade_flow_exhaustion import build_groups, read_per_second, S, M

import os as _os
INSTRUMENT_ID = int(_os.environ.get("TSLWRB_IID", "294973"))
MONTH = _os.environ.get("TSLWRB_MONTH", "2025-10")
SYMBOL = _os.environ.get("TSLWRB_SYMBOL", "ESZ5")
print(f"[env] MONTH={MONTH} SYMBOL={SYMBOL} INSTRUMENT_ID={INSTRUMENT_ID}", flush=True)
LO = pd.Timestamp(f"{MONTH}-01", tz="UTC"); HI = LO + pd.offsets.MonthBegin(1)
T_CHECK = 60; S1_THR = 0.5; S2_THR = 2.5


def scalar(v): return float(np.asarray(v).ravel()[0])


def load(config_path, wrb_path):
    cfg = tomllib.load(open(config_path, "rb"))
    g = build_groups(cfg["paths"]["episodes"], wrb_path)
    g["is_loser"] = g["realized_pnl"] < 0
    ep = pd.read_parquet(cfg["paths"]["episodes"])
    ep["uid"] = ep["source_file"].astype(str) + "::" + ep["episode_id"].astype(str)
    ep["entry_price"] = ep["entry_prices"].map(scalar)
    g = g.merge(ep[["uid", "entry_price"]], on="uid", how="left")
    return g, cfg["run"]["resolved"]["windowed_parquet"], cfg["paths"]["es_1m_front"]


def load_bars(es1m):
    d = pd.read_parquet(es1m, columns=["ts_event", "instrument_id", "open", "close"])
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    d = d.sort_values("ts_event").reset_index(drop=True)
    return (d.ts_event.astype("int64") // 1_000_000_000).to_numpy(), d.open.to_numpy(), d.close.to_numpy()


def prior_body_max(bar_sec, bopen, bclose, entry_ts):
    e_s = np.int64(pd.Timestamp(entry_ts).floor("min").value // 1_000_000_000)
    j = int(np.searchsorted(bar_sec, e_s, "left"))
    return float(np.abs(bclose[j-3:j] - bopen[j-3:j]).max()) if j >= 3 else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--wrb", required=True)
    args = ap.parse_args()

    g, windowed, es1m = load(args.config, args.wrb)
    losers = g[g.is_loser].copy()
    print(f"[redun] losers={len(losers)} (expect 16)")
    bar_sec, bopen, bclose = load_bars(es1m)
    t_min = losers["entry"].min() - M(5); t_max = losers["exit"].max() + M(1)
    sec, buyv, sellv, mid = read_per_second(windowed, t_min, t_max)
    print(f"[redun] per-second rows: {len(sec):,}")

    def mid_at(t_ts):
        i = int(np.searchsorted(sec, np.int64(pd.Timestamp(t_ts).value // 1_000_000_000), "right") - 1)
        return float(mid[i]) if i >= 0 else np.nan

    rows = []
    for _, r in losers.iterrows():
        sgn = 1.0 if r.side == "long" else -1.0
        pbm = prior_body_max(bar_sec, bopen, bclose, r.entry)
        open60 = r.exit > r.entry + S(T_CHECK)
        m60 = mid_at(r.entry + S(T_CHECK)) if open60 else np.nan
        br60 = (((m60 - r.entry_price) * sgn) / pbm) if (open60 and pbm and pbm > 0 and not np.isnan(m60)) else np.nan
        # adverse path over [entry, exit]
        e_s = np.int64(pd.Timestamp(r.entry).value // 1_000_000_000)
        x_s = np.int64(pd.Timestamp(r.exit).value // 1_000_000_000)
        i0 = np.searchsorted(sec, e_s, "left"); i1 = np.searchsorted(sec, x_s, "left")
        s = sec[i0:i1]; px = mid[i0:i1]
        adv = np.maximum(0.0, (r.entry_price - px) if r.side == "long" else (px - r.entry_price))
        run = np.maximum.accumulate(adv) if len(adv) else np.array([np.nan])
        max_adv = float(run[-1]) if len(adv) else np.nan
        # adverse by 60s
        k = np.searchsorted(s, e_s + T_CHECK, "left")
        adv60 = float(run[k-1]) if (len(adv) and k > 0) else (0.0 if len(adv) else np.nan)
        # S2 fire time
        fire = np.searchsorted(run, S2_THR, "left") if len(adv) else None
        s2_fire_s = float(s[fire] - e_s) if (fire is not None and fire < len(run)) else np.nan
        s1 = bool(open60 and not np.isnan(br60) and br60 < S1_THR)
        s2 = bool(not np.isnan(max_adv) and max_adv >= S2_THR)
        rows.append(dict(uid=r.uid, hold=round(r.hold), open60=open60, br60=br60,
                         adv60=adv60, max_adv=max_adv, s2_fire_s=s2_fire_s, s1=s1, s2=s2))
    d = pd.DataFrame(rows)

    print(f"\n  per-loser (S1: br60<{S1_THR} | S2: max_adv>={S2_THR}pts):")
    print(f"  {'hold':>4} {'open60':>6} {'br60':>6} {'adv60':>6} {'maxadv':>6} {'s2fire':>6} {'S1':>3} {'S2':>3}")
    for _, x in d.sort_values("hold").iterrows():
        print(f"  {x.hold:>4} {str(x.open60):>6} {x.br60 if not np.isnan(x.br60) else float('nan'):>6.2f} "
              f"{x.adv60:>6.2f} {x.max_adv:>6.2f} "
              f"{x.s2_fire_s if not np.isnan(x.s2_fire_s) else float('nan'):>6.0f} "
              f"{'Y' if x.s1 else '.':>3} {'Y' if x.s2 else '.':>3}")

    both = int((d.s1 & d.s2).sum()); s1o = int((d.s1 & ~d.s2).sum())
    s2o = int((~d.s1 & d.s2).sum()); neither = int((~d.s1 & ~d.s2).sum())
    s1_na = int((~d.open60).sum())
    print(f"\n  CROSS-TAB (n={len(d)}): both={both}  S1-only={s1o}  S2-only={s2o}  neither={neither}")
    print(f"    of which cut BEFORE 60s (S1 cannot fire, S2-territory): {s1_na}")

    # temporal complementarity: S1 flagged at 60s but S2 not yet (adv60<thr) yet later hit S2
    early = d[(d.s1) & (d.adv60 < S2_THR) & (d.s2)]
    print(f"\n  S1 fired EARLY (flat@60s, not yet adverse) on trades S2 only caught later: {len(early)}")
    if len(early):
        print(f"    these are where S1 adds temporal value (S2 fire times: "
              f"{[int(v) for v in early.s2_fire_s.dropna()]}s vs S1 at 60s)")

    # redundancy correlation (open-at-60 only)
    dd = d[d.open60].dropna(subset=["br60", "max_adv"])
    if len(dd) >= 5:
        c = np.corrcoef(dd.br60, dd.max_adv)[0, 1]
        print(f"\n  corr(br60, max_adv) over {len(dd)} open-at-60 losers = {c:+.2f}  "
              f"(strong negative => redundant; near 0 => independent)")

    # threshold robustness
    print(f"\n  threshold robustness (both/S1only/S2only/neither):")
    for s1t, s2t in [(0.0, 3.0), (0.5, 2.5), (0.5, 2.0)]:
        a = d.open60 & (d.br60 < s1t); b = d.max_adv >= s2t
        print(f"    S1<{s1t} S2>={s2t}: both={int((a&b).sum())} S1only={int((a&~b).sum())} "
              f"S2only={int((~a&b).sum())} neither={int((~a&~b).sum())}")

    print(f"\n[redun] READ: substantial S1-only + S2-only (+ fast-cut S2-territory) => COMPLEMENTARY.")
    print(f"  mostly 'both' with strong negative corr => REDUNDANT (one signal twice).")


if __name__ == "__main__":
    main()
