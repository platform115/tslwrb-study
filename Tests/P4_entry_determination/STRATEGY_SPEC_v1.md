# Strategy spec v1 — FROZEN before any backtest runs (2026-11-15, user-approved defaults)

Scope: profit test on the two discovery months first (full pressure data), then the
validation months. Sizing, commissions and slippage are out of scope (standing
instruction). Variant policy (user): these defaults are v1; future variants are
welcome and run as RECORDED AMENDMENTS (spec v2, v3... each committed before its
run) — never silent edits to this file.

## Entry
- Universe: RTH 08:30–15:00 CT (project convention; where the rules validated) —
  not his personal desk windows.
- Trigger: a 1-minute WRB completes AND rule v6 scores >= 6 of 10
  (frozen settings: event<=15min · zone on 3m/5m · body>=2x prior-session median
  WRB body · 5-min ground>=1.5x trailing-2h median · flow>2 c/s · template minute
  · within 24tk of reaction-WRB edge · 10m zone · 15-min flow<4.6 · 15-min-lagged
  ground above typical). Strictness dial (k) reported as sensitivity, not re-tuned.
- Direction: sign of the last 5 minutes' net move (skip if zero).
- Fill: next bar's open after the trigger (conservative primary); signal-bar close
  reported as the optimistic variant.
- One position at a time; 5-minute cooldown after any exit.

## Exit
- Stop: 2.5 points adverse excursion (S2, holdout-validated loser signature).
- Target: far edge of the interval entered in (reaction-WRB body / zone; T-EX01,
  the 84% traverse). Comparison arm: fixed 2-point target.
- Time stop: exit at market after the episode-table median hold (computed from
  his episodes before the run and written into the run header).
- NOTE, honest: the stop number is validated; the target/time-stop assembly is
  NOT — this test is its first trial.

## Two readings, both reported
1. STANDALONE SYSTEM: all flagged signals traded by the rules above; P&L, win
   rate, average win/loss, equity path, worst stretch. Tests the rules as OUR
   system (it will take flagged signals he skipped).
2. IMITATION TEST (user requirement): restrict to the flagged signals HE also
   took; compare the system's simulated results on those trades against his own
   realized results from the episode table (same trades, his exits vs ours), plus
   overlap stats (share of his entries the system takes; share of system trades
   that were his). Tests how faithfully the reconstruction reproduces him.

## Pass/fail reading
- No pre-registered profit bar for v1 (first trial of an assembled exit stack);
  the deliverable is the full honest readout of both frames. Amendments follow
  the recorded-amendment rule.
