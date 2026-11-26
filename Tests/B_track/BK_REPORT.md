# BK REPORT — BOOK LENS ON WHICH-SIGNAL (T-EN111)
STATUS: CLOSED | 2026-11-26 | Spec: BK_SPEC.md (committed first) | study only | data: per-second book from J's drive (MBP-10 reductions)

Episodes: 21 multi-cross with full book coverage (paired analysis; 0 dropped for missing book seconds), 29 single-cross, 12 unmatched.

Book coverage: 0 crosses without a book second within 5s (dropped, listed not hidden). All features are market-state -> valid in the paired design (no monotone-in-time artifact possible).

## PAIRED TEST: TAKEN CROSS vs ITS PASSED SIBLINGS (within-episode permutation, 10,000 draws)
| feature | taken med | passed med | direction | perm p | verdict (alpha .0071 / .05) |
|---|---|---|---|---|---|
| opp0 | 31.00 | 19.50 | taken HIGHER | 0.4692 | null |
| opp10 | 620.00 | 566.50 | taken HIGHER | 0.5656 | null |
| own0 | 22.00 | 13.00 | taken HIGHER | 0.0394 | suggestive |
| imb0 | -0.09 | -0.21 | taken HIGHER | 0.2838 | null |
| imb10 | -0.02 | -0.07 | taken HIGHER | 0.5032 | null |
| d30_opp0 | 5.00 | 1.00 | taken HIGHER | 0.7670 | null |
| depth_tot | 1259.00 | 1019.00 | taken HIGHER | 0.2374 | null |

Power note: ~21 paired episodes; only large effects can clear the adjusted alpha.
Registry: T-EN111.

## READING
- One suggestive result, parked per the frozen line: own0 — the
  SUPPORTING side's top-of-book size (bid for his longs, ask for his
  shorts) is larger at the crosses he took (med 22) than at the ones
  he passed (med 13), p=0.039 — below .05, above the Bonferroni bar.
  It points the same way as T-EN109's flow direction (taken crosses
  sit on positive aggressor flow): buyers present AND bid stacked
  when he fires. Two same-direction suggestives at n=21 are still
  not a finding; own0 goes to BACKLOG for a validation-months-only
  retest.
- The resistance story is dead at this resolution: the broken side
  (opp0/opp10) is NOT thinner at his taken crosses — if anything
  both sides are bigger (depth_tot higher, null). He is not simply
  picking moments when the wall is gone.
- What this resolution cannot see: intra-second queue dynamics
  (pulling, spoof-fades, iceberg refills) — the per-second
  last-snapshot reduction averages those away. That is the remaining
  book lane and it needs the event-level MBP-10 (on the drive, 2.1G
  + 1.2G windowed), a separate spec'd round if J orders it.
