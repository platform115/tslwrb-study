# MASTER PROGRAM — replicating the trader (tree root)
Version: 1.0 | Created: 2026-11-24 | Change log at the end of this file.
> This is the root document. Every process below uses the same six-field
> template. If any section reads cryptic to a non-specialist, that is a
> defect: report it and it gets rewritten.

## THE GOAL (J, 2026-11-23, verbatim intent)
Develop one or more sets of entry rules and one or more sets of trade
management rules which enter the market in the right direction shortly
before it moves quickly in our favor, then exit; if it does not move
quickly in our favor, exit quickly at a small loss or even a profit -
as he does. Do not assume all his entries/exits share one mechanical
rule set. Reliably replicating 30-50% of his trades without triggering
too many entries he would not have taken - unless those extras are also
profitable - is a good initial achievement.
OBJECTIVE, formalized: maximize the share of his trades caught, subject
to: the extra fires have expectancy >= 0 under their PAIRED management.

## STANDING RULES (apply to every step, every session, without being asked)
R-1 LOOKAHEAD: no measurement, feature, generator, or rule enters any
    analysis until it passes the truncation harness. Mechanical, universal,
    no exceptions. (The T-EN99 lesson, made procedure.)
R-2 METHODS REGISTER: no method is used in any script unless it is in the
    register (below) first, with source and plain-language purpose.
R-3 NAMING: nothing receives a name (strategy, plan, detector, selector,
    group, doc) without a GLOSSARY.md entry in the same commit. Canonical
    names only in scripts, registry, docs; aliases decode history only.
R-4 PLAIN LANGUAGE: every technical choice ships with a plain-language
    companion, as a deliverable. Reviews are shown evidence (tables,
    curves), not verdicts hidden inside thresholds. All numeric criteria
    are provisional flag-lines that force discussion, never silent gates;
    changing one requires a logged reason.
R-5 PRE-REGISTRATION: hypotheses, rule candidates and comparison protocols
    are written and committed before results are seen. Deviations are
    visible as git diffs.
R-6 DOC DISCIPLINE: every process uses the six-field template (Purpose /
    Method+source / Inputs / Outputs / Review / Change log). New doc =
    tree-index entry in the same commit. Each doc carries STATUS
    (LIVING / FROZEN / ARCHIVED) and a version header.
R-7 RESULTS DISPLAY: all entry testing reports per
    RESULTS_DISPLAY_STANDARD.md; the BACKTEST_MATRIX is updated in the
    same commit as any run.

## DATA CONVENTION
Training months: 2025-10, 2022-02. Validation months: 2021-09 (one
validation pass already spent, noted), 2024-11 (untouched - QUARANTINED
until a Track B candidate reaches its validation step). New data months
join the quarantine pool on arrival.

## THE TWO TRACKS (separate, both mandatory, switchable)
Work may switch between tracks at any review; a switch is a logged
decision. Neither track's progress excuses the other.

===========================================================================
### R-8 — MECHANICAL COMPLETENESS PASS (added 2026-11-24, after two recall failures)
Before ANY deliverable reaches J at a review gate: diff it against
ASSETS.md (the generated data-asset inventory) and against the relevant
section of MASTER_PROGRAM - item by item, as a run step, never from
memory. The deliverable ships with a "checked against inventory; not
included: ..." footer. Rationale: both A1 omissions (invented vocabulary
v1.0; his-labels source missing until v1.3) were recall-instead-of-census
failures. Recall does not improve with effort; procedure replaces it.


### R-8 EXTENSION — THE PRE-PRESENT CHECKLIST (2026-11-26; each line
### is a documented miss J had to catch, never hypothetical)
Run mechanically on every deliverable BEFORE it reaches J:
1. CURRENCY: is the headline metric the decision currency (traded P&L,
   catches, fills) or a proxy (proximity, counts, rates)? A proxy may
   inform but NEVER carries a recommendation. [C1 -> C2 flip]
2. BASE RATE: every rate ships beside its null, base rate, or matched-
   density control, or it does not ship. [three saturated metrics]
3. SELECTION LINE: "what selection effect could produce this result for
   free?" - written in the spec before results are read. [key-ness
   confound; chaining]
4. CENSUS BEFORE CITATION: any claim about HIS method checks his corpus
   first; the field's standard constructs are controls, not defaults.
   [pivot/VWAP miss]
5. PREMISE RE-OPEN: when a new result changes the value estimate behind
   a prior decision (defer/adopt/park), that decision re-opens
   AUTOMATICALLY and the change is stated. [W20 deferral]
6. BOUNDARY FLAG: a parameter best at the edge of its tested range gets
   the flag and one extension cell. [reach-8]
7. J'S THREE QUESTIONS: the raw numbers behind every % | plain meaning
   of every term on first use | live-computable or study-only, stated.
The checklist result (pass / items fixed) is part of the deliverable.
Review gates REMAIN: this raises the floor; it does not replace J.

### R-1 AMENDMENT — TWO-TIER EVIDENCE (ACCEPTED WITH CONDITION, J, 2026-11-24)
J's condition: work focuses FIRST on the four per-second months
(training 2025-10 + 2022-02; validation 2021-09 one-pass-spent +
2024-11 quarantined). The 60-month screening tier activates later,
alongside selective Databento per-second purchases. The tier rules
below stand as written for when it does.
Context: 1m bars cover the full 60-month corpus (2021-05..2026-05,
1.77M bars, verified); per-second data covers 4 months. The 1-second
mandate exists because bar-rounding caused the original lookahead.
Proposal:
- TIER 1 - SCREENING (60 months, 1m bars + his message timestamps + his
  reported fill prices): allowed ONLY under the completed-bar rule - at
  time t, use nothing from the bar containing t; price-at-t is the last
  COMPLETED bar's close, with the staleness (up to 1 min) stated on every
  output. The truncation harness is extended to enforce this tier.
  Screening outputs say SCREENING on them and may only decide WHERE to
  look next. They never become rule inputs or performance claims.
- TIER 2 - CONFIRMATION (per-second months): every screening finding
  must reproduce here before it can enter any entry or management rule.
  All backtests and all fill/exit logic remain per-second only, as now.
- Optional: buy further per-second months from the vendor selectively,
  where screening concentrates - J approves each purchase.
Note: the core talk->trade linkage (his message time vs his reported
fill) uses no bar data at all - timestamps and his own stated prices -
so the lookahead surface there is zero by construction.

## TRACK A — THE MAP (breadth: measure everything, find the patterns)
Purpose (plain): a complete, living picture of HIS trading - every trade
measured on everything we can measure, grouped into named types - so we
always know what exists, what each type is worth, and what we have not
yet explained. This is also where new measurements (from the quant field
or from his vocabulary) enter the system.

A1. FEATURE COVERAGE MATRIX
  Purpose: make "what he might see that we don't" a finite checklist.
  Method: enumeration (no statistics). Rows = data sources we hold (1m
    bars, per-second mids, volume/flow, order book, trade prints, his
    messages, KME calendar, cross-market); columns = measurement types
    (speed, range, compression, volume, flow, structure distance/
    interaction, event-anchored, sequence/pattern). Each cell: BUILT /
    PARTIAL / ABSENT.
  Inputs: the battery, the resolver, the data inventory.
  Outputs: the matrix, with the ABSENT cells as the build backlog.
  Review: J sees the matrix; picks/approves which absent cells get built.
  Known at writing: order book, prints, cross-market, event-anchored
    windows, bar-pattern sequences are ABSENT or PARTIAL.

A2. THE MEASUREMENT TABLE
  Purpose: one table, every trade of his x every measurement - the raw
    material for all pattern-finding. ALL measurements, not summaries
    (J's correction 2026-11-24: measure everything first, THEN look for
    relationships).
  Method: the feature battery evaluated at each trade's entry second
    (and exit second), plus structure-interaction measurements from the
    resolver; every new feature passes the truncation harness (R-1)
    before joining the table.
  Inputs: his ~440 trades (3 usable months), battery, resolver.
  Outputs: trades x features table (stored, checksummed), re-built when
    new features or months arrive.
  Review: coverage report - which trades measured, which features present.

A3. GROUPING (two methods, compared)
  Purpose: sort his trades into types.
  Method: (1) HAND taxonomy - category definitions written and committed
    BEFORE any clustering output is seen (R-5). (2) ALGORITHMIC - Ward
    hierarchical clustering (Ward, 1963; deterministic, no random seeds)
    on the standardized measurement table; group count chosen by
    cross-month agreement, scored with the Adjusted Rand Index (Hubert &
    Arabie, 1985) - a standard 0-to-1 "how similar are two groupings"
    score, shown as evidence, not used as a silent gate.
    Comparison: a confusion table hand-vs-algorithm; any algorithmic
    group of meaningful size that matches no hand category is a mandatory
    investigation item ("he does something we have not named").
  Outputs: taxonomy vX - every trade labeled, each group defined in a
    sentence or two (R-4 documentation standard), group sizes, P&L
    share, per-month presence; plus the unexplained remainder, listed.
  Review: J sees group tables per month side by side + the comparison;
    accepts taxonomy vX or directs changes. Versioned; share drift over
    time is itself a finding.

A4. CANDIDATE RANKING (feeds Track B)
  Purpose: rank groups by replicability evidence so Track B picks well.
  Method: per group - (a) separability of his moments vs matched ambient
    null (the fair-null machinery); (b) stability across months; (c) the
    CEILING MODEL: a flexible model (random forest - Breiman, 2001; or
    gradient boosting) fit on ALL measurements to separate his moments
    from null, used ONLY to answer "how much information do our current
    measurements hold, and which ones carry it" (feature importance -
    Lopez de Prado, 2018, ch. 8). Low ceiling = the missing column is in
    an ABSENT cell of A1 - named, built, loop repeats. Shipped rules stay
    deterministic; the model is an instrument, never a strategy.
    (d) the STACKING STUDY (J, 2026-11-24): no single measurement
    separates his moments cleanly (A2.2: strongest family difference
    +0.54), so measure how separation grows as independent families are
    COMBINED - which conjunctions concentrate his entries, at what
    fires-per-catch cost. This is the honest upper bound for any rule
    built from current measurements. Standing premise (J): he has no
    data we cannot get - a low combined ceiling always means a missing
    construction on our side (an ABSENT A1 cell), never "unknowable".
  Outputs: ranked shortlist with plain-language evidence per group.
  Review: J picks Track B's next target (or orders an A1 build instead).

A5. GAP AUTOPSY (added by J's directive, 2026-11-25: "the gap between
  0.81 and 1.00 is a measured statement of how much of his decision we
  haven't captured yet - we need to do this also")
  Purpose: turn the ceiling gap into named build targets.
  Method: (a) profile the his-moments the ceiling model scores lowest -
  group, event, time, shared traits = the measured description of what
  we don't capture; (b) single-trade case studies of the B2-uncaught G2
  entries (Track B case-study mode); (c) verdict = which ABSENT A1
  family gets built next, by evidence. Each cycle of A5 repeats after a
  B-target reaches its verdict.
  Review: J sees the autopsy before the next build is chosen.

===========================================================================
## TRACK B — THE BUILD (depth: one target to "reliable", then the next)
Purpose (plain): take ONE target - a group from Track A, or a SINGLE
specific trade J picks as a case study - and build the full machine for
it: entry rule + paired management, proven on data it was not built from.

B0. TARGET SELECTION
  Two entry modes: (a) a Track A group (usual); (b) a single chosen trade
  - dissected end-to-end as a case study, then tested for generalization
  against lookalike moments. Mode (b) exists because J will sometimes
  point at a specific trade. Target choice is J's, at a review.

B1. TARGET ANATOMY
  Everything measurable about the target's trades: what preceded entry
  (structures, events, tape), entry displacement from trigger, hold,
  his exit relation to events/levels, MAE/MFE. Output: anatomy report,
  plain language. This defines the triple-barrier frame for B3 - the
  profit distance, loss distance and time limit HIS trades imply
  (Lopez de Prado, 2018, ch. 3: triple-barrier labeling).

B2. ENTRY RULE
  Primary trigger (cheap, fires often) + filter (the conditions that
  select the real ones) - the meta-labeling pattern (Lopez de Prado,
  2018, ch. 3): label every trigger fire by (i) was he there, and
  (ii) did it WORK (triple-barrier outcome) - because extras that work
  are acceptable per the objective. Ceiling model bounds what the
  features can do; final rule is deterministic with thresholds taken
  from measured distributions. Harness-passed before any scoring (R-1).

B3. PAIRED MANAGEMENT
  Built from B1's anatomy (the entry-management coupling is proven:
  T-BS02..04). Exit components assembled per target; M-series reused
  where it fits, new plan (M2, M3, ...) frozen only on passing its
  pre-stated test.

B4. UNIT TEST (training months)
  The pair scored per RESULTS_DISPLAY_STANDARD: catch of his trades in
  the target group, fires/day, extras' expectancy under the paired
  management (the objective's second clause), full HIS/OURS block.
  Review: J decides - iterate (logged), accept for validation, or park.

B5. QUARANTINED VALIDATION
  Frozen pair, zero refitting, on 2024-11 (and newer quarantined months).
  Holds -> the pair is RELIABLE, enters the strategy register; Track B
  returns to B0 for the next target. Fails -> documented, back to B2/B3
  with the failure as evidence, or parked.

===========================================================================
## METHODS REGISTER (R-2; add BEFORE use, with source + plain question)
| method | source | plain-language question it answers |
|---|---|---|
| Truncation harness | this project (T-EN101/T-IM28) | could this calculation have seen the future? |
| Pre-registration | this project (standing) | was the hypothesis written before the result? |
| Fair/matched null | this project (T-IM20 design) | is this more common at his moments than at lookalike ordinary moments? |
| Triple-barrier labeling | Lopez de Prado 2018, ch.3 | did this trade/fire work: profit hit before small loss or time-out? |
| Meta-labeling | Lopez de Prado 2018, ch.3 | which fires of a cheap trigger should actually be taken? |
| Feature importance | Lopez de Prado 2018, ch.8 | which measurements carry the information? |
| Random forest / boosting (instrument only) | Breiman 2001 | how much information is in ALL our measurements combined (the ceiling)? |
| Ward hierarchical clustering | Ward 1963 | which trades are most alike, grouped deterministically? |
| Adjusted Rand Index | Hubert & Arabie 1985 | how similar are two groupings (0 = chance, 1 = identical)? |
| Rank-based difference tests + multiple-comparison correction | standard (Mann-Whitney; Benjamini-Hochberg 1995) | does this group really differ, allowing for luck from checking many things? |

## EXISTING ASSETS -> WHERE THEY SLOT
Battery, resolver, generators -> A2 features. Fair-null + gold-anchor
designs -> A4/B2 verification. Strategy 3 family -> draft B2 for the
structure-trade group. Strategy 1 -> certified independent entry rule.
M-series + native stack -> B3 components and the coupling evidence.
BACKTEST_MATRIX, RESULTS_DISPLAY_STANDARD, GLOSSARY, registry -> the
reporting and naming layer (R-3, R-7).

## PROPOSED CLAUDE.md ADDITIONS (per project Rule 5: J reviews + commits)
- "Read MASTER_PROGRAM.md before working; its standing rules R-1..R-7
  bind every session."
- "No method without a METHODS REGISTER entry; no name without a
  GLOSSARY entry in the same commit."

## STATUS BOARD (updated as steps close)
Track A: A1 LIVING v1.5 | A5 gap autopsy DONE | A2.1 T-IM40 | A2.2 T-IM41 | A2.3 T-IM42/43 |
A3 T-IM44/45 + GROUPS OF RECORD (approved) | A4 T-IM46 (G2 top).
Track B: B0 = G2 (J confirmed) | B1 T-IM47 | B2 T-EN103 | B3/B4 T-BS05
(G2-1) | B5 T-BS06 PASS 2024-11 (look 1 spent). ENTRY REFINEMENT CYCLE
CLOSED 2026-11-26: T-EN106/107 (retest line - rejected; his dual-mode
measured), T-EN108 (two-lane; CONTROL ARM EXPOSED the cross-order vs
fill-time engine defect -> FILL-TIME ENGINE NOW STANDARD, incumbent
restated G2-3 = +276.1/607/catch 47/extras +185.6), T-EN110 (cadence
caps - rejected; his sparseness is selection not earliness), T-EN109/
111 (which-signal: tape + per-second book - null/suggestive only),
T-EN112 (window selection - FINDING: tier20 calendar flag = first
decision-tree branch, 78% vs 27% engagement).
REGISTERED, all to the purchased validation months: G2-3 (primary),
G2-4 (two-lane quality-alternate), G2-5 (N=1 cap, high-contract-size
variant). Parked suggestives + tier20 candidate shapes: see
VALIDATION_PLAN.md (pre-registered, one look).
THREE-LAYER FRAMING (J briefed): context layer (tier20 lives here) /
trigger layer (G2-3/4/5) / management layer (M7 etc).
Management/exit lane (drive-connected, 2026-11-26 night): T-MG19/20 -
imb10 exit-into-liquidity FINDING, survives duration+excursion
controls (his best-evidenced exit signal); T-MG21/22 - BOTH
monetization shapes failed on our fills (stall gate mechanism-negative;
clock extension structurally empty: 1/607 trades reach 480s - the
stall, not the clock, ends our trades). M7 stands. STANDING LESSON:
management verdicts are MECHANISM-PRIMARY (twin-matched delta).
Long-hold remainder -> mode 2 and/or event-level book round (J's
call). NEXT: tbbo converter -> VALIDATION_PLAN one look -> TRAINING
FREEZE. G3 cycle after.
Standing: fees ~0 for J's account (J, 2026-11-25) - cost caveats out of
the model by instruction; execution realism still priced at B4.

### THE TWO TRACKS (named plainly; the old Track A/B step labels are
retired to the change log - these are the program's goal tracks)
TRACK 1 - REPLICATE HIM: find his patterns and copy them. Its currency
is catch rate and per-trade parity. Holdings so far: his dual entry
mode (first-take + retest-take, measured), his exit clock, his
level-targeting, his exit-into-liquidity signature (described, not yet
monetized), the tier20 calendar branch of his decision tree, 50%
out-of-sample catch.
TRACK 2 - STANDALONE SYSTEMS: things that earn on their own, usable
across strategies. Its currency is out-of-sample P&L. Holdings so far:
G2-4 (VALIDATED - the sole deployable), G2-3 and G2-5 (DORMANT),
M7 management, the multi-day level detector, the fill-time engine,
the mechanism-primary testing standard.
Every finding files under one track; a track-1 discovery can graduate
into a track-2 component (the retest lane did exactly this).

### STANDING FINDINGS REGISTER (append-only; F-ids; THE single home
for earned findings - OVERVIEW_TREE summarizes and points here; every
future spec cites the F-ids it builds on or contradicts. Backfilled
2026-11-27 from the full test history at J's challenge.)
| id | finding | source | force |
|---|---|---|---|
| F-1 | TAIL CONCENTRATION: top 10% of trades = 169% of pooled net, top quartile = 263%; half of trades win but the tail IS the business. Any "surgical" strategy design starts from this fact. | T-XD01, 4 months | program-shaping |
| F-2 | ENERGY IS ONE FACTOR, measured by rv30 (last-30-min movement): AUC 0.647 alone, all other energy features (vol5/react5/range5/vol30/tier20) add +0.000-0.001 beyond it. Dead tape = stall bleed. | T-XD01 + factor check | gate input |
| F-3 | LEVELS ARE THE ENGINE: earners sit in level-dense territory (room ahead 4.5 vs 6.0) and spike-capture exits made +679 of +483 pooled net; stalls breakeven; stops -345. | T-XD01 anatomy | gate + strategy input |
| F-4 | WINNERS DON'T BREATHE: earner median MAE 0.12 vs rest 1.12; earners fill fast (80s vs 109s). Management implication: early-adverse exit could shrink the stop bill. | T-XD01 | management input |
| F-5 | NEGATIVES THAT STAND: signed flow at entry is NULL for our earners (the 3-sample flow thread is about HIM, not our P&L - D-2 premise weakened); lane is null (two-lane union vindicated). | T-XD01 | guard |
| F-14 | OUR EDGE RESISTS SUBSETTING (3 independent designs agree: feature selection/SEL, cap selection/G2-5 OOS, principled gates/T-EN113): every entry-time selection raises per-trade but discards net-positive trades - the tail lives on both sides of every condition. Earn broadly, manage well. | T-EN113 + G2-5 + SEL | design law |
| F-15 | THE -3.75 STOP IS EFFICIENT: early-adverse exits (120s, X=1.25/2.00 from earner-MAE quantiles) LOSE vs letting M7 ride (twin deltas -58/-36) - recoveries outweigh capped savings. Second independent stop vindication (with M9). F-4 stands as description; its management implication is tested and REJECTED. | T-MG23 + M9 | design law |
| F-16 | M7 OCCUPIES THE EFFICIENT FRONTIER of 1-second-mids + computed-levels information: 11 challengers across 5 families failed (T-MG21..26 + M3B/M4/M5/M6 era). The stop prices recoveries (F-15), the stall is the fastest honest invalidation (T-MG26), the capture monetizes the one validated structure (F-3). Per-trade quality beyond M7 requires NEW INFORMATION (event book) or NEW STRUCTURES (fade entries, G3) - not SIMPLE rule rearrangement. SCOPE ANNOTATION (J, 2026-11-27): this exhausts the tried families, not the 1s data itself - the standardized sequential-statistics family (CUSUM/change-point exits) is untested -> D-26. | T-MG26 consolidation | design law (scoped) |
| F-17 | THE HOLD/EXIT INFORMATION EXISTS AND IT IS DEEP FLOW: at matched duration AND profit, his keeps carry OFI10 (10-level order flow with the position) +831 higher than his exits, both months - he rides while deep flow pushes his way, exits when it fades at churn moments. First beyond-the-clock exit separator (resolves where F-7's residual lives). Live use needs a depth feed (not TradingView). | T-BK02 | the exit-ceiling key |
| F-6 | HE IS DUAL-MODE at entry: first-takes AND retest-takes, both profitable - no single timing rule copies him. | T-EN107 | became G2-4's lane 2 |
| F-7 | HIS EXITS = DURATION CLOCK first (t alone carries 0.805 of 0.814 AUC) + partial LEVEL-TARGETING (1.61x null: ~1 in 7 exits at our computed levels). | M10/M11 (T-MG17/18) | M7's design basis |
| F-8 | EXIT-INTO-LIQUIDITY: deep-book imbalance tilts toward his side at his exits, surviving duration AND profit controls - true description of him; BOTH rule monetizations failed on our fills. | T-MG19/20 vs 21/22 | description, not a rule |
| F-9 | HIS SPARSENESS IS SELECTION, NOT EARLINESS: capping to first fills per window catches almost none of his trades; later fills carry ~2/3 of our net. | T-EN110 | guard vs naive caps |
| F-10 | FLOW-WITH-THE-TRADE at his taken crosses: the only which-signal thread repeating in all 3 samples; never clears single-month bars. | T-EN109/111, T-VL04 | track-1 lead (D-6) |
| F-11 | THE SHRINKAGE GRADIENT: OOS performance shrank roughly with stacked tuned knobs (~50% per-trade); measured-behavior components transferred, grid winners didn't. | T-VL01..03 | design law |
| F-12 | COVERAGE CEILING: 12/62 + 3/14 of his entries match no edge of ours - catch is capped until edge families expand. | T-EN107/T-VL01 | D-11's basis |
| F-13 | THE CONTROL-ARM LAW: three engine/spec defects were caught only by exact-reproduction gates and mechanism accounting, never by inspection. | T-EN108, T-MG21, T-EN110 | why R-9 exists |

### ROADMAP (the ONE register of open directions; v2 after J's completeness audit)
Rules: (1) every open direction lives here as a D-number - an idea
not on this list does not get worked or pitched; a new idea enters as
one line FIRST. (2) APPEND-ONLY (J): items are never removed - a
finished item is marked DONE, an abandoned one RETIRED with ~~strike~~;
the numbering never reuses. (3) One item IN PROGRESS at a time unless
J says otherwise. (4) Statuses: QUEUED / IN PROGRESS / DONE / RETIRED.
(5) Every item names its TRACK (1 = replicate him, 2 = standalone);
track-1 items name their GROUP.

GROUPS OF RECORD (track 1's backbone; from A3/A4):
G1 | G2 (squeeze+news, 62) MINED - produced G2-1..5, validated arc |
G3 (squeeze quiet, 151) QUEUED = D-5 | G4 | G5 | G6 - G1/G4/G5/G6
UNMINED (incl. the oil-Wednesday pattern noted at A4).

| id | track | group | what | why (evidence) | needs | status |
|---|---|---|---|---|---|---|
| D-1 | 2 | - | Extras decomposition: which of OUR trades earn, what earners share | extras carried the OOS P&L (+141/+155); never studied; zero knobs | 4-month corpus | DONE (T-XD01: 14-finding coherent earner profile; feeds D-3-style gate spec; D-2 flow premise weakened) |
| D-2 | 2 | - | Flow-agreement entry gate (30s aggressor flow with the trade) | only thread repeating in all 3 samples | D-1 read; D-8 to judge finally | QUEUED |
| D-3 | 2 | - | Level-aware entries incl. fade-at-level family | level kit validated in G2-4 exits; fade long-parked | D-1 helpful | part 1 DONE (T-EN113: gates FAIL the frozen line - removed trades net-positive; F-14). Fade/new-entry-type family remains QUEUED under D-25 |
| D-4 | 2 | - | G2-4 live port (Pine v6 / TradingView + Python levels; project pine docs) | sole VALIDATED system | nothing | QUEUED |
| D-5 | 1 | G3 | G3 cycle: 151 quiet-squeeze trades, measurement-first | largest unmined group | nothing | QUEUED |
| D-6 | 1+2 | G2/G3 | Deep book round: event-level MBP-10 (which-signal flow thread; exit remainder; G3 features; fade features) | per-second book exhausted; drive holds 3.3G windowed | drive connected | Q1+Q2 DONE (T-BK02: F-17 breakthrough - OFI10 separates holds from exits; Q2 null; M15 switch spec to J). G3/fade feature extraction still available while drive connected |
| D-7 | 2 | - | Lane regime complementarity (first-break vs retest by condition) | 2 observations only | more G2-4 months | QUEUED (parked) |
| D-8 | - | - | Purchase 1-2 fresh months = next clean quarantine | required to finally judge D-2/D-3 and extend G2-4's record | J purchase | QUEUED |
| D-9 | mixed | - | Small parked items: re-entry after stop; regime-conditioned M7; role-flip levels v2; 3m/5m bar anatomy; 3C/3D traded P&L; unique trade_key; M4C-180 revisit; M11 WRB-projection variant | individually small (BACKLOG.md holds detail) | - | QUEUED |
| D-10 | 1 | G2 | tier20 candidate shapes (engagement prior / tier-based size split) | T-EN112 finding now SPLIT OOS (T-VL04) - open question | more months before any shape is testable | QUEUED (parked) |
| D-11 | 1 | all | Edge-coverage expansion: his UNMATCHED entries (12/62 training, 3/14 OOS sit near none of our edges; REMAINDER_LEDGER) | hard ceiling on catch everywhere | anatomy of the unmatched | QUEUED |
| D-12 | 1 | G1,G4-G6 | Remaining groups of record after G3 | unmined behavior | after D-5 | QUEUED |
| D-13 | 2 | - | Scale-outs vs single exits (he scales; we model single) | old simplification note; matters at size | - | QUEUED |
| D-24 | 2 | - | M14 management round: (a) early-adverse exit DONE-REJECTED (T-MG23, F-15); (b) regime-conditioned stall DONE-REJECTED but PRESERVED (T-MG24; helped the weakest month +50 vs +39 - revisit only under a future regime framework); (c) spike-reach DONE-IMMATERIAL (T-MG25: binds 1-2x per 4 months, all positive; T-MG14 boundary flag resolved; M7 kept for parsimony); (d) invalidation exit DONE-IMMATERIAL (T-MG26: the stall already does it faster; J's instinct confirmed as embedded) | F-2/F-3 | mechanism-primary per R-9 | CLOSED (F-16) |
| D-25 | 2 | - | SURGICAL standalone strategy: entries designed from the F-1..F-4 profile (level-approach in active tape) - J's "more surgical trade entry/management at a later point" | the earner profile | REVISED by T-EN113/F-14: selection half weakened; surviving premise = NEW ENTRY TYPES (fade-at-level, level-approach - a different trade universe, not a subset) | QUEUED |
| D-14 | 1+2 | - | Cross-market lane (ES vs NQ/bonds/DX at his moments) | named at in-data exhaustion as the lane beside the book; never registered | data purchase | QUEUED |
| D-15 | 2 | - | Full-month converter certification (old scripts, overnight on J's Mac) | one-day cert passed 99.999%; full month = belt+braces | J's Mac overnight | QUEUED (optional) |
| D-16 | - | - | ~~imb10 third monetization shape (book-conditioned stall)~~ | priced as a losing bet by T-MG21's negative mechanism | - | RETIRED at entry |
| D-17 | 2 | - | Pine track restart: stage 2 + fire vectors (HALTED pending settled entry rules - now settled by G2-4) + owed stage-1 session-stats vectors | BACKLOG 5a; unblocked by validation | folds into D-4 execution | QUEUED |

| D-18 | 2 | - | Stage-1 session-stats GOLDEN VECTORS owed by the research side to the Pine thread (per-session date, bar count, range, mean TR, C(day)) - deliverable NOW, unaffected by the 2A halt | pine-open-questions.md: "STILL DUE AND UNAFFECTED" | nothing | QUEUED |
| D-19 | 1 | - | VTR - his second system: definition hunt (2 corpus rows) | BACKLOG 1d, open since the M1 era | corpus search | QUEUED |
| D-20 | 1 | - | Key-KME-Zone system: generated zone list unsolved (stated-price clusters = validation set) | BACKLOG 1c | - | QUEUED |
| D-21 | 1 | all | His-levels closer look (BACKLOG 4a-4d): full-month day maps, per-object-class behavior, KME vs quiet regimes, emphasis tiers | descriptive series, partly absorbed by MDL work, rest open | - | QUEUED |
| D-22 | 2 | - | ETH scope: everything built is RTH-only; ETH-specific management (BACKLOG 2c) and ETH entries untested | known hole | - | QUEUED |
| D-23 | 2 | - | Python runner / VPS deployment thread (separate conversation; python-runner-handoff.md) | needed for D-4's level detector live | - | QUEUED |

| D-26 | 2 | - | Sequential-statistics exit family on 1s data: CUSUM / change-point detection on the trade's own path as the stall's statistical upgrade (textbook methods: Page 1954 CUSUM; Bayesian online change-point, Adams & MacKay 2007) | J's deeper-standardized-methods push; F-16's untested family | mechanism-primary per R-9 | QUEUED |

OPEN DECISIONS (addressed to J, not work items; append-only too):
| id | decision | since | status |
|---|---|---|---|
| Q-1 | R-1 two-tier evidence amendment (screening on 1m/60mo vs confirmation on per-second) | 2026-11-24 | AWAITING J |
| Q-2 | Move CURRENT_STATE.md + _edits to archive/ with stale banner | 2026-11-24 | AWAITING J |
| Q-3 | G2-1 / G2-2 disposition: both TRAINING-ONLY under the OLD engine; re-base on fill-time, or retire as superseded by G2-4? | 2026-11-26 | AWAITING J |
| Q-4 | Strategy 2A disposition: its entry rules were invalidated (T-EN99 lookahead) and halted; rebuild them, or supersede with G2-4 as the entry feeding the already-built Pine stage-1 infrastructure? | 2026-11-18 halt / surfaced 2026-11-26 | AWAITING J |

J aims; the chosen item moves to IN PROGRESS in the same commit its
spec is written. This register is complete as of 2026-11-26 22:10
(audited against BACKLOG.md, MASTER, VALIDATION_PLAN, DOCUMENT_MAP);
BACKLOG.md holds detail for D-9 only, plus the thread ledger.

### GOAL REFINEMENT (J, 2026-11-26)
"Discretionary" means he has internalized a series of consistent
patterns. Two modes follow: (1) DISCOVER AND REPLICATE those patterns -
most of the edge should be reachable this way; (2) where a pattern
resists discovery after honest cycles, his results become the BASELINE
for designing our own entries and management that may produce FEWER BUT
MORE PROFITABLE trades. Mode 2 is not failure; it is the second half of
the program (precision over volume, benchmarked against him).

## CHANGE LOG
- 2026-11-26 (night): T-MG19..22 closed (exit lane); imb10 finding
  earned and retained as description; both rule shapes rejected with
  mechanism accounting; mechanism-primary verdict standard adopted
  for management rounds; DOCUMENT_MAP v1.1 (VALIDATION_PLAN indexed
  with same-commit registration rule).
- 2026-11-26 (evening): entry cycle closed (T-EN106..112); fill-time
  engine adopted as standard after T-EN108's control arm caught the
  cross-order defect (all pre-correction combo rows kept, labeled);
  G2-4 and G2-5 registered; tier20 finding recorded; VALIDATION_PLAN.md
  created (single pre-registered look at 2023-05/2024-05); exit-switch
  book round opened while J's drive is connected.
- 2026-11-26: M9 closed negative, M7 stands; T-MG15 finding-4 corrected (dataset-mix artifact; stop vindicated by distribution). Management line RESTS pending book data / validation months. G3 cycle next.
- 2026-11-26: R-8 extended with the pre-present checklist (7 lines, each from a documented miss); J may amend.
- 2026-11-26: B2v2 adopted (T-EN104) - G2-3 = 4A-v2 d1.25 x M7, +265.4 training, catch 74% of G2; training-only; the C2 sharpening (J) directly produced this. Next: G3 cycle.
- 2026-11-26: C audit closed (T-IM53) - coverage candidates logged for the next Strategy-4 revision batch; pre-G3 queue COMPLETE. Next: the G3 cycle (B0-B5 for squeeze-quiet, with the book/prints lens built inside it).
- 2026-11-26: goal refinement recorded (two modes: replicate patterns / precision-over-volume original design on his baseline).
- 2026-11-26: M6C stage 1+2 ADOPTED - M7 (level-snap at computed multi-day levels) named; G2-2 = 4A d1.25 x M7, +186.0 training vs G2-1's +135.8, extras ~2x; TRAINING-ONLY pending a fresh pre-committed validation month. Management campaign closes successful; queue: C audit -> G3 cycle.
- 2026-11-25: management campaign M4-M6C closed. M3A stands live. Dual-oracle ceiling +274.9 proven; tested-form failures logged (not idea-deaths, per J); M6C stage 0 weak-positive: KEY-level snap beats M3A (+129 vs +124) where nearest-level fails (+92) - level selection is the lead. Stage 1 = computable key-ness generator (detector build), queued.
- 2026-11-25: M4 round closed, no adoption - M3A stands; OTHER gap cause reopened (not scale-outs); next: squeeze-detector coverage audit (C), then G3 cycle.
- 2026-11-25: B5 PASS - first validated strategy of the program (Strategy 4A d1.25 x M3A on G2); 2024-11 look 1 spent.
- 2026-11-25: A5 gap autopsy added (J's directive); loop: B-verdict -> A5 -> next build/target.
- 2026-11-25: status board added; A-track closed through A4; B0-B2 closed; B3 next.
- 2026-11-24: A4 extended with the stacking study (combined-family separation ceiling) and the no-hidden-data premise, per J.
- 2026-11-24: methods register + Cliff's delta (Cliff, 1993 - rank-based effect size; the chance one group exceeds the other, minus the reverse) for his-vs-null difference ranking in A2 reports.
- 2026-11-24: two-tier amendment ACCEPTED with J's condition - per-second months first; screening tier and vendor expansion deferred.
- 2026-11-24: proposed two-tier evidence amendment to R-1 (screening on 1m/60 months vs confirmation on per-second); awaiting J.
- 2026-11-24: R-8 added (mechanical completeness pass); ASSETS.md generator committed.
- v1.0 2026-11-24: created from the planning discussion of 2026-11-23/24
  (two mandatory switchable tracks; measure-everything correction;
  evidence-at-review replaces numeric gates except R-1/R-5; single-trade
  case-study mode added to B0).
