# VALIDATION_PLAN — THE ONE PRE-REGISTERED LOOK (2023-05 + 2024-05)
STATUS: LIVING until the data arrives, then FROZEN | 2026-11-26
Plain purpose: everything that earned a claim on training data gets
judged ONCE, together, on the purchased months. Nothing on this page
may be tuned after the data is opened. Exact numeric thresholds are
frozen in an addendum BEFORE first read of the purchased files.

## DATA (J purchasing: Databento GLBX.MDP3, ES parent)
- schemas tbbo + bbo-1s; 2023-05-01..31 and 2024-05-01..31
- owed first: tbbo -> per-second converter + equivalence check against
  an existing MBP-10 month (drive has 2021-09 / 2024-11 raw MBP-10)

## WHAT GETS JUDGED (one look, fill-time engine, no costs)
1. G2-3 (primary): full standard. Shrinkage EXPECTED (7 stacked
   training-fitted choices); the pre-stated question is net > 0 both
   months with catch rate in line with training (74%-ish of his
   same-group entries), not a repeat of +276.
2. G2-4 (two-lane quality-alternate): same standard, judged beside
   G2-3; whichever survives better becomes the carried strategy.
3. G2-5 (N=1 cap, high-contract-size variant): per-trade quality is
   its claim (+0.90 on training) - judged on per-trade and both-months
   positivity, not total net.
4. tier20 engagement rates: his-trade engagement 78% (tier20) vs 27%
   (minor) - remeasure on whatever his activity shows in those months
   if his feed covers them; else measure the STRATEGY-conditional
   version (do tier20 windows carry more of the P&L?).
5. Parked suggestives (retest-only, no new tuning):
   - own0 (T-EN111): supporting-side top size higher at taken crosses
     (bbo-1s carries the field)
   - flow_vol_5m (T-EN112): first-5-min volume higher in engaged
     windows (tbbo carries aggressor flow)
   - flow direction at taken crosses (T-EN109)
   - sup0/flow at the 480s clock (T-MG19). imb10 SURVIVED EX2
     (T-MG20) but needs 10-LEVEL depth: bbo-1s cannot test it - either
     extend the purchase to mbp-10 for these months or carry it as
     training-evidenced only (J decides)
6. tier20 candidate shapes - MEASURED, not adopted: (a) engagement
   prior; (b) tier20-full / minor-selective contract split (G2-3 on
   tier20 windows vs G2-5 posture on minor).

## RULES
- One look. No parameter changes after opening the files.
- Every number above is written here BEFORE the data is read.
- Anything that fails here dies here; anything that passes earns the
  next quarantined month, not production.

## ADDENDUM 1 — DATA ARRIVED & CONVERTER CERTIFIED (2026-11-26); EXACT THRESHOLDS FROZEN
Data ingested (checksummed; provenance in Data/inputs/README.md). No
strategy number has been computed on these months. The one look runs
these, verbatim, on the FILL-TIME engine, both months:
1. G2-3: PASS = pooled net > 0 AND each month > 0 AND catch >= 60% of
   his same-group entries (group built by the B5 recipe) AND extras
   net > -20% of pooled net. Expected shrinkage vs +276.1 accepted.
2. G2-4: same four conditions; judged beside G2-3 - the better
   pooled net among those that PASS becomes the carried strategy.
3. G2-5: PASS = per-trade >= +0.60 AND each month > 0 (its claim is
   quality, not total).
4. tier20: his engagement rate on tier20 vs minor windows reported
   (direction must repeat: tier20 > minor) + strategy-conditional
   P&L share.
5. Suggestive retests (report direction + p, no thresholds, no
   adoption from these alone): own0 at taken crosses (book_top),
   flow_vol_5m at engaged windows, flow direction at taken crosses,
   sup0-at-clock (ANALYSIS B twin, top-of-book only).
6. tier20 candidate shapes measured descriptively (no adoption).
No parameter may change after the first strategy number is computed.
Anything failing here dies here.
