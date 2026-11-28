# DATA_LEDGER — WHAT MONTHS WE HOLD, WHAT THEY'RE FOR
STATUS: LIVING | v1.0 | 2026-11-28 | The anti-burn ledger: before ANY
run, this page says what each month may be used for. R-11 MONTHS-SPEND
sections in specs are the per-claim spend records; this is the map.

## CORPUS-WIDE HOLDINGS (span every month below)
| asset | span | used for |
|---|---|---|
| es_1m_front.parquet (1m OHLCV, front, unadjusted) | 2021-05 .. 2026-05 | structure: bands, WRB bodies, levels, resolver |
| kme_calendar / news_sets (economic calendar) | 2021-05 .. 2026-05 | FL-WIN / FL-QT event filters |
| his archive (chat_activity + zone refs etc.) | 2021-05 .. 2026-06 | catch metrics, his-side studies |
| es_roll_calendar | corpus | roll-day exclusion (Rule: roll days excluded) |

## PER-MONTH HOLDINGS AND DESIGNATION
| month | 1s flow | tbbo raw | MBP-10 raw | processed depth | his audit | designation TODAY |
|---|---|---|---|---|---|---|
| 2021-09 | YES (container) | drive | drive | no | YES (a2) | SPENT - training for all current claims |
| 2022-02 | YES | drive | drive | book+OFI10+windowed | YES | SPENT - training (depth months pair) |
| 2023-05 | YES | drive | NO | top-of-book only | NO (no his audit) | SPENT - was G2-4's validation pair (T-VL02); results seen -> training-equivalent for all new claims |
| 2024-05 | YES | drive | NO | top-of-book only | NO | SPENT - same as 2023-05 |
| 2024-11 | YES | drive | drive | no | YES | SPENT - training |
| 2025-10 | YES | drive | drive | book+OFI10+windowed | YES | SPENT - training (depth months pair) |
THE BOTTOM LINE: NOTHING in-corpus is clean. Every registered claim's
judge is a FUTURE purchase (D-8). Any run on these months is training-
side by definition and must say so in its R-11 section.

## WHAT EACH TIER'S VALIDATION NEEDS
| line | needs per fresh month | judges |
|---|---|---|
| Tier-P (all G2-x, G3-x; EN-01/02, FL-WIN/QT/RWY, MP-7/8/9) | tbbo + bbo-1s (certified converter lineage); 1m bars + calendar already held | D-8 STAGE 1 |
| Tier-R (Strategy 5 line; EN-03/04, FL-3S, MP-10) | + mbp-10 full month (processed to book_per_sec + OFI10 by the certified pipeline) | D-8 STAGE 2 |
| Catch metrics (Track 1) | his archive slice for the month (already held, free) | both stages |

## D-8 PURCHASE RECOMMENDATION (J gates; nothing bought yet)
Selection criteria: (1) high his-activity so catch is measurable;
(2) regime independence from owned months; (3) era spread incl. the
most current regime. His-activity density (wrb-tagged minutes) from
the archive supports:
| pick | month | his wrb activity | why |
|---|---|---|---|
| RECOMMENDED | 2022-05 | 1273 (top-5 all-time) | rich his-coverage; 2022 bear regime but 3 months clear of owned 2022-02; high-vol era |
| RECOMMENDED | 2026-03 | 816 (best of the last 2 years) | the most current regime - closest to live deployment conditions |
| alternate | 2022-03 | 1537 (richest ever) | adjacency to owned 2022-02 weakens regime independence |
| alternate | 2025-03 | 559 | if 2026 data pricing/availability disappoints |
EXACT PURCHASE LIST per chosen month (Databento, dataset GLBX.MDP3,
ES front contract / parent symbology as before):
- STAGE 1 (buy first, small): schema `tbbo` full month + schema
  `bbo-1s` full month. Order ~1-3 GB compressed per month.
- STAGE 2 (when bandwidth allows, large): schema `mbp-10` full
  month. Order ~8-15 GB compressed per month.
Already held, no purchase needed: 1m bars, economic calendar, his
archive, roll calendar (all span both recommended months).
PRE-PURCHASE CHECKS (run before paying): converter cert on one day
of the new tbbo (sell-side 'A' convention); front-contract volume
check for the month; his-archive slice extract for catch prep.
