# TradingView setup record

Filled in by J. Scripts are written for exactly this setup; if it changes, update here first.

| Item | Value | Date confirmed |
|---|---|---|
| TradingView plan | Premium | 2026-11-18 (J) |
| Seconds charts available | Yes — 1S chart loaded | 2026-11-18 (Probe 01) |
| Historical bars per chart | 24,130 loaded on 1S, Regular hours = exactly one session (2026-11-17) | 2026-11-18 (Probe 01) |
| CME data on TradingView | CONFLICT: J said real-time; the chart shows "10 min delayed / Get real-time" and the feed is `CME_MINI_DL:ES1!` (DL = delayed). Unresolved. | 2026-11-18 (Probe 01 screenshot) |
| CME data — update | J activated real-time data after the probe run. To confirm: the "10 min delayed" badge is gone and the probe's Symbol row no longer shows `CME_MINI_DL`. | 2026-11-18 (J) |
| Level 2 (market depth) data | Not subscribed, and not needed: Pine scripts cannot read market depth. | 2026-11-18 (J) |
| Symbol charted (specific contract or ES1!) | ES1! (continuous) | 2026-11-18 (Probe 01) |
| If ES1!: back-adjustment setting | Not confirmed — J to check the B-ADJ button | |
| Chart session setting in normal use (Electronic / Regular) | ? | |
| Chart timezone | ? | |
| Alerts: how received (app / email / webhook) | ? | |
| Platform (web / desktop app) | ? | |

## Decided chart (J, 2026-11-18)

ES1!, 1-minute timeframe, Electronic trading hours, real-time data. Route M. Reason for Electronic:
the research takes the first regular-hours bar's true range from the last overnight bar's close, and
the 10-bar true-range mean just after the open reaches into overnight bars; those bars only exist on
an Electronic chart. Cost: about 16 regular sessions fit, a margin of about one over the 14 needed.

## Symbol (recommended 2026-11-18; B-ADJ state still to confirm)

ES1! with back-adjustment OFF. Reason: the research used the unadjusted front-month series, which
changes contract at each roll; ES1! unadjusted is the nearest TradingView equivalent, including for
the trailing 14 sessions just after a roll. A single contract (e.g. ESZ2026) matches mid-quarter but
its trailing sessions just after a roll come from when it was the back month. This corrects the
earlier advice to chart a specific contract. Open item: TradingView's roll date for ES1! vs the
research roll calendar.

## Facts about TradingView that the code depends on

| Fact | Source | Checked |
|---|---|---|
| "Regular hours" for CME futures is 08:30–15:15 CT; research uses 08:30–15:00 | TradingView help article 43000670909 | 2026-11-18 |
| Regular/Electronic setting changes intraday bars only; daily bars are the same under both | TradingView blog, "Regular trading hours for CME futures" | 2026-11-18 |
| Chart history caps: 10K / 20K / 25K / 40K bars by plan | TradingView pricing page, help article 43000480679 | 2026-11-18 |
| Lower-timeframe requests: up to 200,000 intrabars | Pine v6 User Manual, Other timeframes and data | 2026-11-18 |
| `request.*()` accepts named sessions only, not time-based session strings | Pine v6 User Manual, Sessions | 2026-11-18 |
| Back-adjustment is off by default; toggled by the B-ADJ button at the bottom of the chart or "Adjust for contracts changes" in settings | TradingView help article 43000685266 | 2026-11-18 |
| TradingView bars are built from trades; the research 8-second move uses mid-price | Research side, open-questions doc Q5 | 2026-11-18 |

## Probe results

| Probe | Question | Result | Date |
|---|---|---|---|
| 01 | Sessions of 1-minute history available from a seconds chart (Electronic) | Values not readable in the screenshot; not needed, since the Regular run (fewest bars per session) already fails | 2026-11-18 |
| 01 | Same, chart on Regular hours | FAIL — 404 one-minute bars (one session) before the first chart bar; 0 sessions completed at first chart bar, need 15+ | 2026-11-18 |
| 01 | 08:30–15:00 filter works inside a request | PROVISIONAL PASS — 118.5 points for 2026-11-16; J: "I think the range is right" | 2026-11-18 |
| 01 | Skipped seconds in regular hours: count / longest | 23,283 bars checked, 111 gaps, longest 3 s (delayed feed) | 2026-11-18 |
| 02 | Feed after activation | `CME_MINI:ES1!`, no delayed badge — real-time confirmed | 2026-11-18 |
| 02 | Regular sessions held by a 1-minute chart | Regular hours: 50 (20,655 bars). Electronic: 16 (24,273 bars) | 2026-11-18 |
| 02 | 1-second bars readable from a 1-minute chart | Yes. Regular: 40,000 intrabars back to 2026-11-16 10:44 CT. Electronic: ~100,300 back to 2026-11-16 14:08 CT. Under two sessions either way | 2026-11-18 |
| 02 | 1-second completeness in regular hours | 99.1% (Regular run), 99.5% (Electronic run) | 2026-11-18 |
| 02 | Live bar: seconds arrive as the minute forms | Yes. ~3–4 script updates per second; forming-bar count 36 then 8 across a minute boundary; newest 1-second bar opened 0.9–1.0 s before the clock | 2026-11-18 |
