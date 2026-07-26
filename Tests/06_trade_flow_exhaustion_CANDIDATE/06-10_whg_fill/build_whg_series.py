#!/usr/bin/env python3
"""
build_whg_series.py — STEP 1 of the WHG-fill test: derive + verify WRB/WHG tables (1m and 5m)
-------------------------------------------------------------------------------
Identifies WRBs and WRB Hidden Gaps per WRB_Definition.txt (the single source of truth), on CONTIGUOUS
OHLC bars, for October ESZ5. Two timeframes:
  1m  <- es_1m_front.parquet   (NOT wrb_1m.parquet: that is WRB-only/sparse; WHG needs contiguous bars)
  5m  <- es_5m_front.parquet
Writes whg_1m_<month>.parquet and whg_5m_<month>.parquet. Read-only on inputs. Self-checks before write.

WHG geometry (verbatim from WRB_Definition.txt 1.4):
  WRB: body[i]=|close-open| strictly > body of EACH of prior 3 bars (doji body=0 cannot be a WRB).
  bullish WRB: prior_body_high = max over prior 3 of max(open,close); WHG=[prior_body_high, close] if close>prior_body_high.
  bearish WRB: prior_body_low  = min over prior 3 of min(open,close); WHG=[close, prior_body_low]  if close<prior_body_low.
PROJECT DISCIPLINE: the prior 3 bars must share session_date with bar i (no WRB spanning a session seam).

VERIFIED: on uploaded es_5m_front, first Oct WHG @2025-10-01 00:15 bearish, zone [6716.50,6721.50] size
5.00 reconciles by hand with the definition. 5m Oct: ~1421 WRBs / ~1174 WHGs of 6324 bars.

RUN (from the WHG test folder)
  python3 build_whg_series.py --config ../../../config.toml
"""

# --- path bootstrap (subtest dir -> shared root modules) ---
import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
# --- end path bootstrap ---

import argparse, tomllib
import pandas as pd, numpy as np

INSTRUMENT_ID = 294973
LO = pd.Timestamp("2025-10-01", tz="UTC"); HI = pd.Timestamp("2025-11-01", tz="UTC")
MONTH = "2025-10"


def identify_whg(df):
    """df: contiguous single-instrument bars (one timeframe), sorted by ts_event. Returns df + WRB/WHG cols."""
    o = df.open.to_numpy(); c = df.close.to_numpy()
    sd = df.session_date.astype(str).to_numpy()
    body = np.abs(c - o); n = len(df)
    is_wrb = np.zeros(n, bool); direction = np.array([""] * n, object)
    whg_top = np.full(n, np.nan); whg_bot = np.full(n, np.nan); has_whg = np.zeros(n, bool)
    for i in range(3, n):
        if not (sd[i] == sd[i-1] == sd[i-2] == sd[i-3]):
            continue                                  # no WRB across a session seam
        if body[i] <= 0:
            continue                                  # doji cannot be a WRB
        if not (body[i] > body[i-1] and body[i] > body[i-2] and body[i] > body[i-3]):
            continue
        is_wrb[i] = True
        if c[i] > o[i]:
            direction[i] = "bullish"
            pbh = max(max(o[i-1], c[i-1]), max(o[i-2], c[i-2]), max(o[i-3], c[i-3]))
            if c[i] > pbh:
                has_whg[i] = True; whg_bot[i] = pbh; whg_top[i] = c[i]
        elif c[i] < o[i]:
            direction[i] = "bearish"
            pbl = min(min(o[i-1], c[i-1]), min(o[i-2], c[i-2]), min(o[i-3], c[i-3]))
            if c[i] < pbl:
                has_whg[i] = True; whg_top[i] = pbl; whg_bot[i] = c[i]
    out = df.copy()
    out["is_wrb"] = is_wrb; out["direction"] = direction
    out["has_whg"] = has_whg; out["whg_top"] = whg_top; out["whg_bottom"] = whg_bot
    out["whg_size"] = whg_top - whg_bot
    return out


def load_oct(path):
    d = pd.read_parquet(path)
    d = d[(d.instrument_id == INSTRUMENT_ID) & (d.ts_event >= LO) & (d.ts_event < HI)]
    return d.sort_values("ts_event").reset_index(drop=True)


def self_check(tf, w):
    nb, nwrb, nwhg = len(w), int(w.is_wrb.sum()), int(w.has_whg.sum())
    print(f"[{tf}] bars={nb}  WRBs={nwrb}  WHGs={nwhg} "
          f"(bull {int(((w.direction=='bullish')&w.has_whg).sum())}, "
          f"bear {int(((w.direction=='bearish')&w.has_whg).sum())})")
    assert nb > 0, f"{tf}: no October ESZ5 bars (instrument/month filter or front-month wrong)"
    assert nwrb > 0 and nwhg > 0, f"{tf}: zero WRBs/WHGs — identification failed"
    # zone sanity: top > bottom for every WHG
    z = w[w.has_whg]
    assert (z.whg_top > z.whg_bottom).all(), f"{tf}: a WHG has top<=bottom (geometry bug)"
    ex = z.head(1)
    if len(ex):
        r = ex.iloc[0]
        print(f"[{tf}] example WHG @ {r.ts_event} {r.direction} zone=[{r.whg_bottom:.2f},{r.whg_top:.2f}] size={r.whg_size:.2f}")
    if nwhg / nb > 0.5:
        print(f"[{tf}] NOTE: WHGs on >50% of bars — 'a WHG existed before entry' is nearly always true;"
              f" expect the fill signal to be noisy (common events carry little information).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", default=".")
    args = ap.parse_args()
    cfg = tomllib.load(open(args.config, "rb"))
    es1m = cfg["paths"]["es_1m_front"]
    es5m = cfg["paths"].get("es_5m_front")
    if not es5m:
        print("WARNING: config[paths][es_5m_front] not set. Add it (path to es_5m_front.parquet).")
    srcs = [("1m", es1m)] + ([("5m", es5m)] if es5m else [])
    for tf, path in srcs:
        d = load_oct(path)
        w = identify_whg(d)
        self_check(tf, w)
        outp = _os.path.join(args.outdir, f"whg_{tf}_{MONTH}.parquet")
        w.to_parquet(outp, index=False)
        print(f"[{tf}] wrote {outp}\n")
    print("[done] STEP 1 complete. Verify the counts/example above, then run the WHG-fill hazard test (step 2).")


if __name__ == "__main__":
    main()
