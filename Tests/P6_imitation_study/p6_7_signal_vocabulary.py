#!/usr/bin/env python3
"""
p6_7_signal_vocabulary.py — IMITATION STUDY step 7: his 'signal' vocabulary
mined across all 31,838 messages. (T-IM07; inline runs preserved here.)
WHAT WAS FOUND:
- 262 'signal' mentions; 65 negated/missed forms. Words before 'signal':
  trade(128), short(57), long(54), re-entry(7), mixed(6), entry(4).
- Clock-stamped signals exist but are RARE and OLD: 10 total (2021-05..2022-08),
  none in our active month. 'strategy #N': never used. Saved what exists ->
  Data/inputs/his_signal_stamps.parquet (8 missed + 2 stamped).
- Signal mentions in our data months: 2-6 per month (too sparse as a target
  set). One located missed signal in training: 2022-02-22 14:44, 'trade
  signal was @ 4321.50 (missed the entry)'.
- CONCEPTUAL STRUCTURE from his words (2022-02-09): 'intervals by themselves
  are not directional trade signals... only clues that a trade signal is
  pending' -> CLUES precede SIGNALS; a CONFIRMATION step exists; and
  'another early entry prior to confirmation of a trade signal' -> some of
  his entries are deliberately EARLY, pre-confirmation.
- Vocabulary counts (all msgs): contracting 295, volatility spike 277,
  squeeze 218, spike 334, reaction 100 -> his lens is VOLATILITY
  CONTRACTION -> EXPANSION (matches M.A. Perry WRB Analysis methodology).
HYPOTHESIS HANDED TO PRICE-ACTION WORK: the 'quiet 46%' entries may be
CONTRACTION-PHASE entries (early, pre-expansion) - measurable: range
compression at/before his entries vs ambient, per typology group.
"""
