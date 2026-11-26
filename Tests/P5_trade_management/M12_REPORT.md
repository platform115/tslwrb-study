# M12 REPORT — STALL GATE: M7 + imb10 (T-MG21)
STATUS: CLOSED | 2026-11-26 | Spec: M12_SPEC.md (committed first) | engine: fill-time | CONTROL reproduced exactly

| cell | trades | net (22-02/25-10) | caught/62 | extras net | worst | stall exits / extended / forced / no-book | busy-shifted entries (+/-) | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 607 | +276.1 (+111.8/+164.4) | 47 | +185.6 | -3.75 | 0/0/0/0 | - | (incumbent reproduced) |
| M12 th0.00 | 578 | +274.9 (+141.6/+133.2) | 46 | +216.2 | -3.75 | 89/98/77/211 | +8/-37 | no |
|  ^ extended-trade detail: 98 trades, net +83.6 (+0.85/trade) | | | | | | | | |
| M12 th-0.02 | 581 | +280.8 (+148.8/+132.0) | 46 | +209.2 | -3.75 | 104/86/68/211 | +6/-32 | ADOPT |
|  ^ extended-trade detail: 86 trades, net +84.2 (+0.98/trade) | | | | | | | | |

## MECHANISM: THE EXTENDED TRADES vs THEIR M7 TWINS
- M12 th0.00: 96 of 98 extended trades have an identical-entry M7 twin; gate delta on those = -5.8 total (-0.06/trade; 38% improved, worst -7.62)
- M12 th-0.02: 84 of 86 extended trades have an identical-entry M7 twin; gate delta on those = -5.2 total (-0.06/trade; 37% improved, worst -7.62)

Registry: T-MG21.

## READING — THE MECHANISM OVERTURNS THE HEADLINE (Rule 3)
th-0.02 meets the frozen ADOPT line (+280.8 > +276.1, both months
positive, stop intact). But the spec's own mechanism accounting shows
the line was met by a CONFOUND, not by the rule:
- The 84 extended trades, compared with their identical-entry M7
  twins, LOST -5.2 total (-0.06/trade; only 37% improved; worst
  twin-delta -7.62). The gate's actual effect is slightly negative.
- The cell-level +4.7 comes from the busy-clock reshuffle (+6/-32
  different later entries) - noise from holding positions longer,
  not value from the book signal.
- The extended trades' healthy +0.98/trade average is SELECTION (the
  gate extends trades that were already doing fine), not improvement.
RECOMMENDATION TO J: REJECT shape (a) despite the technical ADOPT -
the verdict line as frozen tested cell totals and was mis-specified
for a management change; the mechanism-level test (twin-matched
delta) is the honest criterion and it is negative. LESSON CARRIED:
shape (b)'s spec pre-states the twin-matched delta as PRIMARY.
Why his signal did not monetize here: imb10 describes WHEN HE exits;
gating OUR stall by it is one guess at turning description into rule,
and the stall moment is evidently not where the signal pays.
