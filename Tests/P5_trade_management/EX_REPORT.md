# EX REPORT — EXIT-SWITCH REMAINDER VIA THE ORDER BOOK (T-MG19)
STATUS: CLOSED | 2026-11-26 | Spec: EX_SPEC.md (committed first) | study only | book = per-second drive reduction (news-window coverage)

Population: 313 audited exits with hold >= 30s (221/92 per month); entry-time basis: 307 rows had a finite posting lag applied.

## ANALYSIS A — HIS EXIT MOMENT vs SAME-DURATION HOLD MOMENTS IN HIS OTHER TRADES
Cases with book + >=1 duration-matched control: 300 (dropped: 8 no book second, 5 no eligible control).

| feature | exit med | hold med | direction | perm p | verdict (alpha .0056 / .05) |
|---|---|---|---|---|---|
| sup0 | 19.00 | 20.00 | exit HIGHER | 0.1006 | null (month-inconsistent) |
| opp0 | 20.50 | 19.00 | exit HIGHER | 0.0350 | suggestive (month-inconsistent) |
| sup10 | 586.00 | 538.50 | exit HIGHER | 0.0000 | suggestive (month-inconsistent) |
| opp10 | 554.00 | 563.00 | exit HIGHER | 0.9800 | null (month-inconsistent) |
| imb0 | -0.00 | 0.04 | exit HIGHER | 0.0338 | suggestive |
| imb10 | 0.01 | -0.02 | exit HIGHER | 0.0002 | FINDING |
| d30_sup0 | -1.00 | 0.00 | exit HIGHER | 0.7940 | null (month-inconsistent) |
| depth_tot | 1155.50 | 1077.00 | exit HIGHER | 0.0312 | suggestive (month-inconsistent) |
| flow_net_30 | -44.50 | 10.00 | exit HIGHER | 0.0954 | null |

## ANALYSIS B — AT THE CLOCK (480s): WHO KEEPS HOLDING?
n with book at t=480: clock-exiters 12, holders 33. Power is thin; stated, not hidden.
| feature | exiter med | holder med | p | both months same dir | verdict |
|---|---|---|---|---|---|
| sup0 | 19.00 | 28.00 | 0.0291 | yes | suggestive |
| opp0 | 21.50 | 25.00 | 0.5377 | NO | null |
| sup10 | 574.00 | 691.00 | 0.2926 | NO | null |
| opp10 | 592.50 | 637.00 | 0.3294 | NO | null |
| imb0 | -0.19 | 0.01 | 0.0665 | yes | null |
| imb10 | 0.01 | -0.01 | 0.8074 | NO | null |
| d30_sup0 | 2.50 | 3.00 | 0.8674 | NO | null |
| depth_tot | 1217.00 | 1352.00 | 0.3358 | NO | null |
| flow_net_30 | -163.00 | 15.00 | 0.0209 | NO | suggestive |

Registry: T-MG19.

## READING (careful - one finding, one named confound)
- FINDING (A): imb10 - the 10-level depth imbalance tilts TOWARD his
  position's support side at the moment he exits (+0.01 vs -0.02 at
  matched holds, p=0.0002, same direction both months). The trader's
  reading: he exits INTO liquidity - a long is sold into a stacked
  bid. Selling into strength is standard professional practice, and
  this is the first exit-side signal to survive the clock control
  (every M8 feature died once duration was held fixed; here duration
  is matched by construction).
- THE CONFOUND, NAMED (Rule 3): his exit moments sit at favorable
  price extremes (he takes profit); matched holds sit mid-path. A
  bid-tilted deep book at local highs may be a MARKET regularity at
  extremes, not his private trigger - the match controls the clock
  but NOT the price path. Before any switch rule is built, the
  finding must survive an excursion-matched control (same duration
  AND same current profit) - proposed as EX2, a new spec, J's call.
- Analysis B (the long-hold remainder, n=12 vs 33): two suggestives,
  one coherent story - at the 480s clock, HOLDERS sit on thicker
  top-of-book support (28 vs 19, month-consistent) and still-positive
  flow (+15 vs -163, month-INconsistent). Thin but pointing the same
  way as imb10's logic: support present -> keep holding; support
  gone + flow flipped -> the clock exit is right. Parked as
  BACKLOG/VALIDATION items, not findings.
- Non-independence stated: exits cluster within windows and controls
  are reused across cases; the effective sample is smaller than 300.
