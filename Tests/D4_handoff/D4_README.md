# D4_README — THE G2-4 PINE HANDOFF PACKAGE (manifest)
STATUS: v1.0 COMPLETE | 2026-11-28 | produced by the research side
(this repo); consumed by J's separate Pine conversation.

## J'S DECISIONS BAKED IN (2026-11-28)
- Strategy mode: auto-backtest/paper (simulated; no live routing -
  live execution is the D-23 Python-runner lane).
- Chart: 1-SECOND (J has Premium + 1s data) - M7 runs at its native
  resolution; no bar-level exit approximation needed.
- Inputs: J pastes generated blocks (daily levels, weekly events).
- Scope: G2-4 ONLY. G2-6 becomes an addendum after the pipeline is
  proven.
- Exit verification: (b) FORWARD-PARALLEL default (same new days
  traded by Pine paper and replayed here, compared after); (a) a
  tiny recent-data purchase remains available as an accelerator.

## FILES
| file | what it is |
|---|---|
| D4_PORT_SPEC.md | the rule book (only authority on rules) |
| D4_CONSTANTS.md | every number, named (only authority on values) |
| D4_HANDOFF_PROMPT.md | the prompt that starts the Pine chat |
| d4_levels_gen.py | daily level-list generator -> Pine array block (control: reproduces the committed 2022-05 blind lists exactly) |
| d4_calendar_gen.py | weekly event-times generator -> Pine array block; --names prints the KME event list for forward manual lookup |
| d4_vectors.py | golden-vector generator (controls C1 bit-exact candidates, C2 certified month net) |
| vectors/v_structure_*.csv | per-1m-bar W20 band + sqz10/sqz30 edges, 3 sessions |
| vectors/v_signals_*.csv | every cross/order with fill or expiry |
| vectors/v_trades_*.csv | every trade: entry, arm, exit reason, P/L |
| vectors/V_SUMMARY.md | session roll-up + the J-gated tolerance sheet |
| pine_inputs_2025-10_levels.txt | paste block covering the vector sessions |
| pine_inputs_2025-10_events.txt | paste block covering the vector sessions |

## VECTOR SESSIONS (certified engine output; C1/C2 PASS)
| session | signals | filled | trades | net |
|---|---|---|---|---|
| 2025-10-13 (ordinary) | 27 | 23 | 14 | +8.2 |
| 2025-10-15 (busy) | 165 | 135 | 40 | +25.8 |
| 2025-10-31 (near-empty) | 4 | 3 | 2 | +2.8 |

## KNOWN OPEN ITEMS (stated, not hidden)
- Forward levels need fresh daily 1m bars once paper starts (our
  stored data ends mid-2026): J exports bars, or a small data
  top-up, or (lineage-breaking, needs revalidation) Pine-side
  approximation. Decide at paper-time.
- TradingView feed vs our feed: divergence is measured by the
  vectors and the forward-parallel check, never assumed away.
- Roll days: F-40 convention (trades kept, marked); J owns the
  convention question post-D-8.
