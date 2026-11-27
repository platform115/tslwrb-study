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
