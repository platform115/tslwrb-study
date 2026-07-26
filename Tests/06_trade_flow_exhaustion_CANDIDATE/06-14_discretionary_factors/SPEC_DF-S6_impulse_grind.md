# SPEC DF-S6 — impulse-vs-grind (concentration) + burst timing
**Status: BOTH ROBUST-NULL (12 cells) · key texture finding · mechanism prose demoted** · phase 06-14 · ESZ5 Oct-2025 · registry T-DF08/T-DF09

## Questions
S6: is favorable movement more CONCENTRATED (one burst) for one arm? `impulse_frac` = max favorable
run ÷ total favorable movement, [entry, entry+60s]. "Impulsive vs corrective" is documented practitioner
vocabulary (Elliott tradition); run-length analysis standard; **the ratio is our construction — flagged.**
S6b (user-chosen follow-on): WHEN does the max favorable run occur? `burst_time` (s from entry).

## Design (grid-first per user directive: tunables tested, not decided)
Validity fixed (not tunables): survivor frame decisive (45/24), 60s window (S4b mapped sub-windows),
seed 0, existence of a denominator floor. Direction: S6 unregistered (either-way clears = leads with
observed direction + provenance); S6b registered reach-LATER (mechanism-derived — see demotion below).
- S6 grid: run-break rule ×2 {ADV-ONLY: only adverse seconds break, flats continue · STRICT: any
  non-favorable breaks} × floor ×3 {total_fav ≥ 2/4/6tk}. Reference cell ADV-ONLY/4tk (named pre-output).
- S6b grid: timing anchor ×3 {START/CENTER/END of max run} × rule ×2; floor 4tk fixed (S6 showed the
  floor axis flat). Progress-conditioned (total_fav≥4 → 43R/24S), counts printed.
- Pattern rule both: ≥2 same-direction clears within a rule → lead (Feb list); single → lead-weak;
  none → robust-null. Each grid = 6 looks in the registry (Deflated-Sharpe N counts cells).

## Results — T-DF08 (s6_impulse_grind.py)
**0.559–0.594 ×6, no clears, both rules agree → robust-null.** STRICT-collapse prediction WRONG
(structure intact: medians 0.20 vs ADV-ONLY 0.28) — the feature is definition-robust and robustly
uninformative. ρ(impulse, fnv)=+0.09, ρ(impulse, VR)=−0.06 → orthogonal null.
**THE TEXTURE FINDING (reference-cell extras)** — the most important descriptive line of the family:
reach vs stall gross favorable movement is IDENTICAL — max_run **7.0 vs 7.0tk**, n_runs **10 vs 10**,
total_fav **24.5 vs 24.8tk** — while fav_net_vel separates 0.669. Arithmetic consequence: **the entire
reach/stall difference is the ADVERSE OFFSET** — stalls bleed back what they generate. "Flatline" ≠
absence of favorable movement; it is favorable movement continuously cancelled.
Adverse-TOTAL probe explicitly ruled out (arithmetic identity with fav_net_vel given equal gross);
adverse *timing/clustering* is not identity-bound — legitimate carve-out if ever wanted.

## Results — T-DF09 (s6b_burst_timing.py)
**0.415–0.456 ×6, no clears — and every lean is OPPOSITE the registered direction** (stall bursts
LATER: medians R17/S32s at ADV-ONLY/START; R16/S21 STRICT). ρ(burst, fnv)=+0.002 orthogonal;
ρ(burst, h2)=+0.24 [−0.02,+0.48] indeterminate. Orthogonal null. Note (selftest-documented): ADV-ONLY
run spans are flat-diluted (a pause extends a run to the next adverse tick) — STRICT is the sharper
timing read; both null.

## MECHANISM DEMOTION (binding on future design passes)
Predictions derived from the "reaches follow through / stalls flatline" narrative are now **0-for-2**
(pop-and-fade → fade robust-null ×7; reach-late-burst → leans opposite). The narrative is hereby a
DESCRIPTION of the two clearing features (fav_net_vel, h2_net_vel), not a generative model. Refined
description after S6/S6b: reaches' late accrual happens WITHOUT a distinctive burst (grind); stalls'
(later) bursts get cancelled by the adverse offset. Future probe directions should be argued from
data constructions, not from this prose.

## Disposition
F1 after S1–S4, S6: candidates fav_net_vel + velocity_ratio; leads h2@b=20 (found-by-sweep) and
ATRrel@60 (T-DF04, RELABELED lead-weak → Feb list per exploration-framing correction); informative
robust-nulls S3/S1/S6/S6b. Remaining: **S5** (speed-congruence with the pt1 WRB — thin precedent,
flagged since backlog creation), then F1 closes and F2/F3 open.

## Dependencies & run (from 06_ root)
```
PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 06-14_discretionary_factors/s6_impulse_grind.py  --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 06-14_discretionary_factors/s6b_burst_timing.py --config config.toml --wrb wrb_1m.parquet
```
Imports: forward_battery · trade_flow_exhaustion · range_expansion · velocity_acceleration ·
s2_directional_velocity · fav_net_vel_confirm · (s6b also s4_speed_profile). Both `--selftest`
(one-burst=1.00 / grind=0.14 / pause splits the rules 1.00-vs-0.50 / early-vs-late burst times /
floors / flat-trade NaN).

## Recreation notes
Runs are computed on per-second oriented mid increments; ES flat seconds are common — the run-rule
choice is load-bearing and both variants are archived. burst_time is undefined (NaN) for zero-favorable
trades → progress-conditioned AUC; counts printed. Registry N: count these as 12 looks, not 2 rows —
and note the standing audit item: earlier grid rows (S1=12 cells, S3=18) predate the cells-not-rows
convention and undercount.
