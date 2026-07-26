# SPEC DF-S4 — directional speed-profile + boundary sensitivity sweep
**Status: h2 clears → REFINEMENT of candidate #2 · fade ROBUST-NULL (pop-and-fade disconfirmed) · h2@b=20 = found-by-sweep LEAD** · phase 06-14 · ESZ5 Oct-2025 · registry T-DF06/T-DF07

## Question
The pointed test of the pop-and-fade mechanism (triangulated from S2's decomposition + S3's null):
does *favorable progress* continue into the second half of the first minute (reaches) or fade (stalls)?
DUPLICATE GUARD: the unsigned two-half ratio was already null (`acceleration`, T-SR19 script) — S4 is
the DIRECTIONAL profile or it's a re-run.

## Design (locked with user)
- Window [entry, entry+60s] split 30/30; survivors (hold≥60, 45/24) DECISIVE; ALL(B) needs ≥5s of H2
  (hold≥35s) — survivor-primary by construction. No 90/120s cells. Raw tk/s only (per S1's null);
  DIFFERENCES not ratios (h1≈0 common; ratios blow up — the old acceleration pathology).
- Features: **h2_net_vel** (PRIMARY) = oriented net displacement over [entry+30,entry+60]/30 — the
  follow-through leg (continuation-validates-initiation logic; O'Neil follow-through-day cited as
  precedent for the LOGIC only — daily timescale, flagged). **fade_delta** = h2 − h1 (pop-and-fade
  direct: stall negative expected). Pre-registered extra: **fade|h1>0** (both arms progressed in H1 —
  the mechanism isolator).
- Redundancy locked (±0.4/±0.6); ρ(h2, fav_net_vel) HIGH BY CONSTRUCTION expected (h2 is a component
  of the fnv endpoint). Redundant/component ⇒ refinement of candidate #2, not a 3rd candidate.

## Results — T-DF06 (s4_speed_profile.py)
h2_net_vel **0.669 [0.516,0.808] SURV — CLEARS** (ALL(B) 0.691). fade_delta 0.551 NULL; fade|h1>0
0.598 NULL (27R/16S). Stall H2 median **+0.000 — flatline, not give-back.**
ρ(h2, fav_net_vel) = +0.668 [0.472,0.816] → INDETERMINATE (component by construction).
ρ(h2, VR) = +0.09. → **No 3rd candidate; logged as refinement.** In-probe selection noted (1 of 2
pre-registered features cleared).

## Results — T-DF07 (s4b_boundary_sweep.py) — post-hoc-motivated sensitivity sweep
User challenged whether parameters could revive fade. One knob (split boundary b ∈ {15..45 by 5}),
interpretation rule fixed pre-output (REGION = ≥3 adjacent clears → lead; SPIKE → lead-weak, logged;
ALL-NULL → robust-null). Exploration disposition per user: anything clearing goes to the Feb holdout
list; labels carry provenance.
- **fade: ALL-NULL at all 7 boundaries → ROBUST-NULL.** Pop-and-fade is dead as stated — third
  independent construction to null it (after SR-E give_back and exit retrace).
- **h1: ALL-NULL** (measured; closes the T-DF06 inference gap) — the first ~15–20s carry no signal.
- **h2: REGION [15,20,25,30] (+isolated 45, read as noise), peak b=20: 0.722 [0.580,0.848]** →
  **lead, Feb list, FOUND-BY-SWEEP flag.** Mechanical caveat attached: as b→0, h2 → fav_net_vel
  (at b=20 they share 40 of 60s); the region is partly convergence to the known candidate;
  ρ(h2@20, fnv) UNMEASURED, expected high. Whether [20s,60s] progress genuinely beats [0,60s]
  (0.722 vs 0.669) is a February question, not an October claim.

## Disposition — corrected mechanism language
**Reaches follow through; stalls flatline.** Not give-back. Discriminative displacement accrues from
~20s onward; initiation (first 15–20s) is uninformative everywhere it was measured (S3 attainment/time,
h1 at 7 boundaries). Dashboard/ledger updated to remove the disconfirmed pop-and-fade phrasing.
Feb holdout list from the speed family so far: fav_net_vel (candidate #2), velocity_ratio (candidate #1),
h2@b=20 (found-by-sweep lead, likely fnv-sharpened). Next: S6 impulse-vs-grind, then S5.

## Dependencies & run (from 06_ root)
```
PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 06-14_discretionary_factors/s4_speed_profile.py   --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 06-14_discretionary_factors/s4b_boundary_sweep.py --config config.toml --wrb wrb_1m.parquet
```
Imports: forward_battery · trade_flow_exhaustion · range_expansion · velocity_acceleration ·
s2_directional_velocity · fav_net_vel_confirm (s4 only). Both `--selftest` (constructed sustained /
pop-and-fade / boundary-located profiles; leg floors; short mirror).

## Recreation notes
Leg boundaries snap to the nearest sampled second (searchsorted on elapsed) — velocities divide by
actual elapsed so rates are correct, but legs can be slightly asymmetric on sparse tape. Sweep cells
overlap heavily (same 69 trades, nested legs): adjacent-cell agreement is partly mechanical — that is
why REGION demands ≥3, and why a found-by-sweep lead carries provenance into the holdout.
