# S3 — GENERATOR 2 (Long Upper/Lower Shadow intervals) REPORT (T-IM21)
> Status: CLOSED - OPTION A (user 2026-11-20). D2 + forced most-recent on
> full ranges is the PROVISIONAL G2 selection. Open questions (D1 vs D2,
> full range vs wick band, TF) go to S4 re-reference tracking. Shadows are
> revisited there before anything downstream consumes them.

## Definitions tested (S2-approved, loose first)
Anatomy: upper = high − max(o,c); lower = min(o,c) − low; noise floor
shadow ≥ 0.5 pt [PROJECT CONVENTION]. D1(r): shadow ≥ r × body and ≥
opposite shadow, r ∈ {1.0, 1.5, 2.0}. D2: shadow > each of prior 3 bars'
same-side shadows (WRB-analogy, unsourced — approved to test).
Object: full range [low, high], shadow sub-range kept. TFs 1/2/3/5/15m.

## Findings
1. **Saturation worse than gaps**: 795–1,197 qualifying intervals/session.
   As-stated descriptors: ~60% ambiguous. The D1 ratio barely matters —
   qualification is not the lever; selection is (same lesson as G1).
2. **Forced most-recent** (his dominant phrasing even when a message omits
   it): D2 on 1/2/3/5/15 → **78% identified / 11% ambiguous / 11% miss**,
   fair permutation null 63%, **gap +14%**. D1 r=1.0 → 65%, gap +7%.
   **D2 — the unsourced analogy — beats the documented D1 everywhere.**
3. **Correctness evidence is WEAK (unlike G1)**: consistency only 2/5
   (G1: 5/6); gold-ish refs n=2, both matched to wide 15m intervals, clock
   verification inconclusive ("around 1022am" vs a bar ending 10:15 ET).
   Full-range bands make large intervals catch-alls (price "inside" too
   easily) — a structural bias in the matcher, not proof of correctness.
4. **Sub-range (wick band) matching tested**: coverage drops to 56%
   (gap +12%), consistency still poor (1/3). Does not resolve the question.
5. Caveat on consistency itself: new shadow intervals keep forming
   ("another long shadow interval formed"), so successive references may
   genuinely be to DIFFERENT objects — consistency is a weaker correctness
   proxy for shadows than for gaps.

## Honest verdict
Best candidate: **D2 + forced most-recent on full ranges** (78% coverage,
+14 over fair null). But correctness is NOT established to G1's standard —
no clean clock verifications, weak consistency, and a full-range/15m bias
in the matcher. Which definition (D1/D2), which band (full vs wick), and
which TF his shadow references live on may only be resolvable with S4's
re-reference evidence (does the same interval keep getting referenced and
respected?) rather than more point-in-time calibration.

## Gate options
A. Accept D2+most-recent as the provisional G2 selection (flagged
   provisional), move to G3 (reaction H/L), revisit shadows in S4.
B. Iterate further now (e.g. penalize bandwidth in matching, TF priors).
C. Park shadows until S4 machinery exists; continue with G3/G4.
