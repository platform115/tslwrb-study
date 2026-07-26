# SPEC SR-A — exit-anchored microstructure (stall vs reach)
**Status: NULL (retired — wrong frame for early prediction)** · phase: stall-vs-reach · ESZ5 Oct-2025 in-sample

## Question
Does the trade's order-flow character *near the exit* separate stalls from reaches?

## Population (deterministic; `build_groups`)
92 Oct-2025 ESZ5 episodes = **47 `target_reached`** + **29 `below_target_win` (stall)** + 16 losers
(excluded, incl. 5 that reached pt1 then lost → reach is 47 not 52). All 29 stalls are single-exit
(clean exit instant). pt1 = first in-direction 1m WRB at/after the entry minute, confirmed +60s.

## Design (b) — exit-anchored, matched-elapsed
Anchor = pt1 (reached) / `floor_min(exit)` (stall). Window = trailing **W=60s** to the anchor. Per-cut
AUC over the 29 stall cuts vs matched-elapsed reach risk-set; **cluster bootstrap** CI (seed 0, 10000)
over the 29 stall episodes. Built to strip age/duration/regime and isolate a confound-free exit-moment
mechanism.

## Features, pre-registered direction, result (all two-sided; clears iff CI excludes 0.5)
| script | feature | hypothesis | AUC | read |
|---|---|---|---|---|
| sign_persistence.py | rho1 (lag-1 oriented sign autocorr) | reach>stall clustering | 0.542 | null |
| sign_persistence_dfa.py | Hurst of sign series (DFA-1; Lillo & Farmer 2004) | reach>stall long memory | 0.562 | null |
| sign_persistence.py | flow_level (mean oriented signed flow) | reach>stall | 0.522 | null |
| intensity.py | intensity_slope (within-window arrival-rate slope) | stalls decay into exit | 0.545 | null |
| intensity.py | **intensity_level** (trades/sec) | stalls busier | 0.244 (2-sided 0.756) | **separates but PEEKED + time-of-day/vol-regime confounded; NOT absorption (stalls ~2× trades AND ~2× net move); NOT a candidate** |
| impact.py | impact = \|net mid move\|/trade (Amihud; Kyle λ) | stalls absorb (low) | 0.529 | null |
| efficiency_ratio.py | Kaufman ER on per-second mid | reach trends (high) | 0.477 | null |

## Disposition
All null. The exit-window is endogenous to the trader's decision and the wrong frame for *early*
prediction → family retired. `intensity_level`'s separation is an artifact (peeked direction + open-
clustering regime + effort-and-result scale together) and must not be cited as a finding.

## Dependencies & run
Imports: `trade_flow_exhaustion` (S, TICK, build_groups, read_per_second, score) ·
`horse_race_spine` (designA_perCut, cluster_boot_ci, rank_auc).
```
PYTHONPATH=. python3 06-13_stall_vs_reach/sign_persistence.py --config config.toml --wrb wrb_1m.parquet
```
(each script `--selftest` validates its math on synthetic data first)

## Recreation notes
Anchor asymmetry (pt1 vs floor(exit)) is the whole point of the matched-elapsed design — do not collapse
to a single fixed window. Cluster-bootstrap over **episodes**, not cuts, or the CI is anti-conservative.
