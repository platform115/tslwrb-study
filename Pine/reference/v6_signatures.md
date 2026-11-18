# Verified Pine v6 built-ins

A built-in goes here only with a source. Anything not listed is UNVERIFIED and must be named as such
in the script header. To add one: J pastes the Reference Manual entry (or the editor's hover text), or
Claude quotes a User Manual page it fetched.

Sources: UM = Pine v6 User Manual page fetched by Claude; RM = Reference Manual entry pasted by J;
COMPILED = accepted by the TradingView compiler on the date shown (proves it exists, not that it does what was intended).

| Built-in | Signature / fact | Source | Date |
|---|---|---|---|
| `request.security` | `(symbol, timeframe, expression, gaps, lookahead, ignore_invalid_symbol, currency, calc_bars_count) → series <type>` | UM, Other timeframes and data | 2026-11-18 |
| `request.security_lower_tf` | `(symbol, timeframe, expression, ignore_invalid_symbol, currency, ignore_invalid_timeframe, calc_bars_count) → array<type>` | UM, Other timeframes and data | 2026-11-18 |
| `time` with session | `time(timeframe, session)` returns the bar's opening timestamp, or `na` if the bar is outside the session; a `timezone` argument exists, default is the exchange time zone | UM, Sessions | 2026-11-18 |
| Session string | `"HHmm-HHmm"` optionally `:days`, days 1–7 with 1 = Sunday | UM, Sessions | 2026-11-18 |
| `ticker.modify` | takes a full ticker ID and a session, e.g. `ticker.modify("NASDAQ:AAPL", session.extended)` | UM, Sessions | 2026-11-18 |
| Futures sessions | electronic session is the default and is named "regular"; `"us_regular"` is the Regular-hours named session for US futures | UM, Sessions | 2026-11-18 |

| `request.security_lower_tf` behaviour | returns all available intrabars per chart bar, ascending by intrabar time; empty array where no intrabar data is accessible; up to 200,000 intrabars; tuple expression gives a tuple of arrays | UM, Other timeframes and data | 2026-11-18 |
| `bid`, `ask` | available only on the "1T" timeframe; `na` elsewhere | Reference Manual text via third-party copies (not fetched from TradingView directly) | 2026-11-18 |
| `time(timeframe, session, timezone)` | accepted with three positional arguments | COMPILED (Probe 01) | 2026-11-18 |
| `dayofmonth(time, timezone)` | accepted | COMPILED (Probe 01) | 2026-11-18 |
| `table.new(position, columns, rows)` | accepted | COMPILED (Probe 01) | 2026-11-18 |
| `table.cell(table, column, row, text, text_color =, bgcolor =)` | accepted | COMPILED (Probe 01) | 2026-11-18 |
| `str.tostring(value)` | accepted | COMPILED (Probe 01) | 2026-11-18 |
| `str.format_time(time, format, timezone)` | accepted | COMPILED (Probe 01) | 2026-11-18 |
| `math.max`, `math.min`, `math.round` | accepted | COMPILED (Probe 01) | 2026-11-18 |
| user function with `var` state as a `request.security` expression | accepted and ran | COMPILED (Probe 01) | 2026-11-18 |

## Used but unverified (waiting on a paste or a compile)

None at present.

## Compiled in Probe 02 (2026-11-18)

`array.size(id)`, `array.last(id)`, `barstate.isrealtime`, `timenow`, `varip` declarations,
`str.tostring(value, format)`, `position.middle_right`,
`request.security_lower_tf(symbol, "1S", [time, close])` returning a tuple of arrays.

Observed behaviour (Probe 02, Premium, ES1!, 1-minute chart): the lower-timeframe array for the
forming live bar updates tick by tick; intrabar totals were 40,000 on a Regular-hours chart and
about 100,300 on an Electronic chart, below the manual's 200,000 figure.
