# RT2_SPEC — EXCURSION-GATED RETEST + HIS FIRST-VS-RETEST STUDY (T-EN107)
STATUS: FROZEN BEFORE RUN | 2026-11-26 | Rule 2 pre-registration
Trigger: J approved RT v2 after the T-EN106 spec hole (no minimum
excursion -> "retest" instantly satisfied on most crosses), and added
the behavioral observation: "he doesn't always wait for 2nd or 3rd
entry, sometimes takes the first — we need to figure that part out."

## PART A — STUDY: HOW DOES *HE* ENTER RELATIVE TO THE CROSS STREAM?
Population: the 62 G2 ground-truth entries (squeeze x news-window),
training months. For each entry (month, sec, side):
- Match: the latest cross of a G2-3 edge (resolver SQZ + W20 q0.8
  bands) in HIS direction with cross time in [sec-600, sec+60].
  Unmatched entries reported as their own row (no silent drops).
- For the matched edge key (round(e,2), dir), measure over the 600s
  before his entry:
  - n_prior: crosses of the same key before the matched one
  - max_exc: max excursion of mids beyond e between first cross of
    the key and his entry
  - pulled_back: did mids return to within 0.75 of e after reaching
    excursion >= 1.0, before his entry
- Classification (frozen):
  - FIRST-TAKE: n_prior = 0 AND NOT pulled_back
  - RETEST-TAKE: pulled_back (price left by >=1.0 and came back
    within 0.75 before he entered), any n_prior
  - OTHER: the remainder (reported, not forced into a bucket)
- Output: counts per class per month; for FIRST vs RETEST, medians of
  mins-since-release, max_exc, and his per-trade P&L (audited).
Part A is descriptive. No selection decisions are made from it in
this round; if it shows a split worth a conditional rule, that rule
is a NEW spec presented to J first.

## PART B — TEST: EXCURSION-GATED RETEST ENTRY
Mechanic (replaces RT v1's degenerate gate): after a cross of edge e
in direction d at time t0,
1. EXCURSION GATE: mids must reach >= e + X*d (X beyond the edge)
   within the sequence window Wseq = 600s of t0;
2. PULLBACK: after the excursion, mids must return to within pb of e
   (|mid - e| <= pb), still within Wseq of t0;
3. ENTRY: at the pullback touch, place the stop at e + 1.25*d
   (re-break), TTL 300s from the touch. No fill in TTL = no trade.
Crosses that never meet the gate or never pull back = no trade.
Grid (4 cells): X in {1.0, 2.0} pts x pb in {0.25, 0.75}.
Everything else EXACT G2-3: 4A-v2 edge set (resolver SQZ + W20 q0.8
bands), dedupe (round(e,2),dir) per 300s, d=1.25, M7 management
(levels from the shipped MDL v3 config), single position, 5-45min
post-release RTH windows, both training months, no costs.

## HYPOTHESIS (both directions stated)
For: demanding a confirmed failed-continuation before entry removes
the false breaks that make extras cheap (+0.36/trade), raising
per-trade quality toward his (+3.73). Against: his own behavior
(Part A / J's observation) says he often takes the first break;
gating everything on a retest may discard exactly the fast winners
that pay (fat-tail finding: top 10% of fills = 137% of net).

## VERDICT LINES (identical to RT v1, frozen)
- ADOPT: pooled net > +265.4 AND caught >= 46 AND extras net >= 0
  AND both months positive.
- REGISTER AS QUALITY-ALTERNATE: per-trade >= +0.98 AND pooled net
  >= +150 AND caught >= 30 AND both months positive.
- Otherwise: REJECTED; G2-3 stands.
Full standard shown either way; his G2 same-period numbers beside it.
Registry: T-EN107. Sixth training-fitted knob — training-side freeze
after this and the cadence round, per program.
