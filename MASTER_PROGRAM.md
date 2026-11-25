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
Track A: A1 LIVING v1.5 | A5 gap autopsy QUEUED (after B4, pending J) | A2.1 T-IM40 | A2.2 T-IM41 | A2.3 T-IM42/43 |
A3 T-IM44/45 + GROUPS OF RECORD (approved) | A4 T-IM46 (G2 top).
Track B: B0 = G2 (J confirmed) | B1 T-IM47 | B2 T-EN103 (entries only;
variants 'none' and 'move+flow' carried) | B3 management pairing = NEXT
| B4 joint unit test | B5 quarantined validation untouched.
Standing: fees ~0 for J's account (J, 2026-11-25) - cost caveats out of
the model by instruction; execution realism still priced at B4.

## CHANGE LOG
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
