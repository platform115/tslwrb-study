# LVLR_SPEC — D-31: THE 5W FULL-RTH ANATOMY — CAN IT GET SURGICAL? (T-SR03)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11
Object under study: Strategy 5W measured on its FULL RTH touch
universe (the T-SR02 "LVL-ANY" cell: 750 trades, +0.63/trade, the
program's per-trade leader). J's question: where does the quality
live, and can a live-computable restriction make it MORE surgical
(fewer, better trades)? F-14 warning stands: our edge has resisted
subsetting on the combo line - so the bar for promotion here is
pre-registered and high, and descriptive findings are the floor
deliverable (R-10: anatomy before any ceiling claim).

## R-11 MONTHS-SPEND
- Design has seen: 2022-02 + 2025-10 (T-SR01/02 lineage; the +0.63
  cell itself was observed in T-SR02 - this spec exists BECAUSE of
  that observation, so selection pressure is disclosed up front).
- Newly spends: nothing. No hold-out possible (only two depth
  months). Verdict cap: TRAINING-ONLY; candidates promoted here are
  CANDIDATES for a follow-up spec, never adopted in this round.
  Judge of anything promoted = D-8 stage 2.

## R-9 CONTROLS (abort on any miss)
Builder reproduces T-BK03 exactly (1541 approaches / 1263 mb keys);
sim reproduces the T-SR02 cells exactly: S1-ANY 422/+216.5 and
LVL-ANY (5W full-RTH) 750/+472.1.

## LENSES (descriptive; distribution-never-mean; six, frozen)
Per filled trade, live-computable features only:
L1 NEWS PROXIMITY: mins since last calendar release at touch;
   buckets <=5 (burst), 5-45 (window), >45 (quiet).
L2 HOUR (CT): 08:30-10:00, 10:00-12:00, 12:00-14:00, 14:00-15:00+.
L3 LEVEL STATE: (a) density score of the touched level (same scorer
   as the detector); (b) FIRST touch of that level today vs repeat.
L4 APPROACH KINETICS (flow-only; explicitly NOT F-21's book churn):
   (a) speed60 = |mid(touch) - mid(touch-60s)|; (b) pre-touch 10s
   traded volume vs that day's median 10s volume. Pooled terciles.
L5 FILL DELAY: seconds from touch+3 to entry fill (0-120); terciles.
L6 EXIT ANATOMY: P&L by exit type (stop/fade/capture/cap) per month
   - where the money actually comes from.
Stats: per-bucket n / per-trade / median / win%, by month and
pooled; top-vs-rest Mann-Whitney within each lens, BH-FDR q=0.10
across the lens family; FINDING requires BH-pass AND same direction
in both months.

## PROMOTION RULE (frozen - what "more surgical" must prove)
A restriction becomes a follow-up-spec CANDIDATE only if ALL hold:
(1) it is a monotone gradient across its lens (not one lucky cell);
(2) FINDING per the stats line above; (3) the restricted set has
pooled n >= 150 and per-trade >= +0.85 (1.35x the baseline), both
months positive; (4) live-computable at the touch second. Qualifiers
go to J with a one-variable follow-up spec each (uncombined, per
standing directive). Zero qualifiers is a reportable null: the +0.63
is then flat-structured, and surgical gains must come from Part B's
3s book read instead. Registry: T-SR03.
