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

## THE ARTIFACT TREE (2026-11-26; statuses live)

GOVERNANCE (Stage-0 docs)
├─ MASTER_PROGRAM.md ... goal, R-1..R-8, tracks, status board
├─ GLOSSARY.md ......... naming authority (all designations below)
├─ RESULTS_DISPLAY_STANDARD.md | DOCUMENT_MAP.md | ASSETS.md (generated)
└─ BACKTEST_MATRIX.md .. every entry x management combo ever run

STANDING RULES R-1..R-8 (exactly eight)
R-1 lookahead harness (+two-tier screening/confirmation amendment)
R-2 pre-registration | R-3 flag uncertainty | R-4 plain language
R-5 naming | R-6 docs current | R-7 results standard | R-8 mechanical
completeness passes

TRACK A (the map) — A1 coverage matrix (LIVING v1.5) -> A2 measurement
table (T-IM40/41/42/43: 75 cols, 315 trades + nulls) -> A3 grouping
(T-IM44/45 + GROUPS OF RECORD) -> A4 ranking + ceiling 0.81 + stacking
(T-IM46) -> A5 gap autopsy (T-IM48)

GROUPS OF RECORD (two factual axes)
G1 news-burst(21) G2 squeeze+news(62) G3 squeeze quiet(151)
G4 reaction+news(25) G5 reaction quiet(40) G6 rare(8)
+ intensity = continuous dial (dead-band use only)

ENTRY STRATEGIES
├─ Strategy 1 ... certified signal-score entry + native stack (T-EN102)
├─ Strategy 2A/2B VOID (lookahead era)
├─ Strategy 3A-3D ... structure-interaction selectors (OOS 19-49%)
└─ Strategy 4 ...... the G2 rule (B2, T-EN103)
   ├─ 4A unfiltered | 4B move+flow | displacement d1.25/d2.50

MANAGEMENT
├─ M0 frozen | M1 adopted-general | M1A variant
├─ M3 family (G2-speed): M3A stall-60 (STANDS) | M3B | M3C
├─ M4 ratchet/tiered/event (tested, not adopted; M4C-180 revisit list)
├─ M5 accelerating-trail / speed-gate (no qualifier; DUAL ORACLE +274.9)
└─ M6 level-aware: nearest-edge failed; M6C his-keys cleared stage 0;
   stage 1 (computed levels) = next

VALIDATED PAIRS
└─ G2-1 = Strategy 4A d1.25 x M3A ... training +135.8, B5 PASS on
   2024-11 (+63.6, catch 8/11, extras +61.9); quarantine look 1 spent

DETECTOR LAYER
├─ G1-G4 generators (gaps/shadows/reactions/compression) + resolver
│  (harness-certified, 1s)
├─ signal engine (score>=6 at WRB completion)
└─ MDL multi-day level detector v3 (T-IM50/51): density-peak, 60d/2pt/
   >=4 days, ~10 levels/day; 62% recovery of revealed zones; FIT

TEACHING ASSETS (study-only, never ship)
├─ his episodes (4,842) | zone refs (5,155) | ref->object links (7,533)
├─ ground truth table (audited, T-IM40) | revealed episodes (1,416)
└─ a2 features table (75 cols + labels)

QUEUE: M6C stage 1 -> (joint) -> C squeeze coverage audit -> G3 cycle
(book/prints lens) | registries: T-IM51, T-EN103, T-MG13, T-BS06 latest

## 2026-11-26 EVENING ADDITIONS
- Engine: FILL-TIME single-position convention = standard (T-EN108
  control arm caught the old cross-order defect; old rows kept, labeled)
- Strategies registered: G2-3 (primary, corrected +276.1/607/47),
  G2-4 (two-lane alternate, +325.1/757/48), G2-5 (N=1 cap, +0.90/trade)
- Entry rounds closed: T-EN106 (RT), T-EN107 (RT2 + his dual-mode),
  T-EN108 (TL), T-EN109 (which-signal, tape), T-EN110 (cadence),
  T-EN111 (which-signal, book), T-EN112 (window selection - tier20
  FINDING)
- New data: Data/inputs/book_per_sec_{2022-02,2025-10}.parquet (drive
  MBP-10 per-second reduction, checksummed)
- New governance doc: VALIDATION_PLAN.md (single pre-registered look)
- Open: EX round (exit-switch via book, running), tbbo converter,
  event-level MBP-10 round (optional), G3 cycle
