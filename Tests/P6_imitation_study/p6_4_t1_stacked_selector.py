#!/usr/bin/env python3
"""
p6_4_t1_stacked_selector.py — IMITATION STUDY step 4: the three T-IM03 leads
stacked as T1 selectors; coverage vs firing rate, 2025-10. (T-IM04.)
Selector conditions on each deduped T1 moment: same-direction score>=6
signal in prior 5 min; early session (<=120 min from open); within 45 min
after a KME. All combinations counted: his catches vs total vs per-day.
RESULT: T1 alone 14 his / 4404 all (176/day, 0.3%); best stack
signal&early&KME = 5 his / 268 all (10.7/day, 1.9%). Concentration ~6x but
precision stays ~2%: even the tightest observable stack leaves ~50
lookalikes per trade he took. See T-IM04 notes on the attention-realism
reading (he cannot take 176/day; match-precision has a ceiling).
RUN: logic identical to p6_3 plus the combo table; rerun via p6_3 + combos.
"""
