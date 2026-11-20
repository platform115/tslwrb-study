# BOUNDED SEARCH — ROUND 1 RESULT (T-BS01)
> Hypotheses were written before this run (BOUNDED_SEARCH_SPEC.md);
> parameters fixed from imitation measurements; M1 frozen; 2025-10 RTH.

| strategy | Trades | Win rate | Avg win / loss | Total | Max below start |
|---|---|---|---|---|---|
| S-A edge-break | 1644 | 41% | +1.76 / -1.11 | +84.2 | 47.4 |
| S-B +KME gate | 428 | 40% | +1.84 / -1.25 | -9.5 | 21.2 |
| S-C +signal gate | 373 | 42% | +1.79 / -1.47 | -36.8 | 45.0 |

## Hypothesis verdicts
- S-A: WEAKLY SUPPORTED at face value (+84/month) but ~+0.05 pt/trade
  over 1,644 trades - economically negligible per trade; the total is the
  sum of a huge number of near-zero outcomes. Not a tradeable edge as is.
- S-B: REJECTED - the KME gate that concentrates HIS entries loses money
  under mechanical M1.
- S-C: REJECTED - likewise (echoes T-EN100: signal-gated mechanical
  entries are not profitable with these exits).

## The structural conclusion
Catching his MOMENTS is not the same as capturing his P&L. The triggers
locate the same places he trades, but mechanical M1 on them nets ~zero,
while his management of the same class of entries earns multiples
(T-IM05: his entries + M1 = +108/month; his actual results far larger).
THE EDGE SITS IN MANAGEMENT AND SELECTION-WITHIN-STATE, not in the
trigger. This is the measured justification for the next phase the user
already sequenced: M2 trade-management design from his-vs-M1 differences.
The bounded search's one refinement round is DEFERRED until M2 exists -
P&L verdicts on entries are management-dependent, so refining entries
against M1 would optimize against the wrong exits.
