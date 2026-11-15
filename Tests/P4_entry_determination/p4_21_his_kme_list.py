#!/usr/bin/env python3
"""
p4_21_his_kme_list.py — P4.21: HIS OWN daily KME list, extracted from his messages.
====================================================================================
FIND (2026-11-15): he posts his KME schedule most mornings, e.g. "Good morning...
KME's today @ 1030am, 1100am, 1105am, 1pm, 2pm est today". That is the
Perry-named event list (design decision 3, approach C) — per day, in his words.

THIS SCRIPT: (1) finds every message mentioning KME with clock times; (2) parses
the times (Eastern, as he writes them; '1030am' and '10:30am' and '1pm' forms);
(3) matches each posted time to the committed calendar (same day, +/-3 min, USD)
to NAME the event; (4) prints THE FULL LIST of distinct named events he posted,
with how often, plus unmatched posted times; (5) saves his per-day posted times
for use as a fourth news width ("HIS list") in later conditions.

RUN: python3 Tests/P4_entry_determination/p4_21_his_kme_list.py            (repo root)
OUT: Data/inputs/his_kme_times.parquet (day, posted ET time, matched UTC ts, event name)
"""
import argparse, os, re, sys
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TIME_RX = re.compile(r"\b(\d{1,2})(?::?([0-5]\d))?\s*(am|pm)\b", re.I)
ET = ZoneInfo("America/New_York")


def parse_times(text):
    out = []
    for h, mnt, ap in TIME_RX.findall(str(text)):
        h = int(h); mnt = int(mnt) if mnt else 0
        if not (1 <= h <= 12):
            continue
        if ap.lower() == "pm" and h != 12:
            h += 12
        if ap.lower() == "am" and h == 12:
            h = 0
        out.append((h, mnt))
    return out


def run(repo):
    msg = pd.read_parquet(os.path.join(repo, "Data/inputs/wrb_messages.parquet"))
    kme = pd.read_parquet(os.path.join(repo, "Data/inputs/kme_calendar.parquet"))
    k = kme[(kme.currency == "USD") & kme.ts_utc.notna()].copy()
    k["ts_ns"] = pd.DatetimeIndex(k.ts_utc).as_unit("ns").asi8
    k = k.sort_values("ts_ns")
    kns = k.ts_ns.to_numpy()

    has = msg[msg.message.astype(str).str.contains(r"\bKME", case=False, regex=True)].copy()
    rows = []
    for _, r in has.iterrows():
        times = parse_times(r.message)
        if not times:
            continue
        day = pd.Timestamp(r.datetime_utc).tz_convert(ET).date()
        for h, mnt in times:
            try:
                ts_et = pd.Timestamp(day.year, day.month, day.day, h, mnt).tz_localize(ET)
            except Exception:
                continue
            tns = ts_et.tz_convert("UTC").value
            j = np.searchsorted(kns, tns)
            best, bd = None, 3 * 60e9 + 1
            for jj in (j - 1, j):
                if 0 <= jj < len(kns) and abs(kns[jj] - tns) <= 3 * 60e9 and abs(kns[jj] - tns) < bd:
                    best, bd = jj, abs(kns[jj] - tns)
            rows.append(dict(day=str(day), posted_et=f"{h:02d}:{mnt:02d}",
                             ts_utc_ns=tns,
                             event=(k.event.iloc[best] if best is not None else None),
                             matched=best is not None,
                             source_msg=str(r.message)[:120]))
    df = pd.DataFrame(rows).drop_duplicates(subset=["day", "posted_et"])
    df.to_parquet(os.path.join(repo, "Data/inputs/his_kme_times.parquet"), index=False)
    days = df.day.nunique()
    print(f"KME-list messages parsed: {len(has)} messages -> {len(df)} posted (day,time) slots "
          f"across {days} days; matched to a calendar event: {df.matched.mean():.0%}")

    print(f"\n===== THE FULL LIST: events he posted as KMEs (matched by day+time, all history) =====")
    ev = df[df.matched].event.value_counts()
    for name, n in ev.items():
        print(f"  {n:4d}x  {name}")
    print(f"\n({len(ev)} distinct events; top unmatched posted times below - his list may include")
    print("events our calendar lacks, e.g. crude inventories, bond auctions)")
    um = df[~df.matched].posted_et.value_counts().head(12)
    for t, n in um.items():
        print(f"  {n:4d}x  {t} ET unmatched")
    print("\nREAD: this is HIS stated list, day by day - the fourth news width (approach C).")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    a = ap.parse_args()
    run(a.repo)
