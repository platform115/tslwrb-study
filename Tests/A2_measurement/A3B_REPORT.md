# A3B REPORT — GROUPING, CORRECTED ENCODINGS (T-IM45)
STATUS: CLOSED | 2026-11-25 | Spec: A3B_SPEC.md (committed first)

## CHOICE OF k
| k | mean silhouette | per-cluster stability | all >= 0.6? |
|---|---|---|---|
| 2 | 0.20 | 0.63 0.75 | YES |
| 3 | 0.10 | 0.58 0.50 0.40 | no |
| 4 | 0.10 | 0.43 0.49 0.45 0.44 | no |
| 5 | 0.07 | 0.52 0.44 0.43 0.39 0.39 | no |
| 6 | 0.07 | 0.55 0.44 0.48 0.35 0.40 0.44 | no |
| 7 | 0.07 | 0.56 0.34 0.40 0.50 0.35 0.42 0.42 | no |
| 8 | 0.07 | 0.55 0.36 0.37 0.56 0.25 0.38 0.43 0.44 | no |

Picked k = 2.

## THE GROUPS
| group | n | stability | strongest traits (IQR units vs median trade) |
|---|---|---|---|
| 1 | 105 | 0.63 | approach120 high (+0.9); rng120 high (+0.8); Rest high (+0.7); last_bounce_ticks high (+0.7) |
| 2 | 202 | 0.75 | dwell120 high (+0.3); Rest low (-0.3); last_bounce_ticks low (-0.3); rng120 low (-0.3) |

## AGREEMENT WITH HAND TAXONOMY (ARI)
- hand_label: 0.02

## PATH A — EXACT STRUCTURE COMBINATIONS (R=reaction Q=squeeze G=gap S=shadow, '-'=not interacting)
| combo | his n | his % | null % | ratio |
|---|---|---|---|---|
| RQGS | 214 | 70% | 45% | 1.6x |
| R-GS | 73 | 24% | 22% | 1.1x |
| -QGS | 5 | 2% | 4% | 0.4x |
| RQ-S | 4 | 1% | 2% | 0.7x |
| --GS | 3 | 1% | 5% | 0.2x |
| ---- | 3 | 1% | 9% | 0.1x |
| --G- | 3 | 1% | 1% | 0.7x |
| ---S | 1 | 0% | 1% | 0.3x |
| RQG- | 1 | 0% | 1% | 0.4x |

## PATH B — REVERSED PRIORITY (reaction checked first)
ax_struct_rev
reaction         292
zone               7
squeeze-break      5
open-tape          3
Labels changed by reversing the order: 71% of trades (219/307 interact with BOTH a reaction edge and a squeeze band, so whichever is checked first wins). The single-label priority approach is therefore arbitrary - Paths A and C are the honest views.

## PATH C — ENRICHMENT PRIMARY (rarest-at-null family wins; null rates: SQZ 56%, REA 76%, GAP 80%, SHD 83%)
ax_struct_enr
SQZ     224
REA      73
GAP       6
none      3
SHD       1

Labels appended. Registry: T-IM45.
