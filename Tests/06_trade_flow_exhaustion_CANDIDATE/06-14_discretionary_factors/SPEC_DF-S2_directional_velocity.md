# SPEC DF-S2 — directional (favorable-leg) velocity
**Status: fav_net_vel @ τ=60 = CANDIDATE #2 (confirmed)** · phase: 06-14 discretionary factors · ESZ5 Oct-2025 · registry T-DF01/T-DF02

## Question
velocity_ratio (T-SR19, candidate #1) is UNSIGNED movement. Does DIRECTION carry signal — how fast price
moved *in the trade's favor* after entry? First probe of the F1 price-speed family (backlog S2).

## Design (locked with user before code)
- **Population:** 47 target_reached vs 29 below_target_win (build_arms). Binary label.
- **Windows (user Decision 3-B):** [entry, min(entry+τ, exit)] — ALL trades, capped at exit; ≥5s floor.
  τ=60 primary, 30 secondary.
- **Features (4 pre-registered columns, one pass):**
  `fav_peak_vel` (PRIMARY) = max favorable displacement in window (tk) ÷ seconds to that peak; 0 if never favorable.
  `fav_net_vel` (secondary) = oriented net displacement at window end (tk) ÷ window seconds.
  `*_norm` = each ÷ pre-entry per-second path rate over [entry−60s, entry] (velocity_ratio's denominator).
- **Direction:** reach > stall all columns. AUC + two-sample bootstrap CI (seed 0, 10000).
- **CIRCULARITY GUARD (pre-registered mid-design):** velocity_ratio's own spec chose unsigned because
  signed favorable velocity is partly circular when target attainment falls INSIDE the window (reaches
  exit at/after target). Quantified per run (exits<τ: reach 2 / stall 5 at 60s). Therefore the
  **survivor subset (hold≥τ) is the DECISIVE frame** — no reach in it attained target in-window; it is
  also velocity_ratio's exact arms (45/24). All-trades B-design line = descriptive view only.

## Results — probe (s2_directional_velocity.py, T-DF01)
τ=60: `fav_net_vel` **0.700 [0.575,0.817]** all-trades; **0.669 [0.527,0.800] survivors (DECISIVE) — CLEARS**;
`fav_net_vel_norm` 0.709 / 0.690 survivors — clears. **`fav_peak_vel` NULL everywhere** (0.465–0.567) —
the designed PRIMARY failed; the secondary won. τ=30: nothing clears (net 0.584) → ~60s onset, same
shape as velocity_ratio. Redundancy: ρ(fav_net_vel, velocity_ratio) = **+0.009** (survivors).
Honest headline: **1 of 4 pre-registered columns cleared, and it was the secondary.**

## Results — confirmation (fav_net_vel_confirm.py, T-DF02), pre-set criteria
1. Jackknife (LOO): min **0.655**, max 0.694 → robust (no single trade carries it).
2. Permutation (10000, one-sided): **p=0.0093** → beyond label shuffle. → **candidate confirmed.**
3. Decomposition — ASYMMETRIC: **reach 76% net-positive at 60s vs stall 50% (coin-flip)** → the content
   is *no-progress-is-bad* (cut-side) more than progress-is-good (hold-side).
4. Independence: ρ = +0.009, pair-bootstrap CI **[−0.224, +0.236]** — excludes strong redundancy per the
   pre-set |ρ|<0.4 criterion. NOT proven orthogonal (n=69 CIs are wide; truly independent data at this n
   can show ρ≈±0.2).
5. Stratified F5 preview: VR point-AUC ~0.67 within BOTH fav_net_vel halves, but neither cell clears
   (HIGH half has only 8 stalls = firing floor) → *consistent with* combinable axes, not established.

## Disposition
Two quasi-independent entry-context candidates now exist: **fav_net_vel** (directed progress) and
**velocity_ratio** (sustained movement vs own pre-entry pace), both ~0.66–0.69, both October in-sample.
Caveats carried: single month, one trader, confirm ran on the discovery sample (cannot launder in-probe
selection — the secondary-not-primary clear is a selection event); February holdout adjudicates.
Next: S3 time-to-N-ticks, with redundancy vs fav_net_vel as the central pre-registered read
(numeric ρ-CI thresholds to be fixed BEFORE output is seen).

## Dependencies & run (from 06_ root)
Imports: forward_battery (build_arms) · trade_flow_exhaustion (S, TICK, read_per_second) ·
range_expansion (rank_auc, two_sample_boot_ci) · velocity_acceleration (pathlen_tk) ·
s2_directional_velocity (s2_feats, spearman — confirm only).
```
PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/s2_directional_velocity.py --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/fav_net_vel_confirm.py     --config config.toml --wrb wrb_1m.parquet
```
Both have `--selftest` (synthetic paths; peak-rate, capped-window, never-favorable, short-mirror, floor;
jackknife/permutation/Spearman-CI machinery).

## Recreation notes
B-design windows mean early-cut trades' window length IS the trader's exit decision — never headline the
all-trades line alone; the survivor line is the finding. fav_net_vel is conceptually "early progress
toward target" — legitimate (not circular) on survivors, but the finding reads as "outcome partly
visible in early progress," which is modest by construction. If porting to a rule: the decomposition
says the actionable side is the cut (net ≤ 0 at 60s → elevated stall odds), NOT a hold-confirmation.
