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
