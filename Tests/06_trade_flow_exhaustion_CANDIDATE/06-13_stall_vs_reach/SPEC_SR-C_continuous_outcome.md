# SPEC SR-C — continuous-outcome reframe (stall vs reach)
**Status: apparent lead WITHDRAWN as a window-contamination artifact** · phase: stall-vs-reach · ESZ5 Oct-2025

## Question
Does the binary pt1 threshold hide a *graded* signal? Regress early features on graded development
outcomes instead of the yes/no label.

## Population & outcomes
47 reach / 29 stall. Outcomes: **MFE** (max favorable excursion, ticks, from entry price via 1m-bar
highs/lows) — "how far," all 76; **time_to_pt1** (`pt1_open_el`, seconds) — "how fast," reaches only.
Predictor = early features over **[entry, entry+30s]** (τ=30 chosen so all 76 survive: no capping).
Statistic: Spearman rank correlation + pair-bootstrap CI (seed 0, 10000), two-sided.

## Scripts & results
- **continuous_outcome.py** — Spearman(early-30s feature, outcome).
  - vs MFE: rho1 **−0.269** [−0.484,−0.033] (clears but WRONG sign vs pre-registered +); intensity_level
    **+0.274** [+0.036,+0.497] (clears, but volatility confound); hurst −0.180 (inverts vs SR-B).
  - vs time_to_pt1 (reaches): **flow_level −0.464** [−0.641,−0.227], **ER_abs −0.355** [−0.581,−0.085]
    — both clear in pre-registered negative direction (stronger early flow → faster to pt1). *Looked like
    the best result of the study.*
- **speed_leads_robustness.py** — robustness of that lead: τ-sweep on clean subset + distance partial.
  - **pt1_open_el dist: min −49, p25 −14, median 49, p75 118** → **pt1 lands at/before entry for ~half
    the reaches** (pt1 is the first WRB at/after the entry *minute*; a bar opening up to 59s pre-entry
    counts). So the τ=30 feature window **overlapped/post-dated pt1** for ~half the sample → LOOK-AHEAD.
  - Clean subset (pt1_open_el ≥ τ): flow_level **+0.262 / +0.401 / +0.118** at τ=30/60/120 — all CIs
    straddle 0, sign FLIPS. ER ~0. **The −0.46 was the contamination, not a predictor.**
  - Distance was NOT the confound: Spearman(time_to_pt1, distance) = **−0.061** [−0.369,+0.250]; partial
    Spearman(flow_level, time_to_pt1 | distance) = **+0.242** (null).

## Disposition
The speed-to-pt1 lead is a **window-contamination artifact and is WITHDRAWN.** `time_to_pt1` is not a
trustworthy outcome because pt1 timing relative to entry is not clean. **Lesson enforced downstream: use
the BINARY reach/stall label (SR-D), not pt1-timing outcomes.** Vol-normalized MFE (MFE/ATR) was flagged
as the required control to test whether intensity's +0.27 survives — deferred, not run.

## Dependencies & run
Imports: `forward_battery` (build_arms, read_trade_full, window_features) · `trade_flow_exhaustion`
(S, TICK). speed_leads_robustness also imports `continuous_outcome` (spearman, spearman_ci).
```
PYTHONPATH=. python3 06-13_stall_vs_reach/continuous_outcome.py --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/speed_leads_robustness.py --config config.toml --wrb wrb_1m.parquet
```

## Recreation notes
**The central gotcha of the whole phase lives here:** any feature measured over an early window that can
contain pt1 is contaminated for both time_to_pt1 AND for directional features. Always re-derive pt1
relative to entry and either restrict to pt1_open_el ≥ τ or use the binary label + an unsigned feature.
