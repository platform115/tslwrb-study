# PROJECT TREE — components and their relationships
> Updated 2026-11-19. Arrows show what feeds, became, or governs what.

```
ES TRADING PROJECT (reverse-engineer wrbtrader -> build our own strategies)
|
+-- DATA
|   +-- Market data (Databento)
|   |   +-- es_1m_front bars (all sessions, roll-flagged)
|   |   +-- per-second mids (TBBO) --feeds--> burst measure, fill engine
|   |   +-- flow_per_sec (signed volume), book_per_sec (2 months)
|   |   +-- month budget
|   |       +-- training 2025-10 (ACTIVE - sole month until entries select)
|   |       +-- training 2022-02 (waiting)
|   |       +-- reserved 2021-09, 2024-11 (9 reads, pre-freeze only, closed)
|   |       +-- purchase x4 (SEALED - final exam)
|   +-- His data (ground truth - the only proven edge)
|       +-- tsl_episodes_clean: entries/adds/exits/realized P&L
|       +-- wrb_messages: 31,838 msgs, trade_action tags (his explanations)
|       +-- chat_activity: per-minute presence (was he there)
|       +-- his_kme_times / kme_calendar
|
+-- METHODS & GATES  --govern every branch below--
|   +-- truncation harness (lookahead gate; standing, after T-EN99)
|   +-- per-second fill engine (honest fills/stops)
|   +-- registry: T-EN (entries/audits) T-EX (management) T-IM (imitation)
|   +-- rules: pre-freeze before reserved reads | derive-from-measurement |
|       maximin | two-sided reporting | propose-then-confirm | commit per test
|
+-- STRATEGIES
|   +-- Strategy 1 (v1-v11)  [FROZEN - clean code, honestly unprofitable]
|   |   +-- 10-condition score signals --revived--> P6 separator (AUC .727)
|   |   +-- v11 exit stack --became--> M0
|   +-- Strategy 2  [ENTRIES VOID - thrust lookahead, T-EN99/100]
|       +-- detectors
|       |   +-- D1 8s-burst --was core of--> 2A/2B; clean piece kept in toolkit
|       |   +-- D4 quiet-tape [parked] --aimed at--> quiet-46% group (P6)
|       |   +-- D6, D7 [retired]
|       +-- 2A (quality) / 2B (volume) / overnight  [all void]
|       +-- adapters (clean, reusable by any future entry)
|           +-- C(day) rolling ratio | atr10 | trailing-pct rule | gap rule
|
+-- TRADE MANAGEMENT  (independent layer - works on ANY entry source)
|   +-- M0 = v11 sketch  [frozen control, never modified]
|   +-- M1 = stall clock [ADOPTED] 
|   |   +-- RTH config S=30 / ETH config S=90 (band-derived)
|   |   +-- + session close + inert rails (hard stop, time stop)
|   |   +-- proven: beats M0 on identical fires; profits on HIS entries
|   +-- M2 [planned next]
|       <--built from-- his-vs-M1 differences on identical entries
|                       (he ~+620 scale-confounded vs our +108, T-IM05)
|
+-- ACTIVE PHASE: P6 IMITATION STUDY  (entry detection & selection)
|   +-- object of study: HIS 92 first entries, 2025-10 only
|   +-- typology v0: momentum-join 34% | drift-join 14% | fade 7% | quiet 46%
|   +-- separators found (within momentum-join, n=14 - leads not findings):
|   |   score-signal .727 | early-session .670 | KME-window .667
|   |   stacked: 176/day -> 10.7/day at ~2% precision (ceiling suspected)
|   +-- grouping axes to build (user 2026-11-19):
|   |   presence-known | commentary-explained | KME-tf-WRB rule-catchable
|   +-- target: a % of his entries caught PER DAY by one or several small
|   |   systems; one-rule-for-all not expected
|   +-- feeds--> BOUNDED SEARCH (pre-registered candidates + stopping rule)
|                --> validation --> purchase-month exam
|
+-- TRANSLATION / LIVE  (downstream consumers of frozen results)
    +-- Pine route M (TradingView)
    |   +-- stage 1 readout + alert probe [ACTIVE - clean definitions]
    |   +-- stage 2 detector + fire vectors [HALTED until honest entries]
    +-- Python runner
        +-- handoff doc written; Stage-1 shadow logger waits for a detector

ACTIVE QUEUE - IMITATION STUDY (user-ordered 2026-11-19):
1. TERM-GROUNDING: at the times he says contracting / squeeze / volatility
   spike / expansion etc., measure the tape (compression + movement metrics)
   vs ambient - define HIS terms detectably. Message-lag caveat applies.
2. Compression-at-entries run: squeeze metrics at his 92 entries vs ambient,
   per typology group (tests the quiet-46% = contraction-entry hypothesis).
3. EARLY-ENTRY context study: seconds/minutes BEFORE his entries (what level
   was being approached, why it might matter: session hi/lo, swings, round
   numbers, borders) and AFTER (the signal he expected - did expansion come).
4. BROAD LANGUAGE SEARCH: beyond hand-picked keywords - distinctive-term
   discovery near entries vs general chat (he is not transparent; let the
   text reveal his working vocabulary).
5. 2022-02-22 "signal @ 4321.50" dissection - WHEN 2022-02 OPENS (one-month
   directive holds until entries select).
CAUTIONS (user): do not over-formalize his language (clue/confirmation/
signal are not fixed stages; chart patterns are sometimes-pending, not
always); keywords are a floor, not the method.

PARKED - TRY SOON: active-window restriction | his adds/exits dissection
(feeds M2) | performance-target reframing | finer tape shapes | flow/print
microstructure | day-type | NQ/YM lead-lag | D4-on-quiet | per-type stacks
beyond T1 | burst-rule wiring etc. (moot till entries exist)
```

## BOUNDED-SEARCH CANDIDATES harvested from the imitation study (user 2026-11-20:
## "might be useful for finding an entry strategy as part of the other entry
## work not related to imitating his trades - remember those")
- Structure-edge trigger architecture: maintain resolver edges (harness-
  certified), detect cross/reject interaction, enter at edge + measured
  displacement (REA median +3.0 pts, SQZ +1.5, GAP/SHD at edge). T-IM31.
- KME-window gate: 3x fires-per-catch concentration (87->28). T-IM33.
- REA union definition (5m N=2 swing OR 0.08% pct-zigzag): 86% of his
  reaction refs, +38 over fair null. T-IM27.
- Negative knowledge: price-AT-structure selection fails (T-IM29);
  vol-spike (comp5/mv120) does not discriminate entries (T-IM33);
  implied Key-zone lists inherit market geometry (T-IM27).
