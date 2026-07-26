# SPEC 06-10 — WRB Hidden Gap (WHG) / gap-capture setup + exit test
Status: COMPLETE. In-sample October, holdout-pending. Two distinct outputs: (1) a SETUP
characterization useful for ENTRY work, (2) an EXIT-signal NULL. Not a validated edge. Not advice.

## 0. Why this is a self-contained handoff
The gap-capture SETUP findings here are meant to be picked up by a SEPARATE conversation focused on
ENTRIES. Everything needed to reproduce the population is in this spec + WRB_Definition.txt. The EXIT
question was answered (null) and is recorded for completeness.

## 1. WHG identification (source: WRB_Definition.txt — single source of truth, no invention)
WRB: body[i]=|close-open| STRICTLY > body of EACH of the prior 3 bars (doji body=0 cannot be a WRB).
  bullish WRB: prior_body_high = max over prior 3 of max(open,close); WHG=[prior_body_high, close] if close>prior_body_high.
  bearish WRB: prior_body_low  = min over prior 3 of min(open,close); WHG=[close, prior_body_low]  if close<prior_body_low.
Project discipline: the prior 3 bars must share session_date with bar i (no WRB across a session seam).
Built by build_whg_series.py on CONTIGUOUS OHLC: 1m from es_1m_front, 5m from es_5m_front (NOT wrb_1m —
that is WRB-only/sparse; WHG needs contiguous bars). Verified: 5m Oct example WHG @2025-10-01 00:15
bearish, zone [6716.50,6721.50] size 5.00 reconciles by hand. Oct counts: 1m ~6170 WRBs/4965 WHGs;
5m ~1421 WRBs/1174 WHGs. Typical zone: 1m ~1pt, 5m ~5pt.

## 2. Gap-arrival population (THE REPLICABLE SETUP — for entries)
A trade is a "gap-arrival / WHG-capture" trade if at entry it sits at a LIVE WHG it is pointed to fill:
  - LIVE WHG = WRB bar completed within a validity window before entry AND not yet filled by entry.
    A WHG is DEAD the moment it is fully traversed (high>=top AND low<=bottom by any 1m bar). Validity
    window swept 1/2/3 days — results are window-INSENSITIVE (use 2d); relevant WHGs are mostly recent.
  - distance entry->nearest live WHG zone: INSIDE (entry within zone) or NEAR (<= 8 ticks = 2.0 pt).
  - pointed THROUGH: long with zone top >= entry (room above) / short with zone bottom <= entry.
  - tiebreak: if inside multiple, the most-recently-formed; else the nearest by price.
On 5m, October: INSIDE 31, NEAR 8, of which ~34/40 pointed-through = ~34 gap-arrival trades. Window-
stable. (1m gives a larger, noisier set; 5m is the structural one — use 5m as primary.)

## 3. SETUP CHARACTERIZATION (the useful output, for ENTRY work)
- Gap-arrival is a REAL, identifiable setup: ~34 of 92 October trades. NOT all his trades are gap-
  arrivals (some are WRB-continuation alone) — this is ONE setup among several.
- It is a DISTINCT, higher-quality trade set: of the 34, only 4 are losers (~12%) vs 16/92 (~17%)
  baseline; 22 target_reached, 12 failed. So gap-capture trades skew toward winners.
- Trades overwhelmingly TRAVERSE the gap: 29/34 reach the far edge. Most run WELL PAST it — directional
  traversal_frac median 1.67, mean ~3.2, with ~62% exceeding 150% of the zone. The gap behaves as a
  LAUNCH level (price fills it and continues), NOT a target price stops at.
- Among traversers, eventual winners run far past (reached median traversal_frac 3.43) vs stalls
  (failed median 1.67). The discriminator of trade quality is HOW FAR PAST the gap it runs.

## 4. EXIT-signal result (NULL on early prediction)
Question: among gap-capture trades, does an EARLY forward signal predict big-run vs stall (for exit)?
- Early gap-progress AUC(reached>failed), still-open: τ=30/60/90/120 = 0.464/0.581/0.479/0.537 — bounces
  around 0.5. @60s CI [0.469,0.700] INCLUDES 0.5. Velocity (time-to-half) flat: both 15s median.
- Non-circularity spread @60s: reached early-progress p50=1.12 vs failed p50=1.08 — IDENTICAL early. The
  winners' advantage is in the late upper tail (p90 3.37 vs 1.39), i.e. they diverge LATE, not early.
- VERDICT: no usable EARLY exit signal here. Gap-capture trades start indistinguishably and separate
  late, so the early-checkpoint approach that worked for S1 does not apply to this setup.

## 5. Relationship to S1 (body-progress) — moderate, unresolved at this n
corr(gap_progress@60, body_ratio@60) = +0.59 ; corr(traversal_frac, body_ratio@60) = +0.46.
Moderate positive (share ~35% variance): related but NOT identical (not ~0.8), NOT independent (not ~0).
n too small to resolve. NOTE: S1/S2 are GENERAL exit signals (derived across all trades); they are not
WHG-specific and should not be conflated with the gap-capture setup.

## 6. LABEL-BUG HISTORY (important for provenance)
test_gap_traverse_exit.py (v1) used a BOTH-EDGES coverage label (max_high>=top AND min_low<=bottom).
For a long entering near the bottom and running up, min_low<=bottom rarely re-triggers -> traversal
massively under-counted (FALSE 6/34). ALL v1 outputs (AUC, velocity, the "+0.00 S1 corr") are INVALID.
SUPERSEDED by test_gap_capture_v2.py, which uses the correct DIRECTIONAL far-edge label (29/34). The
descriptive gap_traverse_distribution.py exposed the bug (85% reach far edge).

## 7. Files (in 06-10_whg_fill/)
- build_whg_series.py            CANONICAL — builds whg_1m / whg_5m tables (step 1). Needs es_5m_front in config.
- probe_whg_arrival.py           CANONICAL — gates the population (gap-arrival is real, counts only).
- gap_traverse_distribution.py   CANONICAL — descriptive traversal distribution (exposed the v1 bug).
- test_gap_capture_v2.py         CANONICAL — the exit test, correct directional label.
- test_gap_traverse_exit.py      SUPERSEDED/BUGGY — kept for provenance only; results invalid.
- test_whg_fill_hazard.py        EARLY/SUPERSEDED — first framing (in-trade fill as invalidation);
                                 inconclusive-by-construction (timescale mismatch); kept for provenance.
- whg_1m_2025-10.parquet, whg_5m_2025-10.parquet  — built WHG tables.

## 8. Reproduce (06-10_whg_fill/; add es_5m_front to config[paths]; SSD for the per-second tests)
  python3 build_whg_series.py        --config ../../../config.toml
  python3 probe_whg_arrival.py       --config ../../../config.toml --wrb ../../../wrb_1m.parquet
  python3 gap_traverse_distribution.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet
  python3 test_gap_capture_v2.py     --config ../../../config.toml --wrb ../../../wrb_1m.parquet

## 9. Caveats
34 trades (failed-traverser arm ~8), October, in-sample. The SETUP characterization (§3) is the durable
output; the EXIT null (§4) is on early prediction specifically — it does not say the setup is bad (it is
high-quality), only that it offers no early exit read. Carry the setup, S1, S2, and frozen entry-flow
candidates to HOLDOUT, where n grows. NEAR=8t and the 2d window are parameters — re-confirm out-of-sample.
