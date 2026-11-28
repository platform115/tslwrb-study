# PLAIN MAP — the whole project in plain words
STATUS: LIVING | updated 2026-11-26 | the no-jargon companion to
OVERVIEW_TREE.md; update whenever the tree updates.

## The letters, decoded
G1-G6 = the six kinds of trades he takes (by context). Strategy N =
entry rules. M-series = exit rules. G2-1/2/3 = complete entry+exit
pairs for group 2, in improvement order. A/B = program phases (map /
build). T-xx = test ledger IDs. R-1..R-8 = working rules.

## DONE
- His 315 training trades audited at 1-second resolution; labels certified.
- 75 measurements per trade vs matched ordinary moments; six groups sorted.
- G2-1 (news+squeeze entry x simple patience): VALIDATED incl. one-shot
  pass on an untouched month - the only true out-of-sample result so far.
- G2-2 (+ level-snap exits) and G2-3 (+ wider trigger set): training-only
  improvements; catch 74% of group-2 trades; out-earns him in total on
  the group (+265 vs +231) at ~10x lower per-trade profit.
- Management campaign: patient-vs-snap duality proven (+275 oracle
  ceiling); levels = one real switch; four dead ends documented.
- Multi-day level detector: price-only, recovers 62% of his repeatedly-
  traded zones; survived two challenges and one caught bug.

## LEFT (in order)
1. Validation prep (data converter + equivalence proof).
2. G2-3's one-shot verdict on the purchased months (2023-05, 2024-05).
3. Group 3 full cycle (quiet squeeze - half his book).
4. Order-book lens (inside the G3 cycle): the fade entries + exit-switch
   remainder.
5. The loop: gap autopsy -> groups 1/4/5 -> refine -> repeat.

## GO BACK / REFINE
- Per-trade quality: +0.49 vs his +3.73 - the core gap.
- Exit skill: 63% of his points kept; oracle says ~100% reachable.
- His spoken key levels: only ~35% captured.
- 4 group-2 misses = zone-trigger question (queued into G3).
- Backlog: role-flip levels v2, higher-TF bar anatomy, 3C/3D traded
  P&L, regime splits.

## 2026-11-26 EVENING — WHERE THINGS STAND, NO JARGON
- We finished testing every entry-timing idea on the books. Waiting
  for a pullback before entering: rejected (he does both; a
  pullback-only system can't catch a third of his trades). Taking
  only the first trades after each news release: rejected (his few
  trades per window are the LATER, chosen ones, not the early ones).
- While testing those we found a real bug in how every earlier
  backtest decided which of two pending orders wins. Fixed; the
  honest convention is now standard; our main strategy's numbers got
  slightly BETTER after the fix (+276.1 over the two months, catching
  47 of his 62 trades).
- Three strategies are now saved and will be judged once, together,
  on the two months being purchased (the plan for that judging is
  written down in VALIDATION_PLAN.md so nothing can be quietly tuned):
  the main one; a variant that adds pullback re-entries (more total
  profit, slightly lower per-trade quality); and a one-trade-per-news
  variant (much higher quality per trade - for when trading many
  contracts).
- First confirmed piece of his decision tree: on calendar days
  everyone knows matter (CPI, Fed), he almost always trades (78% of
  those windows); on minor news only 27%. That flag is free public
  information. How he picks among the minor windows is still unknown
  - the order book is the remaining place to look.
- His drive is connected. Now looking at whether the order book
  explains his exit timing (the single biggest gap left: on the same
  trades he makes +3.73 per trade, we make +0.45, mostly because he
  holds winners longer when it is right to).


## 2026-11-27 AFTERNOON — NO JARGON
- We now know where our money comes from (one coherent profile:
  moving markets, near computed levels, collected by the level-snap
  exit) and that it CANNOT be captured by filtering entries - three
  different filter designs all threw away profitable trades.
- Four careful attempts to improve the exit rules all failed or
  proved empty; the surprising summary is that our simple management
  is already as good as its inputs allow. J's instinct ("cut trades
  that won't run") turned out to already BE one of its rules.
- Still open on exits: one standard statistical method never tried
  (change-point detection) and the full-depth order-book data (being
  opened now - the deep-book round).
- Nothing was lost: every finding has an F-number, every open idea a
  D-number, in MASTER_PROGRAM.


## 2026-11-27 LATE AFTERNOON — NO JARGON
- A big day. We found where our money comes from, proved it cannot
  be captured by filtering entries, proved our simple exit rules are
  already at their limit, and then found the two signals that
  finally matter: (1) when a price level is touched, THREE SECONDS
  of order-book behavior tilt the break-or-bounce coin (55% vs 40%);
  (2) he holds winners while deep order flow keeps pushing his way.
- From those we DESIGNED a new strategy (Strategy 5): enter at
  touched levels when the book confirms, stop safely behind the
  level, ride the flow. First test: twice the per-trade quality of
  our validated strategy, smallest worst-loss ever (-2.00). Caveat
  in bold: tested on the same data the signals came from - fresh
  depth data must judge it before it is believed.
- Surprise: HE does not use the 3-second signal (his picks ignore
  it). This new edge is OURS. How he picks his trades is still
  unknown - that hunt stays open.
- Two ways a strategy can run live: "Pine tier" (price only, runs on
  TradingView - our validated G2-4) and "runner tier" (needs the
  depth feed - the new Strategy 5 line).

## 2026-11-27 — Where structure is used, in plain words (the exit-arming story)
The known levels and edge families earn their keep in three places:
picking WHERE to enter (G2-6's wider trigger), picking WHICH touches
to take (the runway rule - only enter when there is 2-8 points of
clear road to the next structure), and, on the surgical line, telling
the exit WHERE the run should end (the capture exit that makes all of
that line's money). What today's test showed is narrower: on the
news-window combo line, using structure to decide WHEN TO START
TRAILING a winner works no better than a fixed rule ("start trailing
once +1.5 points up") - because structure is often too far away to
arm in time. So: G2-7 tries the simple constant, G2-8 keeps the
structure-armed version, G2-4 (the validated one) keeps its original
level-armed exits, and the surgical line keeps level-targeted
captures everywhere. Fresh purchased months decide between them. If
something fails there, we first check whether the mechanism died or
just a dial needs re-fitting to the new regime (J's adapter rule).

## 2026-11-28 — The quiet unlock, the runway law, and the filing system
Three things happened late on 2026-11-27, in plain words. FIRST: we
pointed the same entry machinery at the quiet market (more than 45
minutes after any scheduled news - a clock rule, fully knowable
live) and it walked into 150 of his 151 quiet trades. Combined with
the news-window result, his ENTRIES are now essentially solved in
training; what's left of him is which days he acts and how he holds.
SECOND: the "runway" rule - only take a trade when there are 2 to 8
points of clear road to the next structure - roughly DOUBLES profit
per trade on every strategy line we applied it to (four of four).
One frozen rule, never re-tuned. Its cost: it skips many of his
trades, so catch falls - precision and imitation pull apart, and we
keep both versions of each system. THIRD: everything got a filing
system - entries, filters, and trade-management plans are numbered
parts (EN-, FL-, MP-), every system is a formula of parts, every
part points to the exact script that defines it, and a script
checks the whole web on every commit. Nothing was renamed; the old
names are aliases forever. All of it still awaits the real judge:
fresh purchased months (D-8).

## 2026-11-28 — The 60-second flaw, found and fixed
The lookahead gate (cut the data at a moment, recompute, demand the
same answer) caught a real flaw: two structure types announced
themselves up to 59 seconds before the price bar that defines them
had finished. Fixed the same morning; every number was recomputed.
What held: the validated system (to the decimal), every catch
result, the quiet lines, the simple-trail conclusion, both loss-side
rejections. What shrank: the runway rule's benefit - roughly half of
its advertised doubling had been the flaw. It still helps (about
1.5x on the surgical line) and stays frozen for the fresh-months
judge. Lesson on record: a claim is untested until the machine has
tested it.

