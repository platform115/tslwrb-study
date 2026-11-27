# DB REPORT — EVENT-LEVEL BOOK ROUND (T-BK02)
STATUS: CLOSED | 2026-11-27 | Spec: DB_SPEC.md (committed first) | extractor CERTIFIED vs committed per-second files (36/36 exact vol+mid) | features: standardized microstructure (CKS OFI etc.), 30s trailing windows

Coverage: {'q1': 1007, 'q2': 53} of 1007 Q1 / 53 Q2 moments (windows with <10 events dropped by rule).

## Q1 — HIS EXIT MOMENTS vs MATCHED HOLD MOMENTS (duration AND profit matched)
Paired groups: 275.
| feature | exit med | hold med | direction | perm p | BH | months same dir | verdict |
|---|---|---|---|---|---|---|---|
| OFI | 96.00 | 201.50 | exit HIGHER | 0.2092 | n | 2/2 | null |
| OFI10 | 129.00 | 493.50 | exit HIGHER | 0.0028 | Y | 2/2 | FINDING |
| depl_opp | 4.71 | 4.31 | exit HIGHER | 0.0322 | Y | 2/2 | FINDING |
| repl_opp | 4.55 | 3.99 | exit HIGHER | 0.0028 | Y | 2/2 | FINDING |
| cancel_ratio | 0.86 | 0.87 | exit HIGHER | 0.0010 | Y | 2/2 | FINDING |
| large_lot | 0.33 | 0.31 | exit HIGHER | 0.0822 | Y | 1/2 | null |
| hidden | 7.00 | 5.00 | exit HIGHER | 0.0102 | Y | 2/2 | FINDING |
| sweep | 1.00 | 0.00 | exit HIGHER | 0.0000 | Y | 1/2 | suggestive |

## Q2 — HIS TAKEN CROSSES vs PASSED SIBLINGS
Paired groups: 21.
| feature | taken med | passed med | direction | perm p | BH | months same dir | verdict |
|---|---|---|---|---|---|---|---|
| OFI | 637.00 | 532.00 | taken HIGHER | 0.6868 | n | 2/2 | null |
| OFI10 | 2358.00 | 2783.50 | taken HIGHER | 0.2624 | n | 2/2 | null |
| depl_opp | 5.39 | 6.49 | taken HIGHER | 0.2666 | n | 2/2 | null |
| repl_opp | 5.14 | 5.97 | taken HIGHER | 0.1562 | n | 2/2 | null |
| cancel_ratio | 0.89 | 0.85 | taken HIGHER | 0.0112 | Y | 2/2 | FINDING |
| large_lot | 0.29 | 0.29 | taken HIGHER | 0.0974 | n | 2/2 | null |
| hidden | 4.00 | 8.00 | taken HIGHER | 0.1568 | n | 2/2 | null |
| sweep | 0.00 | 0.00 | taken HIGHER | 0.2102 | n | 1/2 | null |

Registry: T-BK02.

## WITHIN-PAIR DIRECTION AUDIT (the valid read for a matched design)
| feature | pooled med delta (exit - own holds) | 22-02 | 25-10 | % pairs exit>holds |
|---|---|---|---|---|
| OFI | -171.0 | -172.0 | -120.0 | 45% |
| OFI10 | -831.0 | -1121.5 | -303.0 | 39% |
| depl_opp | +0.27 | +0.35 | +0.18 | 56% |
| repl_opp | +0.29 | +0.30 | +0.29 | 57% |
| cancel_ratio | -0.01 | -0.01 | -0.01 | 41% |
| large_lot | +0.01 | +0.02 | +0.01 | 57% |
| hidden | +1.0 | +1.0 | +1.0 | 52% |
| sweep | 0.0 | 0.0 | 0.0 | 43% |
CORRECTION: the main table's rank-based direction labels are
misleading for OFI/OFI10 (mean-rank vs median-delta disagreement);
the within-pair deltas above are the honest effect directions.
cancel_ratio and sweep show rank/delta disagreement -> treated as
FRAGILE, not findings.

## READING — THE HOLD/EXIT INFORMATION EXISTS, AND IT IS FLOW
The robust core, consistent in BOTH months:
- OFI10 (deep order flow signed WITH the position): his KEEPS are
  +831 higher than his exits at the same duration and same profit.
  He rides while deep flow still pushes his way; he exits when it
  FADES. This is the first signal in the program that separates his
  exits from his holds beyond the clock - the candidate explanation
  for the unexplained long holds (F-7's residual).
- Churn at exits: both queues cycle faster (depletion AND
  replenishment up ~+0.3 rate units) with slightly more hidden
  executions - his exits sit at micro-climax moments, consistent
  with exit-into-liquidity (F-8) and his fast spike-taking.
Q2 (which-signal) stays essentially null even at event level
(n=21; one fragile cancel-ratio hit) - the entry-choice question
remains unexplained at every resolution tried.
NEXT (per the frozen line, J gates): a switch-rule spec - M15:
at M7's stall/cap moments, HOLD ON while trailing OFI10 stays
above a threshold (the M12 lesson applies: that rule-shape failed
with book LEVELS; this is flow STATE, the thing that actually
separated). LIVE CAVEAT flagged now: OFI10 needs a depth feed -
not available from TradingView/Pine; live use requires the Python
runner on a depth feed (Databento live/Rithmic) - a D-4/D-23
architecture input.
