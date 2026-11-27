# G26 REPORT — GATED G2-4 (G2-6 CANDIDATE) (T-EN113)
STATUS: CLOSED | 2026-11-27 | Spec: G26_SPEC.md (committed first) | R-9 CONTROL reproduced exactly | circularity declared: gates derive from this corpus - passing is necessary, not sufficient; final judge = D-8 months

| cell | trades | declined | per-trade | pooled net | by month (22-02/25-10/23-05/24-05) | months pos | removed vs CONTROL: n / net | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 1517 | 0 | +0.32 | +483.2 | +138/+188/+119/+39 | 4/4 | 0 / +0.0 | (reproduced) |
| E | 764 | 1287 | +0.46 | +353.8 | +136/+145/+84/-11 | 3/4 | 758 / +135.1 | fails line |
| P | 913 | 1256 | +0.37 | +333.2 | +87/+81/+94/+71 | 4/4 | 647 / +174.6 | fails line |
| E+P | 478 | 1973 | +0.51 | +243.8 | +93/+43/+74/+35 | 4/4 | 1067 / +257.8 | fails line |

Thresholds frozen in spec: rv30 >= 36.0 (corpus median), room_ahead <= 8.0 (M7 arm). Registry: T-EN113.

## READING — THE PROFILE IS A TILT, NOT A SEPARATOR
Every gate raised per-trade quality exactly as the profile predicted
(+0.32 -> +0.46/+0.37/+0.51) and every gate FAILED the frozen line on
the same condition: the REMOVED trades were net PROFITABLE (+135 /
+175 / +258). The earners are enriched inside the gates but not
contained by them - the fat tail (F-1) lives on BOTH sides of every
entry-time condition we have. AUC 0.647 said precisely this and the
traded P&L now confirms it: entry-time selection at this resolution
concentrates quality at the price of roughly half the net. Note also
the energy gate alone turned 2024-05 NEGATIVE (-11): the weakest
month's few earners happened in quieter tape - single-condition
gating is fragile month to month.
CONSISTENT WITH: G2-5's OOS failure (cap-based selection), SEL's
null (feature-based selection of fills), F-9. Three independent
designs now agree: OUR EDGE RESISTS SUBSETTING. The money is made by
being there broadly and managing well, not by picking entries finely.
IMPLICATIONS (per the spec's outcome line):
- F-register annotated (F-14 added).
- D-25 re-examined: its SELECTION half is weakened; its NEW-ENTRY-
  TYPES half (fade-at-level, level-approach entries - different
  trade universe, not a subset) is untouched by this result.
- The anatomy keeps pointing at MANAGEMENT: stops cost -345 while
  winners' MAE is ~0 (F-4). D-24 (M14 early-adverse exit) is the
  lever this round's failure does NOT touch - and the next natural
  test.
