# PARSER v3 SPEC — his structure references (S1, T-IM15)
> Status: SPEC FOR REVIEW. The DB (`his_zone_refs.parquet`) is NOT
> regenerated until this spec + the 50 sample parses pass the review gate.

## Purpose
Upgrade the v2 extractor (p6_9) with everything the T-IM13 hand read taught:
the full object vocabulary, the relational verbs that caused 522 parseable
misses, correction-linking, boilerplate/personal filters, and an open-enum
policy so nothing new is ever silently dropped.

## Row schema (one row per structure reference)
| field | values |
|---|---|
| ts_utc, month | message stamp |
| kind | open enum, ordered match (below) |
| tier | key / regular / small / old / none (zones) |
| direction | up / down / none (hidden gaps, shadows, WRBs) |
| state | open / unfilled / filled / none (hidden gaps) |
| recency_cue | most_recent / prior / new / old / today / none |
| relation | open enum (below) |
| role | S / R / none (side label when stated) |
| role_flip | True when "acting like a/the <other> area" phrasing |
| tf | timeframe token if attached (1m/2m/3m/5m/15m/60m/daily/...) |
| price_1, price_2 | explicit prices (NaN if none) |
| instrument | ES / NQ / VIX / YM / CL / RTY / SPY / SOXL / QQQ / DIA / breadth |
| emphasis | True when !, caps word, "very important/careful", repeated-ref cues |
| ref_type | explicit_price / relational / event / mention |
| confidence | high / med / low |
| is_correction | True when the message corrects a prior reference |
| corrects_ts | stamp of the patched message (nearest prior ref <= 15 min) |
| is_boilerplate / is_personal | filter flags (rows KEPT, flagged, never dropped) |
| needs_review | low confidence, non-ES, or open-enum catch |
| raw | trimmed text |

## KINDS — ordered match (first hit wins; one row per kind found)
1. `key_kme_wrb` — "key kme wrb zone|key kme zone|key kme" (+tier words
   small/old; "midpoint" flag)
2. `kme_wrb_zone` — "kme wrb zone" without key (his "regular KME WRB Zones")
3. `hidden_gap` — "hidden gap" (+up/down, open/unfilled/filled)
4. `shadow_interval` — "long (upper|lower) shadow" (+interval/range)
5. `reaction_hl` — "reaction (high|low)"
6. `contraction` — "contract(ing|ion) volatility|volatility contract"
7. `tight_range` — "tight (trading )?range"
8. `trading_range` — "trading range|rangebound|range bound"
9. `wrb_zone` — "wrb (zone|area)"
10. `wrb` — bare "wrb" (pt events via EVENT regex: pt1/pt2/pt3 reached/formed)
11. `kme_line` — "kme line"
12. `level_sr` — "[SR] area|support|resistance|\blevel\b"
13. `zone_area` — bare "zone|area"
14. `range_generic` — bare "range" (incl. squeeze/battle/sticky price area)
15. `insync` — "insync|in sync"
16. `vtr` — "volatility trading report|VTR"
17. `alert` — "price alert|alert" near structure vocab
OPEN-ENUM: a message with structure-ish context (relation verb + a noun not
above) → kind=`other_structure`, noun captured in raw, needs_review=True.

## RELATIONS — expanded with the 522 parseable-miss verbs (T-IM13)
reached (reach/tagged/hit/touch) · testing (test/probe/attack/challeng/
retest) · approaching (approach/nearing/coming up|down/heading/pushing
toward) · back_to (back to/retrace(d) back) · broken (break/broke/broken/
breakout/thru/through/crossed) · failed_held (fail/reject/held/holding/
defend/bounc) · hugging (hug/stuck/sitting/pinned) · inside (inside/within/
in the) · above · below · at_near (at/near/around/on/off/@) · squeeze
(short squeeze) · battle (battle/fight/sticky) · acting_as (acting like —
sets role_flip) · none

## Correction linking
Message matching "correction|meant the|I meant|typo" → is_correction=True;
corrects_ts = stamp of nearest PRIOR structure-ref message within 15 min.
Later consumers must apply the patch (12 such rows in the hand read).

## Filters (flag, never drop — user rule: nothing ignored)
- boilerplate: the statistics posts ("N hours later the price has
  increased/decreased…", "has shown the most consistent results") and
  chat-room notices.
- personal: "be back in/at…", greetings, off-topic (no structure vocab).

## Instruments
v2 set + SPY, SOXL, QQQ, DIA, breadth ("advancers/decliners/breadth").
Non-ES rows keep needs_review=True (deferred, later system).

## Confidence
high = explicit price + specific kind (1–11) · med = relational + specific
kind, or event · low = generic kind (12–14) relational, or bare mention.

## Acceptance (the S1 gate)
1. 50 stratified sample parses (every kind represented) printed verbatim
   with full field assignments — human review.
2. Re-capture vs the T-IM13 hand read: of the 820 former remainder rows,
   v3 must capture the parseable-miss classes at ≥90% (zone/area 194,
   range 199, KME 129) and the new-vocabulary classes (shadow 68, hidden
   gap 49, reaction 11, contraction 10) at ≥90%; corrections 12/12 linked;
   boilerplate/personal flagged. Unresolved 72 may stay unresolved.
3. No row count drop vs v2 on the kinds v2 already handled (4,358 baseline;
   v3 should be a superset).

## ACCEPTANCE RESULTS (run 2026-11-20, T-IM15)
- Re-capture on the preserved 820-row remainder: **818/820 = 100%** (the 2
  uncaptured are pure psychology/method talk with no structure reference).
- New-vocabulary classes at hand-read counts: shadow 75/68, hidden gap
  48/49, reaction 10/11, contraction 46/10*, insync 11/11, VTR 1/1.
  (*contraction and zone/range family counts differ from the hand read by
  CLASS BOUNDARY, not capture - e.g. "battle in this price area" is
  zone-family+relation=battle here, range-relational in the hand read.)
- Corrections: 11/12 flagged (`meant|correction|typo`); the 12th used
  phrasing not matched - known gap, listed.
- Boilerplate/personal: 28 flagged in the remainder (stats posts, CME Group
  Alert posts, chat-room notices, be-back messages). Flagged, never dropped.
- Full corpus: **5,155 references** (v2 baseline 4,358 - superset, plus the
  new kinds). Corpus-level finds: VTR 2 rows (incl. NEW 2026-03-04 "I
  caught a runner off the VTR strategies and Key KME WRB Zone"), price-alert
  1 row ("price alert when the Emini ES price entered one of my watched Key
  KME WRB Zones").
- 54 stratified sample parses reviewed; fixes applied during review: VTR
  false positive ("contracting volatility trading days"), CME Group Alert
  mis-filed as his alerts, display bugs.
STATUS: AWAITING USER REVIEW before DB regeneration (--write).
