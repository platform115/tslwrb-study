#!/usr/bin/env python3
"""
02_reduce_to_windows.py  —  Stage 0 reduce step.

Streams the per-day MBP-10 .dbn.zst files for ONE month, resolves the front-month
outright ES contract (by traded volume, not by assumption), keeps only that
contract's records that fall inside the union of per-episode windows
[first_entry - pre_entry_min, last_exit + post_exit_min], and writes a single
compact windowed parquet for the month.

Design constraints (M1 Air, 8/16 GB):
  - NEVER load a whole daily file. We stream with DBNStore.to_df(count=chunk_rows),
    which reads the .zst through a buffered reader and yields DataFrames chunk by
    chunk. Peak RAM = one chunk + one parquet row group.
  - DuckDB cannot read .dbn.zst, so the databento library is the only reader for
    this step. (DuckDB is for querying the parquet OUTPUT, downstream.)

What "resolve, don't assume" means here:
  - We do a cheap early-exit pass over each file tallying TRADE volume per outright
    ES symbol, pick the max-volume outright as front month, print the full table,
    and assert the choice is identical across all files in the month. The true gate
    is 03 (reconcile against es_1m_front); this step just refuses to guess silently.

Output:
  - <out_dir>/mbp10_<contract>_<month>_windowed.parquet   (all 10 book levels, lossless within window)
  - <out_dir>/02_resolved_<month>.json                    (resolved contract + per-file symbol/volume table; read by 03)

Run locally:  python3 02_reduce_to_windows.py
"""
from __future__ import annotations
import json, re, sys, tomllib
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import databento as db

HERE = Path(__file__).resolve().parent
OUTRIGHT_RE = re.compile(r"^ES[FGHJKMNQUVXZ]\d{1,2}$")  # ESZ5, ESH6, ... (outright futures, not spreads)


def load_config(path: Path = HERE / "config.toml") -> dict:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _ns(s: pd.Series) -> np.ndarray:
    """tz-aware/naive datetime Series -> int64 nanoseconds since epoch (UTC). pandas-3 safe."""
    return s.to_numpy(dtype="datetime64[ns]").astype("int64")


def build_window_intervals(episodes_path: str, month: str, pre_min: int, post_min: int) -> dict[str, list[tuple[int, int]]]:
    """Return {trading_date 'YYYY-MM-DD': [(start_ns, end_ns), ...]} merged per day. All UTC ns."""
    ep = pd.read_parquet(episodes_path)
    lo = pd.Timestamp(f"{month}-01", tz="UTC"); hi = pd.Timestamp(_month_end(month), tz="UTC")
    ep = ep[(ep["first_entry_utc"] >= lo) & (ep["first_entry_utc"] < hi)].copy()
    bad = ep["first_entry_utc"].isna() | ep["last_exit_utc"].isna()
    if bad.any():
        print(f"[warn] dropping {int(bad.sum())} episode(s) with NaT entry/exit (pre-registered data-integrity exclusion)")
        ep = ep[~bad].copy()
    if ep.empty:
        raise SystemExit(f"[FATAL] no episodes found in {month}; check config[paths].episodes")
    ep["w_start"] = ep["first_entry_utc"] - pd.Timedelta(minutes=pre_min)
    ep["w_end"] = ep["last_exit_utc"] + pd.Timedelta(minutes=post_min)

    out: dict[str, list[tuple[int, int]]] = {}
    for day, grp in ep.groupby("trading_date"):
        iv = sorted(zip(_ns(grp["w_start"]), _ns(grp["w_end"])))
        merged: list[list[int]] = []
        for s, e in iv:
            if merged and s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
        out[str(day)] = [(s, e) for s, e in merged]
    return out


def _month_end(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y + 1}-01-01" if m == 12 else f"{y}-{m + 1:02d}-01"


def _trade_mask(action_col: pd.Series) -> pd.Series:
    # to_df renders action as a single-char code; TRADE -> 'T'. Be tolerant.
    return action_col.astype(str).str.upper().str.startswith("T")


def _in_any_interval(ts_ns: np.ndarray, intervals: list[tuple[int, int]]) -> np.ndarray:
    keep = np.zeros(len(ts_ns), dtype=bool)
    for s, e in intervals:
        keep |= (ts_ns >= s) & (ts_ns < e)
    return keep


def resolve_front_month(path: Path, sample_rows: int, chunk_rows: int) -> tuple[str, dict[str, int], list[str]]:
    """Early-exit pass: tally TRADE volume per outright symbol; return (front, volume_table, all_symbols_seen)."""
    vol: dict[str, int] = {}
    all_syms: set[str] = set()
    seen = 0
    store = db.DBNStore.from_file(str(path))
    for chunk in store.to_df(price_type="float", map_symbols=True, tz="UTC", count=chunk_rows):
        all_syms.update(chunk["symbol"].astype(str).unique().tolist())
        tr = chunk[_trade_mask(chunk["action"])]
        if not tr.empty:
            g = tr.groupby(tr["symbol"].astype(str))["size"].sum()
            for sym, v in g.items():
                if OUTRIGHT_RE.match(sym):
                    vol[sym] = vol.get(sym, 0) + int(v)
        seen += len(chunk)
        if seen >= sample_rows and vol:
            break
    if not vol:
        raise SystemExit(f"[FATAL] no outright-ES trades found in sample of {path.name}")
    front = max(vol, key=vol.get)
    return front, dict(sorted(vol.items(), key=lambda kv: -kv[1])), sorted(all_syms)


# Columns to keep in the windowed parquet: identity + trade fields + all 10 book levels.
LEVEL_COLS = [f"{sd}_{fld}_{i:02d}" for sd in ("bid", "ask") for fld in ("px", "sz", "ct") for i in range(10)]
KEEP_COLS = ["ts_event", "ts_recv", "instrument_id", "symbol", "action", "side",
             "depth", "price", "size", "flags", "sequence"] + LEVEL_COLS


def main() -> int:
    cfg = load_config()
    P, R = cfg["paths"], cfg["run"]
    month = R["month"]
    mbp_dir = Path(P["mbp10_dir"])
    out_dir = Path(P["out_dir"]); out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(mbp_dir.glob(f"glbx-mdp3-{month.replace('-', '')}*.mbp-10.dbn.zst"))
    if not files:
        raise SystemExit(f"[FATAL] no MBP-10 files for {month} under {mbp_dir}")
    print(f"[info] {len(files)} daily files for {month}")

    intervals_by_day = build_window_intervals(P["episodes"], month, R["pre_entry_min"], R["post_exit_min"])
    active_days = set(intervals_by_day)
    print(f"[info] {len(active_days)} active trading days with episodes in {month}")

    # ---- Resolve front month (per file, assert consistent) ----
    front = None
    per_file_report = {}
    for fp in files:
        f_front, vol_tbl, all_syms = resolve_front_month(fp, R["resolve_sample_rows"], R["chunk_rows"])
        per_file_report[fp.name] = {"front": f_front, "outright_volume": vol_tbl, "n_symbols_seen": len(all_syms)}
        print(f"[resolve] {fp.name}: front={f_front}  outright_vol={vol_tbl}")
        if front is None:
            front = f_front
        elif f_front != front:
            raise SystemExit(f"[FATAL] front-month disagreement: {front} vs {f_front} in {fp.name} "
                             f"(unexpected mid-month roll? stop and inspect)")
    print(f"[resolve] month front month = {front}")

    # ---- Reduce pass: filter to front month + window union, write incrementally ----
    out_parquet = out_dir / f"mbp10_{front}_{month}_windowed.parquet"
    writer: pq.ParquetWriter | None = None
    rows_written = 0
    schema_cols: list[str] | None = None

    try:
        for fp in files:
            mdate = re.search(r"(\d{8})", fp.name)
            if not mdate:
                raise SystemExit(f"[FATAL] cannot parse date from {fp.name}")
            d = mdate.group(1)
            day = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
            if day not in intervals_by_day:
                print(f"[reduce] {fp.name}: no episodes this day, skipping")
                continue
            intervals = intervals_by_day[day]
            store = db.DBNStore.from_file(str(fp))
            kept_day = 0
            for chunk in store.to_df(price_type="float", map_symbols=True, tz="UTC", count=R["chunk_rows"]):
                chunk = chunk.reset_index()  # to_df puts ts_recv on the index for MBP-10; recover it as a column
                if schema_cols is None:
                    core = ["ts_event", "symbol", "action", "side", "price", "size", "sequence"]
                    missing_core = [c for c in core if c not in chunk.columns]
                    if missing_core:
                        raise SystemExit(f"[FATAL] core columns missing from to_df: {missing_core}\n"
                                         f"got: {sorted(chunk.columns)}")
                    schema_cols = [c for c in KEEP_COLS if c in chunk.columns]
                    dropped = [c for c in KEEP_COLS if c not in chunk.columns]
                    if dropped:
                        print(f"[warn] columns not present, will not be written: {dropped}")
                sym = chunk["symbol"].astype(str)
                ts_ns = _ns(chunk["ts_event"])
                mask = (sym == front).to_numpy() & _in_any_interval(ts_ns, intervals)
                if not mask.any():
                    continue
                sub = chunk.loc[mask, schema_cols].reset_index(drop=True)
                table = pa.Table.from_pandas(sub, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(out_parquet, table.schema, compression="zstd")
                writer.write_table(table)
                rows_written += len(sub); kept_day += len(sub)
            print(f"[reduce] {fp.name} ({day}): kept {kept_day:,} rows")
    finally:
        if writer is not None:
            writer.close()

    if rows_written == 0:
        raise SystemExit("[FATAL] wrote 0 rows — check window intervals vs file timestamps (tz/day mismatch?)")

    # ---- Sidecar (read by 03). NOTE on config.toml: tomllib is read-only and we
    # deliberately do NOT have a script rewrite a hand-curated config.toml (fragile,
    # easy to clobber). Resolved facts are machine outputs -> JSON sidecar. ----
    sidecar = out_dir / f"02_resolved_{month}.json"
    payload = {
        "month": month,
        "front_contract": front,
        "windowed_parquet": str(out_parquet),
        "rows_written": rows_written,
        "pre_entry_min": R["pre_entry_min"],
        "post_exit_min": R["post_exit_min"],
        "active_days": sorted(active_days),
        "per_file": per_file_report,
    }
    sidecar.write_text(json.dumps(payload, indent=2))
    print(f"\n[done] wrote {rows_written:,} rows -> {out_parquet}")
    print(f"[done] resolved sidecar -> {sidecar}")
    print(f"\nOptional, if you want it in config.toml as well, paste:\n"
          f"[run.resolved]\ncontract = \"{front}\"\nwindowed_parquet = \"{out_parquet}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
