# Test 04 — refill_resiliency (REPRODUCTION SPEC)
Self-contained recipe for a fresh chat (has CURRENT_STATE.md: conventions, grouping, window designs,
sign encoding). Mode: exploration. Status: COMPLETE — near-null.

## Purpose
Stall via "refill slowing": does supporting-side liquidity replenish LESS before failed trades than
reached? Inferred/approximate — a DOM cannot separate a cancel from a trade consuming size
(Large 2007 resiliency / absorption).

## Result (headline)
PRIMARY all 0.506 / excl-22 0.564 ; CONTROL Design A (W=60s) 0.549, 95% CI [0.472, 0.627].
0 undefined windows (every window's support was challenged). refill_ratio median ~1.00 for BOTH groups.
-> No resiliency-stall signature; near-null.

## Inputs
tsl_episodes_clean.parquet; wrb_1m.parquet (pt1); MBP-10 windowed parquet
(ts_event, action, side, size, instrument_id=294973, bid_sz_00..09, ask_sz_00..09).

## Grouping (= CURRENT_STATE; Reading B, inclusive)
target_reached 52 / failed_trades 40.

## Feature
Supporting side = bid (long) / ask (short).
  consumed   = aggressor volume hitting the support over the window
               (sell-aggressor side=='A' for long; buy-aggressor side=='B' for short).
  net_change = supporting_depth_end - supporting_depth_start   (Sum of 10 levels; first/last in-window snapshot)
  refill_ratio = 1 + net_change / consumed
    ~1 = replenished despite being hit (healthy/absorption); <1 = eroding faster than refilled (stall).
    undefined if consumed == 0 (support not challenged) -> flagged & excluded.
Descriptive secondary: supporting-depth slope per second.
Pre-registered: target_reached > failed_trades.

## Designs (= CURRENT_STATE window definitions)
PRIMARY (pt1/exit anchored, 3-bar, entry-bar fallback; 52/40 + excl-22) and CONTROL Design A
(cut-time-matched, 60s trailing, peers pre-pt1-open; auto-excludes the 22).

## Statistic
AUC = P(reached refill_ratio > failed) (primary, NaN excluded); Design A per-cut AUC + cluster-
bootstrap 95% CI (seed 0). Pure-numpy.

## Reproduce
Deterministic, memory-safe streaming (reads book size cols + trade action/side/size).
Script: refill_resiliency.py --config config.toml --wrb /path/to/wrb_1m.parquet.
