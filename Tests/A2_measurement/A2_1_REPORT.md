# A2.1 REPORT — GROUND TRUTH + LABEL AUDIT (T-IM40)
STATUS: CLOSED | 2026-11-24 | Spec: A2_1_SPEC.md (frozen before run)

## VERDICT IN PLAIN LANGUAGE
His reported trades check out against 1-second market data. The labels
are certified fit to build on. One data hole found (ours, not his).

| | 2025-10 (92) | 2022-02 (223) |
|---|---|---|
| entry price verified at 1s | 100% | 96% |
| exit price verified at 1s | 100% | 96% |
| P&L reconciles with his statement | 100% | 97% (98% single-entry) |
| posting lag, median | 5s | 4s |
| posting lag, 99th pct | 64s | 24s |
| lag over 2 min | 1 trade | 0 |
| roll-day trades | 0 | 0 |
| ETH entries | 3 | 0 |

Posting lag (the gap between his entry and his message) is seconds, as
J expected - it is measured, recorded per trade, and needs no model.

## THE DATA HOLE (root-caused)
All 8 "unverified" 2022-02 trades are on Feb 28. The per-second file
ends Feb 27 because the ORIGINAL Databento order (GLBX-20260607, on the
external drive) ends at glbx-mdp3-20220227 - the final day was never
ordered. The derived file is faithful to the raw; the raw is short one
day. FIX: one-day vendor order for 2022-02-28 (J approves purchases).
Until then those 8 trades carry entry_flag=no_data_window and are
excluded from per-second work - never silently dropped from the table.

## OUTPUT
Data/inputs/a2_ground_truth.parquet (checksummed) - 315 rows: identity
keys, audit fields, outcome columns (y: MAE/MFE/hold - never features),
context tags. Registry: T-IM40.
