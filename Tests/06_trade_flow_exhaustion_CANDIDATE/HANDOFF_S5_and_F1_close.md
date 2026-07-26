# HANDOFF — S5 design + F1 close (tslwrb-study, phase 06-14 discretionary factors)
Written at the clean break after T-DF09. Read this first; ledgers and toolkit source uploaded alongside.
ESZ5 Oct-2025 · 92 episodes · binary boundary: 47 target_reached vs 29 below_target_win (16 losers excluded).

## 1. Where the project stands
Exit sweep (06-13/SR-E) proved the cut/hold-a-stalling-winner decision has NO mechanical trigger in the
trade's own tape → discretionary. Phase 06-14 hunts the measurable context behind that discretion.
F1 (price-speed family) is 5/6 done. Remaining: **S5 (speed-congruence with the pt1 WRB)** — then F1
closes and F2 (his WRB/higher-TF structure) / F3 (generic levels: VWAP, prior-day H/L, open, rounds) open.

**Feb holdout list so far:** velocity_ratio (candidate #1, T-SR19/20, AUC 0.660 τ=60 survivors) ·
fav_net_vel (candidate #2, T-DF01/02, 0.669 survivors; decomp: reach 76% net-positive @60s vs stall 50%) ·
h2@b=20 (lead, found-by-sweep, 0.722, shares 40/60s with fav_net_vel, ρ unmeasured) ·
ATRrel@60 attainment (lead-weak, T-DF04, +0.21 [+0.01,+0.40], post-hoc 2nd look, 3 stall attainers).
ρ(fav_net_vel, velocity_ratio) = +0.009 [−0.224,+0.236] — quasi-independent axes.

**Informative robust-nulls:** S3 takeoff (attainment 0.71 vs 0.71 identical; time-to-+4 leans stall-FASTER) ·
S1 session-relative velocity (12 cells; LOCALIZES VR: raw wrong-way / session-norm null / immediate-60s-pace
0.660 → the pre-entry denominator is load-bearing) · S6 concentration (6 cells) · S6b burst timing (6 cells,
leaned OPPOSITE registration — stall bursts later).

**Decisive descriptive (S6 reference cell):** gross favorable movement is IDENTICAL across arms
(max_run 7.0 vs 7.0tk; n_runs 10 vs 10; total_fav 24.5 vs 24.8tk) → the ENTIRE reach/stall difference is
the ADVERSE OFFSET. Adverse-TOTAL probe is ruled out (arithmetic identity with fav_net_vel); adverse
timing/clustering is a legitimate carve-out, unexplored.

**MECHANISM DEMOTION (binding):** the "reaches follow through / stalls flatline" prose is a DESCRIPTION of
the two clearing features, NOT a generative model — its feature predictions went 0-for-2 (pop-and-fade →
fade robust-null ×7 boundaries; reach-late-burst → leans opposite). Argue new probe designs from data
constructions, not from this narrative.

## 2. Standing conventions (all locked; do not re-derive)
- Population via `build_arms(config, wrb_path)` (forward_battery.py) → stall, reach, windowed. Binary label
  ONLY (never time_to_pt1 — SR-C artifact).
- **B-design windows** (user decision): [entry, min(entry+τ, exit)], ≥5s floor, ALL trades included —
  BUT the **survivor subset (hold ≥ τ) is DECISIVE** (anti-circularity: no reach attains target inside the
  window there; also VR's exact arms 45/24 @ τ=60). Exits-within-τ counts printed each run.
- Stats: rank AUC + two-sample bootstrap CI (seed 0, 10000) from range_expansion.py. ≥8 firings/arm or the
  cell is UNINFORMATIVE. All statistics via the toolkit's own scipy-free implementations (the venv has no
  scipy; pandas .corr(method='spearman') will crash — this bug happened once).
- **Redundancy convention (locked):** ρ + pair-bootstrap CI (fav_net_vel_confirm.spearman_boot_ci) on
  survivors@60 vs a PRE-NAMED reference; CI inside (−0.4,+0.4) → new axis; entirely beyond |0.6| →
  redundant (no new candidate; logged as axis-robustness); else INDETERMINATE, logged, no narrative rescue.
- **Grid-first design (user directive):** tunable definitional choices are TESTED in a pre-registered grid,
  not decided by feel. Validity constraints are NOT tunables (survivor frame, seed, floor existence,
  settled windows). Pattern rule fixed pre-output: ≥2 same-direction clears within a rule-slice → `lead`
  (Feb list); single clear → `lead-weak` (logged, Feb list, found-by-sweep provenance); none → robust-null.
- **Exploration framing (user, repeated):** breadth is positive; anything that clears is LOGGED and goes
  to Feb holdout — labels carry provenance (pre-registered vs found-by-sweep vs post-hoc). Discounting
  belongs to validation, not to the search. Validity exclusions (circularity, construction artifacts) do
  NOT soften under any framing.
- **Registry:** one row per probe, 21 columns (match existing rows exactly), test_ids T-DF10+ next.
  Deflated-Sharpe N counts CELLS not rows (grid rows state their look-count in notes). STANDING AUDIT ITEM:
  S1 (12 cells) and S3 (18 cells) rows predate this convention and undercount.
- Docs per family: SPEC_DF-*.md (recreation-grade) + registry rows + dashboard rows (single-table format,
  Movement chip for speed; add Structure/Level chips when F2/F3 open) + backlog status update.
- Run pattern (from 06_trade_flow_exhaustion_CANDIDATE root):
  `PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 06-14_discretionary_factors/<probe>.py --config config.toml --wrb wrb_1m.parquet`
  Every script has `--selftest` on synthetic data; pre-register hypothesis/direction/grid BEFORE code;
  user runs locally (MacBook Air M1, data on external SSD) and pastes output; the LLM never computes results.

## 3. S5 — the design problem (next task; design pass BEFORE any code)
S5 = speed-congruence with the setup WRB: trade's early velocity ÷ the pt1 WRB's own velocity
(range/duration). THIN PRECEDENT — WRB Analysis (M.A. Perry) is his documented method and range-as-speed
is standard, but the congruence RATIO is our construction; flag it in every artifact.

**The trap (why S5 was sequenced last):** pt1 = first in-direction 1m WRB at/after the entry minute, and
pt1_open_el (entry→pt1-open) has median ~49s with p25 NEGATIVE (−14s) — pt1 opens AT OR BEFORE entry for
~half of reaches. Consequences the design must handle:
  (a) If pt1's bar overlaps [entry, entry+τ], the WRB's range partially CONTAINS the trade's early move →
      numerator and denominator share data → built-in correlation, SR-C-class contamination.
  (b) The clean subset (pt1_open_el ≥ τ) was measured in SR-C: roughly 25/21/11 reaches at τ=30/60/120 —
      at τ=60 that is ~21 reaches vs the firing floor of 8; stall-side clean counts UNKNOWN (must be
      printed before any AUC is trusted).
  (c) Design options to argue at the pass: (i) clean-subset only (honest, possibly underpowered — print
      counts first, "UNTESTABLE at this n" is a legitimate F1-closing outcome); (ii) use a PRE-ENTRY WRB
      (last completed in-direction WRB strictly before entry) as denominator instead of pt1 — avoids
      overlap entirely but changes the concept from "the setup WRB" to "the preceding WRB" (deviation
      from his framing; must be flagged); (iii) both as a 2-cell grid with the overlap counts printed.
  Do NOT let the mechanism prose pick the direction (demotion is binding); argue direction from the
  construction or leave it unregistered per the S6 precedent.

## 4. After S5 (the queue)
F1 closes → SPEC/registry/dashboard/backlog housekeeping → F2 (higher-TF/WRB structure: es_5m_front,
whg parquets — his method, biggest build) and F3 (generic levels — 06-11 VWAP infrastructure partially
exists). Then F4 (entry-determination synthesis: does entry-context beat every exit feature — largely
answerable from accumulated results), F5 (PRIM/stratified combination — THE GOAL; needs ≥1 non-speed
axis), F6 (trader-state, exploratory, thin precedent). February holdout: front month resolved by VOLUME,
not assumed.

## 5. Files that travel with this handoff
Ledgers: test_registry_rows.tsv (35 rows) · tests_index.html (43 rows).
Toolkit source (signature truth): trade_flow_exhaustion.py · forward_battery.py · range_expansion.py ·
velocity_acceleration.py · s2_directional_velocity.py · fav_net_vel_confirm.py.
Phase docs: DISCRETIONARY_FACTORS_BACKLOG.md (S5 flagged next) · CURRENT_STATE.md (environment; predates
06-14 — THIS doc carries the 06-14 run pattern).
S5 references: SPEC_SR-C_continuous_outcome.md (pt1 contamination record) · WRB_Definition.txt ·
wrb_1m_parquet.md · config.toml · wrb_1m.parquet.
