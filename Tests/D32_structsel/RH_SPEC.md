# RH_SPEC — R-1 TRUNCATION-HARNESS PASS ON FL-RWY (T-RH01)
STATUS: FROZEN BEFORE RUN | 2026-11-28 | Rule 2 + R-1 + R-9 + R-12
The owed integrity item: FL-RWY (the runway filter) sits inside five
registered systems and F-35, but its no-lookahead status rests on
reasoning, not the mechanical gate R-1 demands. This run applies the
P0 truncation harness (T-EN99/100 lineage) to the runway computation.

## R-11 MONTHS-SPEND
Nothing spent: an integrity test on already-spent months; no trading
outcome is read or compared. No hold-out implications.

## R-12 FINDINGS SWEEP
APPLIED: F-13 (the poisoned sensitivity arm IS the control-arm
principle), F-28/29/35 (the object under test), R-1 (the rule being
satisfied), R-9 (the harness proves itself via the poison arm).
NOT-APPLICABLE: all performance findings - no P&L is touched.

## TRUNCATION RULES (inherited from Tests/P0_audit/truncation_harness.py)
Available at t means: completed 1m bars only (bar open + 60s <= t);
per-second data <= t; prior-day aggregates from strictly earlier
sessions; the exchange calendar is known in advance. The zone-refs
table feeds only the unused KEY family and is outside the tested
path (stated, not tested).

## THE TEST
v_prod = the runway value the pipelines used (banked for the 1,264
touches in lvl_touch_moments_rwy.csv; recomputed via the production
path for sampled volume-line candidates). v_trunc = the same value
recomputed with ALL structure inputs rebuilt from data truncated at
that case's second t: bars -> truncated Resolver, truncated WRB
bodies, truncated prior-day H/L/C. PASS per case: exact equality
(|delta| < 1e-9; inf matches inf).
SAMPLE (frozen, seed 42): 150 touches stratified by month and
quiet/window context from the 1,264; 90 candidate fills (15 per
month) from the G2-6 news-line and G3 quiet-line candidate sets
pooled; 60 poison cases.
## POISON ARM (harness sensitivity - must FAIL to count)
For 60 sampled cases, recompute runway using END-OF-DAY structures
(deliberate future contamination). The harness is proven sensitive
only if >= 1 poisoned case mismatches v_prod; expected many.

## VERDICT (frozen)
R-1 PASS requires: zero mismatches across all 240 production
comparisons AND >= 1 poison mismatch. ANY production mismatch =
FAIL -> every FL-RWY system is frozen pending an anatomy (R-10),
and the mismatch cases are listed in full. Registry: T-RH01.
