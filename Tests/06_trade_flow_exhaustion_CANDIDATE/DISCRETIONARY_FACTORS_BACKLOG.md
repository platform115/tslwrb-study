# Discretionary-Factors Exploration — Standing Backlog (phase 06-14)

**Place at:** `06_trade_flow_exhaustion_CANDIDATE/06-14_discretionary_factors/DISCRETIONARY_FACTORS_BACKLOG.md`
**Status:** open exploration · ESZ5 Oct-2025 · breadth-first (combination is the goal, not a single winner)

## Purpose & reframe
The exit sweep (06-13 / SR-E) found NO consistent mechanical trigger for the stall-bail in the
instrument's own tape → the cut/hold-a-winner decision is **discretionary**. Discretionary ≠ random: it
is driven by context the tape lacks, perceived **at or before the decision**. One foothold already points
upstream — `velocity_ratio` (entry-context speed) is the only feature that ever separated. This phase
enumerates the measurable candidate factors, works through them, and **combines** them (discretionary
rules usually live in the interaction, e.g. "hold if speed good AND above VWAP AND 5m agrees").

This is exploration: breadth is the point, more measured factors = more material to combine. Multiple-
testing / holdout accounting is explicitly deferred to a later validation pass and is NOT a reason to
narrow here. Each probe is still pre-registered (hypothesis + expected shape) before code.

## Shared frame (all probes inherit this)
- **Population:** 47 `target_reached` vs 29 `below_target_win` (the settled 06-13 arms). **Binary** outcome
  (the SR-C lesson — never `time_to_pt1`).
- **Measured at/before the decision:** entry-context primarily; some at the hold/stall point.
- **Stat:** rank AUC + two-sample bootstrap CI (seed 0, 10000), reach>stall convention; plus stall-arm
  tightness (trigger consistency) where a rule is plausible.
- **Reuses (shared reach/stall toolkit):** `build_arms` (forward_battery) · `read_per_second` /
  `read_trade_full`, `S`, `TICK` (trade_flow_exhaustion, root spine) · `rank_auc`,
  `two_sample_boot_ci` (range_expansion) · `pathlen_tk` (velocity_acceleration).

---

## Factor map — 6 top-level veins
| ID | factor | hypothesis (what causes the discretionary read) | data | precedent | status |
|----|--------|--------------------------------------------------|------|-----------|--------|
| **F1** | **Price-speed family** | the move's *speed* (favorable or not) drives hold/cut — the trader's literal account; our one positive lives here | MBP-10 per-second mid | see F1 table below | **active** |
| F2 | Higher-TF / WRB structure | stall happens *at* a 5m/15m level or unfilled WHG vs in open space (his own method) | es_5m_front, whg_*.parquet, wrb_1m | WRB Analysis (M.A. Perry); multiple-timeframe analysis | queued |
| F3 | Generic level context | stall into a level (VWAP / prior-day H/L / session open / round number) vs room to next level | es_1m/5m, vwap (06-11) | VWAP (Berkowitz et al. 1988); support/resistance | queued |
| F4 | Entry-determination | the outcome is largely *set at entry*; entry-context separates better than any exit feature did | (synthesis over F1–F3) | — (lens, not a feature) | queued (after F1–F3) |
| F5 | Conditional / combined | the rule is *gated* — interactions across F1–F4, not any single feature | (all of the above) | PRIM bump-hunting (Friedman & Fisher 1999); stratification | queued (after individual reads) |
| F6 | Trader-state / sequence | prior-trade result, trade-of-day, time-of-day shift the read | episode table | **THIN precedent — flagged**; behavioral-finance sequence effects, not this specific use | queued (exploratory) |

---

## F1 — price-speed family · 6 operationalizations (the immediate work)
`velocity_ratio` (06-13, AUC 0.660) is **one** operationalization: unsigned path-length rate normalized
to the 60s pre-entry window. "Speed" in the trader's sense is a family; these are five more, each
genuinely distinct from velocity_ratio. Pre-registered direction = reach>stall unless noted.

| ID | operationalization | definition (per-second mid, entry-forward) | distinct from velocity_ratio | precedent |
|----|--------------------|---------------------------------------------|------------------------------|-----------|
| **S1** | baseline-relative velocity | early-window path-rate ÷ a **longer** baseline (session ATR / 20-bar realized vol), not the 60s pre-entry | different (longer, regime-level) normalizer — "fast *for this market today*" | ATR (Wilder 1978); realized volatility |
| **S2** | directional (favorable-leg) velocity | **signed** favorable ticks covered per second in the trade's direction | velocity_ratio is **unsigned** path length | momentum / impulse (general price-action) |
| **S3** | time-to-N-ticks | seconds to first **+4 / +8** favorable ticks from entry (lower = faster) | a first-passage *timing* measure, not a rate over a fixed window | first-passage time (stochastic processes); trader "did it take off" |
| **S4** | speed-profile shape | early velocity **slope / sustained-vs-decayed** (did the fast start hold) | velocity_ratio is a single-window *level*; this is the trajectory | Kaufman adaptive/efficiency; persistence |
| **S5** | speed-congruence with the setup WRB | trade velocity ÷ the velocity (range/duration) of the **pt1 WRB** it trades into | ties speed to the structural trigger; untested | WRB Analysis (his method) + range-as-speed — **thin precedent for "congruence" specifically; flagged as our construction** |
| **S6** | impulse-vs-grind | largest single favorable **run** ÷ total favorable move (early window) | a *concentration* measure, not a rate | impulse-vs-corrective (practitioner); run-length |

**Suggested order (richest-first, each one clean probe):** S2 → S3 → S1 → S4 → S6 → S5.
S2 and S3 are the most direct translations of "did the move take off fast *in my favor*" and neither is
what velocity_ratio measured, so they have the best chance of adding an independent read.

---

## How this fits the testing structure
- **Folder:** new phase `06-14_discretionary_factors/`. Probe files `s2_directional_velocity.py`,
  `s3_time_to_ticks.py`, … then `f2_htf_structure.py`, `f3_levels.py`, etc.
- **Imports / run:** probes reuse the 06-13 toolkit + root spine, so run from the **06_ root** with BOTH
  on the path:
  ```
  PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/s2_directional_velocity.py \
      --config config.toml --wrb wrb_1m.parquet
  ```
  (root → spine; `06-13_stall_vs_reach` → build_arms/rank_auc/pathlen; Python auto-adds the script's own
  `06-14` folder for intra-phase imports.) If the dual path is annoying, the alternative is to co-locate
  probes in `06-13_stall_vs_reach/` and keep the single `PYTHONPATH=.` form — a structure-vs-friction call.
- **Registry:** each run appends one row to `test_registry_rows.tsv`, same 21-col legend, `test_id`
  **T-DF01, T-DF02, …**, `family` = `speed` / `structure` / `level` / `state`, `labels_basis`=behavioral,
  `split`=all, `code_ref`=`06-14_discretionary_factors/<probe>.py::<fn>`.
- **Dashboard:** each gets a row in `tests_index.html`. Channel chips: speed ops → existing **Movement**
  chip; F2 → add a **Structure** chip; F3 → add a **Level** chip (same one-line CSS pattern as the
  movement/outcome/exit chips, with matching spine colors). Single table, appended rows (the format you
  kept).
- **Docs accrue as families close:** a per-factor `SPEC_DF-*.md` and a phase `DISCRETIONARY_FINDINGS.md`,
  mirroring SR-A…E.

## Combination plan (F5 — the actual goal)
Once ≥2 speed ops + ≥1 structure/level factor have individual reads, stratify and bump-hunt (PRIM,
Friedman & Fisher 1999) to surface **gated** rules. Individual AUCs are raw material; the discretionary
rule is expected to be an interaction. Combination work is logged like any probe (and is where eventual
validation will most need a holdout).

## Backlog (pre-register here before coding; fill result when run)
| ID | probe | factor | pre-registered shape | status | result |
|----|-------|--------|----------------------|--------|--------|
| S2 | directional favorable velocity | F1 | reach faster favorable ticks/s → AUC>0.5 | **done → candidate #2 (confirmed)** | fav_net_vel 0.669 surv [0.527,0.800]; jk 0.655; p=0.0093; ρ vs VR +0.01; peak NULL (T-DF01/02, SPEC_DF-S2) |
| S3 | time-to-N-ticks (+4/+8/ATRrel) | F1 | reach lower time → AUC>0.5 | **done → NULL** (+ S3b ATR5 post-hoc: weak-grazing, closed) | attain 0.71 vs 0.71; time wrong-way lean 0.572; takeoff ≠ the difference (T-DF03/04, SPEC_DF-S3) |
| S1 | baseline-relative velocity (ATR20/5, 30min-path) | F1 | reach higher vs session baseline | **done → NULL (localizing)** | all 12 cells null; brackets VR → signal = change vs immediate 60s pace (T-DF05, SPEC_DF-S1) |
| S4 | speed-profile shape (sustained) | F1 | reach sustains, stall decays | **done → refinement + robust-null + lead** | h2 0.669 clears (component of fnv → refinement); fade NULL + robust-null ×7 boundaries → POP-AND-FADE DISCONFIRMED, corrected to *no-follow-through/flatline*; h1 null everywhere (first ~20s uninformative); h2@b=20 0.722 = found-by-sweep lead → Feb list (T-DF06/07, SPEC_DF-S4) |
| S6 | impulse-vs-grind (+S6b burst timing) | F1 | (direction unregistered / reach-later) | **done → robust-null ×12** | TEXTURE: gross favorable identical (7.0/7.0, 24.5/24.8tk) → all difference = adverse offset; burst-timing leaned OPPOSITE mechanism prediction → mechanism prose demoted (0-for-2); T-DF08/09, SPEC_DF-S6 |
| S5 | speed-congruence with pt1 WRB | F1 | reach matches WRB impulse | next — LAST F1 item; thin precedent (flagged since backlog creation); pt1 timing gotcha applies (pt1 at/before entry for ~half of reaches) — design pass must handle | — |
| F2 | higher-TF / WRB structure context | F2 | reach aligned w/ 5m structure | queued | — |
| F3 | level context (VWAP / H-L / open) | F3 | stall into a level, reach has room | queued | — |
| F4 | entry-determination synthesis | F4 | entry-context > exit features | queued (after F1–F3) | — |
| F5 | combination / PRIM gating | F5 | a gated rule beats any single feature | queued (after reads) | — |
| F6 | trader-state / sequence | F6 | (thin) state shifts the read | queued (exploratory) | — |
