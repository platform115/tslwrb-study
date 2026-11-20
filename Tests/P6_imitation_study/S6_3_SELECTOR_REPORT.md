# S6.3 — EVENT-BASED SELECTOR SCOREBOARD (T-IM31)
> Status: AWAITING REVIEW. Script: p6_24_s6_3_selectors.py. 2025-10, 23 sessions.

## Scoreboard
| selector | catch | fires/day | displacement q25/50/75 (pts past edge) |
|---|---|---|---|
| SEL-A' REA/15m | 79/92 (86%) | 299 | +0.50 / +3.00 / +4.62 |
| SEL-C' SQZ/15m | 68/92 (74%) | 322 | +0.50 / +1.50 / +3.50 |
| SEL-B' GAP/5m | 87/92 (95%) | 464 | -0.25 / +0.00 / +0.62 |
| SEL-E' SHD/5m | 85/92 (92%) | 466 | -0.25 / +0.25 / +0.50 |
| UNION | 89/92 (97%) | - | >=2 selectors: 85/92 (92%) |
Uncaught (3): 10-03 15:22 short (+2.75), 10-08 17:01 short (+4.25),
10-17 13:38 short (+24.25 - the momentum continuation S6.2 flagged).

## HONEST READING — catch % alone is NOT the result
Fires/day 299-467 against ~276 dedupe slots/day means the gates are on
most of the day: GAP/SHD ~84% of slots (catch 92-95% = little lift), REA
~54% of slots vs 86% catch, SQZ ~58% vs 74% - the real lift is the same
+16-32 points S6.2 measured. An interaction detector is a NECESSARY-
CONDITION filter, not a selector at human scale. He takes ~4 trades/day.

## What the scoreboard DOES deliver for replication
1. THE PRICE LEVELS: the selected structure edges (resolver,
   harness-certified) are the trigger sites.
2. THE ENTRY-PRICE RULE (displacement): at a REA interaction his fill is
   median +3.0 pts past the level (IQR +0.5..+4.6); SQZ median +1.5;
   GAP/SHD fills sit ON the edge (median 0.0/+0.25). Replication: enter
   on the interaction at edge + displacement band, family-specific.
3. The 3-entry uncaught list for the next cycle.

## PROPOSED NEXT (S6.4 + the conjunction cycle)
S6.4 accounting as planned. Then the next cycle must bring fires/day to
human scale by CONJUNCTION: structure interaction (where) x tape state
(when - burst/volatility-spike/signal measures from the battery; his own
clues->signal layer). Pre-registration of the conjunction grid before
any run, same discipline.
