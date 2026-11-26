# CD_SPEC — CADENCE ROUND: CAP ENTRIES PER NEWS WINDOW (T-EN110)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J ordered #2 (cadence) after the retest line closed. He
trades ~1.4/day; we fire ~8x his frequency. Question: does taking
only the first N trades per news window keep the value and drop the
noise?

## MECHANIC
Exact G2-3 configuration on the FILL-TIME engine (the standard since
T-EN108): lane-1 entries only, M7 management, single position, both
training months. Each candidate fill belongs to the news event
window (release es) whose scan produced its cross. Cells cap the
number of FILLED trades per (month, es) window: once N trades have
filled in a window, later candidate fills in that window are
discarded. N in {1, 2, 3}; CONTROL = uncapped.

## MANDATORY CHECKS (run aborts and reports nothing if any fail)
1. CONTROL reproduces the corrected G2-3 line EXACTLY:
   607 trades / +276.1 pooled / catch 47 / extras +185.6.
2. Monotonicity: trades(N=1) <= trades(N=2) <= trades(N=3) <=
   trades(CONTROL), per month and pooled.
3. Subset: every capped cell's (fill second, edge key) set is a
   subset of CONTROL's.
4. No duplicate (fill second, edge key) within any cell; every cell
   has > 0 trades in each month.

## DESCRIPTIVE ANCHOR (reported beside the grid)
HIS cadence: distribution of his 62 G2 entries per news window
(1 / 2 / 3+ per window) — the behavior the cap is imitating.

## HYPOTHESIS (both ways)
For: his cadence is sparse; the first fill(s) in a window carry the
move, later fills chase it — capping raises per-trade quality with
small net cost. Against: the fat-tail finding (top 10% of fills =
137% of net) — if big winners arrive later in windows, capping
amputates the tail.

## VERDICT LINES (frozen; calibrated to the CORRECTED incumbent)
- ADOPT: pooled net > +276.1 AND caught >= 47 AND extras net >= 0
  AND both months positive.
- QUALITY-ALTERNATE: per-trade >= +0.98 AND pooled net >= +150 AND
  caught >= 30 AND both months positive.
- Otherwise REJECTED; G2-3 (and registered alternate G2-4) stand.
Full standard either way; his G2 line (+231.2 / 62 / +3.73) beside
it. Registry: T-EN110. Last pre-freeze entry round unless J orders
otherwise.
