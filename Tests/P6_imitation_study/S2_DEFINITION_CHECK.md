# S2 — DEFINITION CHECK (T-IM16): WRB / Hidden GAP / Long Shadow
> Status: REVIEWED - CLOSED (user 2026-11-20). Decisions:
> (1) WRB + WHG kept as sourced/implemented. (2) Long Shadow: calibrate BOTH
> D1 and D2, with LOOSER initial thresholds than the 2x rule ("a bit less
> strict until we know more") - the wide net first, narrowed by calibration.
> (3) Shadow intervals stored as full-range bands with shadow sub-range
> field; calibration decides which his references track.

## 1. WRB — ALREADY DEFINED, SOURCED, IMPLEMENTED. Proposal: KEEP.
`WRB Definition.txt` (repo root, "single source of truth", sourced to
M.A. Perry / WRBAnalysis.com) §1.2: body = |close−open|; a bar is a WRB when
its body is **strictly greater than each of the prior 3 bars' bodies**;
doji can never be a WRB; direction recorded separately.
Implementation exists and was hand-verified: `build_whg_series.py`
(Tests/06-10), including the project discipline that the prior 3 bars must
share the session_date (no WRB across a session seam).
S3 will re-use this code path on the decided TF set (1/2/3/5/15m).

## 2. WRB Hidden GAP — ALREADY DEFINED, SOURCED, IMPLEMENTED. Proposal: KEEP.
Same file §1.4–1.5: the zone inside the WRB body not traded by the prior
3 bars' bodies (bullish: [prior_body_high, close]; bearish mirror).
Fill status UNFILLED / PARTIAL / FILLED — PARTIAL is marked
[PROJECT CONVENTION], the rest sourced.
Maps directly onto his vocabulary: "open (unfilled) WRB Zones via Up WRB
Hidden GAP intervals" — an UNFILLED WHG is an OPEN zone (T-IM13 discovery
#2). S3's first generator consumes this as-is.

## 3. Long Upper / Lower Shadow interval — THE GAP. Candidates below.
### Anatomy (universal, undisputed)
upper_shadow = high − max(open, close); lower_shadow = min(open, close) − low.
(Nison 1991; every standard reference.)

### What "long" means — no fixed standard exists
- No public quantitative definition from M.A. Perry was found for "Long
  Shadow" (searched; his study guide material is not indexed publicly).
  **Stated per project rule: this is a gap, not a fact.**
- The documented rule of thumb (TrendSpider guide): a shadow is "long" when
  **at least twice the length of the body**, with the body relatively small
  and the opposite shadow small or absent — i.e. the hammer / shooting-star
  family (TradingView's own screener page is qualitative only).
- HIS words (only 2 definitional hints in 31,838 messages):
  "another **small body** with a long upper shadow interval" (2021-12);
  "Long upper and lower shadow intervals on the **same small body**
  interval" (2025-04) — consistent with the small-body requirement, no
  threshold stated. He trades the **range of** the interval ("price moving
  up/down the range of the most recent Long Upper Shadow interval").

### Candidate definitions for S3 calibration
- **D1 (documented rule of thumb)**: same-side shadow ≥ 2× body AND
  opposite shadow ≤ body. Thresholds (the 2×, the opposite-shadow cap, and
  a minimum shadow size in ticks or ATR-fraction to kill noise bars) are
  FREE PARAMETERS calibrated against his shadow-interval references in S3 —
  not assumed.
- **D2 (WRB-analogous, by symmetry with Perry's WRB rule)**: same-side
  shadow strictly > that side's shadow of each of the prior 3 bars.
  **[NO DIRECT PRECEDENT FOUND — constructed by analogy with his sourced
  WRB rule; flagged per project rule. Include in calibration only if
  approved.]**
- Stored object either way: the qualifying interval's **full range
  [low, high]** as the band (his "range of the interval" phrasing), with
  the shadow sub-range kept as a field; S3 calibration tests which one his
  references actually track. Both-shadow bars (his 2025-04 message) are a
  single interval carrying both flags.

## 4. Existing-code audit
- `build_whg_series.py` — WRB+WHG per the definition file, hand-verified
  on 2025-10 5m. No shadow logic exists anywhere in the repo (grep).
- `p4_5a wrb_bodies` / p6_1 border catalog — body boundaries only; 
  consistent with §1 but computed on TFS=(1,3,5); S3 recomputes on the
  decided set.
- `WRB Definition.txt` §5 (WRB pt1/pt2/pt3) matches his event usage
  (targets occurring in trade direction), confirmed by the parser's event
  rows.

## 5. Decisions requested at this gate
1. Keep WRB + WHG definitions as sourced/implemented (recommend: yes).
2. Long Shadow: calibrate D1 (documented) in S3 — and include D2
   (analogy, unsourced) alongside it, or drop D2?
3. Confirm: store shadow intervals as full-range bands with shadow
   sub-range field, calibration deciding which his references track.

## Sources
- WRB Definition.txt (repo; sourced to M.A. Perry, WRBAnalysis.com)
- Nison, S. (1991). *Japanese Candlestick Charting Techniques* (shadow anatomy)
- TrendSpider Learning Center, "Long Shadow Candlesticks: A Trader's Guide" (2× rule of thumb)
- TradingView support: "Long Upper Shadow - Bearish" (qualitative only)
- His messages (2021-12-15, 2025-04-23) — small-body hints
