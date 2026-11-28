# D4_PORT_SPEC — G2-4 FOR PINE v6 (THE RULE BOOK)
STATUS: v1.0 FROZEN FOR HANDOFF | 2026-11-28 | Owner: research side
(tslwrb-study). Changes only by amendment here, never verbally.
System: G2-4 = EN-01 x FL-WIN x MP-7 (VALIDATED; J: PORT-READY).
Out-of-sample record: 4/4 fresh months positive (+158.0 then +276.8).

This document is the ONLY authority on the rules. The constants
table (D4_CONSTANTS.md) is the ONLY authority on numbers. If a rule
here is ambiguous, missing, or conflicts with anything: STOP AND
ASK J. Never fill a gap with an assumption.

## 0. MODE AND MARKET
- Pine Script v6 STRATEGY (simulated backtest/paper only - it
  places no real orders). 1 contract per trade. One position at a
  time, long or short.
- Instrument: CME ES futures. Chart: the current front-month
  contract, or continuous ES set to UNADJUSTED (must match: our
  research data is the unadjusted front month).
- Chart timeframe: 1-SECOND bars. All strategy logic evaluates per
  1s bar. Structure inputs (bands, squeeze episodes) come from
  1-MINUTE bars of the same symbol.
- Price source note (honest divergence): the research engine
  watched the QUOTE MIDPOINT each second from CME data; TradingView
  1s bars are built from TRADES on TradingView's feed. Close, not
  identical. Divergence is measured at the vector stages, never
  tuned away.

## 1. TIME AND SESSIONS
- All session logic is CT (America/Chicago), CME convention.
- A SESSION runs from the globex open (17:00 CT) to the next day's
  15:15 CT close and is named by its RTH date (overnight bars
  belong to the NEXT day's session).
- All structure state (bands, squeeze episodes) RESETS at session
  start (17:00 CT) and builds from the session's own 1m bars,
  overnight included.
- Entries happen only inside event windows (section 3), which must
  start during RTH (08:30-15:15 CT).

## 2. STRUCTURE (computed from the session's 1m bars)
Knowability rule for everything in this section: a 1m bar's values
may be used only from 60 seconds AFTER that bar's close. (In Pine:
confirmed bars only, plus the one-minute lag this implies. The
research stamp is "bar close time + 60s".)

### 2a. W20 QUIET BANDS (one pair of edges)
Per 1m bar i of the session:
- rng20[i] = highest high of bars i-19..i minus lowest low of bars
  i-19..i (needs 20 bars).
- med[i] = median of rng20 over the PRIOR 60 bars (shifted by one
  bar: bars i-60..i-1; needs at least 10 defined values).
- The bar is ACTIVE when rng20[i] <= 0.8 * med[i].
- A RUN is a maximal streak of consecutive ACTIVE bars. While a run
  lives, its band is: band_lo = lowest low since 20 bars before the
  run's first bar... precisely: at the run's first bar i0, band_lo/
  band_hi = min low / max high of bars (i0-19..i0); each further
  ACTIVE bar extends them with its own low/high.
- The band VALUES PERSIST after the run ends (the last run's
  band_lo/band_hi stay the current band) until a new run replaces
  them. Before the first run of a session there is no band.
- The two W20 edges at any moment = current band_lo and band_hi.

### 2b. SQUEEZE EPISODE EDGES (up to four edges)
Two independent families, W = 10 and W = 30. Per family, per 1m
bar i:
- rngW[i] = highest high minus lowest low of bars i-W+1..i
  (defined from bar W of the session).
- medW[i] = median of rngW over bars max(W, i-60)..i-1 (needs at
  least 10 defined values).
- ACTIVE when rngW[i] <= 0.67 * medW[i].
- An EPISODE is a maximal streak of ACTIVE bars, span (a..e)
  inclusive. An episode only becomes usable if at least one bar
  exists after it (e+1 must exist).
- Episode band: lo = lowest low of bars (a-W+1..e), hi = highest
  high of the same span (clip the start at the session's first
  bar).
- The episode is knowable from: close time of bar e+1, plus 60s.
- At any moment, each family contributes the lo and hi of its MOST
  RECENTLY knowable episode only (older episodes are ignored).
  Nothing before the session's first episode.

### 2c. THE EDGE SET
At any second t, the watched edges = the W20 pair (2a) plus the
SQZ edges (2b), each rounded to 2 decimals, duplicates removed.
Edges refresh when the minute rolls; within a minute they are
constant.

## 3. THE FILTER (FL-WIN) — EVENT WINDOWS
- Input: the week's scheduled economic-release times (section 6).
- For each event at time E: the ENTRY WINDOW is [E + 300s,
  E + 2700s) (5 to 45 minutes after the release).
- The window is used only if its start falls inside RTH.
- All signal detection (section 4) runs ONLY on seconds inside an
  entry window. Management (section 5) continues outside windows
  once a trade is on.

## 4. ENTRY (EN-01) — SIGNALS AND ORDERS
Evaluated each 1s bar inside an entry window, against every edge e
in the current edge set. "price" = the 1s series value; prev =
previous 1s value.

### 4a. CROSS SIGNAL
- Long cross of edge e: prev <= e AND price > e.
  Short cross: prev >= e AND price < e. (A touch that closes
  exactly on e is not a cross.)
- LOCKOUT: per (edge price rounded to 2 decimals, direction), a
  new signal is ignored for 300s after the last signal of that
  same key.
- On a signal at time t: place a STOP ENTRY order at
  lvl = e + 1.25 * dir (1.25 beyond the edge, in the cross
  direction). The order EXPIRES 300s after t if unfilled.
- Fill: the first second within those 300s whose price reaches lvl
  (>= lvl for longs, <= lvl for shorts). Entry price = lvl.

### 4b. PULLBACK-RETEST SIGNAL (the second technique)
After a cross of edge e at time t (same lockout key space):
- Watch up to 600s from t. If excursion reaches >= 1.0 beyond e
  in the cross direction, and AFTER that pulls back to <= 0.75
  beyond e: at that pullback second, place a fresh STOP ENTRY at
  the same lvl = e + 1.25 * dir, expiring 300s later. Fill rule
  identical to 4a.

### 4c. POSITION RULES
- One position at a time. While a position is open, fills do not
  occur (an order whose trigger happens while busy is skipped, not
  queued). After the exit second, new fills may occur.
- Duplicate protection: the same (fill second, edge, direction)
  never fires twice.

## 5. EXIT (MP-7 / M7) — THE STATE MACHINE
On entry at price lvl, direction dir, with the day's LEVEL LIST
(section 6):
- ahead = the handed-in levels p with (p - lvl) * dir > 0.25,
  sorted by that distance; best = the nearest, if any.
- ARM THRESHOLD: if best exists and best_distance <= 8.0, then
  arm = max(best_distance - 0.75, 0.5). If no such level, or
  best_distance > 8.0, the trail NEVER arms.
Each second, with exc = (price - lvl) * dir (points in favor):
1. Track peak = highest exc so far (starts 0) and the time of the
   last new peak.
2. STOP: if exc <= -3.75 -> exit at lvl - 3.75*dir. Checked first.
3. ARMING: once exc >= arm, the trail is ARMED (stays armed).
4. TRAIL: if armed and exc <= peak - 0.75 -> exit at
   peak - 0.75 (in favor), i.e., price lvl + (peak-0.75)*dir.
5. STALL: if 60s pass with no new peak -> exit at current price.
6. CAP: at 480s in the trade -> exit at current price.
Priority within one second: the research engine checks in the
order: new-peak update, arming, STOP, TRAIL, STALL/CAP.
- Trade P/L in points = exc at exit (stop = -3.75 exactly; trail =
  peak - 0.75; stall/cap = current exc).

## 6. THE TWO PASTED INPUTS
Both are generated by the research side as ready-to-paste Pine
array code (not input boxes - size and determinism):
- LEVEL LIST (daily): per session date, the day's levels. Used
  ONLY by section 5 (exit arming). Generated by d4_levels_gen.py.
- EVENT TIMES (weekly): the release timestamps. Used ONLY by
  section 3. Generated by d4_calendar_gen.py (which also prints
  the KME event-name list so J can read next week's times off any
  public calendar).
The pasted blocks are part of the script's record: never edit them
by hand.

## 7. ROLL DAYS (F-40 convention)
The certified convention: structure keeps running; trades on roll
sessions are KEPT but must be identifiable (mark them). TradingView
continuous charts switch contracts on TradingView's own schedule -
note in the file header which symbol/roll setting was used.

## 8. WHAT IS OUT OF SCOPE
No volume, no order-book data, no catch metrics, no position
sizing, no commissions (handled elsewhere), no G2-6 (separate
addendum later), no live order routing (that is the D-23 Python
runner's job).

## 9. ACCEPTANCE
The build is DONE when it reproduces the golden vectors
(D4_GOLDEN_VECTORS/) within the stated tolerances, stage by stage,
per D4_HANDOFF_PROMPT.md. A mismatch is REPORTED with diagnosis -
never resolved by nudging a rule or constant.
