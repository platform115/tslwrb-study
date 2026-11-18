# Pine — compile and chart log

Newest at the bottom. One entry per paste into TradingView.

| Date | File | Chart (symbol / timeframe / session) | Compiled? | Result or error (verbatim) | Action |
|---|---|---|---|---|---|
| 2026-11-18 | probes/probe_01_history_rth_gaps_v1.pine | not yet run | not yet | written, never compiled | run after framework approved |
| 2026-11-18 | probes/probe_01_history_rth_gaps_v1.pine | CME_MINI_DL:ES1! / 1S / Regular (us_regular), 10-min delayed feed | Yes, first paste | Bars loaded 24130; first bar 2026-11-17 08:30:00 CT; 1-min bars before first chart bar 404; RTH sessions at first bar 0; sessions now 1; last session 2026-11-16 range 118.5; RTH bars checked 23283; gaps 111; longest gap 3 s | P1 FAIL: request route cannot supply 14 sessions. P2 provisional pass. Feed is delayed — conflicts with setup answer. |
| 2026-11-18 | probes/probe_01_history_rth_gaps_v1.pine | ES / presumably Electronic | Yes | Screenshot shows labels only; value column not visible | Not re-requested; Regular run is decisive |
| 2026-11-18 | probes/probe_02_ltf_seconds_v1.pine | not yet run | not yet | written, never compiled | J to run per probe_02_RUN.md |
| 2026-11-18 | probes/probe_02_ltf_seconds_v1.pine | CME_MINI:ES1! / 1 min / Regular (us_regular), real-time, run outside RTH | Yes, first paste | Bars 20655; RTH sessions 50; bars with 1S data 676, without 19979; first 1S bar 2026-11-16 10:44 CT; RTH days with 1S 2; intrabars 40000; RTH coverage 99.1%; live updates 0 (expected, session closed); forming-bar count 55; lag 54606.4 s (stale last bar) | B3 pass with wide margin. Intrabar total stops at exactly 40,000. |
| 2026-11-18 | probes/probe_02_ltf_seconds_v1.pine | CME_MINI:ES1! / 1 min / Electronic, real-time, ~06:30 CT, two screenshots 20-30 s apart after 5-7 min | Yes | Shot 1: bars 24273; RTH sessions 16; with 1S 2305, without 21968; first 1S bar 2026-11-16 14:08 CT; RTH days 2; intrabars 100297; coverage 99.5%; live updates 1319; forming-bar count 36; most in a live bar 51; lag 0.9 s. Shot 2: bars 24274; intrabars 100320; updates 1418; forming-bar count 8; lag 1.0 s | B4 PASS: 1S array grows inside the forming minute, newest entry ~1 s behind clock. B3 pass with margin of one session. Route M is viable. |
| 2026-11-18 | indicators/s2a_readout_indicator_v01.pine | not yet run | not yet | written, never compiled | J to run per s2a_readout_indicator_v01_RUN.md; stage-1 gate = research reference values |
| 2026-11-18 | probes/probe_03_alert_live_seconds_v1.pine | not yet run | not yet | written, never compiled | J to run per probe_03_RUN.md |
