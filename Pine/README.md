# Pine — TradingView Pine Script v6 ports of researched strategies

Purpose: live signal display and alerts on TradingView for strategies researched in this repo.
Not a backtest and not the source of truth. The Python research code is the source of truth;
a Pine script is a translation that is checked against it.

Current scope: Strategy 2A entries (indicator only). 2B waits. Exits are not final.
Everything in this folder implements Strategy 2A.

## Decided design (J, 2026-11-18)

**Route M**: the detector runs on a 1-minute, Electronic-hours ES1! chart. It computes the 14-session
numbers from the chart's own bars and reads 1-second bars from inside the chart
(`request.security_lower_tf`). A typed-in C(day) override input is kept for when fewer than 14
sessions are available.

Naming: **route M** = minute chart, self-computing. **route S** = seconds chart with a typed-in daily
number (the fallback). These replace the earlier "option (b)" and "option (a)", which collided with
the strategy names 2A/2B. The frozen file `probes/probe_02_ltf_seconds_v1.pine` still says
"option (b)" in its header; read that as route M.

## Build stages

1. Readout indicator (14-session mean range, C(day), R_est). Acceptance gate: its numbers are checked
   against the research side's reference values. No detector code before this passes.
2. Alert test (Probe 03): does a server-side alert see the live 1-second data?
3. Burst detector — NOT STARTED, waits for the rigid spec and reference outputs in `spec/`.

## Read in this order

1. `CONVENTIONS.md` — the rules every script and every chat follows.
2. `setup.md` — the TradingView account and chart this code is written for.
3. `OPEN_QUESTIONS.md` — what is not yet known. Nothing depending on an open item gets built.
4. `spec/` — the strategy spec and reference outputs (pending from the research side).
5. `reference/v6_signatures.md` — Pine built-ins that have been verified, and against what.

## Layout

| Path | Holds |
|---|---|
| `prompts/` | Task prompts pasted at the start or end of a request |
| `reference/` | Verified Pine v6 signatures |
| `spec/` | Strategy spec and reference outputs exported from the research code |
| `probes/` | Throwaway scripts that answer one setup question each |
| `indicators/` | Deliverable scripts, one file per version |
| `setup.md` | TradingView plan, symbol, data feed, session settings |
| `LOG.md` | Dated record of every compile and chart result |
| `OPEN_QUESTIONS.md` | The one open-questions list |

## Workflow

1. Claude proposes a file on a branch. Nothing is committed without J's approval.
2. J pastes the file into the TradingView Pine editor.
3. J reports back: compiler output verbatim, or a screenshot / the values shown.
4. The result is written to `LOG.md`.
5. J approves; the file is committed. After that the file is never edited — a change is a new version file.

## Related

- Rules source: project doc `claude/pine-v6-agent-handoff.md` (amended 2026-11-18).
- Strategy 2 research code: `Tests/P4_entry_determination/`.
