# Strategy 2 — preserved entry candidates (pre-v1)

> Preserved by user decision 2026-11-17: replicating his entries is only part
> of the goal; these stand as candidates on their own P&L merits.
> All results: honest per-second engine, v11 exit stack (acknowledged rough
> sketch, to be redone), entries at fire-second mid, costs excluded.

## D1-A  (FROZEN)
Trigger: 10-sec displacement burst >= 99th pct (13-14 ticks/10s) · direction =
burst sign · context: 5-min move >= 30 ticks, old score>=6 signal same
direction in prior 5 min, first ~2/3 of session (min_into_sess <= 1050).
Results: +12.9 / +11.6 / +16.4 / +4.2 — positive ALL FOUR months, 92 trades,
+0.49/trade, max DD 8-12 pts. Precision vs his entries: 30/37% train,
27% 2021-09, 5% 2024-11.

## D1-B  (FROZEN)
As D1-A but 5-min move >= 40 ticks AND day range so far < 150 ticks.
Results: -0.8 / +12.8 / +9.4 / -0.5 = +20.9 on 40 trades. Precision: 33/50%
train -> 0%/0% reserved (the 46% in-sample frontier row - confirmed overfit
AS AN IMITATION DEVICE; preserved for P&L).

## Flagged variables (not settled)
99th-pct trigger threshold · 120s clustering/match windows · ret5m cut (30/40)
· day-range cut (150, in ticks, NOT regime-normalized) · min_into_sess <= 1050
(includes overnight bars - re-express as clock time) · vol5_r definition
(day-median denominator) · mid fills (half-tick optimism).

## Standing hypothesis for the management phase (user-flagged, keep front of mind)
Levels (WRB boundaries / KME zones) select nothing at ENTRY - five nulls - but
may govern everything once a trade is on (aim, hold, re-entry). Test when
exits are redone: do his exits/holds cluster at boundaries the way his entries do not?
