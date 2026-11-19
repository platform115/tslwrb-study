# Trade Management Phase — Charter
> User-set ground rules, 2026-11-18. Governs all management/exit work.
> Same discipline as the entry phase: training months only until the user
> authorizes validation; derive numbers from measurements; registry row per
> test; run-over-run baselines; propose-then-confirm decisions.

## M0 — the frozen incumbent (DO NOT MODIFY)
The current exit stack (the "v11 sketch": pt-ladder targets, trail, fast-fail
reversal, time stop, session close) is hereby FROZEN and NAMED **M0**.
- It has been the placeholder through all entry testing on training AND
  validation data and "isn't terrible" — it stays exactly as is, as the
  permanent control baseline every new management candidate must beat.
- New management work starts FRESH from evidence, the way Strategy 2's
  entries started fresh after the v10/v11 10-condition reset. No tweaking M0.

## Structure
- AT LEAST TWO management strategies will be developed in parallel: start
  with one, develop at least one additional; kill it later or keep it —
  the data decides. (Mirrors the 2A/2B experience.)
- RTH vs ETH: measure first, split only if the measurements differ — but a
  separate ETH management stack is expected as plausible, not resisted.
- Working draft of exit TYPES (user: "maybe too little or too much, unsure"
  — to be revised by evidence): (1) targets, (2) loss cutting,
  (3) ditching non-movers.

## Work plan
1. EXCURSION ANATOMY first (confirmed foundation): per-second MFE/MAE after
   every 2A fire (then 2B) on training months — how far in favor before
   1/2/3 pts against, time to favorable peak, decay after peak; every
   measurement split RTH vs overnight fires. The overnight entry baseline is
   refreshed under the current 2A stack as part of this.
   HONEST SCOPE (user correction): this replaces guessing about general /
   average behavior — idea generation, variable testing, and adaptation
   rules still follow, exactly as in the entry phase.
2. LEVEL HYPOTHESIS next, before any parameter tuning (standing user flag):
   do favorable excursions stall at WRB boundaries / KME zones? Entry found
   levels select nothing; the hypothesis is they govern everything once a
   trade is on.
3. USER IDEA LIST (to be tested in the candidate phase):
   - "Relative reverse" of entry conditions: exit mechanisms built from the
     same measurement families as the entries (burst/thrust-like), with
     their own adaptations and thresholds, pointed at exits.
   - WRB pt testing - MECHANISM CORRECTED by user 2026-11-18: his
     pt1/pt2/pt3 are SEQUENTIAL SAME-DIRECTION WRBs OCCURRING during the
     trade (hold while they keep forming; 1st new WRB = pt1, 2nd = pt2,
     3rd = pt3) - an event count / progress clock, NOT static price levels
     from prior WRBs ("he's not looking at where they are in relation to
     previous WRBs... at least rarely"). M0's size-based pt ladder (uref
     multiples) is an approximation, not this mechanism. T-EX04's
     level-geometry test does not bear on this.

## Parked entry items (address during breaks from management work)
1. Wire the burst-window rule live (code currently fixed 8s).
2. 2B trailing-pct coefficient adapter (user priority note stands).
3. 2B live form (trailing 14 sessions) vs tested form — one equivalence check.
4. Overnight entry variant re-run under current 2A stack (folded into
   Work plan step 1).

## Data budget
Training months only for development. Reserved months (read 8x in the entry
phase) used only on user authorization. User is acquiring additional data
during this phase. Purchase months stay sealed until entries + management
are frozen together.

## Decisions appended 2026-11-18 (user)
- Taxonomy: MECHANISM-ONLY (targets / loss-cutting / ditching). The state
  framing is dropped as overcomplication; the anatomy evidence simply
  informs which mechanisms have a constituency.
- Timescale: management's natural units are minutes (T-EX02 peak times),
  but the DOOR STAYS OPEN for seconds-precision "move is done" detection
  (the entry phase's drift/flow machinery pointed at exits).
- Non-mover check verified across windows (not just 10 min): RTH fires
  never fail to move 1 pt at ANY window 3-20 min (0% both months); at
  +/-1.5pt only 0-4% at 3 min. OVERNIGHT non-movers are real at short
  windows (8-17% never move 1 pt in 3 min; 4% never 1.5 pt in 20 min).
  The ditch mechanism is an ETH mechanism on this evidence.
- RTH vs ETH: ONE management design in session-scaled units (R_est-style),
  instantiated and frozen as TWO configs (operationally two strategies,
  structurally one design). Revisit if later measurements break the
  same-shape finding.
- REPORTING RULE: REALISTIC, biased in neither direction (user
  clarification 2026-11-18). (a) De-overlap clustered fires (one path per
  episode) for any number used in decisions - this corrects a known
  double-count, it is accuracy, not pessimism. (b) Where fills matter,
  BRACKET reality: show mid (slightly optimistic) and 1-tick-against
  (slightly pessimistic) side by side; the truth sits between. Never
  discount numbers one-sidedly in either direction.

## Post-T-EX07 direction (user, 2026-11-18)
Structural change confirmed as the path (trail tuning rejected - T-EX07).
- #1 MEASURED MOVE-DEATH EXIT: active design discussion first (variables,
  adapters), then derivation, then trade sim.
- RE-ENTRY after profit-protect exits: wanted SOON, after the basics are
  scripted and running. User note: continuation may already be captured as a
  new 2A/2B fire; where momentum is lower a DIFFERENT re-entry trigger may
  be needed - parked as its own design question.
- SCALE-OUT: necessary eventually, too early now - 1-contract trades are
  the norm for a while.

## M2 slot resolved + phase pause (user, 2026-11-18)
- The "at least two management strategies" requirement was INTENDED as
  RTH + ETH coverage - achieved inside M1 (one design, two session configs,
  T-EX13). No separate M2 design is required.
- The remaining structural candidates (flow-death exit, opposite-burst,
  the C3b full-capture profile) are PAUSED pending the Pine detector work.
- PRIORITY DELIVERABLE NEXT (user): the rigid, translation-ready rule spec
  (Python-exact definitions + golden test vectors) for the Pine agent -
  entries first; M1's spec follows once validated.
- M1 stands at: stall clock (S inside the session's measured alive-gap band:
  30s RTH / 90s ETH) + session close + inert rails. NOT yet validated on
  reserved months - awaiting user authorization.

## M1 ADOPTED (user decision 2026-11-18, post-T-EX14)
M1 replaces M0 as the working management. Grounds stated honestly: RTH
totals parity (not superiority) with materially better risk (win 79% vs 74%,
avg loss -0.93 vs -1.62, DD 0 vs 3.0), overnight +28% with 1/5 the DD, and
a 3-rule implementation suited to translation. M0 remains frozen as the
historical control. User note: M0 was created under a less optimal research
plan. Purchase months remain the final judge.

## STANDING GATE added 2026-11-19 (post-T-EN99): THE TRUNCATION HARNESS
Tests/P0_audit/truncation_harness.py - mechanical lookahead detection: every
signal quantity recomputed on data truncated at its decision second must
match the pipeline's value; exits re-run with post-exit prices poisoned must
reproduce identical outcomes. NO new entry/signal script earns a registry
row until its fire logic passes this harness. First run: all clean
components pass on 300 fire seconds + 150 exits per training month; the
known contaminated thrust is caught 300/300 (sensitivity proven).

## ENTRY REBUILD PROGRAMME (user decision 2026-11-19)
Order: (1) THE IMITATION STUDY, then (2) THE BOUNDED SEARCH (pre-registered
candidate list + stopping rule, drafted for approval after the study).
Names chosen to avoid the A/B collision with strategy names.
User directives for the study:
- WRBs / zones / KMEs return to the mix, with a changed level definition:
  the BORDER AREAS of WRB bodies (bands, not exact prices), and only
  (a) levels formed in the CURRENT session, plus (b) older levels whose
  border area price has NEVER traversed between formation and now
  ("virgin" levels). Previous-day levels that price has already crossed
  are out.
- Group his entries LOGICALLY BY TYPE from whatever the data reveals -
  not by solved/unsolved.
- Start with ONE training month.
- Keep it honest, carefully: every feature computed from data at or before
  the entry second; truncation-harness discipline applies.

## ZONE/LEVEL WORK CONSTRAINTS (user, 2026-11-19)
- Resolution tolerance: START WIDE at 2-3 points (user: ~1pt was arbitrary;
  1.25 can be fine depending) - narrowed later BY TESTING, not assumption.
- His chart timeframes: mostly 1m / 3m / 5m (not exclusively) - zone
  construction searches those first.
- RECENCY RULE - the anti-saturation principle: active levels are SAME-DAY
  KMEs and SAME-DAY-OR-MOST-RECENT WRBs "for the most part". Levels are NOT
  valid forever. The failure mode to prevent: "there are levels all over the
  chart" - he watches SPECIFIC ones; the work is finding WHICH.
- Instrument tagging required: he also discusses NQ/VIX/YM - non-ES
  references flagged, never silently mixed in (parser v2 does this).
  NON-ES WORK IS DEFERRED (user): "that's for a later system".
- Prior-day validity (user ruling): (a) re-referenced today, (b) never
  traversed since formation, (c) most-recent-until-replaced are ALL valid
  carriers - PLUS an emphasis criterion: a level remarked as important more
  than once, or even once if emphasised strongly, stays active.
- PROCESS RULE (user): no assumptions - ASK when unsure.
