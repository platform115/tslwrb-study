# UM REPORT — ANATOMY OF THE UNMATCHED ENTRIES (T-EN114)
STATUS: CLOSED | 2026-11-27 | Spec: UM_SPEC.md (frozen first)

Unmatched found: 12 (expected 12 per T-EN107).

## PER-ENTRY ANATOMY
| month   |        sec |   side |      px |   pnl |   mins_since |   mom5 | n1                 | n2            | n3            | attributed    |   his_msgs_10min |
|:--------|-----------:|-------:|--------:|------:|-------------:|-------:|:-------------------|:--------------|:--------------|:--------------|-----------------:|
| 2022-02 | 1643990933 |      1 | 4454.25 | -2    |         23.9 |   1.5  | edge_REA=0.00      | edge_GAP=0.00 | edge_SHD=0.00 | edge_REA      |                0 |
| 2022-02 | 1644332530 |     -1 | 4460    |  0.5  |          6.2 |  13.75 | wrb_body=0.25      | edge_GAP=0.50 | edge_SHD=2.00 | wrb_body      |                2 |
| 2022-02 | 1644332700 |     -1 | 4459.75 | -2.5  |          9   |   8.25 | edge_GAP=0.00      | wrb_body=0.00 | edge_SHD=1.50 | edge_GAP      |                2 |
| 2022-02 | 1645021830 |      1 | 4447    |  3.25 |         15.5 |   4.75 | edge_GAP=0.75      | edge_SHD=0.75 | wrb_body=0.75 | edge_GAP      |                3 |
| 2022-02 | 1645023008 |     -1 | 4443.25 | 11.5  |         35.1 |   1.75 | edge_SHD=0.00      | edge_GAP=0.25 | wrb_body=0.25 | edge_SHD      |                6 |
| 2022-02 | 1645199688 |      1 | 4360.5  | -0.25 |          9.8 |   5.75 | edge_GAP=0.00      | edge_REA=0.25 | edge_SHD=0.25 | edge_GAP      |                0 |
| 2025-10 | 1759330062 |     -1 | 6730.5  |  0.25 |         17.7 |  -0    | edge_GAP=0.00      | wrb_body=0.50 | edge_SHD=0.75 | edge_GAP      |                0 |
| 2025-10 | 1759417194 |     -1 | 6750.25 |  1.5  |         29.9 |   0.75 | edge_SHD=0.25      | round50=0.25  | edge_GAP=0.50 | edge_SHD      |                1 |
| 2025-10 | 1759499071 |      1 | 6780.25 |  2.25 |          9.5 |  -1.75 | prior_day_HLC=0.00 | wrb_body=0.00 | edge_SHD=0.25 | prior_day_HLC |                2 |
| 2025-10 | 1759932627 |      1 | 6786    |  4.5  |         10.4 |   1.75 | edge_GAP=0.50      | edge_SHD=0.50 | mdlevel=0.75  | edge_GAP      |                1 |
| 2025-10 | 1760446897 |      1 | 6632    |  5.5  |         16.6 |   2.75 | edge_SHD=0.00      | wrb_body=0.00 | W20band=0.50  | edge_SHD      |                0 |
| 2025-10 | 1761313810 |     -1 | 6826    |  1.25 |          5.2 |   5.62 | wrb_body=0.00      | edge_SHD=0.25 | edge_GAP=0.50 | wrb_body      |                0 |

## ATTRIBUTION BUCKETS (nearest structure <= 1.5 pts)
- edge_GAP: 5
- edge_SHD: 3
- wrb_body: 2
- edge_REA: 1
- prior_day_HLC: 1

## PRICE-ACTION CLASS
- continuation (entered WITH prior 5-min move): 10; fade (AGAINST): 1; flat: 1

Registry: T-EN114.

## READING — THE CEILING IS A LISTENING PROBLEM, NOT A MYSTERY
Every one of the 12 sits ON a structure we ALREADY COMPUTE - at
0.00-0.75 pts in 11 of 12 cases. The attribution: gap edges (5),
shadow-zone edges (3), WRB body edges (2), reaction edge (1),
prior-day level (1). And 10 of 12 are CONTINUATION entries - the
same break mechanic our stream runs. The problem: our G2 entry
stream only LISTENS to squeeze edges + W20 bands; he treats gap
edges, shadow edges and WRB bodies as breakout lines in exactly the
same way. F-12's "hard ceiling" dissolves into a configuration
choice: widening the trigger's edge families (edges_at already
serves GAP/SHD/REA; WRB bodies and prior-day are computed daily)
could re-match up to 12/12 - a catch ceiling of 59/62.
THE COST SIDE, unknown until tested: more edge families = more
crosses = more extras; whether the added trades carry G2-grade
quality is an empirical question. NEXT (J gates): a spec'd entry
round - the MULTI-FAMILY edge stream (candidate: Strategy 4A-v3) on
the 4-month corpus with the full standard, R-9 controls, judged
finally on D-8 months. Note: F-12 stands corrected - his unmatched
entries match none of our edges IN USE, not none of our structures.
