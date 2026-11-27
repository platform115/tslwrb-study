# PARTB_SPEC — D-30 PART B: THE 3s BOOK READ ON TOP OF RWY (T-SR06)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9 + R-11 + R-12
The selection stack test: does F-21's book read (Strategy 5's ACTIVE
trigger) add per-trade quality ON TOP of the structural runway gate
(F-28/29), and on the full 5W universe? Device-side extraction from
RAW full-day MBP-10 (the windowed files cover only 56%/39% of the
touch universe - insufficient, stated).

## R-11 MONTHS-SPEND
Both depth months (2022-02, 2025-10) already spent for surgical-line
claims (T-SR01..05). Spends nothing new; no hold-out exists;
TRAINING-ONLY cap; judge = D-8 stage 2.

## R-12 FINDINGS SWEEP (F-1..F-29)
APPLIED: F-3/F-7 (capture targets/level travel - unchanged exits),
F-11 (haircut expectation stated in verdict reading), F-13 (controls
below), F-17 (flow-fade exit retained), F-19 (break direction =
approach direction), F-21 (THE tested mechanism - the 3s read),
F-22 (ACTIVE/ANY ablation design), F-23/24/25/26 (family-edge
vocabulary IS the RWY gate), F-27 (why only the book read remains),
F-28/F-29 (the RWY gate under test for stacking), F-20 (frozen
constants carried, none re-fit).
NOT-APPLICABLE (why): F-1/F-2 (tail/energy - combo-line decomposition,
superseded here by T-SR03/04 anatomies), F-4/F-5 (flow-agreement -
entry-gate family, dead per F-14 on combo line; RWY is the surviving
selector), F-6 (dual-mode entries - combo-line lanes, no lanes here),
F-8..F-10/F-12 (superseded or corrected earlier), F-14..F-16 (combo-
line management frontier - S5 exits are a different organism),
F-18 (no transplanted his-rules anywhere in this spec).

## DATA + EXTRACTION
Raw GLBX MBP-10 day files (drive), front contract by instrument_id
taken from the certified windowed parquet (unique id per month).
Per day: decode day file, stream row-groups, keep [t-35, t] event
windows for every one of the 1,264 full-RTH touch moments
(lvl_touch_moments_rwy.csv, committed to the drive). Features:
db3_extract's feats_multi VERBATIM (horizons 3/10/30; windows END at
the touch second t - the certified construction; the "3s read" reads
the approach into the touch. Entry arms at touch+3, so knowability
holds with margin). Resumable day-by-day; one reusable tmp file.

## R-9 CONTROLS (abort on fail)
1. OVERLAP CERT: for touch moments shared with db3's covered set,
   raw-path features must match db3_features (|delta| < 1e-6 on
   churn3 components and sweep_3) - proves raw-path == windowed-path.
   Checked on every overlapping moment before any cell is read.
2. Sim controls as T-SR05: builder 1541/1263; 5W full-RTH
   750/+472.1; RWY[2,8] 102/+157.1 reproduced exactly.
## TRIGGER CONSTANT (frozen, no refit)
ACTIVE = churn3 (depl_opp_3 + repl_opp_3) >= T2 OR sweep_3 > 0,
where T2 is the T-SR01 threshold recomputed identically from the
693-touch B universe (a carried constant, never re-fit on the new
extraction).

## CELLS
- 5W-ACTIVE vs 5W-ANY (750 baseline): the read on the full universe.
- RWY-ACTIVE vs RWY-ANY (102 baseline): the stack.
Coverage stated per cell (moments with <10 window events get no
features and stay un-gated - counted and reported).

## VERDICT (frozen flag-lines)
- 5W-ACTIVE upgrade: per-trade > +0.63 AND both months positive.
- RWY-ACTIVE upgrade: per-trade > +1.54 AND n >= 40 AND both months
  positive.
- If RWY-ACTIVE adds nothing while 5W-ACTIVE does: the book signal
  and the structural gate are REDUNDANT (they select the same
  trades) - reportable finding either way.
Partial -> facts to J, J decides. Registry: T-SR06.
