# M11 REPORT — WHERE HIS EXITS LAND (T-MG18)
STATUS: CLOSED | 2026-11-26 | Spec: M11_SPEC.md (committed first)

Audited exits analyzed: 305 (fast-take subset, <=150s & >1pt: 75).

| target family | exits within 2 ticks | null | ratio | within 1 pt | null | ratio |
|---|---|---|---|---|---|---|
| wrb_proj | 20% | 28% | 0.73x | 30% | 46% | 0.64x |
| mdl_level | 14% | 9% | 1.61x | 23% | 18% | 1.26x |
| intraday_edge | 64% | 68% | 0.93x | 76% | 83% | 0.93x |
| round | 45% | 40% | 1.15x | 87% | 79% | 1.11x |

## FAST-TAKE SUBSET (the pre-placed-limit suspects; within 2 ticks)
- wrb_proj: 33/75
- mdl_level: 12/75
- intraday_edge: 51/75
- round: 32/75

Verdict line: >= 1.5x null = destination evidence. Registry: T-MG18.
