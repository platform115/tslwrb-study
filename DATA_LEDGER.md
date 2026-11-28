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

## PER-MONTH REFERENCE TABLE (J's tracking table - the one to check first)
| month | bbo-1s | tbbo | mbp-10 | processed | his audit | designation | what has been tested / judged there |
|---|---|---|---|---|---|---|---|
| 2021-09 | drive | drive | drive (raw) | 1s flow | YES | SPENT (training) | training for every current claim; his-entry audits |
| 2022-02 | drive | drive | drive (raw) | 1s flow + book + OFI10 | YES | SPENT (training) | depth-pair: every surgical-line claim (T-SR01..08, T-SA02) + combo training + deep-book studies |
| 2023-05 | drive | drive | NO | 1s flow + top-of-book | NO | SPENT (validation used) | JUDGED G2-3/G2-4/G2-5 out-of-sample (T-VL01/T-VL02 - G2-4's validation pair); training-equivalent since |
| 2024-05 | drive | drive | NO | 1s flow + top-of-book | NO | SPENT (validation used) | same pair as 2023-05 |
| 2024-11 | drive | drive | drive (raw) | 1s flow | YES | SPENT (training) | training; his-entry audits |
| 2025-10 | drive | drive | drive (raw) | 1s flow + book + OFI10 | YES | SPENT (training) | depth-pair twin of 2022-02 |
| **2022-05** | **drive (new)** | **drive (new)** | **drive (new)** | none yet | archive ready (1273 wrb) | **QUARANTINED** | NOTHING - reserved for the D-8 frozen judgments (stages 1+2) |
| **2026-03** | **drive (new)** | **drive (new)** | **drive (new)** | none yet | archive ready (816 wrb) | **QUARANTINED** | NOTHING - reserved for the D-8 frozen judgments; the most-current-regime month |
QUARANTINE RULES: (1) no script touches a QUARANTINED month except
the frozen D-8 judgment spec (J gates it) and the pre-judgment
processing pipeline (convert + cert, which reads no outcomes);
(2) the catch-by-group peek at unmined groups (G1/G4/G5) is an
EXPLICIT POST-JUDGMENT GATE - J decides whether to spend these
months' future G4/G5-validation usefulness (decided 2026-11-28);
(3) every judgment result updates the "tested there" column in the
same commit.

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

## EVENT LOG
- 2026-11-28: F-36 stamp fix + T-RH02 re-mint. Designations unchanged (all
  six months remain SPENT). D-8 purchase UNBLOCKED from the program
  side - awaiting J's go on the recommended months.
- 2026-11-28: PURCHASE LANDED - 2022-05 + 2026-03 on the drive, all three
  products (tbbo, bbo-1s, mbp-10; 27 day-files each; zips verified).
  Both months QUARANTINED. Next pipeline steps (outcome-blind):
  unzip, one-day converter cert per month, per-second flow build,
  his-slice extraction, then the frozen D-8 judgment spec to J.

