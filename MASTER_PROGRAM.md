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
R-9 PROVE THE TOOL (text landed 2026-11-27; rule in force since
    T-MG21/T-EN108, F-13): no report is read until the engine that
    produced it reproduces its certified control numbers exactly, in
    the same run. Management verdicts are mechanism-primary
    (twin-matched deltas), never cell-total. Patches are verified
    applied before results are trusted.
R-10 REMAINDERS GET ANATOMIES (J's avoid-this-mistake instruction,
    T-EN114): an unexplained remainder (unmatched trades, a residual
    gap) is a clue, not a ceiling - it receives a case-by-case anatomy
    before any claim that it is irreducible.
R-11 MONTHS-SPEND GATE (J confirmed 2026-11-27): every new-claim spec
    must contain a MONTHS-SPEND section before freezing: which months
    the claim's design has already seen (and through what channel),
    which months the run will newly spend, and whether any could
    instead be held out - with the hold-out taken by default unless
    the spec argues otherwise. J gates the spend, not just the spec.
R-12 FINDINGS SWEEP (J confirmed 2026-11-27): every new spec (entry,
    management, or selector) must contain a FINDINGS-SWEEP section
    before freezing: each standing F-finding is listed as APPLIED
    (how) or NOT-APPLICABLE (why). A finding spotted missing
    retroactively triggers a follow-up round, as F-23..26's omission
    from T-SR03 did. Added to the R-8 pre-present checklist.
R-1a TWO-TIER EVIDENCE (Q-1, J approved 2026-11-28): screening
    claims may run on 1m bars across the 60-month corpus; any claim
    that advances to registration or a frozen verdict must be
    confirmed on per-second data. The truncation harness enforces
    both tiers.
R-13 FAILURE AUTOPSY (J directed 2026-11-27, generalizing his D-8
    adapter flag): whenever ANY entry strategy, entry component,
    selector, or exit management fails on brand-new data, the
    autopsy must separate MECHANISM failure from PARAMETER-TRANSFER
    failure (a mis-calibrated constant is an adapter problem, not a
    dead mechanism). R-10 applies before any DEAD verdict;
    recalibration proposals go to J.

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


### R-8 ADDITION (2026-11-27): scripts/taxonomy_audit.py runs in the
### mechanical pass - SYSTEMS_MATRIX formulas, registers and GLOSSARY
### must match bidirectionally before any registry commit.

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
PROPOSED 2026-11-27 (the cross-session forcing function - CLAUDE.md
is auto-read at every session start, so this survives compaction and
new sessions without relying on memory):
  "Before presenting or committing any registry-affecting result,
  run: python3 scripts/preflight.py - it must PASS. Every new
  system, component, or management lands in SYSTEMS_MATRIX.md with
  a formula and an implementation anchor in the same commit; every
  new runner's docstring names the certified source it derives from
  and reproduces that source's numbers (R-9) before any look."

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
| F-18 | THE TRANSFER LAW: signals that truly separate HIS behavior fail as rules on OUR fills - three instances (imb10->M12, entry-flow->F-5, OFI10->M15). His exit skill is ENTANGLED with his entry selection; the pair cannot be split and transplanted. Monetizing his separators requires entries that are HIS-LIKE BY DESIGN (D-25), not retrofits onto G2-4. | T-MG27 consolidation | design law |
| F-19 | AT MULTI-DAY LEVEL APPROACHES: hold-vs-break is a 50/50 coin that pre-approach book state does NOT tilt (clean null, 339v335); HIS participation at levels is BREAK-BIASED (52 breaks vs 36 holds traded, fading a minority mode). D-25's his-like entries = level-BREAK participation + context selection, NOT fading-first. | T-BK03 | D-25 course correction |
| F-20 | CONSTANTS AUDIT (T-SA01): no knife-edges; ONE sensitive constant (cross-dedupe 300 - the only number whose value materially matters, flagged on record); stop flat across 3.0-5.25 (F-15 reinforced); F-17's exit-fade is a SUSTAINED ~1-minute flow change (grows 15s->60s windows), not a sub-second blip - in principle partially visible in coarse flow data; T-BK03's null robust to all outcome labelings. | T-SA01 | trust foundation |
| F-21 | THE TOUCH-REACTION DISCRIMINATOR: at a multi-day level touch, the next ~3 SECONDS of book behavior tilt the 50/50 hold/break coin - hard churn + sweeps INTO the level = real break; quiet touch = hold (FINDINGs both months, decaying by 10s, gone at 30s; explains T-BK03's pre-approach null). First entry-side book discriminator. Plus: our earners fill into cycling books at every horizon. Together with F-17/F-18/F-19 this completes D-25's design foundation: touch -> 3s read -> break entry + flow-fade exits, born as one organism. | T-BK04 | D-25 foundation |
| F-22 | S-1 (the first DESIGNED strategy) passes its full in-corpus test: +119.6/198, per-trade 2x G2-4, worst -2.00 structural. AND: his participation is FLAT across the 3s touch signal (13%/13%) - S-1's edge is OURS; what HE uses to pick trades remains unexplained after every lens. Mode 2 delivers where mode 1 could not. | T-SR01 | first surgical result |
| F-23 | THE CATCH CEILING DISSOLVES: all 12 unmatched entries sit ON structures we already compute (gap edges 5, shadow edges 3, WRB bodies 2, REA 1, prior-day 1; 11/12 within 0.75 pts; 10/12 continuation breaks). Our stream listens only to SQZ+W20 edges; he breaks the other families identically. Multi-family trigger (4A-v3 candidate) -> ceiling 59/62; extras-cost unknown until spec'd. F-12 stands corrected: "none of our edges IN USE". | T-EN114 | the catch unlock |
| F-24 | HIS STRUCTURAL GRAMMAR GENERALIZES: 148/151 of his quiet-market (G3) entries sit within 1.5 pts of a price-computable resolver edge - GAP-dominant (77), then SHD (43), SQZ only 23. The multi-family vocabulary is his GENERAL method, strongest outside news windows. All families verified price-only in source (the KEY his-feed family appears in zero attributions). D-5 starts with attribution ~solved. | T-EN114 extension | the grammar |
| F-25 | THE MULTI-FAMILY TRIGGER WORKS: G2-6 (4A-v3 x M7) on all six months = 6252 trades / +1659.0 / +0.27 per-trade (exactly G2-4's) / catch 59/62 / extras +1556.8 / all months positive / no toxic family. The F-23 prediction lands to the trade: widening the listening vocabulary closes the catch gap WITHOUT diluting per-trade quality - WRB bodies (+0.38) and W20 (+0.30) are the richest sources, SQZ the poorest (+0.09) once other families take its stacked entries. TRAINING-ONLY until D-8. | T-EN115 | the catch gap closed |
| F-26 | THE SURGICAL LINE SCALES THE SAME WAY (T-SR02): family-edge touches give the S-1 machinery ~6x trades and ~4x pooled (+1985.6/4369) at DILUTED per-trade (+0.45) - volume, not quality, echoing F-25. AND the sleeper: the incumbent multi-day-level universe run on FULL RTH (no coverage restriction) is the per-trade leader of the whole program so far - +0.63 on 750 trades, both months positive, before any 3s filter. GAP+SHD dominate the family book again (F-24 echo). PDY negative-tiny (watch). | T-SR02 | surgical universe law |
| F-27 | THE SURGICAL LINE RESISTS CHEAP SUBSETTING TOO (T-SR03 null): 5W full-RTH's +0.63 is FLAT across news-proximity, hour, level score, first-vs-repeat, approach speed, pre-touch volume and fill delay - zero BH survivors under a pre-frozen promotion rule. F-14 extends to the surgical line's flow/calendar dimensions. Exit anatomy repeats F-3: capture exits +973.2/237 (+4.11 each) ARE the strategy; stops -706. Directional leads (non-FINDING, for Part B): quiet-hours +0.70 vs window +0.49; LOW pre-touch volume best cell +0.83. The surgical upgrade waits on the 3s BOOK read (F-21/Part B) - the 1s-visible surface is exhausted. | T-SR03 | the cheap path closed |
| F-28 | ROOM-TO-STRUCTURE IS THE FIRST WORKING SELECTOR (T-SR04 FINDING, BH both-months): surgical-line per-trade is MONOTONE in the distance to the nearest family edge ahead of entry - edge <2 pts ahead chokes the run (+0.53, 86% of trades); 2-8 pts of runway earns +1.5 to +2.5; no edge ahead loses (-0.22). Supporting same-direction gradients: level-target 2-4 ahead best, backstop 2-6 behind best, range-extension entries worst. The F-23/24 vocabulary acts as BRAKES when close and TARGETS when reachable (F-7's 1.61x logic in our own data). | T-SR04 | the selection key [CORRECTION 2026-11-28: numbers pre-F-36; corrected effect = F-37/T-RH02] |
| F-29 | 5W-RWY PASSES EVERYTHING (T-SR05): the runway gate run constructively = 102 trades / +157.1 / +1.54 per-trade / 63% win / stops 47%->31% / capture 32%->45% / months +79/+78 / plateau across bands (lower bound = a clean volume-quality dial; not optimized further per F-20). FIRST selection gate to survive a frozen verdict - because it is MECHANISM-LINKED to the exit engine (capture needs a reachable target), where flow/calendar/grid gates all failed (F-14/F-27 refined: subsetting fails unless tied to the earning mechanism). TRAINING-ONLY; F-11 haircut expected; judge = D-8 stage 2. | T-SR05 | the surgical breakthrough [CORRECTION 2026-11-28: numbers pre-F-36; corrected effect = F-37/T-RH02] |
| F-30 | THE SURGICAL STOP IS EARNING ITS KEEP (T-SR07): the failed-break exit (exit on level reclaim) is REJECTED at every threshold - it rescues all 32 stops yet loses -32.9 twin-matched, because dipping back through the level is NORMAL for these entries (the retest is part of the pattern, F-6 echo) and clipped winners cost multiples of what rescued stops save. Monotone: deeper reclaim thresholds approach baseline - L-1.25 is at or inside the efficient stop depth. The S5-line analog of F-15. Loss-size gains must come from SELECTION (Part B), not earlier price-path exits. | T-SR07 | the loss side resists |
| F-31 | DYING DIPS ARE DISTINGUISHABLE - BUT THE EXIT PRICE BINDS (T-SR08): time-to-reclaim and prior-MFE separate stopped from recovering trades at BH p~0 both months (fast+never-profited dips: ~70-77% stop; slow or post-profit dips: 18-42% stop, strongly positive means). Yet NO -1.00-exit rule can profit: saving 1.0 pt on stops vs forfeiting ~2 pts on recoverers needs >75% stop purity, and the worst identifiable cell runs 70% (mean final -0.75 > -1.00 - still worth holding on average). The flow-sign conditioner is dead (RWY: flow-against reclaims mostly RECOVERED, 4% stop, n=25 - rule killed 7 winners to rescue 2). The capture engine's asymmetry protects even bad dips; differentiation's value, if any, is in scratch-on-bounce mechanics (R3, J gates) or as Part-B context - not in deeper reclaim exits. | T-SR08 | the loss-side map complete |
| F-32 | M8 WORKS WHERE TARGETS WERE SPARSE (T-MG28): family-edge capture targets lift the G2 line mechanism-primary (G2-4: twin +143.6, 5/6 months, per-trade +0.27->+0.34, pooled +46%; G2-6: twin +165.2, pooled +61%) because M7's multi-day-level targets were often absent beyond 8 pts - while the SAME change is a wash on RWY (twin -3.9), whose selection already guarantees a reachable edge. Sensitivity monotone up in D_min (brake-zone exclusion earns its keep; D=3.0 twin +188.2, 6/6 - plateau, not adopted). The two-line split is the mechanism showing itself: targets help exactly where they were missing. TRAINING-ONLY; judge = D-8. | T-MG28 | capture targets completed |
| F-33 | M8 RE-EXPLAINED - THE ARM LEVEL WAS THE VARIABLE (T-MG29, J's simplicity challenge): a fixed trailing arm (peak>=1.5 arms, exit peak-0.75, no targets at all) matches/beats M8 twin-for-twin (+173.4 vs +143.6, both 5/6). Family edges worked only by implying a lower, more frequent arm; the vocabulary itself adds nothing to exits. Arm-window widening alone does nothing (+5.8 - distant levels arm too high); longer stalls hurt. CORRECTS F-32's mechanism story (the G2-line numbers stand; the explanation changes). Parsimony: proposed M9 = trail-arm management (A plateau 1.5-2.0), one constant, resolver-free, Pine-trivial. The second time a J challenge replaced a complex mechanism with a simpler true one (cf. T-SR03 null). | T-MG29 | the dial behind M8 |
| F-34 | THE QUIET MARKET IS HIS MARKET AND OURS (T-EN116): the identical 4A-v3 trigger moved from news windows to quiet RTH catches 150/151 of his quiet entries and triples the book (+3689 x M7 / +5728 x M9, all six months positive, extras huge). Family regime-dependence: SHD/WRB/GAP earn quietly (+0.24/+0.27/+0.16) while SQZ/W20 - the news-window champions - collapse to +0.09; PDY toxic quietly. Per-trade sits at the +0.19/+0.24 (M7/M9) boundary of the flag line. F-24's census is now a trading result, not a description. | T-EN116 | the quiet unlock |
| F-35 | THE RUNWAY LAW (T-EN117): the frozen [2,8] runway gate roughly DOUBLES per-trade on EVERY universe it touches - surgical (+0.63->+1.54), quiet volume (+0.24->+0.51), news-window volume (+0.27->+0.52), M7-quiet (+0.19->+0.38) - four universes, one frozen constant, zero re-fitting. The program's first transferable selection law. Cost is catch (150->88 quiet): precision serves Track 2 at Track 1's expense, both recorded. The lower bound (brake-zone exclusion) does the work; the upper bound is inert. PDY's quiet toxicity vanishes under the gate. | T-EN117 | the selection law |
| F-36 | THE STAMP DEFECT (T-RH01 anatomy): resolver zigzag pivots and squeeze episodes were born-stamped at the closing bar's OPEN, not its CLOSE - a bounded <=59s early-visibility lookahead in every resolver-fed edge since the family machinery shipped. Found ONLY by the mechanical R-1 harness after reasoning had twice declared the path clean. Fixed at source (+60s); fixed code harness-certified 0/240. All resolver-fed baselines stale pending re-mint; 5W/EN-03 line unaffected. The lesson is structural: comp-stamp conventions are now a harness-checked contract, never an assumption. | T-RH01 | the stamp fix |
| F-37 | THE RUNWAY EFFECT, CORRECTED (T-RH02, supersedes F-35): under fixed stamps the frozen [2,8] gate lifts per-trade ~1.5x on the surgical line (+0.63 -> +0.93; deeper band [3,8] +1.36), ~1.2-1.5x on the quiet lines, and ~nothing on the news line. The original ~2x was partly the stamp defect: just-born edges sit near price, so early sight let the gate key on structure-formation moments. Still the only working selection mechanism; materially smaller than first registered. Catch costs unchanged in kind. | T-RH02 | the law, corrected |
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
| D-5 | 1+2 | all | G3 quiet-market cycle | F-24 grammar | T-EN116 run | DONE PENDING J-VERDICT (catch 150/151; M7 cell partial on per-trade +0.19 and PDY toxic-flag; M9 secondary passes all lines - J decides registration shape; F-34) |
| D-6 | 1+2 | G2/G3 | Deep book round: event-level MBP-10 (which-signal flow thread; exit remainder; G3 features; fade features) | per-second book exhausted; drive holds 3.3G windowed | drive connected | FULLY DONE (T-BK02 F-17; T-BK03 F-19 + complete G3 bank + 1,541-approach universe). Drive no longer required - all extractions banked in repo |
| D-7 | 2 | - | Lane regime complementarity (first-break vs retest by condition) | 2 observations only | more G2-4 months | QUEUED (parked) |
| D-8 | - | - | Purchase 1-2 fresh months = next clean quarantine (now judges: G2-6, Strategy 5/5W, D-29/D-30 results, dormant ride-alongs) | the single validation event for everything TRAINING-ONLY | J purchase; TWO-STAGE option: stage 1 flow-only (1s+tbbo, small download) judges the whole Tier-P line; stage 2 MBP-10 depth (large download) judges the Tier-R line later. Months must be his-journal-covered so catch stays measurable | DEFERRED (J, 2026-11-27: download constraint); spec can be written before purchase; FAILURE-AUTOPSY RULE (J, 2026-11-27): when a TRAINING-ONLY claim fails on fresh months, the autopsy must separate MECHANISM failure from PARAMETER-TRANSFER failure (a constant like A=1.5 mis-calibrated for the new regime is an adapter problem, not a dead mechanism - R-10 applies before any DEAD verdict) |
| D-9 | mixed | - | Small parked items: re-entry after stop; regime-conditioned M7; role-flip levels v2; 3m/5m bar anatomy; 3C/3D traded P&L; unique trade_key; M4C-180 revisit; M11 WRB-projection variant | individually small (BACKLOG.md holds detail) | - | QUEUED |
| D-10 | 1 | G2 | tier20 candidate shapes (engagement prior / tier-based size split) | T-EN112 finding now SPLIT OOS (T-VL04) - open question | more months before any shape is testable | QUEUED (parked) |
| D-11 | 1 | all | Edge-coverage expansion: his UNMATCHED entries | hard ceiling on catch | anatomy + spec'd strategy | DONE (T-EN114 anatomy -> T-EN115 G2-6 REGISTERED TRAINING-ONLY: catch 59/62, +1659.0/six months, per-trade held at +0.27; F-23/F-25; judge = D-8) |
| D-12 | 1 | G1,G4-G6 | Remaining groups of record after G3 | unmined behavior | after D-5 | QUEUED |
| D-13 | 2 | - | Scale-outs vs single exits (he scales; we model single) | old simplification note; matters at size | - | QUEUED |
| D-24 | 2 | - | M14 management round: (a) early-adverse exit DONE-REJECTED (T-MG23, F-15); (b) regime-conditioned stall DONE-REJECTED but PRESERVED (T-MG24; helped the weakest month +50 vs +39 - revisit only under a future regime framework); (c) spike-reach DONE-IMMATERIAL (T-MG25: binds 1-2x per 4 months, all positive; T-MG14 boundary flag resolved; M7 kept for parsimony); (d) invalidation exit DONE-IMMATERIAL (T-MG26: the stall already does it faster; J's instinct confirmed as embedded) | F-2/F-3 | mechanism-primary per R-9 | CLOSED (F-16) |
| D-25 | 2 | - | SURGICAL standalone strategy: entries designed from the F-1..F-4 profile (level-approach in active tape) - J's "more surgical trade entry/management at a later point" | the earner profile | S-1 REGISTERED TRAINING-ONLY (T-SR01: all lines pass; in-sample by construction; judge = future depth purchase). Strategy 5W (wide variant) SAVED per J (TRAINING-ONLY); fade variant = possible Strategy 6, J gates. Naming folded into Strategy-N family | PART 1 DONE |
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

| D-27 | 1+2 | - | SENSITIVITY AUDIT of arbitrary load-bearing constants (TTL 300, dedupe 300, give-back 0.75, arm floor 0.5, stop upward, cap 480, Wseq 600, OFI window 30s, T-BK03 outcome thresholds): perturb +-50% one at a time, flag knife-edges, change nothing - robustness check, NOT optimization (F-11-compatible) | J's ranges directive | R-9 controls | DONE (T-SA01: no knife-edges; dedupe flagged SENSITIVE; F-20) |
| D-28 | 2 | - | ENTRY-SIDE BOOK LENSES never examined: (a) book dynamics AT THE FILL moment (the live decision second - all prior tests measured at cross/pre-approach), (b) the touch reaction at levels (first seconds of book meeting level, T-BK03's stated open lens). Scoped as D-25 design input per F-18 | J's entry-focus audit | drive data banked | DONE (T-BK04: touch-reaction discriminator found at 3s - F-21; D-25 foundation complete) |

| D-29 | 2 | - | BUILD M8: capture targets widened to family edges (D_min 2.0, F-28 brake zone) | F-7/F-23..26/F-28 | mechanism-primary both lines | DONE (T-MG28, F-32: G2 line ADOPT-AS-CANDIDATE - J gates naming/adoption; S5 line REJECTED-wash; D gradient monotone up, noted not chased) |
| D-29b | 2 | - | Ablation controls for M8 (J's challenge: can M7's dials reproduce it?) | parsimony discipline | frozen match-criterion | DONE (T-MG29, F-33: fixed-trail A=1.5 matches M8 - simpler dial wins; M9 proposed, J gates re-basing of G2-7/G2-8) |
| D-30 | 2 | - | S5-MF Part A + Part B (3s read) | F-24/F-21 | full pipeline | DONE (Part A T-SR02; Part B T-SR06: extraction 35/35 + bit-exact cert; 3s read fails on the full universe, adds +0.45/trade stacked on RWY - facts to J) |
| D-31 | 2 | - | 5W full-RTH anatomy: six-lens decomposition + frozen promotion rule (can +0.63 get surgical from 1s-visible data?) | T-SR02's sleeper observation (selection disclosed in spec) | BH q=0.10, both-months, promotion rule frozen pre-look | DONE (T-SR03: NULL - zero qualifiers; F-27; upgrade path = Part B book read) |
| D-32 | 2 | - | Structural selectors for the surgical line (F-7/F-23..26 vocabulary: runway, confluence, backstop, range position) + the runway selector run constructively | J's push: T-SR03 had not incorporated F-23..26; exit anatomy showed stops are the whole deficit | frozen promotion rule; constructive re-run per T-MG21 lesson | DONE (T-SR04 FINDING + T-SR05 ALL LINES PASS: 5W-RWY TRAINING-ONLY; F-28/F-29) |
| D-33 | 2 | - | Loss-side management for the surgical line: (R1) failed-break exit DONE-REJECTED (T-SR07, F-30); (R2) reclaim anatomy + flow-conditioned exit DONE (T-SR08, F-31: differentiators found - time + prior-MFE - but breakeven arithmetic blocks all reclaim-price exits; FCR rejected); (R3) scratch-on-bounce PARKED-AS-TOOL (J, 2026-11-27: too much conditional machinery for the payoff now; kept on record for a later refinement-phase management plan); (R4) S5 constants ranges audit - QUEUED, R-1 harness pass OWED first | stops are 31% of RWY | mechanism-primary; R-11/R-12 | R1-R2 DONE; R3 PARKED (tool); R4 QUEUED |

OPEN DECISIONS (addressed to J, not work items; append-only too):
| id | decision | since | status |
|---|---|---|---|
| Q-1 | R-1 two-tier evidence amendment (screening on 1m/60mo vs confirmation on per-second) | 2026-11-24 | DECIDED YES (J, 2026-11-28) - amendment landed in STANDING RULES |
| Q-2 | Move CURRENT_STATE.md + _edits to archive/ with stale banner | 2026-11-24 | DECIDED YES (J, 2026-11-28) - archived with stale banner |
| Q-3 | G2-1 / G2-2 disposition: both TRAINING-ONLY under the OLD engine; re-base on fill-time, or retire as superseded by G2-4? | 2026-11-26 | DECIDED (J, 2026-11-28): retire as superseded - G2-1/G2-2 DORMANT |
| Q-4 | Strategy 2A disposition: its entry rules were invalidated (T-EN99 lookahead) and halted; rebuild them, or supersede with G2-4 as the entry feeding the already-built Pine stage-1 infrastructure? | 2026-11-18 halt / surfaced 2026-11-26 | DECIDED (J, 2026-11-28): supersede - G2-4 feeds the Pine stage-1 kit (D-4) |

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
- 2026-11-27: T-EN115 closed. G2-6 (4A-v3 multi-family x M7) run on all six months under R-9 control (both certified pairs exact). All five frozen verdict lines pass -> G2-6 REGISTERED TRAINING-ONLY, Tier-P. F-25 filed. D-11 closed end-to-end. Judge = D-8 purchased months.
- 2026-11-27: R-11 confirmed by J and landed; R-9/R-10 full text landed in STANDING RULES (was referenced-only - doc-sync defect found and fixed). D-29 bumped to MID priority. D-30 (S5-MF) registered. D-8 marked DEFERRED with the two-stage purchase option. GLOSSARY R-series table synced (8 -> 11).
- 2026-11-27: T-SR02 Part A closed. S5-MF (family-edge touches, ANY arm) passes all frozen lines -> TRAINING-ONLY, Tier-R. F-26 filed (volume-not-quality again; LVL-ANY full-RTH +0.63 is the program's per-trade leader). Part B queued on device. mf_touch_moments.csv banked (45,454).
- 2026-11-27: T-SR03 closed on a clean null. 5W full-RTH is flat across every 1s-visible lens (F-27); capture exits carry the book; surgical upgrade deferred to D-30 Part B (3s book read). D-31 registered and closed same-day. Trade tables for S1-ANY/5W-full/S5-MF banked as parquets.
- 2026-11-27: D-32 closed end-to-end in one session: T-SR04 structural lenses (F-28: room-to-structure monotone) -> T-SR05 constructive test (F-29: 5W-RWY all lines pass, +1.54/trade, TRAINING-ONLY - the program's per-trade leader and first working selection gate). D-33 registered (loss-side management + S5 constants ranges). J's F-23..26-incorporation push directly produced the breakthrough.
- 2026-11-27 (post-audit): T-SR05 integrity audit on J's challenge: month-balanced (49/53 trades, +1.61/+1.48), NOT tail-driven (median trade +2.12, top-decile 46% of net vs the program's usual ~190%), no busy-reshuffle artifact (92/102 trades identical to baseline, 0 same-fill-pnl-drift, 10 cleanly busy-freed), 28 days traded with best day 17% of net and 5 negative days. OWED under R-1: a formal truncation-harness pass on the runway feature code (knowability currently rests on comp-gating + the T-EN115 minute-alignment check, not the mechanical harness) - attached to D-33 preconditions.
- 2026-11-27: R-12 (findings sweep) confirmed by J and landed. M8 named (D-29's content): capture targets -> family edges; S5-line variant targets the runway edge. Device confirmed available for compute (no large downloads) -> D-30 Part B unblocked via moment-targeted extraction.
- 2026-11-27: T-SR07 closed - failed-break exit REJECTED on mechanism accounting (F-30: the S5 stop is efficient; retest-dips are part of the pattern). D-33 R2 (constants ranges) queued. Device link dropped mid-T-SR06 extraction (session-side); extractor and state safe on the drive, resumes on relink.
- 2026-11-27: T-SR08 closed. FCR rejected; F-31 filed - the dips that die ARE identifiable (time-to-reclaim, prior-MFE; BH p~0 both months) but no reclaim-price exit clears the breakeven arithmetic (needs >75% stop purity; best cell 70%). J's differentiation question answered quantitatively. R3 (scratch-on-bounce) proposed, J gates. T-SR06 extraction paused at 10/35 days per J; resumes on request.
- 2026-11-27: R3 (scratch-on-bounce) PARKED-AS-TOOL per J - kept for a later refinement-phase management plan, not built now. J's correction logged against F-31's wording: the lenses shift probability, they do not separate in kind - no pure cell exists, which is exactly why no rule clears the arithmetic.
- 2026-11-27: T-MG28 closed. M8 ADOPT-AS-CANDIDATE on the G2 line (twin +143.6, 5/6; pooled +824.8 vs +565.9), REJECTED on the S5 line (wash - RWY already targets structure). F-32 filed. Naming of the M8 combos (4A-v2xM8, 4A-v3xM8) awaits J at the gate per R-3. D-29 closed.
- 2026-11-27: J approved M8 adoption on the G2 line: G2-7 (4A-v2xM8) and G2-8 (4A-v3xM8) minted TRAINING-ONLY, Tier-P; G2-4xM7 remains the sole VALIDATED strategy and the D-4 port target. D_min stays at the frozen 2.0 (gradient noted; D-8 arbitrates). J's simplicity challenge -> T-MG29 ablation round (can M7's own dials reproduce M8's gain?).
- 2026-11-27: T-MG29 closed - J's simplicity challenge vindicated. Fixed trail-arm A=1.5 reproduces M8's entire gain with one constant (F-33 corrects F-32's mechanism story; G2-line numbers unaffected). Proposed M9 (trail-arm management, resolver-free, Pine-trivial); J gates naming + re-basing G2-7/G2-8.
- 2026-11-27: M9 minted per J (trail-arm A=1.5). G2-7/G2-8 re-basing explained to J, awaiting his go; rows unchanged until then.
- 2026-11-27: per J - G2-7 re-based to M9 (constant arm), G2-8 deliberately KEPT on M8 (structure-armed) so D-8 judges constant-vs-structure head-to-head on fresh months; M8 un-superseded, carried by G2-8. J's adapter flag registered on D-8: fresh-month failures get mechanism-vs-calibration autopsies before any DEAD verdict. Exit-side levels remain live in: G2-4xM7 (VALIDATED, level-armed capture), the whole S5 line (level-targeted capture = the P&L engine, T-SR03), and G2-8 (M8). Only G2-7 runs the pure constant.
- 2026-11-27: J's controlled-pair directive: the constant-vs-structure exit question now rides on two IDENTICAL-but-for-the-arm pairs - (G2-7 v2xM9 vs G2-9 v2xM8) and (G2-10 v3xM9 vs G2-8 v3xM8); missing cell run (v3xM9: 8153/+2644.0, twin +139.5, 4/6). R-13 (failure autopsy everywhere) landed. All four combos TRAINING-ONLY to D-8 stage 1.
- 2026-11-27: T-EN116 closed pending J's verdict. Catch 150/151 - the quiet gap closed in training (F-34). Near-miss logged: quiet generation first ran WITHOUT tail families (tag guard); caught by the per-family table, not the controls - R-9 scope lesson (controls must cover every new branch). G3-1 registration shape = J's gate.
- 2026-11-27: J's verdict on T-EN116: record ALL - G3-1 (xM7) and G3-2 (xM9) both minted TRAINING-ONLY for testing and modification. Next per J's precision push: the frozen RWY selector carried onto the volume lines (T-EN117).
- 2026-11-27: T-EN117 closed - the runway selector generalizes (F-35: ~2x per-trade on all four universes, band carried frozen). G3-2-RWY passes all lines -> QUALITY-VARIANT, J gates naming (proposed G3-3). D-5b DONE.
- 2026-11-27: per J's record-all: G3-3 (G3-2+RWY), G3-4 (G3-1+RWY), G2-11 (G2-6+RWY) minted TRAINING-ONLY. RWYLAW_TABLE appendix added (by-month breakdown of all four runway pairs). Fill-vs-cross gating quantified: median delay 99s - exact live replication possible in the Python runner (per-second order pull), Pine approximates at bar granularity; limitation restated accurately.
- 2026-11-27: TAXONOMY BUILD (J-approved Option A+B): SYSTEMS_MATRIX.md created - 16 components (EN-01..06, FL-WIN/QT/ALL/RWY/3S/CAD, MP-7..10), 19 systems as formulas, industry terms locked, M10 minted (the S5 organism). taxonomy_audit.py wired into R-8; audit PASS. Nothing renamed - formulas are additive; legacy names canonical forever.
- 2026-11-27: historical anchors upgraded to live files (b5_validation/b2_entry_rule/cd_round - nothing was actually lost; all era runners are committed code). scripts/preflight.py created as THE single pre-present command (taxonomy hard-fail + advisories); it immediately caught two docs missing from DOCUMENT_MAP. CLAUDE.md addition proposed per Rule 5 (J commits).
- 2026-11-27: CLAUDE.md CREATED for this repo per J's approval (discovery: tslwrb-study had none - the auto-loaded instructions came from the other project). Boot order + preflight + lineage convention now guaranteed-read at every future session start.
- 2026-11-28: DOC-SYNC SWEEP (J's governance double-check): three drifts found and fixed (VALIDATION_PLAN missing the two-stage D-8 + R-13; RESULTS_DISPLAY_STANDARD missing the month-level rule; PLAIN_MAP missing the quiet/runway/taxonomy story). FOURTH finding, the serious one: ASSETS.md is a GENERATED file and had silently clobbered hand-appended banked-artifact rows during a preflight regeneration - fixed structurally: the generator now scans Tests/** itself (nothing hand-maintained left in ASSETS.md). OVERVIEW_TREE's systems section is now GENERATED from SYSTEMS_MATRIX (gen_overview_systems.py) with a HARD preflight sync check - hand drift there is no longer possible.
- 2026-11-28: DATA_LEDGER.md created per J (anti-burn ledger): per-month holdings x designation, tier validation needs, and the D-8 purchase recommendation (2022-05 + 2026-03, stage-1 tbbo+bbo-1s, stage-2 mbp-10; alternates 2022-03/2025-03). Grounded in his-archive activity density, not guesswork. J gates the purchase.

## THE GOVERNANCE SWEEP PROMPT (canonical copy, v2.0, 2026-11-28)
J pastes this periodically; this copy is the versioned original.
---
GOVERNANCE SWEEP. All hats on. Work through every step, show one
line of evidence each, fix what is mechanical, bring judgment calls
to me. Do not start new research in this sweep.
1. MECHANICAL: run python3 scripts/preflight.py - must PASS
   (taxonomy, overview-systems sync, doc coverage). Paste the tail.
2. REGISTRIES: every system/component/management born since the
   last sweep has, in the same commit: GLOSSARY row, SYSTEMS_MATRIX
   formula + implementation anchor, BACKTEST_MATRIX entry, roadmap
   D-id, change-log line. Name any that do not.
3. DATA DISCIPLINE: DATA_LEDGER designations match reality (no
   month used beyond its designation; every spec since last sweep
   has R-11 and R-12 sections). Name violations.
4. DRIFT: diff the story across MASTER_PROGRAM / OVERVIEW_TREE /
   PLAIN_MAP / VALIDATION_PLAN - any contradiction, stale status,
   or missing recent event. Check the generated docs regenerated
   cleanly (ASSETS, tree systems).
5. DEBTS: list everything OWED (R-1 harness passes, D-18 vectors,
   Part B state, pending Q-decisions) with age. Nothing silently
   dropped.
6. RESULTS HYGIENE: spot-check the two most recent reports against
   RESULTS_DISPLAY_STANDARD (month-level breakdowns present;
   mechanism-primary verdicts; controls stated).
7. LANGUAGE: confirm closed vocabularies only (status words, R-ids,
   component ids); flag any new informal term that needs a GLOSSARY
   row or retirement.
8. VERDICT: one line - CLEAN or N issues (listed, each tagged
   FIXED / PROPOSED-TO-J). Then stop.
---
- 2026-11-28: T-RH01 R-1 HARNESS FAIL on FL-RWY - 14/240 mismatches, both directions; poison arm proves sensitivity. 5W-RWY, G2-11, G3-3, G3-4 and F-35 under INTEGRITY-HOLD pending anatomy (R-10). Preliminary signature: month-global resolver construction (future-dependent object selection behind honest-looking comp stamps). Scope may extend to EN-02 triggers - anatomy decides. THE HARNESS DEBT WAS REAL: reasoning said clean, the mechanical gate said otherwise.
- 2026-11-28: T-RH01 anatomy complete in-session: one defect class (open-vs-close stamps), fixed at source, harness v3 = 0/240 on fixed code (F-36). Baseline RE-MINT launched: all resolver-fed candidates regenerating under fixed stamps (parts_v2); OLD-vs-NEW tables next; integrity-holds stay until then. G2-4's validation re-derivation included. 5W line unaffected.
- 2026-11-28: T-RH02 re-mint complete, same day as the defect was found. Survivors: G2-4 VALIDATION STANDS (+158.0 OOS vs +158.1), all catch results unchanged, quiet lines improve, M9 strengthens. Casualties: the RWY-gated cells (F-35 superseded by F-37; 5W-RWY +0.93, G2-11 no lift). Verdict proposals to J in chat; holds lift on his word. Runner assert re-pointing to new baselines = mechanical task queued.
- 2026-11-28: REFRESH (J confirmed, with his amendments: G2-11 and G3-4 KEPT TRAINING-ONLY for validation): all baselines re-pointed to T-RH02 numbers in GLOSSARY and SYSTEMS_MATRIX; integrity-holds LIFTED; parts_v2 promoted to canonical (old-stamp parts archived). Unattended queue running per J: assert re-pointing, artifact regeneration, correction notes, T-SR07/08 re-checks, Part B extraction resume, closing governance sweep.
- 2026-11-28: T-SR07-v2/T-SR08-v2 re-checks: both loss-side rejections and F-31's findings SURVIVE on the corrected universe. DATA_LEDGER event log + PLAIN_MAP plain-words account added. Queue continues: Part B extraction resuming on the drive (J pre-authorized).
- 2026-11-28: D-30 PART B EXTRACTION COMPLETE (35/35 days, device; J pre-authorized drive access). Concat 1,264 moments; OVERLAP CERT bit-exact (0 mismatches, 691 moments x 4 features) - raw path == certified windowed path. rwy_features.parquet banked + checksummed. T-SR06 cells next; RWY-cell verdict line is stale post-F-36 (facts to J).
- 2026-11-28: T-SR06 closed - Part B complete end-to-end. The 3s read does NOT generalize to the full touch universe (+0.58 vs +0.63) but STACKS on RWY (+0.93 -> +1.38 on 58 trades, balanced months). Registration = J's gate. D-30 fully closed.
- 2026-11-28: J's decisions executed: 5W-RWY-3S REGISTERED (T-SR06 stack, +1.38/58, Tier-R TRAINING-ONLY); Q-1 R-1a landed; Q-2 CURRENT_STATE docs archived; Q-3 G2-1/G2-2 DORMANT (superseded); Q-4 Strategy 2A SUPERSEDED by G2-4 for the Pine plan. Q register cleared. Clarification logged: G3-3's 'drop' = the stamp-fix re-measure (+1944->+1412), not a status change - it remains TRAINING-ONLY and a refinement candidate.
