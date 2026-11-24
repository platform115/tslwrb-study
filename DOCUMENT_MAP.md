# DOCUMENT_MAP — WHERE EVERY DOCUMENT SITS IN THE END-TO-END PROCESS
STATUS: LIVING | Version 1.0 | 2026-11-24
Plain purpose: one page that places every document in the pipeline, says
when it is read, when it is updated, and by what trigger. The coverage
check at the bottom is mechanical (R-8), so no document can go missing
from this map silently.

## THE END-TO-END PROCESS, WITH ITS DOCUMENTS

```
STAGE 0 — STANDING GOVERNANCE (read at the start of every work session)
  MASTER_PROGRAM.md ........ the program: goal, standing rules R-1..R-8,
                             Track A (map) and Track B (build) steps.
                             Updated only at review gates, change-logged.
  GLOSSARY.md .............. naming authority: every designation family,
                             every canonical name, aliases. Updated in the
                             same commit as anything that names a new thing.
  RESULTS_DISPLAY_STANDARD.md how every entry-test result is shown to J.
                             Updated only if J changes the standard.
  DOCUMENT_MAP.md .......... this file. Updated whenever a doc is added,
                             retired, or changes role.

STAGE 1 — DATA LAYER (read before any measurement)
  ASSETS.md ................ generated inventory of every data file:
                             rows, columns, which scripts read it.
                             Regenerate after any data change:
                             python3 scripts/gen_assets_inventory.py
  Data/CHECKSUMS.txt ....... traceability (Rule 4): data identity.
  Data/inputs/README.md .... how each input file was produced.

STAGE 2 — ELICITATION / PLANNING (per program cycle)
  A1_FEATURE_COVERAGE.md ... Track A step A1: everything we measure or
                             could measure, sources, build order. LIVING.
  BACKLOG.md ............... parked ideas and owed items, being absorbed
                             into MASTER_PROGRAM tracks. Append-and-prune.

STAGE 3 — EXECUTION (per test; inside Tests/<phase>/)
  *_spec / *PLAN docs ...... pre-registration: written BEFORE the run
                             (Rule 2). Frozen once the run starts.
  *_REPORT docs ............ what happened, with status header
                             (CLOSED/LIVING) and verdicts vs the
                             pre-stated criteria.
  Tests/test_registry_rows.tsv one row per test (T-xx ids). Written by
                             script only, never by hand.
  Tests/P6_imitation_study/REMAINDER_LEDGER.md  the uncaught-entries
                             ledger: which of his trades no selector
                             explains yet, and what has been ruled out.
                             Updated each entry-search cycle.

STAGE 4 — AGGREGATION (read when choosing what to do next)
  BACKTEST_MATRIX.md ....... every entry x management combo tried, full
                             results stats, untested grid. Updated the
                             same turn as any new backtest.
  OVERVIEW_TREE.md ......... the whole project as one tree: data,
                             studies, entries, management, detectors,
                             open queues. Updated at phase closes.

STAGE 5 — ARCHIVE (kept, not current; do not plan from these)
  CURRENT_STATE.md ......... STALE (July-2026 MBP-10 era). Pending the
  CURRENT_STATE_edits.md ... parked doc-cleanup J approved exploring:
                             proposal is to move both under archive/ with
                             a stale banner. Awaiting J go.
  Tests/01..07 (pre-P4 era)  earlier program's specs/reports; superseded
                             by the P4-P7 line but kept for traceability.
  Tests/P4 STRATEGY_SPEC_v1..v9  superseded spec versions (v10 is the
                             certified Strategy 1 reference).
```

## THE READ ORDER FOR ANY NEW SESSION
1. MASTER_PROGRAM.md (rules + where the program stands)
2. GLOSSARY.md (what names mean)
3. DOCUMENT_MAP.md (this page)
4. The LIVING docs of the active step (today: A1_FEATURE_COVERAGE.md)
5. ASSETS.md before touching any data

## COVERAGE CHECK (mechanical, part of R-8)
`python3 scripts/gen_assets_inventory.py` also prints every .md file in
the repo that this map does not mention by name or by covered group.
A non-empty list fails the completeness pass.

## CHANGE LOG
- v1.0 2026-11-24: created (J's request: place all documents in the
  end-to-end process).
