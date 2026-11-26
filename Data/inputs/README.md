# Data/inputs — committed small derived inputs (policy exception)

Exception to the no-parquet rule, approved 2026-11-14: DERIVED inputs under 50MB
each are committed here with sha256 checksums, so the session container can run
bar-level research without the user's machine. Raw data (.dbn.zst, MBP-10
windowed parquets, scraped chat HTML) remains banned from git — SSD/local only.

| file | source of truth | note |
|---|---|---|
| tsl_episodes_clean.parquet | es-trading-agent-v3 Data/processed/chatlogs/ | his trades (chat-log derived) |
| es_1m_front.parquet        | es-trading-agent-v3 Data/processed/es/       | 1m front-month bars, unadjusted |
| wrb_1m.parquet             | canonical WRB table (WRB_Definition.txt)     | same file as Tests/06_*/wrb_1m.parquet |
| kme_calendar.parquet       | Tests/P4_entry_determination/build_kme_calendar.py | from KME-<year>-Raw.xlsx exports |

Copies here are snapshots: if a source regenerates, re-copy + update CHECKSUMS.sha256
in the same commit. Verify: `shasum -a 256 -c CHECKSUMS.sha256`

- `flow_per_sec_2025-10.parquet` / `flow_per_sec_2022-02.parquet` — per-second
  aggressor flow (buyv, sellv, mid last), instrument-filtered (ESZ5 294973 /
  ESH2 5782), reduced 2026-11-15 on the user's Mac from the windowed MBP-10
  extracts by `Tests/P4_entry_determination/reduce_flow_device.py`. Oct 256,482
  rows; Feb 334,944 rows. Coverage = the exit program's trade windows
  (60 min before first entry -> 5 min after last exit, per day).

- `wrb_messages.parquet` / `chat_activity.parquet` — the trader's full forum-chat
  message stream (31,838 messages, 2021-05..2026-06, trade calls tagged) and
  per-minute room message counts, exported 2026-11-15 from the user's scraped
  corpus via es-trading-agent-v3 `chatlog-scraper/tsl_data/export_messages.py`
  (1,312 HTML files; ~81 non-chat-log topics skipped). The room is effectively
  his narration log (median 24 of 30 daily messages are his).

- `flow_per_sec_2021-09_full.parquet` / `flow_per_sec_2024-11_full.parquet` —
  FULL-MONTH per-second aggressor flow (no trade-window boundaries), reduced
  2026-11-15 on the user's Mac from freshly purchased daily MBP-10 batch zips
  by `/Volumes/2TB-Lexar/make_flow_validation.py` (front contract auto-resolved
  by last-3-day volume: ESZ1 / ESZ4; identity gate vs committed bars: mid
  tracks closes within half a tick). 1.36M / 1.40M rows.
- book_per_sec_{2022-02,2025-10}.parquet: per-second last-in-second top-of-book sizes (bid0/ask0) + 10-level depth sums (bid10/ask10); built by reduce_book.py (J's drive, tslwrb_windowed) from Databento GLBX.MDP3 MBP-10, instrument-filtered ESH2/ESZ5; ingested 2026-11-26 for T-EN111.
- flow_per_sec_{2023-05,2024-05}_full.parquet + book_top_per_sec_{2023-05,2024-05}.parquet:
  VALIDATION months, built 2026-11-26 by Tests/V_validation/convert_v4.py on J's
  device from the purchased Databento GLBX.MDP3 tbbo + bbo-1s (ES.FUT parent;
  jobs GLBX-20261126-{LJNLAWJDTM,LP5HY33ATB,5QRJSDPDXY,ND57PU8Q5X}). Conventions
  = old pipeline (buyv side B / sellv side A / mid last-in-second; front id by
  top volume over the month's last 3 day-files: 95414 / 5602). Converter
  CERTIFIED by Tests/V_validation/equiv_check3.py vs raw MBP-10 day 20241105:
  73,045/73,045 seconds joined, volumes exact on 99.999% of seconds (2 of 572k
  contracts at a day boundary), mid exact everywhere. QA: mids within a tick of
  tbbo trade-tops on 99.97% of trade seconds (qa_*.json). QUARANTINE: these
  files feed ONLY the pre-registered VALIDATION_PLAN look - no training, no
  tuning, no feature mining.
