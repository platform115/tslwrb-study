# DB2 REPORT — LEVEL-APPROACH UNIVERSE + G3 FEATURES (T-BK03)
STATUS: CLOSED | 2026-11-27 | Spec: DB2_SPEC.md + addendum 1 (touch-required outcomes; base-rate tell caught the flaw pre-analysis) | extractor: certified T-BK02 lineage

E1 universe: 1541 approaches; with book features 844 (windowed MBP-10 covers news windows only - coverage 55%, skewed to news-window approaches by construction; stated).
Outcome base rates (with-features set): {'HOLD': 339, 'BREAK': 335, 'NO_TEST': 141, 'CHOP': 29}

## HOLDS vs BREAKS ON BOOK STATE AT THE APPROACH (n=339 vs 335)
NOTE: features were extracted signed by APPROACH direction (side = direction of travel toward the level), so positive OFI = flow pressing TOWARD the level.
| feature | hold med | break med | p | BH | months same dir | verdict |
|---|---|---|---|---|---|---|
| OFI | 110.00 | 135.00 | 0.9502 | n | 1/2 | null |
| OFI10 | 324.00 | -29.00 | 0.8290 | n | 2/2 | null |
| depl_opp | 4.75 | 5.14 | 0.4126 | n | 1/2 | null |
| repl_opp | 4.26 | 4.55 | 0.5694 | n | 1/2 | null |
| cancel_ratio | 0.87 | 0.87 | 0.9683 | n | 2/2 | null |
| large_lot | 0.33 | 0.33 | 0.3560 | n | 1/2 | null |
| hidden | 9.00 | 8.00 | 0.9924 | n | 1/2 | null |
| sweep | 1.00 | 1.00 | 0.8285 | n | 1/2 | null |

## HIS BEHAVIOR AT THESE APPROACHES (descriptive)
- BREAK: 52 approaches he traded (fading the approach on 17)
- CHOP: 3 approaches he traded (fading the approach on 2)
- HOLD: 36 approaches he traded (fading the approach on 13)
- NO_TEST: 10 approaches he traded (fading the approach on 9)

## E2 — G3 FEATURE BANK: 151 of 151 G3 entries have event-book features (saved in db2_features.parquet for the D-5 cycle; no analysis this round).

FINDINGS (0) -> D-25 design inputs (J gates).
Registry: T-BK03.

## READING — A CLEAN NULL AND A COURSE CORRECTION
1. THE NULL (339 vs 335, the cleanest case-control of the program):
   book state in the 30s BEFORE a level approach predicts NOTHING
   about hold vs break. The 50/50 coin is not tilted by pre-approach
   flow. Honest scope limit: we measured the trailing window at zone
   ENTRY - the touch reaction itself (first seconds AT the level) is
   a different, untested lens and belongs to D-25's design if wanted.
2. THE COURSE CORRECTION (his behavior at these same approaches):
   he traded 101 of them - and he is BREAK-BIASED at levels: 52
   breaks vs 36 holds traded, and he fades the approach in only a
   minority of cases (17/52, 13/36). The D-25 premise "fade-at-level
   like him" is WEAKENED: at levels, his primary mode is trading the
   BREAK; fading is his minority play. D-25's his-like entry design
   should center on level-BREAK participation (which our G2 line
   already approximates) and level-context selection, not fading.
3. DELIVERED REGARDLESS: the full approach universe with outcomes
   (1,541 events, 4-month-extensible price-side), the 50/50 base
   rate (any level entry needs a discriminator to beat a coin), and
   the COMPLETE G3 feature bank (151/151 entries).
NEXT CHEAP STEP (no drive needed): hold-vs-break on PRICE-side
discriminators (level score/age, prior tests, approach speed, time
of day) - the Tier-P question D-25 actually needs answered.
