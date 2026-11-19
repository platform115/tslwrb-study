# STRUCTURE PROGRAM — step plan (for review before each step)
> 2026-11-20. Process rule (user): plan each step; user reviews details
> before anything is set. Truncation harness applies to ALL chart code.
> Registry row per step. No step starts before the prior step's review.

## DATA MODEL (revised per user 2026-11-20)
Central table = PRICE LEVELS / BANDS, not exclusive "objects":
- level_id | band_lo, band_hi (prices; band_lo == band_hi = a PRECISE
  level) | WIDTH HISTORY: a band can narrow to a precise level as tests
  accumulate, or widen - S/R or any attribute attaches to either form and
  can change between them (user 2026-11-20) | timeframe(s)
- source_attributes: LIST, may hold several simultaneously
  (wrb_body_top, zone_S_area, hidden_gap_edge, shadow_range_bound,
  reaction_low, contraction_range_bound, tested_level_inside_zone, ...)
- role history: S / R over time, with FLIP events (role switches after
  traversal per standard S/R behaviour) and TEST events (each return =
  evidence of importance; usable for targets/exits/entries)
- created_at | his_references (msg ids) | traversal events | lifetime stats
Objects (zones, intervals) live in a second table LINKING to levels, so a
zone's S area and a tested level inside the same zone coexist on the same
price without conflict. The attribute vocabulary is OPEN - unknown forms are
flagged for review, never forced into an existing class.

## FULL LIST OF DISCOVERED OBJECTS (open list; from T-IM01..13)
1. Key KME WRB Zone - HIS tiers, his words: "small Key KME" = S-R span
   narrow ("s/r levels too close to each other"); "Old" vs new = vintage;
   "I color code my Key KME WRB Zones based upon their importance";
   maintained as his list; midpoint used; S/R areas; role flips
2. WRB Zone (non-key) - his tier distinction, action-relevant: "ignored
   [a Short signal] because it only occurred in a regular WRB Zone and not
   a Key KME WRB Zone"; hierarchy WRB Zone -> KME WRB Zone -> Key KME WRB
   Zone
3. WRB interval (plain)
4. WRB Hidden GAP interval (Up/Down; FILLED vs UNFILLED - unfilled = open
   zone, his words)
5. Long Upper Shadow interval (range traded along)
6. Long Lower Shadow interval
7. Reaction high / Reaction low (with S/R areas)
8. Contraction range (contracting-volatility S/R) - possibly the process
   (ranges shrinking) vs...
9. Tight trading range - ...the state (price confined). SAME OR DIFFERENT
   UNKNOWN (user): kept separate; S3 co-occurrence/boundary data decides
10. Plain support / resistance level
11. Tested level inside a zone (repeat-test importance)
12. KME (time anchor; "Key KME line" can itself be the S OR R area)
13. WRB pt levels (management targets; +pt notation)
14. Cross-market insync (condition, not a price)
15. VTR signal (second entry system; definition unknown, parked)

## STEPS (each ends in a REVIEW GATE)
S0. TIMEFRAME USAGE MINING - verify, don't assume: extract every timeframe
    mention in his messages with context (entry / exit / structure / zone);
    test the "1m for entries" hypothesis. Output: TF usage report. REVIEW.
    [DONE - T-IM14, S0_TF_USAGE_REPORT.md. DECIDED TF SET: 1m, 2m, 3m, 5m,
    15m (+60m for zones). 1m kept on user's direct observation + his docs;
    corpus added 2m/15m; 15m/60m are his "higher time frames".]
S1. PARSER v3 SPEC - full pattern inventory (incl. anything new from S0);
    open-enum policy; correction-linking; boilerplate/personal/instrument
    filters. Output: spec + 50 sample parses + precision vs the T-IM13 hand
    read. REVIEW before the DB is regenerated.
S2. DEFINITION CHECK - Long Shadow / WRB / Hidden GAP: gather the KNOWN
    definitions first (M.A. Perry WRB Analysis materials; standard
    candlestick references) as hypotheses; audit what early project code
    already implements; state candidate definitions. REVIEW.
S3. GENERATORS, one at a time, each cycle = define -> implement (<=t,
    harness-passed) -> calibrate vs his references -> hit-rate report ->
    REVIEW before the next generator. Order: hidden-gap/zones -> shadow
    intervals -> reaction H/L -> contraction ranges.
S4. LEVEL/BAND DB ASSEMBLY (multi-attribute model above) + LIFETIME
    MEASUREMENT (creation -> last reference; traversal effects; his words
    AND the data both in evidence). REVIEW.
S5. RESOLVER + HIT-RATE DASHBOARD per generator per month. Tolerance
    schedule: START 3 pts (may widen briefly if needed), narrow as quality
    improves - end goal much narrower. REVIEW.
S6. ONLY THEN: his entries vs validated structures (the selection goal).

## STANDING CAUTIONS (user)
- No jumping ahead; nothing set without review.
- Lookahead discipline: every chart computation harness-gated (the T-EN99
  lesson); his text is ground truth and unlimited-use, market data honest.
- S and R are names of roles, not fixed types; the same price can carry
  several attributes at once; roles switch per standard trading knowledge.
- WORKING S/R DEFINITION (confirmed with user): Support = level/band below
  current price where buying repeatedly appears - price stalls/bounces;
  Resistance = mirror above. Break WITH follow-through flips the role;
  each held test adds importance; labels are roles relative to current
  price, never permanent properties.
