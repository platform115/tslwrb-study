# M13 REPORT — CLOCK EXTENSION: HOLD PAST 480s WHILE THE BOOK SUPPORTS (T-MG22)
STATUS: CLOSED | 2026-11-26 | Spec: M13_SPEC.md (committed first) | engine: fill-time | CONTROL reproduced exactly | verdict: MECHANISM-PRIMARY (T-MG21 lesson)

| cell | trades | net (22-02/25-10) | caught/62 | extras net | worst | stall exits / extended / forced / no-book | busy-shifted entries (+/-) | verdict |
|---|---|---|---|---|---|---|---|---|
| CONTROL | 607 | +276.1 (+111.8/+164.4) | 47 | +185.6 | -3.75 | 0/0/0/0/0 | - | (incumbent reproduced) |
| M13 th0.00 | 607 | +276.1 (+111.8/+164.4) | 47 | +185.6 | -3.75 | 1/0/0/0/0 | +0/-0 | secondary PASS |
|  ^ extended-trade detail: 0 trades, net +0.0 (+0.00/trade) | | | | | | | | |
| M13 th-0.02 | 607 | +276.1 (+111.8/+164.4) | 47 | +185.6 | -3.75 | 1/0/0/0/0 | +0/-0 | secondary PASS |
|  ^ extended-trade detail: 0 trades, net +0.0 (+0.00/trade) | | | | | | | | |

## PRIMARY VERDICT — EXTENDED TRADES vs THEIR M7 TWINS
- M13 th0.00: 0 of 0 extended trades have an identical-entry M7 twin; twin delta +0.0 total (+nan/trade; nan% improved; worst +nan; per month {'2025-10': 0.0, '2022-02': 0.0}) -> PRIMARY FAIL
- M13 th-0.02: 0 of 0 extended trades have an identical-entry M7 twin; twin delta +0.0 total (+nan/trade; nan% improved; worst +nan; per month {'2025-10': 0.0, '2022-02': 0.0}) -> PRIMARY FAIL

Registry: T-MG22.

## READING — A STRUCTURAL RESULT, NOT A PARAMETER RESULT
Only 1 of 607 trades ever reaches the 480s clock: under M7, surviving
to 480s requires the peak to keep advancing every 60s, so the STALL
rule ends essentially every trade first. The clock cap is vestigial
on OUR trade population. Shape (b) is therefore structurally empty -
there is nothing to extend - and the result is decisive without any
parameter sensitivity.
Why he has long holds and we cannot copy them this way: HE does not
run a stall-60. His unexplained long holds are not "the clock plus a
book condition"; they are a different stall tolerance altogether. The
one lane that could express that is a book-conditioned STALL (stall
fires only when the book also says exit) - but shape (a) already
measured the stall-moment book signal's value on our fills and it was
NEGATIVE (-0.06/trade twin-matched). Both monetization guesses are
now resolved against; a third guess in the same family is not
justified by the evidence in hand.
WHERE THIS LEAVES THE EXIT EDGE: imb10 stands as true DESCRIPTION of
his exits (T-MG20, clock and path controlled) that does NOT transfer
as a rule onto our trade population on training data. Per the goal
refinement, the long-hold remainder moves to mode 2 (his results as
baseline) and/or the event-level book round.
