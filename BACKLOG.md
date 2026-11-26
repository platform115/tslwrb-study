# NOTE (2026-11-24): this backlog is being absorbed into MASTER_PROGRAM.md tracks; items not yet absorbed remain valid.

# OUTSTANDING TASKS (2026-11-20; the working backlog)

## 1. ENTRY SEARCH (ongoing, no fixed end)
1a. Imitation cycle 3 - the drift remainder, with data not yet used:
    order book (book_per_sec), trade prints / large-lot sweeps,
    cross-market insync (NQ/YM/VIX lead-lag), his sequence context
    (previous trade outcome), finer path shapes.
1b. Our own system (bounded search): resumes once a management plan
    better than M1 exists; current rules locate his places but earn
    ~zero mechanically.
1c. Key-KME-Zone system: generated zone list still unsolved (stated-price
    clusters = validation set; implied lists proven dead).
1d. VTR (his second system): definition hunt still open (2 corpus rows).
1e. More data months when acquired (user has more to load) - every frozen
    rule revalidates there first.

## 2. TRADE MANAGEMENT TESTING (regime-aware)
2a. Pre-registerable next candidates: time-stop adapter (peak-time
    distribution); DIRECTION-FLIPPED stop rule (tighter in high vol -
    what MG-3d's failure points at); management conditioned on the
    trade's own early excursion shape.
2b. His winner-holding mechanism - the unexplained +620-vs-+657 gap:
    what does he see that keeps him in? (ties to 1a data).
2c. ETH-specific management (M1's ETH settings inherited, lightly tested).
2d. Re-entry mechanism (charter item, "soon" since the M1 era).
2e. Scale-out / adds management - BLOCKED until months with multi-entry
    episodes are in the data (2025-10 has none; check 2022-02/2021-09).
2f. Any new winner validates on untouched months before freezing
    (the 437 episodes used today carry selection pressure).

## 3. BACKTESTING PROGRAM (the X-entry x Y-management matrix)
3a. Matrix plan: {Strategy 1 (certified T-EN102), 3A, 3C, 3D, future} x {M0, M1, M1A,
    future M2} x {RTH, ETH, both} - each cell pre-registered, run once.
3b. STANDARD RESULTS SET (user-specified + additions):
    - comparison vs HIS trades in the same period (totals + per-trade)
    - win / loss rate; points gained / lost (avg win, avg loss, totals)
    - worst drawdown within a single trade (max adverse excursion)
    - max drawdown from the period's starting point (existing mandate)
    - ADDITIONS: profit factor; expectancy per trade; longest losing
      streak; trade count and fires/day (attention realism); time in
      market; trade-duration distribution; per-regime split (volatility
      terciles, KME-day vs quiet-day); month-by-month stability table;
      equity curve; flat-day count
    - costs/sizing stay out of scope per project instructions
    - DISPLAY: every entry test uses RESULTS_DISPLAY_STANDARD.md (agreed 2026-11-21)
3c. Harness rule: every entry gate passes truncation checks before any
    cell runs (standing).

## 4. HIS LEVELS - THE CLOSER LOOK (study, descriptive)
4a. Full-month day maps: every trade with its identified trigger object,
    level lifecycle before/after (formation -> tests -> his reaction ->
    traversal -> role flip), not just the 3 busiest days.
4b. How he trades each object class differently (reaction levels vs gaps
    vs squeeze bands vs Key zones): direction, displacement, hold time,
    exit relation to the next level.
4c. KME-day vs non-KME-day regimes: which machinery he runs on each
    (visible already in the Oct 1 vs Oct 17 maps - make it systematic).
4d. His emphasis tiers (color-coded Key zones): any measurable correlate.

## 5. INFRASTRUCTURE / OTHER
5a. Pine track: stage 2 + fire vectors still HALTED pending settled entry
    rules; stage-1 session-stats vectors still owed to that thread.
5b. Python runner / VPS thread (separate conversation) - unchanged.
5c. 2022-02 "signal @ 4321.50" dissection (parked since that era).
5d. Registry hygiene: naming map (V1/U -> ER-SIG/ER-WIDE) done; keep.
- RESOLVED (T-MG10): the OTHER exit-gap class = his FAST PROFIT-TAKING (14/16 exited at the spike before a 60s stall could fire); 1 long-hold window-cap case; 1 data noise. Open successor: SPEED-CONDITIONED dual-mode exit study/round (M5).

- STANDING SIMPLIFICATION (J, 2026-11-25): scale-outs are modeled as single regular exits (mean price); J does not plan to scale for a long time.
- DETECTOR DESIGN CONSTRAINT (J + census, 2026-11-25): the multi-day
  level detector must be built from HIS structure families (WRB bodies,
  gap edges, shadow zones, S/R reactions persisting across days) with
  the formed-at-news flag first-class - NOT generic floor levels
  (census: he never says pivot/value area/POC/VWAP). Generic levels
  enter only as a comparison arm. Recovery check vs his stated keys
  (S4: n=7 clusters - direction solid, magnitude uncertain) runs with a
  pre-stated flag-line BEFORE any rule consumes a generated level;
  a miss = detector unfit for the M6C path, documented, no surprise.
  Order: C (squeeze coverage audit) first, this build second,
  management (M6C stage 1) resumes only after the recovery check.
- Role-flip levels, smarter form (T-IM52): blanket persistence fails at fair density; candidate = flipped levels kept only with a freshness window / retest confirmation. Low priority until G3 cycle.
- Strategy 4 revision batch (post-G3): add squeeze cell W20 q0.8 (T-IM54: converts 5/9 misses, extras +239.8 under M3A) - NOT q0.5 (toxic at trigger level, -107.1). MUST model overlap with the shipped W10/W30 fills in the re-run (combined is not the sum). The 4 residual misses are zone-break trades (on GAP/SHD edges) -> G3-cycle zone-trigger question.
