# RT REPORT — BREAK-AND-RETEST, UNCOMBINED (T-EN106)
STATUS: CLOSED | 2026-11-26 | Spec: RT_SPEC.md (committed first) | incumbent on this config: G2-3 +265.4 / catch 46 / extras +173.0 / per-trade +0.49

| cell | trades | per-trade | net (22-02/25-10) | caught/62 | extras net | verdict |
|---|---|---|---|---|---|---|
| Wr120 pb0.25 | 521 | +0.48 | +250.4 (+134.6/+115.8) | 43 | +163.8 | no |
| Wr120 pb0.75 | 540 | +0.50 | +269.6 (+158.2/+111.4) | 45 | +177.0 | no |
| Wr300 pb0.25 | 525 | +0.50 | +265.0 (+148.4/+116.6) | 43 | +177.5 | no |
| Wr300 pb0.75 | 540 | +0.50 | +269.6 (+158.2/+111.4) | 45 | +177.0 | no |

Registry: T-EN106.

## DIAGNOSTIC — THE SPEC HAD A HOLE (flagged, not silently resolved; Rule 3)
Post-run instrumentation of the same cross stream (1,911 deduped
crosses, both months): at the cross second the mid has typically moved
only a tick or two past the edge (median overshoot 0.12 pt, q75 0.38).
So "pullback to within pb of the edge":
- pb 0.75: instantly satisfied at the cross itself for 94.5% of
  crosses -> those cells are the G2-3 baseline wearing a costume (the
  small +269.6 vs +265.4 and 45 vs 46 differences come from the 5.5%
  that gapped through, plus touch-anchored TTL).
- pb 0.25: instantly satisfied for 68.6% -> only ~1/3 of signals faced
  any retest requirement at all; on those it mildly hurt (pooled
  +250-265 vs +265.4, catch 43 vs 46).
The spec as frozen did not require price to LEAVE the edge before
"returning" to it. The hypothesis (filter false breaks by demanding a
confirmed retest) was therefore only weakly tested. What IS answered:
a retest gate layered on top of the current trigger adds nothing and
loses 1-3 catches wherever it binds. A true retest test would require a
minimum excursion beyond the edge (e.g. >= 1.0-1.5 pt) before the
pullback counts — that is a NEW spec (RT v2), not a cell of this one,
and it is one more training-fitted knob on the pile of five. Decision
to run it or bank the freeze belongs to J.

## VERDICT (per the frozen lines)
No cell meets ADOPT (catch 43-45 < 46; pb0.75 cells are baseline
replicas, not improvements). No cell meets QUALITY-ALTERNATE
(per-trade +0.48..0.50 << +0.98). Break-and-retest as spec'd: REJECTED.
G2-3 stands. His G2 same-period line for scale: +231.2 on 62 trades
(+3.73/trade).
