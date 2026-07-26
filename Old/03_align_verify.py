#!/usr/bin/env python3
"""
03_align_verify.py  —  Stage 0 verification GATE.

Resamples the windowed MBP-10 TRADES to 1-minute OHLCV and reconciles them
against es_1m_front on the minutes that are FULLY inside a window (boundary
minutes are excluded so a truncated edge-minute can't create a false mismatch).

This single comparison confirms three things at once:
  (a) right contract        -> a constant O/H/L/C offset means wrong contract
  (b) clocks agree          -> scattered mismatches mean a tz / session-boundary bug
  (c) trades are complete   -> per-minute VOLUME matching es_1m_front means we are
                               seeing every trade (no need to buy a separate Trades feed)

GATE: exits non-zero if reconciliation fails. Do not build features until this passes.

Run locally:  python3 03_align_verify.py
"""
from __future__ import annotations
import importlib.util, json, sys, tomllib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
NS_MIN = 60_000_000_000

# import helpers from 02 (single source of truth for window intervals / trade mask)
_spec = importlib.util.spec_from_file_location("reduce02", HERE / "02_reduce_to_windows.py")
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
build_window_intervals = _m.build_window_intervals
_trade_mask = _m._trade_mask
_ns = _m._ns
_month_end = _m._month_end


def load_config(path: Path = HERE / "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def covered_minutes(intervals_by_day: dict[str, list[tuple[int, int]]]) -> np.ndarray:
    """Minute-start ns that are FULLY covered: [m, m+60s) subset of some window interval."""
    mins: set[int] = set()
    for ivs in intervals_by_day.values():
        for s, e in ivs:
            first = ((s + NS_MIN - 1) // NS_MIN) * NS_MIN          # first minute-start >= s
            last = (e // NS_MIN) * NS_MIN - NS_MIN                  # last m with m+60s <= e
            m = first
            while m <= last:
                mins.add(m); m += NS_MIN
    return np.array(sorted(mins), dtype="int64")


def resample_windowed_trades(parquet_path: Path, covered: np.ndarray, chunk: int = 1_000_000) -> pd.DataFrame:
    """Stream the windowed parquet, keep trades on covered minutes, aggregate to 1m OHLCV. RAM-safe."""
    pf = pq.ParquetFile(parquet_path)
    cols = ["ts_event", "sequence", "action", "price", "size"]
    parts: list[pd.DataFrame] = []
    for batch in pf.iter_batches(batch_size=chunk, columns=cols):
        df = batch.to_pandas()
        df = df[_trade_mask(df["action"])]
        if df.empty:
            continue
        ts = _ns(df["ts_event"])
        minute = (ts // NS_MIN) * NS_MIN
        keep = np.isin(minute, covered)
        if not keep.any():
            continue
        df = df.assign(minute=minute, _ts=ts).loc[keep]
        df = df.sort_values(["minute", "_ts", "sequence"])
        part = df.groupby("minute").agg(
            open=("price", "first"), close=("price", "last"),
            high=("price", "max"), low=("price", "min"), vol=("size", "sum"),
            o_ts=("_ts", "first"), o_seq=("sequence", "first"),
            c_ts=("_ts", "last"), c_seq=("sequence", "last"),
        ).reset_index()
        parts.append(part)
    if not parts:
        raise SystemExit("[FATAL] no trades on covered minutes — windowed parquet empty or all boundary?")
    allp = pd.concat(parts, ignore_index=True)
    # reduce across chunk boundaries with scalar sort keys (no tuple comparisons)
    op = allp.sort_values(["minute", "o_ts", "o_seq"]).groupby("minute", as_index=True)["open"].first()
    cl = allp.sort_values(["minute", "c_ts", "c_seq"]).groupby("minute", as_index=True)["close"].last()
    hi = allp.groupby("minute")["high"].max()
    lo = allp.groupby("minute")["low"].min()
    vo = allp.groupby("minute")["vol"].sum().astype("int64")
    res = pd.DataFrame({"open": op, "high": hi, "low": lo, "close": cl, "vol": vo}).reset_index()
    res["ts_event"] = pd.to_datetime(res["minute"], utc=True)
    return res.set_index("ts_event").sort_index()[["open", "high", "low", "close", "vol"]]


def main() -> int:
    cfg = load_config()
    P, R = cfg["paths"], cfg["run"]
    month = R["month"]
    tol = R["recon_tol_ticks"] * R["tick"]

    sidecar = Path(P["out_dir"]) / f"02_resolved_{month}.json"
    if not sidecar.exists():
        raise SystemExit(f"[FATAL] {sidecar} not found — run 02 first")
    meta = json.loads(sidecar.read_text())
    front = meta["front_contract"]
    win_parquet = Path(meta["windowed_parquet"])

    intervals = build_window_intervals(P["episodes"], month, R["pre_entry_min"], R["post_exit_min"])
    covered = covered_minutes(intervals)
    print(f"[info] front={front}  fully-covered minutes={len(covered):,}  tol={tol} pts")

    mbp = resample_windowed_trades(win_parquet, covered)

    es = pd.read_parquet(P["es_1m_front"], columns=["ts_event", "symbol", "open", "high", "low", "close", "volume", "session"])
    lo = pd.Timestamp(f"{month}-01", tz="UTC"); hi = pd.Timestamp(_month_end(month), tz="UTC")
    es = es[(es["ts_event"] >= lo) & (es["ts_event"] < hi) & (es["symbol"] == front)]
    es = es.set_index("ts_event").sort_index()

    j = mbp.join(es, how="inner", lsuffix="_mbp", rsuffix="_es")
    if j.empty:
        raise SystemExit("[FATAL] no overlapping minutes between windowed MBP-10 and es_1m_front")

    def field_report(f: str) -> dict:
        d = (j[f"{f}_mbp"] - j[f"{f}_es"]).astype(float)
        return {"within_tol_pct": float((d.abs() <= tol).mean() * 100),
                "max_abs": float(d.abs().max()),
                "median_signed": float(d.median())}  # constant offset detector

    rep = {f: field_report(f) for f in ("open", "high", "low", "close")}
    vol_match = float((j["vol"] == j["volume"]).mean() * 100)
    vol_close = float((np.abs(j["vol"] - j["volume"]) <= np.maximum(1, 0.001 * j["volume"])).mean() * 100)

    print(f"[recon] minutes compared: {len(j):,}")
    for f, r in rep.items():
        print(f"  {f:>5}: within_tol={r['within_tol_pct']:.2f}%  max_abs={r['max_abs']:.4f}  median_signed={r['median_signed']:+.4f}")
    print(f"  volume exact-match={vol_match:.2f}%   within0.1%={vol_close:.2f}%")

    # per-session visibility (OVERLAP/auction minutes can legitimately differ in volume)
    if "session" in j:
        print("[recon] by session:")
        for s, g in j.groupby("session"):
            cm = float((np.abs(g["close_mbp"] - g["close_es"]) <= tol).mean() * 100)
            vm = float((g["vol"] == g["volume"]).mean() * 100)
            print(f"   {s:>8}: n={len(g):>5}  close_within_tol={cm:5.1f}%  vol_exact={vm:5.1f}%")

    ohlc_ok = all(r["within_tol_pct"] >= 99.0 and abs(r["median_signed"]) <= tol for r in rep.values())
    vol_ok = vol_match >= 99.0
    summary = (f"# 03_align_{front}_{month}\n\n"
               f"- minutes compared: {len(j):,}\n"
               f"- OHLC within {tol} pts: " + ", ".join(f"{f} {rep[f]['within_tol_pct']:.2f}%" for f in rep) + "\n"
               f"- max abs diff (pts): " + ", ".join(f"{f} {rep[f]['max_abs']:.4f}" for f in rep) + "\n"
               f"- median signed diff (offset check): " + ", ".join(f"{f} {rep[f]['median_signed']:+.4f}" for f in rep) + "\n"
               f"- volume exact-match: {vol_match:.2f}%  (within 0.1%: {vol_close:.2f}%)\n"
               f"- GATE: {'PASS' if (ohlc_ok and vol_ok) else 'FAIL'}\n")
    out_md = Path(P["out_dir"]) / f"03_align_{front}_{month}.md"
    out_md.write_text(summary)
    print(f"\n{summary}\n[done] wrote {out_md}")

    if not (ohlc_ok and vol_ok):
        print("[GATE] FAIL — do not build features. "
              "Constant OHLC offset => wrong contract; scattered => clock/session; "
              "volume gap => incomplete trades or wrong volume field.", file=sys.stderr)
        return 1
    print("[GATE] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
