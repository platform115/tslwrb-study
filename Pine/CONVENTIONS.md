# Pine conventions

Status: APPROVED by J 2026-11-18 (as committed in 5aeabfd).

## Non-negotiables

1. `//@version=6` on every file.
2. No lookahead. Every `request.security` call states `lookahead = barmerge.lookahead_off` explicitly.
3. Anything not stated in the spec is an open question: log it in `OPEN_QUESTIONS.md` and ask. Never assume.
4. Claude proposes; J reviews and commits.
5. A script's history on the chart is never presented as a replication unless it was computed on
   bars that can see the 8-second scale. Approximations say "approximation" in the title.
6. Every built-in used is either in `reference/v6_signatures.md` or listed as UNVERIFIED in the script header.

## File naming

- Indicators: `<strategy>_<what>_v<NN>.pine`, e.g. `s2a_entry_indicator_v01.pine`
- Probes: `probe_<NN>_<topic>_v<N>.pine`
- Lower case, underscores, no spaces.

## Versions

- Before a file's first commit, compile fixes edit it in place.
- After commit a file is frozen. Any change, including a bug fix, is a new version file with the
  change stated in its header. Old versions stay in the folder.

## Header template (every script)

```
//@version=6
// =============================================================================
// <NAME> v<NN>
// Purpose:
// Implements: <strategy and spec file + version, or "probe">
// Run on: <symbol>, <timeframe>, <session setting>, <adjustment setting>
// Session window implemented: <e.g. 0830-1500 America/Chicago>
// Data source validated against: <or "not validated">
// Known differences from the research implementation:
// Historical vs live behaviour:
// request.security calls: <count; symbol/timeframe/gaps/lookahead for each>
// Hardcoded values (flag for later testing):
// UNVERIFIED built-ins:
// Changed from previous version:
// =============================================================================
```

## Pre-delivery checklist (answers go in the reply and in LOG.md)

1. Repaint: can any plotted or alerted signal change after its bar closes?
2. Historical vs live: where do they differ, and is it in the header?
3. Lookahead: every `request.security` call and its settings.
4. Lookback: is there enough history for the 14-session and 10-bar windows on the target chart?
5. Target chart: symbol, timeframe, session, adjustment.

## Code style

- TradingView's style guide: camelCase variables, SNAKE_CASE constants, explicit types on declarations.
- Strategy numbers (0.022, 0.17, 14, 10, 8, 45) are named constants or inputs, never bare in formulas.
- Times are compared as exchange timestamps (`time`), never as bar counts, on seconds charts.
- Session logic uses `"America/Chicago"` explicitly.

## Translating Python to Pine

- Translate from the research function, line by line, with the Python shown beside the Pine in the reply.
- Each translated quantity gets a stage check against the reference outputs in `spec/` before the next one is built.
- Where Pine cannot do what the Python does (no mid-price, no bar for an empty second, history caps),
  the difference is written in the header, not worked around silently.
