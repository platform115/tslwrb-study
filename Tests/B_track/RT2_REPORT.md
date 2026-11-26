# RT2 REPORT — EXCURSION-GATED RETEST + HIS ENTRY STYLE (T-EN107)
STATUS: CLOSED | 2026-11-26 | Spec: RT2_SPEC.md (committed first) | incumbent G2-3: +265.4 / catch 46 / extras +173.0 / per-trade +0.49 | his G2: +231.2 / 62 trades / +3.73

## PART A — HOW HE ENTERS, RELATIVE TO THE CROSS STREAM (62 ground-truth G2 entries)
| class | n | 22-02/25-10 | his per-trade P&L med (mean) | max excursion before entry (med) | mins since release (med) |
|---|---|---|---|---|---|
| FIRST-TAKE | 17 | 12/5 | +2.50 (+3.63) | 1.00 | 9 |
| RETEST-TAKE | 32 | 21/11 | +2.25 (+4.41) | 3.50 | 12 |
| OTHER | 1 | 1/0 | -0.50 (-0.50) | 0.88 | 11 |
| UNMATCHED | 12 | 6/6 | +1.38 (+2.15) | nan | 13 |

## PART B — EXCURSION-GATED RETEST GRID (everything else = exact G2-3)
| cell | trades | per-trade | net (22-02/25-10) | caught/62 | extras net | verdict |
|---|---|---|---|---|---|---|
| X1.0 pb0.25 | 383 | +0.60 | +228.4 (+137.5/+90.9) | 34 | +157.1 | no |
| X1.0 pb0.75 | 439 | +0.52 | +228.4 (+114.0/+114.4) | 37 | +171.5 | no |
| X2.0 pb0.25 | 300 | +0.80 | +240.8 (+165.2/+75.5) | 32 | +162.9 | no |
| X2.0 pb0.75 | 342 | +0.52 | +176.4 (+153.1/+23.2) | 38 | +151.0 | no |

Registry: T-EN107.

## READING (Part A -> Part B, one picture)
- J's observation CONFIRMED by direct measurement: he is dual-mode.
  Of 50 matched entries, 32 (64%) came after a confirmed
  break-pullback-return sequence, 17 (34%) on the first break with no
  pullback. His P&L is good in BOTH modes (means +4.41 vs +3.63) —
  no clean "he only pays for retests" split exists.
- 12/62 entries sit near no cross of our edge set in his direction
  within 600s — the known coverage ceiling, counted, not hidden.
- Part B follows directly: a retest-ONLY system is structurally
  capped near his 32 retest-takes (catch 32-38 across cells), so it
  cannot reach the catch-46 bar. What the gate DOES do: best cell
  (X2.0 pb0.25) lifts per-trade quality to +0.80 vs the incumbent's
  +0.49 (+63%) while keeping extras strongly positive — the first
  entry-side lever that has moved per-trade quality at all. Still
  below the +0.98 quality-alternate bar.

## VERDICT (per the frozen lines)
No cell ADOPTs (net <= +240.8 < +265.4; catch <= 38 < 46). No cell
reaches QUALITY-ALTERNATE (best per-trade +0.80 < +0.98). REJECTED as
a replacement; G2-3 stands. The two-lane synthesis (first-break lane
+ retest lane, matching his measured dual-mode) is a COMBO and goes
to J before any spec is written.

## IMPLEMENTATION NOTES (bugs caught and fixed before the clean run)
1. First run: single-position busy clock carried across months ->
   2022-02 (earlier epoch) produced zero trades. Fixed: busy resets
   per month (as in rt_round.py). First-run numbers discarded.
2. Part A P&L first joined pnl_recon, which is a BOOLEAN
   reconciliation flag (every class showed mean exactly +1.00 — the
   impossible-coincidence check caught it). Fixed to pnl_calc with
   pnl_stated fallback.
Both are implementation bugs, not spec changes; mechanics ran as
frozen.
