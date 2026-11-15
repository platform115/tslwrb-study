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
