# TL REPORT — TWO-LANE ENTRY: FIRST-BREAK + RETEST (T-EN108)
STATUS: CLOSED | 2026-11-26 | Spec: TL_SPEC.md (committed first) | incumbent G2-3: +265.4 / 542 / catch 46 / extras +173.0 / per-trade +0.49 | his G2: +231.2 / 62 / +3.73

| cell | trades (L1/L2) | per-trade | net (22-02/25-10) | caught/62 | extras net | lane2 net | verdict |
|---|---|---|---|---|---|---|---|
| CONTROL | 607 (607/0) | +0.45 | +276.1 (+111.8/+164.4) | 47 | +185.6 | +0.0 | MISMATCH - RUN INVALID |
| TL-A | 760 (490/270) | +0.36 | +272.2 (+108.9/+163.4) | 47 | +207.4 | +71.9 | ADOPT |
| TL-B | 757 (517/240) | +0.43 | +325.1 (+137.6/+187.5) | 48 | +246.8 | +66.2 | ADOPT |

Registry: T-EN108.

## CONTROL GATE TRIPPED — ENGINE DEFECT FOUND IN THE INCUMBENT (Rule 3)
The control arm (lane 1 only, new engine) did NOT reproduce G2-3:
607 trades / +276.1 / catch 47 vs the recorded 542 / +265.4 / 46.
Root cause, confirmed exactly: the original engine (b2v2_run.py and
every combo backtest before it) applies the single-position rule in
CROSS order, not FILL order. When stop A (placed first, fills later)
and stop B (placed second, fills earlier) are both working, the old
engine gives the position to A and discards B — but a real account
is filled by B first and cancels A. The new engine sorts candidate
fills by fill time, which is the executable convention. Rerunning
the new engine with the OLD (cross-order) convention reproduces the
recorded G2-3 line to the decimal: 542 trades, +265.4
(+140.5/+124.9). The mismatch is fully explained; no other
difference exists.

Scope: this convention sits in every prior combo backtest (B4 line,
G2-1, G2-2, G2-3, RT rounds). It is not lookahead — no future
information improves P&L — but it is not executable as simulated.
Direction of the correction here: realistic ordering slightly HELPS
(+276.1 vs +265.4), i.e. the recorded numbers were not inflated by
the defect on this config.

## NUMBERS UNDER THE REALISTIC ENGINE (provisional until J rules)
| cell | trades (L1/L2) | per-trade | net | caught/62 | extras |
|---|---|---|---|---|---|
| lane1-only ("G2-3 corrected") | 607 | +0.45 | +276.1 | 47 | +185.6 |
| TL-A (+ retest X2.0 pb0.25) | 760 (490/270) | +0.36 | +272.2 | 47 | +207.4 |
| TL-B (+ retest X1.0 pb0.75) | 757 (517/240) | +0.43 | +325.1 | 48 | +246.8 |
Read against the corrected incumbent (+276.1/47), not the frozen
+265.4 line: TL-A LOSES net (-3.9) — its lane 2 subtracts. TL-B adds
+49.0 net and +61.2 extras for +1 catch, but its lane-2 trades earn
only +0.28/trade (240 trades), diluting per-trade 0.45 -> 0.43.

## VERDICT STATUS
Per the frozen spec, the control mismatch makes the pre-stated
verdict lines unjudgeable as written (they were calibrated to the
defective convention). NO ADOPTION is declared. Two decisions belong
to J:
1. RE-BASELINE: adopt the fill-time engine as the standard and
   restate the incumbent (G2-3 becomes +276.1 / 607 / 47 / +185.6),
   keeping the old numbers in the matrix marked "cross-order
   convention"; all future runs use fill-time.
2. TL-B: judged against the corrected incumbent it clears net,
   catch, extras and both months — but buys total P&L with 240
   low-quality trades (+0.28 each). Adopt, register as alternate,
   or reject on the quality argument.
