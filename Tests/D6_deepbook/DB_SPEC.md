# DB_SPEC — D-6: EVENT-LEVEL ORDER BOOK ROUND (T-BK02)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 discipline
Trigger: J aimed D-6 (IN PROGRESS this commit). The last unopened
information source: the full MBP-10 event stream (drive:
mbp10_ESH2_2022-02 / mbp10_ESZ5_2025-10 windowed parquets, 3.3GB) -
what the per-second snapshots average away. STUDY ONLY.

## QUESTIONS (two, frozen; G3/fade features deferred to their cycles)
Q1 - THE EXIT CEILING (F-16's "new information" lane): at matched
moments inside HIS trades (duration-matched AND excursion-matched -
the EX2 lesson), do event-level book dynamics separate his exit
moments from his keep-holding moments?
Q2 - THE FLOW THREAD (F-10): at his taken vs passed crosses (the
T-EN109 episodes), do the 30 seconds BEFORE differ in queue
dynamics (stacking/pulling RATES, not levels)?

## FEATURES (standardized microstructure, computed per moment over
a trailing 30s event window; all live-computable from a depth feed)
1. OFI       - order-flow imbalance, best level (Cont-Kukanov-
               Stoikov 2014 construction), signed with the position/
               trade direction
2. OFI10     - same summed over 10 levels
3. depl_opp  - depletion rate of the opposing best queue (size
               removed by trades+cancels per second / starting size)
4. repl_opp  - replenishment rate of the opposing best queue
5. cancel_ratio - cancels / (cancels + trades) on the opposing side
6. large_lot - share of trade volume in prints >= 10 contracts
7. hidden    - count of executions exceeding displayed size at
               touch (iceberg evidence)
8. sweep     - count of events clearing >= 2 levels in one action
8 features -> BH-FDR q=0.10 within each question; FINDING needs
>= both months same direction (only 2 months exist here) AND BH
pass. Paired/matched permutation designs as T-MG20 / T-EN109.

## MECHANICS
Extraction runs ON THE DEVICE (data is there; databento+pandas
confirmed), moment-targeted: only the time slices needed (his trade
spans +-60s; episode cross windows), checkpointed per slice batch
(the convert_v3 pattern). Slice list built in the container from
audited episodes + the T-EN109 episode definitions, shipped to the
device. Features computed per slice on-device; the small feature
table staged back; analysis in the container.
R-9 analog: the extractor is certified first on one slice by
reconciling its per-second trade volumes and last-mid against the
committed per-second files (must match exactly).
Registry: T-BK02.
