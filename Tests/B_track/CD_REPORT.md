# CD REPORT — CADENCE CAP PER NEWS WINDOW (T-EN110)
STATUS: CLOSED | 2026-11-26 | Spec: CD_SPEC.md (committed first) | engine: fill-time (standard) | corrected incumbent G2-3: +276.1 / 607 / catch 47 / extras +185.6 | his G2: +231.2 / 62 / +3.73

MANDATORY CHECKS: all passed (control reproduced exactly; monotonicity, candidate-membership with busy-explained non-control fills (corrected check 3, spec addendum 1), no-duplicate, no-empty-month).

## HIS CADENCE (descriptive anchor)
| his entries per window | windows |
|---|---|
| 1 | 20 |
| 2 | 8 |
| 3 | 3 |
| 4 | 3 |
| 5 | 1 |

## GRID (cap on filled trades per news window)
| cell | trades | per-trade | net (22-02/25-10) | caught/62 | extras net | verdict |
|---|---|---|---|---|---|---|
| CONTROL | 607 | +0.45 | +276.1 (+111.8/+164.4) | 47 | +185.6 | (incumbent reproduced) |
| N=3 | 262 | +0.55 | +144.8 (+62.4/+82.4) | 30 | +93.1 | no |
| N=2 | 184 | +0.70 | +128.5 (+44.5/+84.0) | 25 | +68.5 | no |
| N=1 | 98 | +0.90 | +88.0 (+41.8/+46.2) | 14 | +28.1 | no |

Registry: T-EN110.

## READING
- His cadence: 20 of 35 windows he traded, he traded ONCE. The cap
  imitates that surface statistic — and fails, because he is
  SELECTIVE, not EARLY: caps keep our first fills per window, and
  his entries are typically the window's later signals (median 9-12
  min after release; 2nd cross when several exist). N=1 catches only
  14 of his 62.
- Quality gradient is real and monotone: +0.45 -> +0.55 -> +0.70 ->
  +0.90 per trade as the cap tightens. But it never reaches the
  +0.98 bar, and net collapses (N=1 keeps 98 trades earning +88.0
  of +276.1 — the LATER fills in a window carry two-thirds of the
  net). The fat-tail warning in the spec's against-hypothesis is
  what happened.
- Combined with T-EN109: "trade less" only works as "pick better,"
  and picking better within a window is exactly the question that
  went null on tape features and now waits on the order book.

## VERDICT (per the frozen lines)
All cells REJECTED (no cell ADOPTs; best per-trade +0.90 < +0.98
with net +88.0 << +150's companion conditions met but the per-trade
bar missed). G2-3 stands; G2-4 remains the registered alternate.

## PROCESS NOTE
The first execution ABORTED at the mandatory checks before any
results were computed: check 3's own premise (capped cells are
subsets of control) was wrong — capping frees the busy clock, so a
capped cell can legitimately take a fill control missed while in a
position. Spec addendum 1 documents the correction; the corrected
check (every fill is a known candidate, and every non-control fill
lands while control was busy) passed. This is the checks working as
designed: the error was stopped at the gate, not found in published
numbers.
