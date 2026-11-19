# PROJECT OVERVIEW TREE
> The one-page map. Updated 2026-11-19 after the lookahead reset (T-EN99).
> Detail lives in the registry (Tests/test_registry_rows.tsv) and phase docs.

## PHASES
- P1-P3  (done)    Data/infrastructure; Strategy 1 era; early imitation work
- P4     (HALTED)  Strategy 2 mechanical entries - lookahead found (T-EN99);
                   honest edge: none (T-EN100). Clean pieces salvaged.
- P5     (paused)  Trade management - M1 built & adopted; full resumption
                   waits for honest entries (M2 planning begins per user)
- P6     (ACTIVE)  THE IMITATION STUDY - learn entry selection from HIS trades
- next   BOUNDED SEARCH (pre-registered, stopping rule) -> validation ->
         purchase-month final exam

## STRATEGIES
- Strategy 1 (v1-v11)   FROZEN. Clean code, honestly unprofitable. Reference.
- Strategy 2A / 2B      ENTRIES VOID (lookahead). The 8s burst trigger is
                        clean code but loses alone. No honest entry exists yet.
- (2A overnight)        Void with them.

## MANAGEMENT PLANS
- M0  v11 sketch        FROZEN control. Not modified, ever.
- M1  stall-30 (RTH) / stall-90 (ETH) + session close + rails
                        ADOPTED. Clean (harness-passed). Profits on HIS real
                        entries (+107.8, DD 0, T-IM05). Not modified much/at all.
- M2  (planned)         Built from THE DIFFERENCES between his management and
                        M1 on identical entries (he: ~+620 scale-confounded vs
                        our +108). First step: dissect his adds/exits per
                        episode (n_entries, entry_prices, exit_prices held).

## DETECTORS (historical layer)
- D1          became the 2A/2B burst core - clean, void as a strategy
- D4          quiet-tape - parked, aimed at the quiet 46% entry mass
- D6, D7      retired
- 10-cond score signals  retired from profit lane; REVIVED as the best
              within-type separator (AUC 0.727, T-IM03)

## CLEAN TOOLKIT (survives the reset; all harness-passed)
per-second mids & burst measure | C(day) rolling ratio | atr10 | gap clock |
flow per-second (signed/total) | book_per_sec (2 months) | score signals |
KME calendar + his KME times | WRB catalogs | M1 exits | per-second fill
engine | TRUNCATION HARNESS (standing gate: no new signal without a pass)

## HIS-DATA ASSETS (imitation study fuel)
tsl_episodes_clean (entries/exits/adds/realized P&L per episode) |
wrb_messages (31,838 msgs, trade_action tags - HIS EXPLANATIONS) |
chat_activity (per-minute presence - WAS HE THERE) | his_kme_times

## REGISTRY & DATA BUDGET
- Tests: T-EN1..101 (entries+audits), T-EX01..14 (management), T-IM01..05
  (imitation study). Every test scripted, committed, 21-col row.
- Training (active): 2025-10, 2022-02 - current work = 2025-10 ONLY until
  entries select a good share of his trades (user directive).
- Reserved: 2021-09, 2024-11 (9 reads, pre-freeze discipline; closed for now).
- Purchase months: 4, SEALED - final exam only.

## ACTIVE WORKSTREAMS (user-set, 2026-11-19)
1. ENTRY GROUPING of his trades, new axes (data confirmed available):
   a. presence-known entries (chat_activity: he was demonstrably there)
   b. commentary-explained entries (wrb_messages around entry time; his
      stated reasons; exit-level descriptions reveal his price interests)
   c. KME-window WRBs on specific timeframes with known entry conditions -
      catch them whether he took them or not
   d. further groups as the data reveals them (typology v0: momentum-join /
      drift-join / fade / quiet)
   GOAL: some % of his entries caught per day by A SYSTEM OR SEVERAL -
   multiple small systems accepted, one-rule-for-all NOT expected.
   METHOD: start with the group we know the MOST about; find price-action
   markers per group; selectivity matters (few non-his unless they work).
2. MANAGEMENT: find the his-vs-M1 differences on identical entries; distill
   into M2. M0/M1 stay essentially untouched.

## PARKED - TRY SOON (consolidated 2026-11-19)
- Active-window restriction of lookalikes (presence data) - precision ceiling
- His adds/exits dissection per episode (feeds M2)
- Performance-target reframing (select moments that WIN under M1, not
  moments that match him) - candidate for the bounded search
- Finer tape shapes (pullback-then-resume; final 10-20s structure)
- Flow/print microstructure (large prints, imbalance persistence; book data)
- Day-type context (trend vs range day from early stats)
- Cross-market lead-lag (NQ/YM; YM interest long-parked)
- D4 quiet-tape applied to the quiet 46%
- Per-type separator stacks beyond T1 (drift-join, fade)
- Pine stage 2 (detector + fire vectors) - HALTED until honest entries exist
- Python runner Stage 1 shadow logger - waits for an honest detector
- Burst-window rule wiring; 2B percentile adapter; trailing-form equivalence
  check (entry-era items, moot until entries exist again)

## STANDING RULES (unchanged)
Pre-freeze before any reserved-month read | derive numbers from measurements
| maximin | conservative two-sided reporting | truncation harness gate |
registry row + commit per test | propose-then-confirm decisions
