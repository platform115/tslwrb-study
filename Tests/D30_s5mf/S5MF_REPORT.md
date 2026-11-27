# S5MF REPORT — S5-MF PART A: FAMILY-EDGE TOUCHES, ANY ARM (T-SR02)
STATUS: CLOSED | 2026-11-27 | Spec: S5MF_SPEC.md (frozen first) | R-9 dual controls exact (builder 1541/1263; S1-ANY 422/+216.5) | Tier-R | TRAINING-ONLY cap per R-11

NOTE: the certified mb list excludes day-slice NO_TEST rows (an artifact of the T-BK03 labeler); the LVL-ANY and MF-ANY cells use the spec's clean definition (full-series touch within 600s, no outcome machinery) - for the incumbent universe that differs from mb by exactly 1 touch in 1264.

| cell | touches | trades | win | per-trade | pooled | by month (22-02/25-10) | worst | exits (stop/fade/capture/cap) |
|---|---|---|---|---|---|---|---|---|
| S1-ANY control (693 covered) | 693 | 422 | 50% | +0.51 | +216.5 | +134/+82 | -2.00 | 169/146/107/0 |
| LVL-ANY (full RTH) | 1264 | 750 | 47% | +0.63 | +472.1 | +195/+278 | -2.00 | 353/149/237/11 |
| MF-ANY (family edges) | 45454 | 4369 | 46% | +0.45 | +1985.6 | +1031/+955 | -2.00 | 1848/1058/1306/157 |

## PER-FAMILY (MF-ANY; first-family tag, shared busy — NOT additive)
| family | trades | net | per-trade | months net<0 |
|---|---|---|---|---|
| GAP | 1400 | +733.6 | +0.52 | 0/2 |
| PDY | 26 | -2.8 | -0.11 | 1/2 |
| REA | 508 | +201.6 | +0.40 | 0/2 |
| SHD | 1651 | +781.9 | +0.47 | 0/2 |
| SQZ | 145 | +87.0 | +0.60 | 0/2 |
| WRB | 639 | +184.2 | +0.29 | 0/2 |

## VERDICT vs THE FROZEN LINES
- controls exact: PASS
- MF-ANY pooled > LVL-ANY pooled: PASS (+1985.6 vs +472.1)
- MF-ANY per-trade >= +0.40: PASS (+0.45)
- both months > 0: PASS
- worst trade >= -2.1: PASS (-2.00)
- no unflagged toxic family: PASS
OVERALL: REGISTER S5-MF TRAINING-ONLY

Part B deliverable: mf_touch_moments.csv (45454 touch moments) for device-side 3s extraction.

Registry: T-SR02.
