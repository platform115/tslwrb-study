# EX_SPEC — EXIT-SWITCH REMAINDER THROUGH THE ORDER BOOK (T-MG19)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J's drive connected (standing trigger item (b)); J approved
priorities with exit-switch first. The earned picture (M8-M11): his
exits = duration clock (t-only AUC 0.805 of 0.814) + partial
level-targeting (1.61x null) + RARE UNEXPLAINED LONG HOLDS (the
residual that beats the dual oracle). The book is the designated
instrument for that remainder. STUDY ONLY.

## DATA
Data/inputs/book_per_sec_{2022-02,2025-10}.parquet (per-second top +
10-level depth, from the drive's windowed MBP-10). Coverage is news
windows only (the reduction's source was windowed); exits without a
book second within 5s are counted and dropped, never silently filled.

## POPULATION
His audited exits (a2_ground_truth), training months. Exit moment =
actual entry (entry_msg_s - posting_lag_s where finite, else
entry_msg_s; basis counted) + hold_s. Exits with hold_s < 30s
excluded (no 30s-lookback features exist yet at that age).

## ANALYSIS A — DURATION-MATCHED CASE-CONTROL (the clock controlled
by construction)
Case = book state at his exit moment. Controls = for each case, up
to 3 moments at the SAME duration (+-0 by construction) inside his
OTHER trades of the same month and side-orientation that were still
held well past that duration (hold_s >= 1.2x case duration). Cases
with no eligible control are counted and dropped.
Features at the moment, oriented by position side (support = bid for
longs): sup0, opp0, sup10, opp10, imb0, imb10, d30_sup0 (support
change over last 30s; pulling = negative), depth_tot, flow_net_30
(tape benchmark). 9 features -> Bonferroni alpha .0056 FINDING (with
same direction both months), .05 suggestive.
Test: within-case rank permutation (10,000 draws), as T-EN109/111.

## ANALYSIS B — THE LONG-HOLD REMAINDER DIRECTLY
At duration 480s (M7's time cap), compare book state between:
CLOCK-EXITERS (hold_s in [400, 560]) and HOLDERS (hold_s >= 700).
Same features, Mann-Whitney, same alpha discipline, months pooled
with per-month direction required. Small n expected - power stated,
not hidden.

## OUTCOME LINES
FINDING -> candidate switch rule (hold while <condition>) spec'd to
J for a backtest round against M7. Suggestive -> BACKLOG +
VALIDATION_PLAN item. All null -> per-second book closed for exits;
remainder goes to event-level MBP-10 or stays unexplained (mode 2 of
the goal refinement applies: baseline, not mimicry).
Registry: T-MG19.
