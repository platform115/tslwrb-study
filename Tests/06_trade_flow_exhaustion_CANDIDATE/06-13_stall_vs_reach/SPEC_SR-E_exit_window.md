# SPEC SR-E — exit-window sweep (stall-bail trigger)
**Status: NO mechanical exit trigger found → cut/hold decision is DISCRETIONARY** · phase: stall-vs-reach · ESZ5 Oct-2025

## Question
The trader never documented a rule for exiting a stalling winner. Is there a consistent, mechanically-
measurable price event in the lead-up to exit that fires before a stall-bail but not before a
target-exit? (Reverse-engineer the TRIGGER, not predict the group.)

## Reframe & method
The exit is the trader's OWN decision → endogenous; reach/stall differ at exit partly by construction
(profit-take vs bail). So each probe is judged on whether the **stall arm clusters in a tight, distinct
band** (a consistent mechanical trigger = candidate rule), NOT on group-separation AUC alone.
Population: 47 `target_reached` vs 29 `below_target_win`. Per-second mid. Binary label (the SR-C lesson).
Rank AUC + two-sample bootstrap CI (seed 0, 10000) + stall-arm tightness read.

## Probes & results (run order B → A → D → C)
**B · exit_velocity.py — velocity death into the exit.** Hypothesis: stalls decelerate into the bail.
- `exit_decel` (final-W vel / preceding-W vel): **NULL** 0.514 / 0.535 (W=30/60). Stall band tight but
  centered ~1.0 (no deceleration) → not a trigger, just "no change for everyone."
- `exit_vel_norm` (exit vel / pre-entry pace): clears W=30 (0.637 [0.509,0.764]) but this is the ENTRY
  velocity_ratio signal re-expressed at a later timestamp (whole-trade property), not an exit trigger;
  W=60 0.612 no clear. → the bail is NOT a velocity-death event.

**A · give_back.py — give-back from the MFE peak (Sweeney 1996; Tomasini & Jaekle 2009).** Hypothesis:
stalls surrender more of peak profit before bailing.
- `give_back_frac` (scale-free): AUC **0.287** (stall>reach, "matches") — BUT this is CONSTRUCTION
  (a target-take is near a peak by definition). **Stall band WIDE**: q25 0.20 / med 0.52 / q75 0.80
  (IQR 0.60) → no consistent give-back level → NO rule.
- `time_since_mfe`: NULL 0.466. → not a give-back trigger.

**D · stagnation.py — time-stop / deadweight time (Raschke & Connors 1995).** Hypothesis: stalls spend
more of their life making no new favorable progress.
- `no_progress_frac` 0.553, `late_no_progress_frac` 0.569: **NULL**. Both arms ~**0.93** (new highs are
  punctate for everyone). Stall band tight but AT the shared 0.93 (tight ≠ discriminating). → not a
  stagnation/time-stop event.

**C · exit_reversal.py — adverse reversal into the exit (most construction-coupled).** Hypothesis: stalls
exit as price turns against them.
- `exit_adverse_move` 0.555 / 0.590, `exit_retrace_ticks` 0.506 / 0.511: **NULL** (did not even produce
  the construction separation expected). Stall retrace band WIDE (IQR ~6 tk) → no soft-stop level.

## Disposition — the finding
Four trader's-eye exit hypotheses, **four "no consistent mechanical trigger."** The one separation
(give_back_frac) is construction with a wide band; the one clear (exit_vel_norm) is the entry signal
re-expressed. **Conclusion: the moment a stalling winner is cut is not marked by a univariate threshold
in the trade's own price tape → the cut/hold decision is DISCRETIONARY** — consistent with the standing
prior that the trader never documented a rule for it.

## Pivot (next veins; the discretionary CAUSE is context the instrument's own tape lacks)
1. Entry-determination — is reach/stall set at ENTRY by setup context (builds on the one positive,
   velocity_ratio, an entry signal)? **Test first.**
2. Higher-TF / WRB structural context (his own method; `es_5m_front` joined to each episode).
3. Conditional / context-gated (PRIM, Friedman & Fisher 1999) — discretion is usually a gated rule.
Pre-commit a stop: if entry-context separates no better than the exit sweep did, conclude the outcome is
weakly entry-encoded (velocity) and otherwise genuinely discretionary, and stop expanding the search.

## Dependencies & run
Imports: `forward_battery` (build_arms) · `trade_flow_exhaustion` (S, TICK, read_per_second) ·
`velocity_acceleration` (pathlen_tk, used by B) · `range_expansion` (rank_auc, two_sample_boot_ci) ·
episodes parquet for entry_px (A, D).
```
PYTHONPATH=. python3 06-13_stall_vs_reach/exit_velocity.py  --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/give_back.py      --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/stagnation.py     --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=. python3 06-13_stall_vs_reach/exit_reversal.py  --config config.toml --wrb wrb_1m.parquet
```

## Recreation notes
Windowed parquet keeps pre_entry_min=60 / post_exit_min=5 → exit window present for BOTH arms (anchoring
reaches at pt1 in design-b was a choice, not a data limit). Judge on stall-arm tightness, not AUC: a
"tight band" only signals a trigger if it is tight AND distinct from the reach arm (D's 0.93 was the
trap — tight at the shared value). give_back & adverse-direction are construction-coupled to the label;
deadweight-time (D) is the least-coupled and was a clean null.
