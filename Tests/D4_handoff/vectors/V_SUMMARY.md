# D4 GOLDEN VECTORS — SUMMARY (certified engine output; controls C1/C2 PASS)
| session | signals | orders filled | trades | net |
|---|---|---|---|---|
| 2025-10-13 | 27 | 23 | 14 | +8.2 |
| 2025-10-15 | 165 | 135 | 40 | +25.8 |
| 2025-10-31 | 4 | 3 | 2 | +2.8 |

## TOLERANCES (J-gated; stage gates in D4_HANDOFF_PROMPT.md)
- S2/S3 structure values: EXACT when TradingView 1m bars equal
  ours; where bars differ, each differing bar is listed and
  explained by the bar difference, nothing else.
- S4 signals: >= 90% of signals matched within +/- 60s, same edge
  (+/- 1 tick) and direction; every unmatched signal listed.
- S5 fills: same fill/expiry outcome on >= 90% of matched signals.
- S6 trades: per-trade exit reason matches on >= 85% of matched
  fills; per-trade P/L within 0.50 on matched same-reason trades.
- Any systematic one-direction bias in mismatches = STOP, report.
