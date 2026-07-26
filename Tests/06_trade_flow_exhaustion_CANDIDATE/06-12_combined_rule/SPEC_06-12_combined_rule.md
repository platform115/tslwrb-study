# SPEC 06-12 — combined-rule: union + ladder (coverage vs winner-kill)
Status: COMPLETE for October exploration. In-sample, holdout-pending. Synthesis of the three exit
candidates (S1, S2, z-VWAP) as a combined rule. NET P&L VALUE UNMEASURED (see §5). Not advice.

## 0. Why this exists
S1 (06-7), S2 (06-8/MAE), and z-VWAP (06-11) each separate cuts from runners in-sample and are partially
independent (S1-S2 corr +0.03; S1-VWAP +0.56). This test asks: combined, how many losers do they catch
(COVERAGE) and how many winners do they falsely flag (WINNER-KILL)? Counts only — not P&L.

## 1. Signals (indicative thresholds, @60s, still-open; trades cut before 60s -> S1/VWAP can't read,
## S2 evaluated on full path)
  S1   fire = body_ratio@60 < 0.5            (favorable displacement vs prior-3-bar max body)
  S2   fire = max adverse over [entry,exit] >= 2.5 pt   (path-based)
  VWAP fire = vwap_z@60 (N=20) < 0           (rolling z-scored VWAP distance, unfavorable side)
COVERAGE = fraction of the CUT arm flagged. WINNER-KILL = fraction of the SPARED arm falsely flagged.
Populations: clean (losing16 vs reached47) and pt1 (failed40 vs target_reached52).

## 2. UNION (any-of-3) result  [test_combined_union.py]
  clean: S1 10/16(62%)/wk13/47(28%) · S2 8/16(50%)/wk9(19%) · VWAP 7/16(44%)/wk10(21%) ·
         UNION 16/16(100%)/wk19/47(40%)
  pt1:   S1 20/40(50%)/wk15/52(29%) · S2 6/40(15%)/wk12(23%) · VWAP 8/40(20%)/wk14(27%) ·
         UNION 24/40(60%)/wk24/52(46%)

## 3. LADDER (singles / OR-pairs / majority / AND-pairs / unanimous)  [test_combined_ladder.py]
clean (cut=16 / spared=47)            coverage   winner-kill
  S1 alone                            10/16 62%   13/47 28%
  S2 alone                             8/16 50%    9/47 19%
  VWAP alone                           7/16 44%   10/47 21%
  S1 OR S2                            16/16 100%  16/47 34%   <- EFFICIENT FRONTIER
  S1 OR VWAP                          12/16 75%   17/47 36%
  S2 OR VWAP                          13/16 81%   15/47 32%
  union (any of 3)                    16/16 100%  19/47 40%
  majority (>=2 of 3)                  9/16 56%   10/47 21%   <- DOMINATED
  S1 AND S2                            2/16 12%    6/47 13%
  S1 AND VWAP                          5/16 31%    6/47 13%
  S2 AND VWAP                          2/16 12%    4/47  9%
  unanimous (all 3)                    0/16  0%    3/47  6%
pt1 (cut=40 / spared=52): every column WEAKER — best is union/S1∨S2 at 57-60% coverage, ~40% winner-kill;
  majority 9/40(22%)/14/52(27%); unanimous 1/40(2%)/3/52(6%). (Full pt1 row set in test output.)

## 4. Findings (in-sample)
1. **S1 OR S2 is the efficient point**: 100% loser-coverage (clean) at 34% winner-kill — MATCHES the
   3-way union's coverage at LOWER cost. VWAP adds only winner-kill (40 vs 34), no extra coverage =>
   VWAP is REDUNDANT-FOR-COVERAGE in the combo. (This is deterministic given S1∨S2 already hits 100%:
   adding any signal can only add false positives. So it's logic, not a lucky cell — but the 100%
   itself is 16 losers and may not replicate; re-check on holdout.)
2. **Majority and AND-rules are DOMINATED**: requiring agreement throws away unique catches, because the
   signals catch DIFFERENT losers (the same complementarity that makes the UNION strong makes MAJORITY
   weak). Majority 56%/21% is beaten by S2-alone 50%/19%.
3. **Loss-boundary >> target-boundary**: every combination is markedly stronger on clean than pt1
   (union 100%->60% coverage). The signals read "will it LOSE money", not "will it reach TARGET" — the
   29 profitable-early-exits (below_target_win) sit in pt1's failed arm and the signals correctly stay
   quiet on them. Robust in-sample pattern across union AND ladder. (Still 16/40, one month — holdout-
   pending, tagged in-sample.)

## 5. UNMEASURED — net P&L value
Whether catching losers is WORTH the winner-kill in points is NOT answered here (counts only). A P&L
magnitude test was attempted and SCRATCHED for mechanical errors — its numbers/conclusions are withdrawn
and must not be relied on. The net-value question is OPEN. A corrected P&L test is the natural next build
if net value is wanted; until then "S1∨S2 catches all losers" is a COVERAGE result, not a profit claim.

## 6. Files (in 06-12_combined_rule/)
- test_combined_union.py    CANONICAL — union (any-of-3) coverage + winner-kill, both populations.
- test_combined_ladder.py   CANONICAL — full ladder (singles/pairs/majority/unanimous), both populations.
(test_pnl_magnitude.py — SCRATCHED, do not use / do not re-document.)

## 7. Reproduce (06-12_combined_rule/; SSD mounted)
  python3 test_combined_union.py  --config ../../../config.toml --wrb ../../../wrb_1m.parquet
  python3 test_combined_ladder.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet

## 8. Caveats
Indicative thresholds (not pre-registered/optimized); winner-kill is threshold-sensitive — these are ONE
point on the tradeoff, not the curve. 16 losers across 12 combinations = multiple-comparison risk in
PICKING a combination; read the SHAPE, and any chosen rule needs pre-registration before holdout.
In-sample, October. The "drop VWAP from the combo" call is in-sample; VWAP stays a standalone candidate
(06-11). Net P&L value unmeasured.
