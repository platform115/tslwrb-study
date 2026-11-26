# EX2_SPEC — EXCURSION-MATCHED CONTROL FOR THE imb10 FINDING (T-MG20)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: T-MG19's named confound — his exits sit at favorable price
extremes; duration-matched holds sit mid-path, so a book regularity
at extremes could masquerade as his trigger. This round is the
REQUIRED robustness check before any switch rule exists.

## DESIGN (one change from EX Analysis A, everything else identical)
Controls must now match the case on BOTH:
- duration (by construction, as before), and
- current excursion: control's open profit at that moment within
  max(0.5 pt, 25%) of the case's exit profit, where excursion =
  (mid(t) - entry_price) * side from the per-second mids, and the
  case's exit profit is measured the same way at t_exit (not the
  stated P&L, so both sides of the match use one yardstick).
Up to 3 controls per case; cases with none are counted and dropped
(expected to be many — stated, not hidden).

## WHAT IS JUDGED (frozen)
Only the three survivors of T-MG19 are retested — imb10 (the
FINDING), imb0 and depth_tot (its suggestive neighbors). Alpha:
.0167 (Bonferroni over 3), month consistency required, 10,000
within-case permutations.
- imb10 survives -> the finding stands as HIS signal (not a
  price-extreme artifact); a hold/exit switch backtest vs M7 is
  spec'd to J.
- imb10 dies -> T-MG19's finding is reclassified as a market
  regularity at extremes; the registry row is annotated; no rule.
Registry: T-MG20.
