# STANDARD RESULTS DISPLAY — ENTRY TESTING (agreed 2026-11-21)
> Every entry test reports in this exact shape. No test result is
> presented in any other layout. Cells with no measured value show "-",
> never an estimate.

## Header (one line)
Strategy <id> | management <id> | period | slice (RTH/ETH/all, other filters)

## Block A — ACTIVITY (how the rule relates to HIS trading, same period)
| metric | value |
|---|---|
| his trades | n |
| signals fired | n (and per day) |
| his trades caught | n (share of his trades) |
| fires without a trade of his | n (= fired - caught) |

## Block B — PERFORMANCE (always two columns, HIS first)
| metric | HIS | OURS |
|---|---|---|
| trades | | |
| win rate | | |
| points won (sum of winners) | | |
| points lost (sum of losers) | | |
| net points | | |
| avg win / avg loss | | |
| worst single trade (incl. its max adverse excursion) | | |
| max drawdown from period start | | |
Optional rows when relevant: median hold time; capture of own-window MFE;
entry displacement vs trigger level.

## Footer (one line each, when applicable)
- harness status of the entry gate (passed / date)
- regime note (KME-day share, volatility tercile of the period)
- which table rows are out of scope (e.g., OURS blank in pure catch tests)

## Worked example — Strategy 3C | M1 | 2025-10 | RTH
A: his trades 92 | fired 423 (18.6/day) | caught 35 (38%) | extra fires 388
B:
| metric | HIS | OURS |
|---|---|---|
| trades | 92 | 373 |
| win rate | 82% | 42% |
| net points | +620.0 | -36.8 |
| avg win / avg loss | +8.56 / -1.31 | +1.79 / -1.47 |
| max drawdown from start | ~0 | 45.0 |
| worst single trade (MAE) | - (not yet computed) | - (not yet computed) |
Footer: entry gate harness-passed (T-IM28); per-trade MAE added to the
standard going forward - earlier tests show "-" until recomputed.

## ADDITION 2026-11-28 (J's RWYLAW catch, 2026-11-27): MONTH-LEVEL DISPLAY
Every headline claim (a system registration, a law, a selector or
management verdict) must show its per-month breakdown - n, net,
per-trade per month - not only pooled numbers. Pooled means hide
regime variance (the runway law's 2021-09 weakness was invisible
until J demanded the month table). Pooled-only presentation of a
headline claim is a display violation.

