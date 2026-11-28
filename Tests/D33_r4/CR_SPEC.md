# CR_SPEC — D-33 R4: S5-LINE CONSTANTS RANGES (T-SA02)
STATUS: FROZEN BEFORE RUN | 2026-11-28 | Rule 2 + R-11 + R-12 + R-12a
Question (F-20's): is any Strategy-5-line constant a knife-edge?
Labels only - NOTHING is changed in any shipped system regardless of
outcome (T-SA01 law). The labels become the reading key for D-8
failures under R-13 (SENSITIVE dial fails fresh months = adapter
problem; FLAT dial fails = mechanism problem).

## R-12a COMPONENT MAP
| component | what it is | dials touched here |
|---|---|---|
| EN-03 entry | level touch-break: setup (multi-day level + approach), signal (touch <=0.5), technique (stop order past level) | entry offset 0.75; order TTL 120; universe dials: approach zone 2.0, touch distance 0.5, per-level spacing 600 |
| FL-ALL filter | no time filter | none |
| FL-RWY / FL-3S | gated variants | NOT perturbed (n too small); inherit findings |
| MP-10 management | stop behind level; capture-trail into next level; flow-fade; time cap | stop 1.25; arm distance 1.0; give-back 0.75; fade start 60 / step 30; cap 900 |
| LEVEL DETECTOR (shared: feeds EN-03 setup AND MP-10 targets) | 60-day density levels | tolerance 2.0; score >=4; window 60d; kill distance 5.0 (NOT covered by T-SA01 - verified) |
| flow feed / busy engine | OFI10 input; one-position rule | none |

## R-11 MONTHS-SPEND
2022-02 + 2025-10 (the only depth months; OFI-dependent exits), both
already spent. No new claim is made and NO value may be adopted -
nothing is spent. Any tempting variant goes on an AFTER-D-8 list.

## R-12 FINDINGS SWEEP
APPLIED: F-20 (method + no-adoption law), F-13 (center-cell
controls), F-3/F-7 (capture earns everything - trail dials read
hardest), F-30/F-31 (stop-range readings must reconcile with the
reclaim results), F-17 (fade window basis), F-36/37 (EN-03 path
stamp-clean; no resolver dial here), F-11 (labels are training-side).
NOT-APPLICABLE: F-15 (other line's stop), F-21/22 (book read
untouched), F-28/29 (runway untouched), F-23..26 (families untouched).

## DIALS AND RANGES (one at a time; center = shipped values)
Trade dials (sim-only): offset {0.50, 0.75, 1.00}; TTL {90, 120,
180}; stop {1.00, 1.25, 1.50}; arm {0.75, 1.0, 1.5}; give-back
{0.50, 0.75, 1.00}; fade start {45, 60, 90}; fade step {15, 30,
45}; cap {600, 900, 1200}.
Universe dials (touch set rebuilt per cell): approach {1.5, 2.0,
2.5}; touch {0.25, 0.50, 0.75}; spacing {300, 600, 900}.
Level-detector dials (levels + touches rebuilt): tolerance {1.5,
2.0, 2.5}; score {3, 4, 5}; window {45, 60, 75}; kill {3.75, 5.0,
6.25}.

## METHOD, CONTROLS, VERDICT (T-SA01 convention verbatim)
Universe: 5W full-RTH. Metric per cell: n / pooled net / per-trade /
both-month nets. R-9 CONTROL: the center cell must reproduce the
certified builder (1541 approaches / 1263 touches) and sim
(750/+472.1) exactly - abort otherwise. Per dial: ROBUST (all
variants within +-15% of baseline pooled net AND month direction
unchanged) | SENSITIVE (beyond that, flagged with direction) |
KNIFE-EDGE (sign flip or conclusion reversal - escalated to J).
Registry: T-SA02.
