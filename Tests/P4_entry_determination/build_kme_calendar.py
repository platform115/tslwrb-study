#!/usr/bin/env python3
"""
build_kme_calendar.py — P4.1: parse the six KME-<year>-Raw.xlsx exports into one
kme_calendar.parquet. Deterministic; read-only on inputs; selftest on synthetic rows.

Export defects handled (verified on the real files 2026-11-14):
  1) COLUMN SHIFT: continuation rows of multi-event days slide every value one column
     left (Date holds the time, Impact holds the event name). ~43% of rows.
  1b) TIME COLLAPSE: events sharing a release time print the time once; follower rows
     have a BLANK Date cell, the same one-left shift (currency in "Time UTC", event in
     Impact), and INHERIT the previous row's time. NFP/FOMC rows live in this shape.
  2) Date only on a day's first row ("SatJan 1", no year) -> forward-fill + year from filename.
  3) Impact tier did NOT survive the export (it was an icon). The tier mapping is a
     SEPARATE, versioned file (kme_tiers.*) — flagged as our construction, since Perry
     states no formal KME definition (criterion given: "impactful on the S&P 500").
  4) "All Day" / "Tentative" / day-only rows -> kept, flagged, ts_utc = NaT.
"Time UTC" verified genuinely UTC across DST (ADP 13:15 Jan / 12:15 May / 13:15 Dec 2022).

RUN:   python3 build_kme_calendar.py --in-dir <dir with KME-*-Raw.xlsx> --out kme_calendar.parquet
       python3 build_kme_calendar.py --selftest
GATES: shift-reassembly clean · NFP rows land on Fridays at 12:30/13:30 UTC ·
       FOMC Statement present on Fed-calendar dates (2022+2025, reported) · per-year spans printed.
"""
import argparse, datetime as dt, glob, os, re
import numpy as np
import pandas as pd

DAY_RE = re.compile(r"^[A-Z][a-z]{2}([A-Z][a-z]{2})\s*(\d{1,2})$")   # "SatJan 1"
TIME_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
MONTHS = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

COLS = ["Date", "Time UTC", "Currency", "Impact", "Unnamed: 4",
        "Alerts", "Detail", "Actual", "Forecast", "Previous"]

FOMC_STMT = {  # Fed-published statement days (gate is REPORTED, not asserted)
    2022: ["2022-01-26", "2022-03-16", "2022-05-04", "2022-06-15",
           "2022-07-27", "2022-09-21", "2022-11-02", "2022-12-14"],
    2025: ["2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
           "2025-07-30", "2025-09-17", "2025-10-29", "2025-12-10"],
}


def _cell(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, dt.time):
        return v.strftime("%H:%M:%S")
    s = str(v).strip()
    return s if s and s.lower() != "nan" else None


def parse_file(path: str, year: int) -> pd.DataFrame:
    raw = pd.read_excel(path)
    missing = [c for c in COLS if c not in raw.columns]
    if missing:
        raise SystemExit(f"[FATAL] {os.path.basename(path)} missing columns {missing}")
    CURRENCY_RE = re.compile(r"^[A-Z][A-Za-z]{1,3}$")   # USD, EUR, "All"
    rows, cur_date, cur_time, n_shift, n_inherit = [], None, None, 0, 0
    for _, r in raw.iterrows():
        vals = [_cell(r[c]) for c in COLS]
        d0 = vals[0]
        m = DAY_RE.match(d0) if d0 else None
        if m:                                   # day row (may carry the day's first event)
            cur_date = dt.date(year, MONTHS[m.group(1)], int(m.group(2)))
            time_s, currency, event = vals[1], vals[2], vals[4]
            actual, forecast, previous = vals[7], vals[8], vals[9]
        elif d0 and TIME_RE.match(d0):          # SHIFTED continuation row (time present)
            n_shift += 1
            time_s, currency, event = d0, vals[1], vals[3]
            actual, forecast, previous = vals[6], vals[7], vals[8]
        elif d0 is None:
            if vals[1] and CURRENCY_RE.match(vals[1]) and vals[3]:
                # TIME-COLLAPSED shifted row: blank time inherited from previous row
                n_shift += 1; n_inherit += 1
                time_s, currency, event = cur_time, vals[1], vals[3]
                actual, forecast, previous = vals[6], vals[7], vals[8]
            else:                               # canonical continuation / blank
                time_s, currency, event = vals[1], vals[2], vals[4]
                actual, forecast, previous = vals[7], vals[8], vals[9]
                if time_s is None and event is None:
                    continue
        else:                                   # "All Day" etc. landing in Date -> shifted label row
            time_s, currency, event = d0, vals[1], vals[3]
            actual, forecast, previous = vals[6], vals[7], vals[8]
            n_shift += 1
        if cur_date is None:
            continue
        if time_s:
            cur_time = time_s                   # remembered for time-collapsed followers
        if event is None and time_s in (None, "All Day", "Tentative"):
            continue
        is_time = bool(time_s and TIME_RE.match(time_s))
        ts = (pd.Timestamp(f"{cur_date} {time_s}", tz="UTC") if is_time else pd.NaT)
        rows.append(dict(ts_utc=ts, date=cur_date, time_label=time_s, event=event,
                         currency=currency, actual=actual, forecast=forecast,
                         previous=previous, all_day=(time_s == "All Day"),
                         tentative=(time_s == "Tentative"),
                         source_file=os.path.basename(path)))
    df = pd.DataFrame(rows)
    print(f"[parse] {os.path.basename(path)}: events={len(df)} shifted-rows reassembled={n_shift} "
          f"span={df.date.min()} -> {df.date.max()}")
    return df


def gates(df: pd.DataFrame) -> int:
    fails = 0
    # G1: no event name that looks like a time (shift reassembly clean)
    bad = df.event.dropna().astype(str).str.match(TIME_RE).sum()
    print(f"[gate G1] event names matching a time pattern: {bad} (expect 0)")
    fails += int(bad > 0)
    # G2: NFP on Fridays at 12:30/13:30 UTC
    nfp = df[(df.event == "Non-Farm Employment Change") & (df.currency == "USD") & df.ts_utc.notna()]
    if len(nfp):
        fri = (pd.to_datetime(nfp.date).dt.dayofweek == 4).mean()
        times = sorted(nfp.time_label.unique())
        ok = fri >= 0.9 and set(times) <= {"12:30:00", "13:30:00"}
        print(f"[gate G2] NFP n={len(nfp)} friday-frac={fri:.2f} times={times} -> {'OK' if ok else 'FAIL'}")
        fails += int(not ok)
    else:
        print("[gate G2] no NFP rows found -> FAIL"); fails += 1
    # G3: FOMC statement on Fed-calendar dates (reported; discovery years)
    for yr, dates in FOMC_STMT.items():
        sub = df[df.event.fillna("").str.contains("FOMC Statement")]
        have = set(str(d) for d in sub.date)
        hits = [d for d in dates if d in have]
        print(f"[gate G3] FOMC Statement {yr}: {len(hits)}/{len(dates)} Fed dates present "
              f"(missing: {[d for d in dates if d not in have] or 'none'})")
    # G4: timestamp sanity
    n_ts = df.ts_utc.notna().sum()
    print(f"[gate G4] rows with UTC timestamp: {n_ts}/{len(df)} "
          f"({df.all_day.sum()} all-day, {df.tentative.sum()} tentative, "
          f"{len(df) - n_ts - df.all_day.sum() - df.tentative.sum()} other no-time)")
    return fails


def selftest():
    print("=== SELF-TEST: synthetic shift/date logic ===")
    raw = pd.DataFrame([
        {"Date": "MonJan 3", "Time UTC": "13:30:00", "Currency": "USD", "Impact": None,
         "Unnamed: 4": "EvA", "Alerts": None, "Detail": None, "Actual": "1", "Forecast": "2", "Previous": "3", "Graph": None},
        {"Date": "14:00:00", "Time UTC": "USD", "Currency": None, "Impact": "EvB",
         "Unnamed: 4": None, "Alerts": None, "Detail": "4", "Actual": "5", "Previous": None, "Forecast": "6", "Graph": None},
        {"Date": "TueJan 4", "Time UTC": "All Day", "Currency": "USD", "Impact": None,
         "Unnamed: 4": "Holiday", "Alerts": None, "Detail": None, "Actual": None, "Forecast": None, "Previous": None, "Graph": None},
    ])
    tmp = "/tmp/_kme_selftest.xlsx"; raw.to_excel(tmp, index=False)
    df = parse_file(tmp, 2022)
    assert len(df) == 3, df
    a, b, c = df.iloc[0], df.iloc[1], df.iloc[2]
    assert a.event == "EvA" and str(a.ts_utc) == "2022-01-03 13:30:00+00:00" and float(a.actual) == 1.0
    # shifted row: actual comes from the Detail slot (one-left shift), forecast from Actual, previous from Forecast
    assert b.event == "EvB" and str(b.ts_utc) == "2022-01-03 14:00:00+00:00" and float(b.actual) == 4.0 \
        and float(b.forecast) == 5.0 and float(b.previous) == 6.0
    assert c.event == "Holiday" and c.all_day and pd.isna(c.ts_utc)
    os.remove(tmp)
    print("SELF-TEST OK.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir"); ap.add_argument("--out", default="kme_calendar.parquet")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest(); return
    if not a.in_dir:
        raise SystemExit("--in-dir required (or --selftest)")
    files = sorted(glob.glob(os.path.join(a.in_dir, "*KME-*-Raw.xlsx")))
    if not files:
        raise SystemExit(f"[FATAL] no KME-*-Raw.xlsx under {a.in_dir}")
    parts = []
    for f in files:
        m = re.search(r"KME-(\d{4})-Raw", f)
        if not m:
            raise SystemExit(f"[FATAL] cannot read year from {f}")
        parts.append(parse_file(f, int(m.group(1))))
    df = pd.concat(parts, ignore_index=True).sort_values(
        ["ts_utc", "date"], na_position="last").reset_index(drop=True)
    df["date"] = df["date"].astype(str)
    print(f"\n[all] events={len(df)}  span={df.date.min()} -> {df.date.max()}")
    print(df.groupby(df.date.str[:4]).size().rename("events/yr").to_string())
    nfail = gates(df)
    df.to_parquet(a.out, index=False)
    print(f"\n[done] wrote {a.out}  |  hard-gate failures: {nfail}")
    raise SystemExit(1 if nfail else 0)


if __name__ == "__main__":
    main()
