# HOLDOUT FINDINGS — Feb-2022 (tslwrb-study)
**Place at:** `tslwrb-study/holdout_2022-02/HOLDOUT_FINDINGS_2022-02.md`
Adjudication of the 16-row October carry-list on the pre-registered Feb-2022 holdout.
Registry rows **T-DF10–24** are the record; this doc is the synthesis. Written 2026-07-26.

## 0. Frame
- Data: ESH2, instrument_id 5782, MBP-10 windowed parquet (117.4M rows), 02/03 gates PASS
  (OHLC ~100% within 1 tick, volume 99.2% exact) on invasion-month volatility.
- Episodes: 223 Feb-2022 → **213 usable** (8 excluded Feb-28 pre-registration; 2 excluded
  NaT-exit data-integrity pre-registration). Arms: **91 reach / 72 stall / 60 losers**
  (Feb loser rate 27% vs Oct 17% — regime fact).
- Discipline: frozen October specs adjudicated as written (T-DF10/11); where no October bar
  existed, the bar was pre-declared in-chat BEFORE the number and is logged verbatim in the
  registry row (T-DF12+). No re-tuning, no re-sweeping, no post-hoc direction changes.
  Every run: env-guard line, frozen seeds/windows/thresholds, one registry row.

## 1. Scoreboard
| Verdict | Tests (registry) |
|---|---|
| **CONFIRMED (7)** | in_trade_flow_exhaustion 0.805 [0.741,0.860] (T-DF10) · early_flow_confirmation 0.683 [0.633,0.729] (T-DF11) · fav_net_vel 0.649 [0.556,0.739] (T-DF13) · h2@b=20 0.618 [0.521,0.715] (T-DF14) · S1/S2 complementarity, corr +0.05, 15 temporal (T-DF20) · **wrb_body_progress S1 0.871 [0.817,0.916]** (T-DF21) · combined S1∨S2 90%/25% (T-DF24) |
| **CONFIRMED-WEAK (2)** | whg_gap_capture setup — exists (37%), extension discriminates; quality-skew & launch-level did not replicate (T-DF22) · z-VWAP 0.633 [0.553,0.707] — passes its bar, dominated & subsumed by S1 (T-DF23) |
| **REJECTED (3+1)** | velocity_ratio 0.440, decomposition INVERTED (T-DF12) · VR sweep null all cells (T-DF19) · hurst 0.460 (T-DF17) · [velocity_acceleration: accel null, VR leg dead (T-DF16)] |
| **REPLICATED NULLS / FAMILY (3)** | fav_peak_vel & norms stayed null; τ=30 all-null (T-DF15) · acceleration null (T-DF16) · s4 profile = s4b b=30 cell, fade null (T-DF18) |
| **ON HOLD (1)** | loser_submodes — code never committed, nothing frozen; revisit post-Feb |

## 2. The pattern (the actual finding)
**Every directional signal confirmed; every unsigned-pace signal died.**
- Confirmed axes reduce to roughly THREE validated things, not seven independent facts:
  (1) **directional early flow** (oriented aggressor volume: T-DF10/11),
  (2) **body-progress toward the WRB target** (S1: T-DF21, the strongest single signal,
      0.871 clean, hazard peak @60s, calibration monotonic P(cut) 0.77→0.08),
  (3) **net favorable displacement** (fav_net_vel + its h2 refinement: T-DF13/14/18) —
      quasi-independent of the dead VR axis (ρ +0.14 [−0.04,+0.31]).
- Rejected axis: **unsigned speed/pace** (velocity_ratio and everything built on it).
  October's 0.660/jackknife-robust/p=0.014 clear inverted outright in February. "Is it
  moving fast" is not the trader's read; "is it moving MY WAY, with flow behind it" is.
- The two-part exit system is now out-of-sample fact: S1 (not building) + S2 (went against
  me) are complementary (different losers, corr +0.05, S1 earlier on 15), and S1∨S2 at
  frozen thresholds covers 90% of Feb losers at 25% winner-kill (ratio 3.6:1 > Oct 2.9:1).
  Adding z-VWAP buys ZERO coverage (+6 kills): the generic baseline is a weaker correlate
  of S1 (corr +0.71, VWAP-only losers 0/44), not an independent axis.

## 3. Honest limits (carry these forward verbatim)
1. **Net P&L is UNMEASURED.** 90%/25% is a coverage/kill count, not a value claim. The
   06-12 P&L machinery was withdrawn in October and was not rebuilt here.
2. **Bar provenance is mixed.** T-DF10/11 had October-frozen decision rules; T-DF12–24 bars
   were pre-declared mid-holdout (before each number, logged). A stricter regime would have
   frozen every bar in October. T-DF24's coverage leg was arithmetically pre-known from
   T-DF20; the blind weight was moved to winner-kill and that is stated in the row.
3. **Correlated confirmations.** The 7 confirmations share trades and families; treat as ~3
   validated axes. Deflated-Sharpe accounting should count the October discovery grid AND
   these 15 holdout rows.
4. **Two-month evidence.** Oct-2025 (low vol) + Feb-2022 (crisis vol) is regime-diverse but
   still n=2 months, ~315 episodes, one trader. Confirmed ≠ deployable.
5. **Feb-specific observations logged, NOT promoted** (would be discovery-on-holdout to
   chase here): ER_abs cleared both frames @60/120 (T-DF17 notes) · WHG early-progress
   INVERTED (0.288, n=13 failed-open, T-DF22) · S2-alone much stronger in Feb (73%/5%) ·
   session_phase 0.610. Each needs its own pre-registered test on a THIRD dataset.

## 4. What unblocks next (queue, user decides)
- **Port confirmed rules to es-trading-agent-v3 YAML** — S1 (body_ratio@60 < 0.5), S2
  (max_adv ≥ 2.5pt), S1∨S2 gate; flow features if the engine can host them. The P&L question
  gets answered THERE, in the backtester, not by resurrecting 06-12.
- **Third-dataset checks** for the §3.5 observations and the confirmed-weak rows (WHG setup,
  z-VWAP) if wanted.
- **06-14 exploration resumes on October** where it paused (S5 design pass at the F1 seam)
  — the holdout does not close the discovery program; it prunes it. VR-derived veins are dead;
  directional/adverse-offset veins are alive and now validated as the right neighborhood.
- **loser_submodes**: design on October first if revived (nothing frozen exists).

## 5. Reproduction
Every run: `TSLWRB_MONTH=2022-02 TSLWRB_SYMBOL=ESH2 TSLWRB_IID=5782` env prefix +
`--config holdout_2022-02/config.toml` (exact per-row commands in registry notes).
Data prep: HOLDOUT_RUNBOOK_2022-02.md steps 0–6 (all gates recorded there).
Parameterization: HANDOFF_step6a_parameterization.md (Option A env-vars; October
reproduces bit-for-bit with env unset — proven via velocity_ratio_confirm 0.660 smoke test).
