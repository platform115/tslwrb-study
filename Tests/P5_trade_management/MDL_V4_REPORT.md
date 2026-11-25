# MDL V4 REPORT — SCALING x BREAK-HANDLING GRID (T-IM52)
STATUS: CLOSED | 2026-11-26 | Spec: MDL v4 addendum (committed first)

| tolerance | break rule | recovery (actions-only) | levels/day | G2 coverage (level ahead) |
|---|---|---|---|---|
| fixed2.0 | kill | 879/1416 (62%) | 12 | 44/62 |
| fixed2.0 | persist | 1415/1416 (100%) | 99 | 56/62 |
| 0.04% | kill | 866/1416 (61%) | 17 | 45/62 |
| 0.04% | persist | 1415/1416 (100%) | 81 | 57/62 |
| 0.06% | kill | 758/1416 (54%) | 9 | 44/62 |
| 0.06% | persist | 1400/1416 (99%) | 51 | 57/62 |

Registry: T-IM52. Winner goes to the M7-scaled stage-1/joint rerun under the frozen bars.

## RESOLUTION CELL (persist at matched density, pre-registered)
persist + top-12 pruning (12 levels/day, equal to kill's density):
recovery 667/1,416 (47%) | G2 coverage 30/62.
VERDICT: at EQUAL density the kill rule WINS on both metrics (62%/44
vs 47%/30) - deleting broken levels frees the daily budget for live
ones; persistence's apparent advantage was pure density saturation.
Combined v4 verdict: (1) percentage scaling does not improve recovery
(fixed 2.0 stands); (2) blanket persistence hurts at fair density (kill
stands). The shipped config (fixed 2.0 / kill / ~12 levels/day) SURVIVES
both pre-registered challenges. The 18-trade coverage gap stands as a
structural limit of this version; role-flip in a smarter, fresher form
remains a backlog idea, not a free win.
