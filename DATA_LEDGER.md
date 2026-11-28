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
| **2022-05** | **drive (new)** | **drive (new)** | **drive (new)** | 1s flow + top-of-book (certified) | archive ready (1273 wrb) | **QUARANTINED** | NOTHING - reserved for the D-8 frozen judgments (stages 1+2) |
| **2026-03** | **drive (new)** | **drive (new)** | **drive (new)** | 1s flow + top-of-book (certified; ROLL MONTH - see log) | archive ready (816 wrb) | **QUARANTINED** | NOTHING - reserved for the D-8 frozen judgments; the most-current-regime month |
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
- 2026-11-28: OUTCOME-BLIND PROCESSING DONE for both months
  (convert_v5/v6 on the drive; no outcomes read).
  - 2022-05: flow 1,141,637 secs / 27 days. Cert day 20220517 vs
    mbp-10 emulation: vol 50786/50787 exact; mid 95.3% exact,
    99.5% of misses <=1 tick (median 0.125, max 11.125).
  - 2026-03: FIRST ROLL MONTH in the corpus (ESH6->ESM6). Per-day
    top-volume front ids required (convert_v6): single-month id
    left pre-roll days 97% empty. ROLL GUARD added: an id that is
    day-top on only ONE day is a roll artifact - on 20260316 the
    ESH6-ESM6 calendar spread (id 42018017, price ~49.5)
    out-traded both outrights; re-picked among >=2-day ids ->
    ESM6. Volume transition 20260316 matches es_roll_calendar's
    volume_roll (2026-03-16, ratio 1.37) from independent 1m data.
    20260316 is a roll day - excluded from analysis per Rule.
    Flow 1,349,989 secs / 27 days (weekdays 48-73k, Sundays 3-6k).
    Certs: 20260310 (pre-roll, ESH6) vol 62907/62907 exact, mid
    92.8% exact, 95.9% of misses <=1 tick (median 0.125, max
    16.375); 20260317 (post-roll, ESM6) vol 48797/48798, mid
    91.3% exact, 96.4% of misses <=1 tick (median 0.125, max 4.375).
    NOTE TO J: mid exact-rate a few points below 2022-05's; secs
    off by >1 tick ~0.3% vs ~0.02% in 2022-05 (10x more, still
    small; median miss = half a tick). Reads as faster 2026 quote
    churn under the same sampling conventions, not corruption.
  - Drive outputs + sha256 (first 16): flow_per_sec_2022-05_full
    26aab9ff9bc90772; book_top_per_sec_2022-05 72eacc3d5966e245;
    flow_per_sec_2026-03_full 96832d157740a6a6;
    book_top_per_sec_2026-03 7a7fcf7037d1a0be;
    front_days_2026-03.json c323743bbec721f6.
  - mbp-10 zips remain ZIPPED (stage-2 processing waits for the
    frozen spec).
  - HIS-ARCHIVE COVERAGE CONFIRMED (no extraction needed - catch
    scripts filter the corpus-wide inputs at runtime):
    chat_activity wrb-tagged messages 1273 (2022-05) / 816
    (2026-03) - matches this ledger's recommendation counts
    exactly; his episodes 206 / 137; zone refs 184 / 151.
  - Flow + book + front_days staged to repo Data/inputs,
    sha256 bit-exact vs drive; CHECKSUMS.txt updated.
  - PROCESSING COMPLETE. Next: the frozen D-8 judgment spec (J
    co-drafts; nothing judged until it is frozen and committed).

