# SPEC SR-B — entry-forward & structure family (stall vs reach)
**Status: NULL + one marginal-and-inverting lead (hurst)** · phase: stall-vs-reach · ESZ5 Oct-2025 in-sample

## Question
Does early *entry-forward* order-flow/structure predict which non-losers reach pt1 vs stall? (The
predictive frame design-b couldn't be.)

## Population
47 `target_reached` / 29 `below_target_win`. Forward windows use **survivors-only** (hold ≥ τ): the
leakage-free read where both arms read the full [entry, entry+τ] with no exit-capping. 120s-survivors =
pre-registered primary (reach 41 / **stall 13**). ≥180s underpowered (stall ≤5).

## Design (c) — entry-anchored forward, pooled two-sample
Feature over [entry, entry+τ]; pooled AUC reach vs stall; two-sample bootstrap CI (seed 0, 10000).

## Scripts & results
- **forward_battery.py** — τ=30s pooled battery (intensity_level, flow_level, intensity_slope, ER_abs,
  hurst, rho1, abs_move, session_phase). All straddle 0.5 (hurst 0.612, flow_level 0.536, session_phase
  0.602 — none clear). *Also the shared library for the rest of the phase:* `build_arms`,
  `read_trade_full`, `window_features`, `two_sample_boot_ci`.
- **forward_sweep.py** — window sweep 60/120/180/300, **capped vs survivors-only** control. hurst CLEARS
  only at **120s survivors: 0.657, CI [0.507, 0.795]**. Capped-pooled clears at W≥180 (intensity_slope,
  ER, abs_move) are the **whole-life-capping ARTIFACT** (a stall's capped window = its entire life) and
  collapse in survivors — not signal.
- **structure_family.py** — 120s-survivors primary. `flow_consistency` (NEW: Kaufman ER on *cumulative
  signed flow*, = ER + OFI) 0.612, CI [0.435, 0.782] — leaner, no clear, corroborates the persistence
  axis but is correlated with it (not independent). hurst 0.657 reconfirmed. **impact 0.531 FLAT →
  magnitude family CLOSED** in the clean frame.

## Disposition
hurst is the only leakage-free clear (weak: LB 0.507, n=13) and is reach>stall across all 8 reads this
phase (0.562/0.612/0.584/0.607/0.599/0.657/0.605/0.577, mean 0.600) — but it **inverts vs MFE** in SR-C
(−0.18) and is flat vs pt1-speed, so it is treated as a weak lean, **not carried**. flow_consistency
corroborates, not independent. Magnitude closed.

## Dependencies & run
Imports: `forward_battery` (build_arms, read_trade_full, window_features, two_sample_boot_ci) ·
`horse_race_spine` (rank_auc, designA helpers) · `trade_flow_exhaustion` (S, TICK).
```
PYTHONPATH=. python3 06-13_stall_vs_reach/structure_family.py --config config.toml --wrb wrb_1m.parquet
```

## Recreation notes
Survivors-only is the clean control — capped-pooled is for *context only* and its W≥180 "clears" are
artifacts. Read the primary at 120s-survivors (stall n=13); do not over-read a single marginal CI — the
only evidence above noise for hurst is the 8-read directional consistency, and SR-C undercuts even that.
