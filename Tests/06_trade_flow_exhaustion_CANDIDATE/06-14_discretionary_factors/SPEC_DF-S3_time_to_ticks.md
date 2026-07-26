# SPEC DF-S3 — time-to-N-ticks (first-passage) + ATRrel variant
**Status: NULL (primary cell) · ATRrel variant weak-grazing, closed** · phase 06-14 · ESZ5 Oct-2025 · registry T-DF03/T-DF04

## Question
"Did it take off or trudge": seconds from entry to the first +N favorable ticks (first-passage time).
The most direct translation of trader-felt takeoff speed; S2's fav_net_vel measures the *rate*, S3 the *timing*.

## Design (locked with user)
- Thresholds: **+4tk PRIMARY**, +8tk, N_rel = 1.0×ATR(20, 1m, strictly-pre-entry completed bars; Wilder 1978).
  k=1.0 hardcoded, no k-sweep. ATR loader hand-verified in selftest (s3b).
- Horizons: **60s PRIMARY**, 90, 120 (user D2). 120s survivor frame thin (41/13) → directional only.
- Frames: B-design capped windows, ≥5s floor; **survivor (hold≥H) DECISIVE**; exits-within-H printed.
- Reads per cell (user D3 — multiple separate reads, NO censoring blend):
  (i) attainment fraction per arm + bootstrap CI on reach−stall diff (expect >0);
  (ii) time|attained AUC, reach faster ⇒ AUC<0.5, ≥8 attainers/arm else uninformative (selection-conditioned).
- PRIMARY CELL: **N=+4, SURV, 60s**. 18 cells exist by design (D1/D2 additions); one pre-named primary guards
  "something clears somewhere."
- Redundancy (locked pre-output): ρ(t4|attainers, fav_net_vel), CI ⊂ ±0.4 new / beyond |0.6| redundant → no
  candidate / else indeterminate.

## Results — T-DF03 (s3_time_to_ticks.py)
PRIMARY CELL **NULL twice over**: attainment 0.71 vs 0.71 (identical); time|attained AUC 0.572
[0.401,0.738] — leans **wrong-way** (stall median 8s vs reach 12s; stalls hit +4 as fast or faster).
+8tk: no clears. ATRrel(20): ALL(B) attainment clears at every horizon (+0.22/+0.23/+0.37) but **never on
the decisive SURV frame** → capped-window construction artifact (early-cut stalls get short windows; large-N
attainment mechanically harder in a short window). ATR(20) med 12.5tk (my pre-run 8–10 prediction wrong).
Redundancy: ρ(t4|att, fav_net_vel) −0.09 [−0.42,+0.23] → **INDETERMINATE**, logged, moot (nothing cleared).
ρ(attained4, fav_net_vel) = +0.62 — attainment and net-progress overlap heavily, yet attainment separates
nothing while fav_net_vel separates 0.669: the *retention*, not the *event*, discriminates.

## Results — T-DF04 (s3b_atr5_variant.py) — POST-HOC second look, logged as such
User-requested lookback 20→5 after seeing T-DF03. Pre-registered expectation (stated before output):
lookback changes responsiveness not size — confirmed: ATR(5) med 13.2 vs ATR(20) 12.5, ρ +0.88 across
entries. One grazing clear: SURV@60 attain diff +0.21 **[+0.01,+0.40]** — lower bound one trade from zero,
stall side = 3 attainers, no replication at 90/120 SURV. **No candidate.** Likely fav_net_vel coarsened
(redundancy UNMEASURED — inference, not measurement). **ATRrel closed at k=1.0**; any k change = a third
look at the family and must be weighed as such.

## Disposition — the finding is the null
Takeoff is not the difference: stalls reach +4tk as often and as fast as reaches. With S2's decomposition
(stall 50% net-positive at 60s vs reach 76%) the composite mechanism is **pop-and-fade vs retain** — the
discriminating quantity is *persistence of early directional progress*, not its initiation. Points S4
(sustained-vs-decayed profile) as the pointed next test — with the caveat on record that S4-positive would
be corroboration-by-reconstruction on the same October trades, not independent evidence.

## Dependencies & run (from 06_ root)
```
PYTHONPATH=.:06-13_stall_vs_reach python3 06-14_discretionary_factors/s3_time_to_ticks.py  --config config.toml --wrb wrb_1m.parquet
PYTHONPATH=.:06-13_stall_vs_reach:06-14_discretionary_factors python3 06-14_discretionary_factors/s3b_atr5_variant.py --config config.toml --wrb wrb_1m.parquet
```
Imports: forward_battery · trade_flow_exhaustion · range_expansion · velocity_acceleration ·
s2_directional_velocity · fav_net_vel_confirm · (s3b also imports s3_time_to_ticks). Both `--selftest`
(first-passage on constructed paths; ATR(5) hand-computed to 7.20tk exactly).

## Recreation notes
es_1m_front schema: ts_event (UTC bar-open), OHLC; TR/ATR from completed bars with open < entry-minute
floor (no in-progress bar, no look-ahead). The ALL(B)-vs-SURV divergence on ATRrel cells is the
anti-circularity design working — record ALL(B) ATRrel clears as construction-suspect, never headline.
