# A2.2 SPEC — THE MEASUREMENT TABLE (pre-registered; frozen at run)
STATUS: FROZEN at run (J approved with window check) | 2026-11-24 | Track A step A2.2 | Registry: T-IM41
Months: training only (2025-10, 2022-02). Rows: 315 trades + matched nulls.

## PURPOSE (plain)
Measure EVERYTHING we have built, at every one of his training-month
entries and at matched ordinary moments, into one table. No verdicts
here - this is the raw material A3 groups and A4 ranks. Measure first,
then look for relationships (J's standing correction).

## ROWS
- His 315 trades (ground-truth table T-IM40). The 8 Feb-28 trades stay
  as rows; their per-second features are honestly NaN (no data).
- 10 matched null moments per verified trade: same session, same 30-min
  time-of-day band, at least 10 min from ANY of his entries, drawn with
  fixed seed 113. Nulls carry the trade's direction so signed features
  compare like with like (S6.1 discipline).

## COLUMNS (all computable from data at or before the moment, R-1)
1. THE FULL BATTERY (p6_0, harness-certified): ~45 measures - moves,
   ranges, compression, tape volatility, volume rates/ratios, signed
   flow, bursts, stall, day structure, session scale, signal state.
2. STRUCTURE STATE (resolver + p6_24 interaction logic): per family
   (reaction edges 15m, squeeze 15m, gaps 5m, shadows 5m): interacted
   now yes/no, distance to nearest interacted edge, distance to nearest
   edge of the family regardless of interaction.
3. KME EXPANDED (cheap new fields, approved family rank 3): minutes
   since last event, inside-45-min flag, window phase (0-5 vs 5-45 min),
   latest event name, SURPRISE = actual vs forecast parsed to numbers
   where the calendar strings allow (%, K/M/B suffixes), NaN where not -
   parse coverage reported, never guessed.

## SELF-CHECK AMENDMENTS (before run, 2026-11-24, per J)
- WINDOWS vs HIS TIMESCALE: ladder spans 8s-30min trailing from the
  moment, dense at the short end - matches his measured behavior (hold
  ~183s median, stall clock 30s, burst scale 8s). Nothing reads prior
  days EXCEPT Cday/Rest (session-scale yardstick from prior sessions).
  Both carry a prior_session_derived flag so grouping can exclude them;
  rng1800 is the intraday-only alternative in the same table.
- FRESHNESS GUARD: if the latest per-second datum is more than 5s older
  than the moment (data gap), features are NaN - never silently computed
  from stale prices.
- NULL FALLBACK: if a 30-min band has fewer than 10 eligible seconds
  (busy cluster days), widen to the surrounding 2 hours; fallback count
  reported.
- KME name/surprise come from the calendar row matching the certified
  event time (within 1s); no match = NaN, reported.

## HARNESS (the A2 extension, with the self-test folded in as agreed)
Before results count: (a) at 40 sampled trade-moments, recompute every
column from truncated arrays - any difference fails; (b) PLANTED-BUG
test: two deliberate lookahead bugs injected into a throwaway copy
(a feature reading one second ahead; a bar-containing-t read) - the
check must catch both, or the harness itself fails (test the test).

## OUT OF SCOPE HERE
New feature families (recent-bars/level-story, talk->trade) = A2.3.
Any selection, grouping, or verdict = A3/A4. Validation months = never.

## OUTPUT
Data/inputs/a2_features.parquet (one row per trade and per null, "who"
column) + checksum + registry row + a short report showing, per feature,
his-vs-null distribution quantiles with Mann-Whitney flag-lines
(Benjamini-Hochberg corrected) - provisional flags, never gates (R-4).
