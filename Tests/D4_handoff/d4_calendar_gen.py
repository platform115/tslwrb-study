#!/usr/bin/env python3
"""
d4_calendar_gen.py — D-4: the WEEKLY EVENT-TIMES feed for the Pine
port (FL-WIN input).
Emits ready-to-paste Pine v6 array code: the release timestamps
(unix seconds, UTC) in a date range, from the SAME calendar every
certified test used (news_sets "all").
Also prints (--names) the distinct event names in the calendar so J
can read NEXT week's times off any public economic calendar and
hand-build the same block (format documented below).
RUN:
  python3 Tests/D4_handoff/d4_calendar_gen.py 2025-10-01 2025-10-31
  python3 Tests/D4_handoff/d4_calendar_gen.py --names
FORWARD USE (hand-built block): one line,
  var int[] d4_ev_utc = array.from(<unix seconds, comma-separated>)
Window rule (spec 3): entries allowed in [E+300s, E+2700s), window
start must be in RTH.
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "Tests/P4_entry_determination")
from p4_3_confluence_news import news_sets                   # noqa: E402

if len(sys.argv) == 2 and sys.argv[1] == "--names":
    cal = pd.read_parquet("Data/inputs/kme_calendar.parquet")
    names = sorted(cal.event.astype(str).str.strip().unique())
    print("# KME event names in the certified calendar "
          f"({len(names)}):")
    for n in names:
        print("-", n)
    sys.exit(0)

if len(sys.argv) != 3:
    print("usage: d4_calendar_gen.py YYYY-MM-DD YYYY-MM-DD | --names",
          file=sys.stderr)
    sys.exit(2)

ev = np.asarray(news_sets(".")["all"], dtype=np.int64) // 10**9
lo = int(pd.Timestamp(sys.argv[1], tz="UTC").timestamp())
hi = int(pd.Timestamp(sys.argv[2], tz="UTC").timestamp()) + 86400
sel = ev[(ev >= lo) & (ev < hi)]
if not len(sel):
    print("# no events in range", file=sys.stderr)
    sys.exit(2)
ct = pd.to_datetime(sel, unit="s", utc=True).tz_convert(
    "America/Chicago")
print(f"// ==== D4 EVENT TIMES ({sys.argv[1]}..{sys.argv[2]}; "
      f"{len(sel)} events; paste whole block, never edit) ====")
print("var int[] d4_ev_utc = array.from(%s)"
      % ", ".join(str(int(s)) for s in sel))
print("// CT view (reference only):")
for s, c in zip(sel, ct):
    print(f"//   {int(s)} = {c.strftime('%Y-%m-%d %H:%M %Z')}")
