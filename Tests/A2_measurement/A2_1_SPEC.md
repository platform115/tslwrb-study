# A2.1 SPEC — GROUND TRUTH TABLE + LABEL AUDIT (pre-registered before run)
STATUS: FROZEN at run time | 2026-11-24 | Track A step A2.1 | Registry: T-IM40
Months: training only (2025-10, 2022-02) = 315 episodes. Validation months untouched.

## PURPOSE (plain)
One canonical table of his trades that everything downstream joins
against, with the reported labels AUDITED against 1-second market data
before anything is built on them.

## CRITERIA — fixed before the run, no additions after results
1. ENTRY VERIFIED: some second in [message-600s .. message+120s] has
   per-second mid within 0.5 pt of his reported entry price.
   posting_lag_s = message second minus the LAST such touch at or before
   the message. Touch only after the message = flag "touch_only_after".
   No touch at all = flag "entry_unverified", with the closest distance
   recorded.
2. EXIT VERIFIED: same test per reported exit price around the last-exit
   message second.
3. P&L RECONCILIATION: (mean exit - mean entry) x side vs his stated
   points; consistent if within 0.5 pt. Known limitation (stated, not
   hidden): unequal add/scale-out sizes are unknowable from messages, so
   multi-entry episodes may reconcile imperfectly without being wrong.
4. OUTCOME COLUMNS (y, never features): MAE, MFE (1s mids, signed by his
   side, entry message second to exit message second), hold seconds.
5. CONTEXT TAGS: session date, roll-day flag, RTH/ETH at entry (CT
   08:30-15:00).
6. AMBIGUITY LEDGER: every flagged episode listed verbatim in the report
   for J's review. Nothing silently dropped; nothing silently kept - the
   table carries the flags.

## LOOKAHEAD NOTE
This step reads data AFTER his message times by up to 120s (entry
verification) and through the trade (outcomes). That is legal here and
only here: this table defines LABELS (y and audit fields), not features.
No column of this table may be used as a feature at entry time, except
the identity/context tags knowable at entry (session date, roll flag,
RTH flag).

## OUTPUT
Data/inputs/a2_ground_truth.parquet (checksummed) + report + registry row.
