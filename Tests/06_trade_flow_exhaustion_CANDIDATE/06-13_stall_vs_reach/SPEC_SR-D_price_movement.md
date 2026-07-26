# SPEC SR-D — price-movement vein (stall vs reach)
**Status: ONE surviving candidate — `velocity_ratio` @ τ=60** · phase: stall-vs-reach · ESZ5 Oct-2025 in-sample

## Motivation
The trader's own account: the **movement/speed of price action** drives his cut/hold. Order-flow was
null (SR-A/B); the one apparent positive (SR-C) was an artifact. This vein tests **price-domain
movement** directly, on the **binary** label (the SR-C lesson) with **unsigned** features (not
pt1-circular).

## Population & design
47 reach / 29 stall, **survivors-only** (hold ≥ τ): τ=60 → 45/24, τ=90 → 42/18, τ=120 → 41/13.
Outcome BINARY reach vs stall. Statistic: rank AUC + two-sample bootstrap CI (seed 0, 10000). reach>stall,
clears iff CI excludes 0.5. τ=60 primary. pathlen = Σ\|Δmid\| over per-second mids, in ticks (total
variation = distance travelled; unsigned).

## Scripts & results
- **range_expansion.py** — `expansion_ratio` = range[entry,entry+τ]/range[entry−τ,entry]; `within_accel`
  = 2nd-half range / 1st-half. expansion_ratio **0.594 / 0.598** (τ60/30) — LEANS reach>stall, CI through
  0.5 (no clear). within_accel null/inverts.
- **velocity_acceleration.py** — `velocity_ratio` = (fwd per-second pathlen)/(pre-entry per-second pathlen),
  unsigned. **★ CLEARS: τ=60 AUC 0.660, CI [0.522, 0.788], reach>stall.** τ=30 0.627 (CI grazes 0.5).
  `acceleration` (2nd/1st-half pathlen) null.
- **velocity_ratio_confirm.py** — robustness of the clear: **decomposition** (stall frac<1.0 = 0.62 vs
  reach 0.44 → stalls DECELERATE vs own pre-entry pace); **jackknife** min 0.645 (no single point carries
  it); **permutation** p=0.014 (beyond label-shuffle). All three hold at τ=60.
- **variance_ratio.py** — Lo & MacKinlay (1988) VR(q) = Var(q-ret)/(q·Var(1-ret)); trend (VR>1) vs chop
  (VR<1), as INDEPENDENT primitive. **NULL / wrong-way: 0.353 (τ60, q10), 0.540 (τ30, q5).** Both arms
  VR<1 (microstructure mean-reversion). → signal is **SPEED, not trend-SHAPE**; velocity_ratio is
  **uncorroborated** (stands alone, hence weaker).
- **velocity_ratio_sweep.py** — forward-window sweep keeping fixed-60s pre-norm (pre and forward windows
  are independent; only pre is data-capped at 60s). norm_ratio **0.660 / 0.660 / 0.629** at 60/90/120 →
  **STABLE, not growing** (a ~60s-onset effect, not strengthening with horizon). raw (un-normalised) fwd
  velocity **0.421 / 0.462 / 0.491** → wrong-way/null: **the signal lives ENTIRELY in the pre-entry
  normalization** (the volatility control is doing all the work).

## Disposition — the study's one finding
`velocity_ratio` @ **τ=60** is the single surviving candidate: AUC 0.660 [0.522,0.788], jackknife-robust,
permutation-real, mechanism = **stallers decelerate relative to their own pre-entry pace**. Freeze as the
τ=60 candidate for any future out-of-sample (Feb) work.
**Caveats (do not overstate):** single feature; **normalization-dependent** (no raw effect — fragile to
the 60s baseline being representative); **uncorroborated by shape** (variance_ratio null); n=47/24; one
trader / one month; in-sample. Modest, real, not strong.

## Dependencies & run
Imports: `forward_battery` (build_arms) · `trade_flow_exhaustion` (S, TICK, read_per_second) ·
`velocity_acceleration` (pathlen_tk) · `range_expansion` (rank_auc, two_sample_boot_ci).
```
PYTHONPATH=. python3 06-13_stall_vs_reach/velocity_acceleration.py --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/velocity_ratio_confirm.py --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/velocity_ratio_sweep.py  --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/variance_ratio.py        --config config.toml --wrb wrb_1m.parquet
```

## Recreation notes
Use UNSIGNED path length (a choppy stall is also "fast") to avoid pt1-circularity. Keep the pre-entry-60s
normalization — the raw forward velocity is volatility-confounded (wrong-way), so the normalization is
the feature, not a nicety. Forward window sweeps freely; only the *pre* window is capped at 60s by the
windowed parquet. velocity_ratio @ τ=60 must reproduce 0.660 exactly (it is the rate-ratio at τ=60).
