# MG-3d — STOP AS SHARE OF R_est: CRITERION FAILED (T-MG07)
> First run collapsed into the clip ceiling (all shares -> stop 8.0) and
> was discarded as an implementation artifact - disclosed, not counted.
> Corrected run (shares 0.08/0.12/0.17, clip [1.5, 10]):

| pooled | HIS | M1 | S90/stop4 | S90/R.08 | S90/R.12 | S90/R.17 |
|---|---|---|---|---|---|---|
| total | +1755 | +588.6 | +657.5 | +620.1 | +619.9 | +622.1 |
All three shares FAIL the criterion. R-scaled stops run 5-10 pts in the
high-volatility month and lose ~30 points pooled vs the plain 4.0 stop.
The chartered direction (wider stops when the expected range is bigger)
is wrong on his entries: the high-vol month's losses need LESS room, not
more - but flipping the direction now would be a post-hoc search, so it
is recorded as a hypothesis for a future pre-registered round, not run.

# MANAGEMENT ROUND — CLOSED (M1 STANDS)
Five gated runs (MG-1..MG-3d), every freeze criterion enforced:
- The patience diagnosis is solid: his edge over M1 is holding through
  activity (183 s vs 50 s, 83% capture of 2x the move).
- Fixed S=90 is the best mechanical variant found (+657.5 pooled, +12%
  over M1) but loses the high-volatility month - regime-fragile, so per
  the criteria it was not frozen.
- Every adapter tested (prior-session gaps, intraday gaps, R-share stops)
  failed; the gap-clock forms tighten exactly when his behavior holds.
- M2 remains undesigned; M0/M1 untouched throughout.
Open, pre-registerable later: time-stop adapter (peak-time distribution);
tighter-stop-in-high-vol (direction-flipped stop rule); management
conditioned on the trade's own early excursion shape.
