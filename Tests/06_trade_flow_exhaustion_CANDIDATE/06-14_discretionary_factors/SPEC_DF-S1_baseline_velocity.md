# SPEC DF-S1 — baseline-relative velocity (session-scale normalizers)
**Status: CLEAN NULL — localizes velocity_ratio to immediate-pace change** · phase 06-14 · ESZ5 Oct-2025 · registry T-DF05

## Question
A controlled experiment on velocity_ratio (VR, T-SR19) rather than a new-candidate hunt: VR's sweep
(T-SR22) showed the signal lives entirely in its normalization (raw forward velocity wrong-way
0.42–0.49). Keep VR's numerator, swap the 60s pre-entry denominator for SESSION-SCALE baselines —
"fast for this market today" (ATR: Wilder 1978).

## Design (locked with user)
- Numerator (identical to VR): per-second path length over [entry, min(entry+τ, exit)] ÷ window s (tk/s);
  B-design, ≥5s floor.
- Denominators (3 columns): **s1_atr20 = ÷(ATR(20,1m,pre-entry)/60) PRIMARY** · s1_atr5 (user-added;
  near-duplicate expected, ATR ρ +0.88 across entries — treat as one denominator family) ·
  s1_longpath = ÷(pathlen[entry−30min, entry]/1800) — same primitive as VR, timescale-only swap
  (the sharper scientific control; windowed parquet carries 60 min pre-entry).
- τ=60 PRIMARY / 30 (no long horizons — S3's cell-sprawl lesson). Survivor decisive; PRIMARY CELL
  s1_atr20 SURV@60.
- Direction registered: reach>stall. **Prediction on record (pre-output): null-to-wrong-way** — a
  session-scale denominator is ~constant within a day, so S1 ≈ raw velocity with cross-day vol removed.
- Redundancy (locked): ρ vs VR central, with the shared-numerator "partly mechanical" flag; ±0.4/±0.6
  convention; ρ vs fav_net_vel secondary.

## Results (s1_baseline_velocity.py, T-DF05)
**All 12 cells null.** PRIMARY 0.509 [0.367,0.651]; best cell anywhere 0.544 (atr5 @30, CI to 0.679).
Redundancy: ρ(s1_*, VR) = +0.41/+0.43/+0.47 (CIs into the indeterminate zone; partly mechanical —
shared numerator) yet S1 separates nothing → **VR's discriminating variance lives in the part S1
removed: the 60s pre-entry denominator.** ρ(s1_atr20, fav_net_vel) = +0.04 — S1 is not the directional
axis either. Registered prediction scored: hit (noted with the standing caveat that one hit does not
repair the probe-forecast miss record).

## Disposition — the null is the finding
Three-way bracket on VR now complete:
- raw forward numerator alone → **wrong-way** (T-SR22)
- ÷ session scale (ATR / 30-min path) → **null** (this test)
- ÷ 60s immediate pre-entry pace → **0.660, candidate** (T-SR19/20)

The signal is specifically **deceleration vs the trader's own immediate entry context**, not absolute or
session-relative speed. Sharpens VR's interpretation AND flags its fragility surface for February: the
60s pre-entry window is load-bearing; if that window's character shifts across months, VR shifts with it.
No new candidate; S4 (sustained-vs-decayed speed profile) next per the pre-registered order.

## Dependencies & run (from 06_ root)
```
PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 \
    06-14_discretionary_factors/s1_baseline_velocity.py --config config.toml --wrb wrb_1m.parquet
```
Imports: forward_battery · trade_flow_exhaustion · range_expansion · velocity_acceleration ·
s2_directional_velocity (s2_feats, spearman) · fav_net_vel_confirm (spearman_boot_ci) ·
s3b_atr5_variant (load_atr_ticks). `--selftest` verifies all three ratio columns against hand-computed
values. NOTE: pandas `.corr(method='spearman')` requires scipy (not in the venv) — all statistics use the
toolkit's own scipy-free implementations; keep that convention (a violation of it was this script's one
runtime bug, fixed).

## Recreation notes
read_per_second span starts 30+ min before the earliest entry (longpath denominator) — larger read than
prior probes; fine on the M1 in practice. If a future month strains memory, chunk per-episode.
