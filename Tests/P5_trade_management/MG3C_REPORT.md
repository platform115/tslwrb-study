# MG-3c — INTRADAY ADAPTER RESULT: CRITERION FAILED (T-MG06)
> Same pre-stated criterion. Outcome: pooled +564.8 (below both fixed
> settings), worst in 2021-09. FAIL - M1 stands. No M2 frozen.

| month | HIS | S=30 | S=90 | intraday (S q50) |
|---|---|---|---|---|
| 2025-10 | +620.0 | +200.0 | +242.5 | +207.8 (23 s) |
| 2022-02 | +751.2 | +246.2 | +222.4 | +227.9 (20 s) |
| 2021-09 | +383.8 | +142.4 | +192.6 | +129.1 (27 s) |
| pooled | +1755 | +588.6 | +657.5 | +564.8 |

## The structural finding from both adapter failures
Gap-based clocks tighten exactly when his entries happen, because his
entries sit in ACTIVE tape - extremes update fast there, measured gaps
are short, so the adapter reads "busy" and cuts patience. His behavior is
the opposite: he holds THROUGH the activity (median 183 s) and his hold
time does not shrink with tape speed. The patience that wins is not a
function of local tape speed at entry - both chartered-direction forms of
that idea are now tested and failed on his entries.

## Management round status
M1 stands (per the criterion, twice). Recorded findings: fixed S=90 wins
2 of 3 months (+12% pooled) but is regime-fragile through LOSS SIZE in
high volatility (avg loss -5.30 vs -4.67); every stall-clock adapter
tightens when it should not. The one chartered adapter NOT yet tested is
the STOP as a share of R_est (the dial the 2022-02 failure actually
points at - patience costs money there through bigger stopped losses,
not through the clock). Decision to test it, or to close the round with
M1 standing, sits with the user.
