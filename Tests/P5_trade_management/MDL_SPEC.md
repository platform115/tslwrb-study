# MDL SPEC — MULTI-DAY LEVEL DETECTOR (pre-registered)
STATUS: FROZEN | 2026-11-25 | Registry: T-IM50 | detector-layer build
Primary goal: recover HIS key levels from price-computable inputs.
Design constraint (J + census): built from HIS structure families; no
pivot/POC/VWAP concepts as candidates - generics are the CONTROL arm.
## INPUTS (per COMPLETED session day; all certified machinery)
Reaction evidence records (price, day, family, formed_in_news):
daily swing highs/lows (certified swing + zigzag detectors); WRB body
edges; unfilled hidden-gap edges; shadow-zone edges.
## CLUSTERING (ranges, J's rule)
Trailing window {20, 40} days; tolerance {2, 3} pts; a LEVEL = >= {3, 4}
distinct member-DAYS within tolerance; level price = member median;
score = member count x 0.97^age_days; a level deactivates after a close
beyond it by 5+ pts.
## KNOWABILITY (R-1)
Day-d evidence becomes usable at day d+1's open; truncation check at
day boundaries is part of the build.
## PRE-STATED VERDICT LINES (no surprises - J)
RECOVERY CHECK vs his stated keys (the 146 priced mentions + S4 cluster
centers): recovered = an active generated level within 3 pts on the
date. >=50% = fit for the M6C exit path; 25-50% = partial, investigate
before use; <25% = UNFIT for his-path. Comparison arm: identical check
for generic levels (prior-day/weekly H/L/C).
INDEPENDENT-VALUE CHECK (J: save useful-but-not-his): reaction rate at
generated levels vs matched random prices, same sessions - beyond-
chance reactions = retained as an OWN-SYSTEM asset regardless of
recovery outcome, labeled as such.
## OUTPUT
Levels parquet (checksummed) + report with both checks + the his-vs-
generic comparison. Review gate: J sees the checks before ANY rule
(M6C stage 1 or entries) consumes a generated level.

## V2 ADDENDUM (pre-registered 2026-11-25, J-approved; frozen before run)
REVEALED-PREFERENCE TEACHING SET (J: use ALL the data): his-important
levels = clusters over price x time of EVERY attention trace - entry
prices + exit prices (all episodes, full corpus), mention-linked object
edges, priced mentions, alert stamps. A region active on >= 3 distinct
days within tolerance {2,3} pts over a trailing 60-day window = a
REVEALED KEY. Teaching-only; never ships.
V2 MARKET EVIDENCE (the deficiency fix): add 5m and 15m WRB body edges
(certified definition, body > max of prior 3 bodies, computed from
resampled bars) and shadow-zone edges where available; news-born
evidence double-weighted in clustering.
V2 RECOVERY: primary target = the revealed-key set (region recovered if
a generated level sits within 3 pts while it is active); secondary =
the 55 priced key mentions (continuity with v1). Same verdict bands
(>=50% fit / 25-50% partial / <25% unfit) now applied to the PRIMARY
target. Same review gate before anything consumes a level.

## V4 ADDENDUM (pre-registered 2026-11-26; J's scale challenge)
Fixed-point parameters embed era drift over a 3,400->6,900 price range.
V4 = the same detector with a FIXED META-RULE generating parameters:
tolerance = {0.04%, 0.06%} of the local price (~1.8/2.6 pts at 4400,
~2.7/4.1 at 6800); kill = 2.5 x tolerance; member threshold unchanged.
M7-scaled: reach = 4 x tolerance; pullback = 0.3 x tolerance (floor one
tick); stall/stop unchanged this round (management scaling is its own
later question). Head-to-head vs the fixed version under the SAME
frozen bars (recovery bands; stage-1 >+123.9; joint >+135.8 etc.).
The pre-committed validation months (2023-05, 2024-05, J purchasing)
arbitrate whichever ships.
