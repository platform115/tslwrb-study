# STALL-vs-REACH — exploration findings & close-out (COMPREHENSIVE; supersedes earlier draft)

**Question.** Among NON-losing trades, can we recognise EARLY which will STALL short of target
(`below_target_win`, n=29) vs REACH target (`target_reached` non-loser, n=47)?
Target = WRB **pt1** (first 1m WRB in trade direction, completes +60s) — the only target the data defines.
Population resolved deterministically via `build_groups`: 92 Oct-2025 ESZ5 episodes =
47 reach (non-loser) + 29 below_target_win + 16 losers (5 reached pt1 then lost → kept OUT of reach arm).
All 29 stalls are single-exit (not scaled) → `last_exit_utc` is a clean exit instant.

**Status: CLOSED (in-sample).** One marginal, leakage-free lead (early order-flow *persistence*);
magnitude family closed clean; everything else null. Not a strong result.

---

## Designs tried
- **(b) exit-anchored, matched-elapsed** (per-cut AUC, cluster bootstrap over 29 stall cuts, W=60s).
  Built to strip age/duration/regime -> isolates confound-free exit-moment mechanism. Wrong frame for
  *early prediction*; retired after 6 nulls + 1 confounded positive.
- **(c) entry-anchored, forward, pooled** (47 vs 29, two-sample bootstrap, seed 0). The predictor frame.
  Window swept 30/60/120/180/300s. **Survivors-only** control (both arms read full [entry,entry+W],
  no exit-capping) is the leakage-free read; powered at W<=120s (stall n 24/13), underpowered >=180s (5/2).

## Results — design (b), exit-anchored matched-elapsed (W=60s)
| feature | AUC | CI | read |
|---|---|---|---|
| sign autocorr rho1 | 0.542 | [0.426,0.657] | null |
| sign Hurst (DFA) | 0.562 | [0.450,0.673] | null |
| flow level (oriented imbalance) | 0.522 | [0.424,0.617] | null |
| intensity slope | 0.545 | [0.433,0.660] | null |
| **intensity LEVEL** | 0.244 (two-sided 0.756) | [0.167,0.326] | separates — **PEEKED + time-of-day/volatility-regime confounded; NOT absorption; not a candidate** |
| impact/trade (abs) | 0.529 | [0.423,0.635] | null |
| efficiency ratio | 0.477 (0.523) | [0.367,0.581] | null |

Diagnostics: stalls cluster at session open (33% vs 8% in first 30 min); exit-window slope ~0 both
arms (activity gap sustained, not an exit spike); impact null because stalls have 2x trades AND 2x net
move (7 vs 3 tk) -> impact/trade equal (NOT absorption).

## Results — design (c), entry-forward, SURVIVORS-only (leakage-free), W=120s PRIMARY
| feature | AUC | CI | read |
|---|---|---|---|
| **hurst (sign memory)** | **0.657** | **[0.507,0.795]** | **clears 0.5 — the one leakage-free lead** |
| flow_consistency (NEW) | 0.612 | [0.435,0.782] | leaner, no clear |
| ER_abs | 0.600 | [0.422,0.767] | leaner, no clear |
| rho1 | 0.598 | [0.439,0.752] | leaner, no clear |
| flow_level | 0.568 | [0.403,0.734] | leaner, no clear |
| impact/trade | 0.531 | [0.345,0.719] | flat — magnitude family CLOSED in clean frame |

(capped-pooled W>=120 shows slope/ER/abs_move clearing — these are the whole-life-capping ARTIFACT,
collapse in survivors; not signal.)

## The single lead, stated honestly
**Early order flow is marginally more ORGANIZED/PERSISTENT in trades that reach** (developing auctions
sustain same-side signing — Lillo & Farmer 2004). Evidence:
- hurst clears the leakage-free 120s-survivors control (0.657, CI [0.507,0.795]).
- hurst is **reach>stall at ALL 8 reads** (0.562/0.612/0.584/0.607/0.599/0.657/0.605/0.577; mean 0.600).
- flow_consistency, rho1, flow_level, ER all lean the SAME way (sub-threshold) -> one coherent axis.

**Caveats (do not overstate):** lower bound 0.507, stall n=13 in the clean control; across ~60+ AUC
cells this conversation, one clear at ~0.51 is near chance — the evidence is the **directional
consistency**, NOT the single CI. This is ONE axis with ONE clean member + four correlated leaners,
**not five findings**. flow_consistency CORROBORATES, does not independently confirm (shares inputs).

## Closed
- **Magnitude family** (intensity level/slope, impact, abs_move): null in the correct entry-forward
  clean frame. The exit-window intensity-level positive (0.756) was peeked + regime/timing, NOT an
  early predictor (inverts/flattens forward).
- **Exit-window microstructure** (all of design b): retired — wrong frame for early prediction.
- **Session-timing** (stalls cluster at open; session_phase 0.602, CI incl 0.5): regime/descriptive,
  likely month-specific; context not microstructure.

## Meta-conclusion
Second independent phase to land here. Part 1 (loss/exit mining, ~90 cells): "his exit timing is not
encoded in MBP-10 at this resolution." This phase (stall boundary, ~20 feature x window reads): the
trade's order-flow/price character barely separates reach from stall, with one marginal persistence
lean. Per project owner: the trader never documented a rule for exiting failed/stalling trades ->
plausibly discretionary -> a microstructure search SHOULD return near-empty. The negative is consistent
with "little/no stable rule to recover," not only "rule absent from this feed." No mechanism invented.

## To Feb holdout (weak — judge against the cell count)
- **hurst** (DFA sign memory), entry-forward, W=120s, survivors-eligible (hold>=120s), reach>stall.
  The only leakage-free clear; consistent direction across 8 reads. Frozen as a WEAK lead.
- **flow_consistency** — frozen as part of ONE "organized early flow" axis WITH hurst (tested together,
  never composed on October). Not an independent candidate.
- Everything else: do not carry.

## Ledger
~20 feature x window reads this phase + Part 1's ~90 cells feed the Deflated-Sharpe N. A future probe
must read against this count; the hurst lean must clear a multiple-testing-aware bar in Feb, not just 0.5.

## Files (06_trade_flow_exhaustion_CANDIDATE/; all reuse build_groups + horse_race_spine; unit-tested)
sign_persistence.py - sign_persistence_dfa.py - intensity.py - impact.py - efficiency_ratio.py -
forward_battery.py - forward_sweep.py - structure_family.py - STALL_VS_REACH_FINDINGS.md (this) -
test_registry_rows.tsv - NEXT_DIRECTIONS_reach_vs_stall.md
