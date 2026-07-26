# SPEC 07 — VX-regime #2: front-month VX futures LEVEL at entry vs cut/reached
Status: COMPLETE. NULL (both populations). In-sample, October. Opens the VX/vol channel. Not advice.

## 0. Why this exists
Hypothesis (J): the vol regime may factor into wrbtrader's outcomes. #2 is the first VX test: does the
vol LEVEL at entry separate cuts from reached trades? (Planned VX sequence: #2 level -> #3 intra-trade
spike -> #4 normalizer -> #1 regime filter on S1/S2/VWAP.)

## 1. Data & instrument — IMPORTANT
Uses FRONT-MONTH VX FUTURES (XCBF.PITCH, VX.FUT, ohlcv-1m, Oct 2025), NOT the spot VIX index.
- The uploaded VIX *options* file (OPRA.PILLAR VIX.OPT) does NOT contain a VIX level — it is 8,741 option
  contracts' premiums. Unusable as a level without reconstruction. Set aside.
- Databento does not carry the spot VIX index (CBOE-calculated, not an exchange feed). Spot VIX is free
  daily from CBOE/datahub; 1-min is paid (firstratedata ~$99/yr, Barchart).
- Front VX = market's expectation of VIX ~30d out: correlated with spot (~0.8-0.95 typical) but smoother
  and offset by contango/backwardation. A legitimate vol-REGIME proxy. CRUCIALLY it trades ~24h, so it
  COVERS his overnight ES entries — spot VIX (US cash hours only) would MISS them. For this trader VX is
  the MORE appropriate instrument, not a second-best proxy. Reported as "front VX", not "VIX".

## 2. Method
Front-month roll = deterministic, CBOE rule (NOT hand-set): each VX contract's final settlement = the
Wednesday 30 days before the THIRD FRIDAY of the month FOLLOWING the contract month. Front at entry =
nearest outright whose expiry date is AFTER the entry date (rolls on expiry day). Spreads excluded
(symbols with ':'/'-'). Verified: V5 expiry 2025-10-22, X5 2025-11-19 (correct). Oct entries split
V5:54 / X5:38.
  vx_at_entry = front-month close at most recent 1m bar at/before entry.
AUC two-sided + cluster-bootstrap CI (seed 0). Populations: clean (losing16 vs reached47), pt1
(failed40 vs target_reached52).

## 3. Result — NULL
Coverage: 92/92 trades had a live front-VX at entry (24h coverage confirmed). Range 17.55-23.80, median
18.59 vol points (a NARROW band — no spike, no calm-to-crisis spread in October).
  clean: median VX cut=18.31 / reached=18.59. AUC 0.539, CI [0.387, 0.680] — spans 0.5.
  pt1:   median VX cut=18.58 / reached=18.59. AUC 0.502, CI [0.409, 0.591] — spans 0.5.
Medians near-identical in both. The vol level at entry does NOT separate his outcomes.

## 4. Interpretation — scope the null honestly
- RULED OUT: VX level at entry as a standalone cut/reached predictor, ACROSS THE VOL RANGE PRESENT IN
  OCTOBER (~6 points, 17.6-23.8). He neither avoids elevated vol nor fails more in it — within this band.
- NOT ruled out: behaviour across a WIDER vol range (a calm VIX-13 vs panic VIX-35 month) — those
  conditions are not in October; this is a low-dispersion-month null, weak evidence not strong.
- NOT addressed: vol CHANGE during the trade (#3) — a flat entry-level relationship says nothing about
  an intra-trade vol spike preceding cuts.
- Would spot VIX change this? Almost certainly NOT for the LEVEL null (VX/spot highly correlated) — and
  spot VIX has worse coverage here. The vol feature both level tests MISS is the TERM-STRUCTURE SLOPE
  (front - next-month), computable from the VX file already (V5/X5/Z5...) — a candidate future test.
- POWER NOTE: front VX is autocorrelated within a day; effective n ~ number of vol-days (~22), not 92.
  A daily-clustered CI is the honest read; null conclusion is unaffected (point estimates already ~0.5).

## 5. Files (in 07_vx_regime/)
- test_vx_level_entry.py   CANONICAL — front-VX level at entry, AUC+CI both populations. Reads VX dbn
  directly (databento), --vx path arg. Path bootstrap points at 06_trade_flow_exhaustion_CANDIDATE/
  for the shared spine (see §7 note).

## 6. Reproduce (07_vx_regime/; no SSD needed — episodes + VX file only)
  python3 test_vx_level_entry.py --config ../../config.toml --wrb ../../wrb_1m.parquet \
      --vx xcbf-pitch-20251001-20251031.ohlcv-1m.dbn.zst

## 7. Notes / debt
- The spine (horse_race_spine, trade_flow_exhaustion) lives inside 06_trade_flow_exhaustion_CANDIDATE/;
  07 reaches it via an EXPLICIT path bootstrap. FRAGILE: renaming the 06 folder breaks this. CLEANUP:
  hoist the spine to Tests/ (or project root) so all channels import it by walking up. Do between tests.
- config needs a [paths] vx entry once the VX file's permanent location is set (currently --vx arg).
- NEXT: #3 intra-trade VX spike — but flag: over his ~60-120s holds, 1-min VX may barely move; #3 could
  be null-by-construction. A quick "how much does front-VX move over hold windows" diagnostic is advised
  before building #3 in full.
