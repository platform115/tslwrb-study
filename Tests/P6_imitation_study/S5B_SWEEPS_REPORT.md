# S5b — WEAK-KIND SWEEPS + IMPLIED KEY-ZONE TEST (T-IM27)
> Status: AWAITING REVIEW (with S5 gate). Script: p6_20_s5b_improvements.py.
> User direction: reaction and contraction needed more variables; Key-zone
> list derivable through implications.

## A. Reaction — material improvement found: the UNION
Full grid (15 swing cells + 3 pct-zigzag cells + union; all reported):
best singles stay swing 5m N=2 (+40) / N=3 (+41); pct-zigzag 0.08% is
strong on its own (77% hit, +36).
**UNION (swing 5m N=2 OR pct-zigzag 0.08%): 86% hit vs null 48% (+38).**
Coverage of his reaction refs jumps 67% -> 86% (misses 33% -> 14%) with
the gap within noise of the best single. Reading: his "reaction high/low"
is sometimes the N=2 swing, sometimes the last zigzag pivot — two
documented families covering one concept. ADOPTION PROPOSAL: the union.
(Pct-zigzag is scale-adaptive, fixing the regime flaw of point-based
reversal.)

## B. Contraction — no material gap improvement; shorter window ties
12 W x q cells + 2 band variants (all reported). Decision metric
(role-stated subset): W=10 q=0.67 +26 (hit 65%) vs adopted W=15 q=0.67
+25 (hit 59%) — a TIE on gap, better raw coverage at W=10. Close-quantile
band and min-length variants are worse. PROPOSAL: adopt W=10 q=0.67 for
the better coverage, with the disclosed caveat that the gap metric is tied
and the choice rests on the secondary metric; W=15 remains recorded as
equivalent. The contraction family stays the weakest kind — tolerance
stays 3; S6's SEL-C carries the weakness flag.

## C. Implied Key-zone list — FAILED, documented
Naive (every relational ref deposits an anchor at market price,
prior-session-only forward test): +4-5 over null. Recurrence-confirmed
(>=2 distinct prior sessions): +2. Cause: implied anchors ARE market
prices, so the list inherits market geometry by construction — no
separation is possible from this design. VERDICT: implication-derived
lists do not reconstruct his Key-zone list; the stated-price channel
(2x null, T-IM26) remains the only validated one; generated-from-data
zones + tier semantics stay the open problem. S6 SEL-D uses the
stated-price list only.
