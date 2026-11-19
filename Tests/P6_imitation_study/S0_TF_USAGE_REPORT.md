# S0 — TIMEFRAME USAGE REPORT (T-IM14)
Structure program step S0. Source: his 31,838 messages, whole corpus.
Script: `p6_10_tf_usage_mining.py`. STATUS: REVIEWED - CLOSED (decision below).

## Method and the trap it caught
A naive mention count (312 hits) is dominated by **durations**, not chart
timeframes: "be back in 20 mins", "for the past 12 minutes", and ~150 hits
from the "N hours later the price has increased…" statistical boilerplate
posts. Counting those as TF usage would have been exactly the kind of silent
assumption the plan forbids. Pass 2 isolates genuine **chart-TF statements**:
compact tokens (2min/15min…), chart/time-frame vocabulary, TF lists.

## The complete chart-TF evidence — 14 messages, all of them
| Date | Message (trimmed) | TF(s) | What it shows |
|---|---|---|---|
| 2021-12-27 14:51 | "2min and 3min" | 2m, 3m | bare TF list mid-session (likely answering a room question; we only have his side) |
| 2022-02-10 | "Sometimes I like to change my chart interval to view the 15min or 60min chart" | 15m, 60m | higher TFs are a deliberate *change* from his working view |
| 2022-05-27 | "I was looking at the 1min and 2min chart of the VIX" | 1m, 2m | **only 1min mention in the corpus — and it's the VIX, not ES** |
| 2022-06-29 14:23 | "higher time frames like the 15min…several long shadow intervals" | 15m | he calls 15m a HIGHER time frame; shadows read there |
| 2022-06-29 14:26 | "another long shadow interval formed on the 15min intervals" | 15m | shadow intervals on 15m |
| 2022-06-29 18:35 | "how tight of a trading range…by looking at the higher time frame like 1 hour (60min) chart" | 60m | range character judged on 60m |
| 2022-12-07 | "The 15min chart reveals the range for today back to about 12pm est yesterday and the amount of contracting volatility" | 15m | range + contraction read on 15m |
| 2023-04-17 | "pay more attention to the daily / weekly chart of the VIX…when the price action was difficult to trade" | D, W | regime, VIX, not ES execution |
| 2023-09-21 | "bearish bias…SPY open below the R area of a Key KME WRB Zone **on the hourly chart**" | 60m | a Key KME WRB Zone living on an HOURLY chart (SPY) |
| 2024-12-10 | "I was caught watching the 15min chart too much :(" | 15m | 15m is NOT his execution view — watching it too much hurt |
| 2026-03-02 15:42 | "2min, 3min and 15min charts today" | 2m, 3m, 15m | his stated chart set for a trading day; entries follow minutes later |
| 2026-03-02 15:43 | "The interval in question is on the 5min chart that I've been taking a peek at" | 5m | the 14-pt Hidden-GAP interval he's trading around lives on 5m |
| (supporting) 2021-05-11 | "dropped from 14 minutes in time duration to 4 mins 17 seconds" | — | durations, kept to show the exclusion rule |
| (supporting) 2022-06-22 | "takes about 2 minis…platform and charts" | — | noise, excluded |

## Hypothesis verdict
**"Mostly 1m, with 3m/5m sometimes — 1m for entries" is NOT supported by his
explicit words.** 1min appears once in the entire corpus, and for the VIX.
What his own statements support instead:
- **2min and 3min are the stated working/execution charts** — both TF-list
  messages (2021-12-27, 2026-03-02) name them, four years apart, and the
  2026 one is immediately followed by entries.
- **15min and 60min are explicitly "higher time frames"** — used for range
  character, contraction, shadow intervals, and at least one Key KME WRB
  Zone (hourly, SPY). Watching 15m "too much" is something he regrets.
- **5min carries structure at least once** (the Hidden-GAP interval he was
  trading around in 2026-03).
- Daily/weekly: VIX regime only.

## Honest limits (do not over-read)
- 14 messages out of 31,838. He almost never names TFs; absence of "1min"
  is weak evidence of absence, not proof — but there is **zero positive
  evidence for 1m on ES**, and positive evidence for 2m/3m.
- "2min and 3min" (2021) has no visible question before it — we only have
  his side of the room.
- The 2026-03-02 pair is the strongest single datum: stated chart set +
  structure tied to a named TF + immediate trading.

## DECISION (review gate passed, user 2026-11-20)
TF set for structure generation: **1m, 2m, 3m, 5m, 15m (+60m for zones)**.
1m is KEPT despite its single corpus mention: user has directly observed him
using 1m many times and it appears in his documentation — it is implied, not
narrated, in the chat room. Corpus evidence added 2m and 15m to the set and
established 15m/60m as his "higher time frames" (context/structure, not
execution). The p6_1 border catalog (1/3/5) predates this; its descriptive
results stand; all level machinery forward uses the decided set.
STATUS: REVIEWED - CLOSED.
