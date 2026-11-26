# M9 REPORT — THE STATE-MACHINE POLICY (T-MG16)
STATUS: CLOSED | 2026-11-26 | Spec: M9_SPEC.md (committed first)

## FINDING-4 DISTRIBUTION (why the stop stays): outcomes after first touch of -1.5 (raw paths, 300s on)
n=892 | mean -0.12 | q5/q25/q50/q75/q95 = -8.86/-3.50/-0.25/+3.25/+9.38
Reading: the mean recovery is real BUT q5 shows the tail that a stop exists to cut. Stop unchanged this round, as specified.

## STAGE 1 — HIS 62 FILLS (qualify: net > M7's +146.0)
| candidate | net | win | worst | share of his |
|---|---|---|---|---|
| M9 Se90 Sl45 r0.5 | +130.6 | 68% | -3.75 | 56% |
| M9 Se90 Sl45 r0.75 | +134.6 | 68% | -3.75 | 58% |
| M9 Se90 Sl60 r0.5 | +133.4 | 69% | -3.75 | 58% |
| M9 Se90 Sl60 r0.75 | +137.9 | 69% | -3.75 | 60% |
| M9 Se120 Sl45 r0.5 | +136.0 | 69% | -3.75 | 59% |
| M9 Se120 Sl45 r0.75 | +141.0 | 69% | -3.75 | 61% |
| M9 Se120 Sl60 r0.5 | +138.8 | 71% | -3.75 | 60% |
| M9 Se120 Sl60 r0.75 | +144.2 | 71% | -3.75 | 62% |
| M7 baseline | +146.0 | 76% | -3.75 | 63% |
| DUAL ORACLE (ceiling) | +274.9 | 97% | -2.88 | 119% |

Stage-1 qualifiers (top 3 to joint): NONE

## STAGE 2 — JOINT (incumbent on this universe: M7 +186.0 / caught 40 / extras +88.4)
| candidate | trades | net (22-02/25-10) | caught/62 | extras net | ADOPT? |
|---|---|---|---|---|---|
| M7 baseline | 500 | +186.0 (+84.6/+101.4) | 40 | +88.4 | no |

Registry: T-MG16.
