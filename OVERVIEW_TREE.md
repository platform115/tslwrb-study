# MASTER TREE — the grander plan (2026-11-20, supersedes the previous tree)

ES / wrbtrader STUDY
|
+-- DATA LAYER
|   +-- bars: es_1m_front.parquet (2021-05 .. 2026-05), wrb_1m.parquet
|   +-- per-second: flow_per_sec (2021-09, 2022-02, 2024-11, 2025-10)
|   |               book_per_sec (2022-02, 2025-10) [NEVER USED - cycle-3 backlog]
|   +-- his record: wrb_messages (31,838 msgs) | tsl_episodes_clean (his trades)
|   |               his_zone_refs (parser v3.1, 5,155 refs) | his_kme_times | kme_calendar
|   +-- derived:   s4_objects (3.34M structures) | s4_ref_links | s6_presence | s6_selectors_final
|
+-- INTEGRITY GATES (standing)
|   +-- truncation harness T-EN101 - entries / signals / M1 exits
|   +-- resolver harness T-IM28 - all structure generators at 1-second precision
|   +-- test registry (one row per test, T-xxNN) | Rule 2: hypotheses before backtests
|   +-- review gates: no step starts before the prior step's gate passes
|
+-- STUDIES (phases)
|   +-- P0-P3  early audits and candidates (historic)
|   +-- P4     entry era -> Strategy 2A/2B VOID (T-EN99 thrust lookahead)
|   +-- P5     trade management (active)
|   +-- P6     imitation study (complete; cycle 3 open)
|   +-- P7     bounded search (round 1 done; refinement waiting on management)
|
+-- STRUCTURE PROGRAM (P6, S0-S6, all gates passed)
|   +-- S0 timeframes: HIS set = 1m 2m 3m 5m 15m (+60m zones); named objects live on 5m/15m
|   +-- S1 parser v3.1 (direction binding fixed) -> his_zone_refs
|   +-- S2 definitions: WRB + Hidden GAP (Perry-sourced, kept) | Long Shadow D1/D2
|   +-- S3 GENERATORS (each calibrated vs his words, fair nulls)
|   |   +-- G1 hidden gaps: identification 64%; gold clock-verified; KME gaps = 5m, others 1m
|   |   +-- G2 shadows: D2 + most-recent PROVISIONAL (78%, +14)
|   |   +-- G3 reaction levels: swing 5m N=2 UNION 0.08% zigzag (86%, +38) - STRONGEST
|   |   +-- G4 compression: W=15 contraction / W=30 tight range (+24 role-stated)
|   +-- S4 lifetime: ordinary structures intraday (4-23 min); Key KME zones weeks-months
|   |      (his stated prices, 2.4x null) -> recency rule refined
|   +-- S5 resolver: tolerance 1 pt (gaps, shadows) / 3 pts (reaction, compression)
|   +-- S6 entries vs structures (below)
|
+-- ENTRIES
|   +-- VOID: Strategy 2A / 2B (lookahead era)
|   +-- IMITATION SELECTORS (frozen, catch-rate only, no P&L)
|   |   +-- ER-SIG  = reaction-edge interaction + score>=6 signal
|   |   |            38% catch training, 19-26% validation, 13-19 fires/day
|   |   |            entry price = edge + displacement (median +2.3..+3.0 pts)
|   |   +-- ER-WIDE = interaction + (KME window OR signal)
|   |   |            49% / 32-44%, 34-50 fires/day
|   |   +-- key facts: he enters OFF levels (break/reject), not AT them;
|   |   |             KME window = 4x enrichment; momentum entries uncaught by design
|   |   +-- REMAINDER (his drift entries, ~60% of trades, bigger half of his P&L)
|   |       +-- unexplained by: tape state (288 cells), interaction x drift,
|   |       |   vol-spike, KME, signals - all documented failures
|   |       +-- CYCLE-3 BACKLOG: order book, prints, cross-market insync,
|   |           sequence context, path shapes
|   +-- BOUNDED SEARCH (our own entries, P&L in scope)
|       +-- S-A edge-break: +84/month but ~+0.05/trade - negligible
|       +-- S-B (+KME), S-C (+signal): REJECTED (lose under M1)
|       +-- verdict: triggers locate his places; profit lives in management
|       +-- refinement: deferred, resumes when management improves
|
+-- TRADE MANAGEMENT (P5)
|   +-- M0 - FROZEN incumbent (fast-fail + stop + time + session; no stall)
|   +-- M1 - ADOPTED working plan (stall S=30 RTH / 90 ETH + stop 4.0 + time 27 + session)
|   +-- M2 - NOT YET FROZEN; design runs so far:
|   |   +-- MG-1  diagnosis: HIS +620 vs M1 +200 per-unit; gap = patience
|   |   |         (he holds 183s vs 50s, captures 83% of 2x the move)
|   |   +-- MG-2  patience plateau S=60..180 -> +235..+248 (vs 200); L-rules weaker
|   |   +-- MG-2b structure-breakeven cells: ALL LOSE (edge pullbacks are normal)
|   |   +-- MG-3  S=90 validation: wins 2/3 months, loses high-vol 2022-02 - NOT frozen
|   |   +-- MG-3b prior-session gap adapter: FAIL (too tight)
|   |   +-- MG-3c intraday gap adapter: FAIL (tightens in active tape - backwards)
|   |   +-- MG-3d stop = share of R_est: FAIL (wider-in-high-vol is wrong direction)
|   |   +-- ROUND CLOSED - M1 stands; S=90 best-but-fragile on record
|   +-- exit taxonomy in force: stall clock | hard stop | time stop | session close
|   +-- HIS exits: ride WRB pt occurrences; NOT level-parked (measured)
|   +-- remaining chartered adapters: time stop (peak-time distribution)
|
+-- DETECTOR / SIGNAL layer (legacy, clean components)
|   +-- 8s burst measure (honest) | atr10 | C(day) | gap clock | flow features
|   +-- score>=6 signals - the strongest selection conjunct found (7x concentration)
|   +-- FAILED as conditions: volatility-spike at entry; session-extreme reading
|
+-- PINE / LIVE track
|   +-- stage 1 (readout indicator, probes) - continues
|   +-- stage 2 + fire vectors - HALTED until honest entries firm up
|   +-- python runner / VPS - separate conversation thread
|
+-- OPEN QUEUES
    +-- cycle 3 (remainder): book, prints, cross-market, sequence, path shapes
    +-- Key-zone generated list (proxy failed; stated-price clusters = validation set)
    +-- G2 shadows D1-vs-D2 / band form -> future re-reference evidence
    +-- time-stop adapter | re-entry mechanism | scale-out (needs multi-contract months)
    +-- 2022-02 "4321.50" dissection | M2 freeze | second-era months

## TRACK A/B PROGRESS (2026-11-25)
- Track A closed through A4: measurement table (75 cols, harness-
  certified), groups of record G1-G6, ranking -> G2 squeeze+news top.
- Track B: B1 anatomy (74% win, +231 pts his; trigger shape 62/62);
  B2 entry rule (catch 45-47/62 raw, 40/62 filtered; extras positive
  pre-management). B3 management pairing next; B4 joint test; B5
  quarantined.
