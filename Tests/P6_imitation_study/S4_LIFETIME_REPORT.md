# S4 — LEVEL/BAND DB + LIFETIME MEASUREMENT (T-IM24/25)
> Status: AWAITING REVIEW. Scripts: p6_17_s4_emit.py, p6_18_s4_link.py.

## What was built
- Objects table: 3,336,407 objects from all adopted generators + recorded
  rivals, every session his references touch (s4_objects.parquet,
  checksummed, gitignored).
- Links table: every price-anchored ES reference (1,645) linked through its
  kind's ADOPTED selection (7,533 links, ~4.6/ref). A first all-within-
  tolerance run produced ~645 links/ref — saturated, discarded, documented:
  the S3 lesson (selection carries the information) applies to linking too.

## THE LIFETIME ANSWER — the charter tension resolved, both sides right
1. **His NAMED ordinary structures are intraday.** Age at reference,
   through each generator's matcher: hidden gaps median 16 min (q90 44),
   shadows 4–6 min (q90 ~25), reaction swings 23 min (q90 56), squeezes
   10 min (q90 69). When he names a gap / shadow / reaction level /
   squeeze, it formed within the last hour, usually the last ~20 minutes.
   This supports the charter's same-day recency rule — and the user's
   "I haven't observed much of months-long".
2. **Key KME WRB Zones are long-lived maintained objects.** From his OWN
   stated prices (53 priced Key-zone refs, no matching ambiguity):
   12 recurring price clusters; 7 span ≥30 days vs 2.9 ± 1.4 expected from
   market geometry (50-perm null) — 2.4x, z≈2.9. Direct cases: ~3874
   (5 refs over 52 days — the same "I have the 3874.50 as the R area"
   level the G4 anchors flagged), ~3837 (4 refs / 61 days), ~3950
   (3 refs / 120 days). The two longest clusters (358/577 days, 2 refs
   each) are likely coincidence and are not counted as evidence.
   This supports HIS "follow for many months" — for Key zones only.
   => RULE REFINEMENT CONFIRMED (proposed at T-IM13): same-day/most-recent
   applies to ordinary structures; Key KME WRB Zones live on a maintained
   list measured in weeks-to-months.
3. Objects referenced ≥2 times (443): most re-references are same-session;
   compression bands persist longest (median span ~1 day, q90 ~2 weeks
   among multi-referenced ones) — consistent with the G4 anchor misses.

## Arbitration (S3 handoffs)
- G2 D1 vs D2: D2 slightly better on his shadow refs (in-band 70% vs 63%,
  mean dist 0.43 vs 0.52). D2 stays adopted; not decisive.
- G3 siblings: N1/N2/N3 effectively tied (mean dist 1.36/1.32/1.16).
  5m N=2 stays; N=3 noted as marginally closer.
- Full-range vs wick band (G2) and swing vs zigzag (G3): NOT settled by
  linking; needs the behavioral test (does price react at the band?) -
  that is S5/S6 territory.

## Honest limits
- The zone/level-talk linking ("nearest band per family, 30-session
  lookback") does NOT discriminate: all five families land ~equally
  (in-band 99%), so "which generator makes Key zones" stays OPEN. The
  stated-price clustering is the solid Key-zone evidence; band identity of
  Key zones needs his list semantics (color-coded, maintained) modeled in
  S5, likely anchored on the stated-price clusters themselves.
- Priced Key-zone refs n=53; cluster counts are small.
- is_newest/staleness as computed is inflated by construction for specific
  kinds; not used in conclusions.
