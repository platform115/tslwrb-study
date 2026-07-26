# 06-5 — Behavioral baseline: MAE / time-stop  (test_behavioral_baseline.py)

Status: RUN (Oct-2025 ESZ5 discovery). Result: MAE SEPARATES strongly; losers cut FAST.
The most informative result of the session. This doc = recreatable spec + plain-terms meaning +
what builds on it + practical trading use.

===============================================================================
## A. SPEC (recreatable exactly)

### Claim tested
Can a mechanical risk rule with ZERO order-flow data — "exit when price has gone against entry by
X" (a stop), or "exit after T minutes" (time-stop) — separate losing exits from runners as well as
the tape did? If yes, his exits are substantially stop-like and exit-microstructure adds little.

### Contrast (from the 06-4 relabel)
losing_trade (16) vs reached_target (47). below_target_win (29) HELD OUT. (= the clean exit contrast.)

### Feature 1 — MAE (Maximum Adverse Excursion; Sweeney 1996), from ENTRY, BAR-DOMAIN
    long : MAE = max(0, entry_price - min(bar lows  over [entry, anchor]))   [points]
    short: MAE = max(0, max(bar highs over [entry, anchor]) - entry_price)   [points]
- Source = es_1m_front 1m bars (bar-domain by design; a behavioral baseline built from ticks is not a
  behavioral baseline). entry_price = entry_prices[0] (Oct verified single-entry/unscaled; reconciles
  with realized_pnl at corr 1.0).
- Window = [entry, anchor] (cumulative FROM ENTRY — NOT the trailing-60s flow window). Cut-time-matched
  Design A: each loser MAE over [entry, exit] vs reached peers (pt1_open_el > tau=loser hold) MAE over
  [entry, entry+tau]. Same elapsed exposure -> not "losers held longer". Per-cut AUC = P(reached MAE >
  loser MAE); cluster-bootstrap CI (seed 0, 10000) over the 16 losers. TWO-SIDED (prior: losers larger
  adverse -> P<0.5 = stop-consistent).
- Bars overlapping [entry, anchor]: indices [searchsorted(e_s-60), searchsorted(anchor)). NOTE: the
  entry bar's full low/high is included (entry-bar inclusion) — symmetric across arms; tighten to
  strict-from-entry-tick if MAE is ever marginal.

### Feature 2 — Time-stop (hold-duration separation, population-level)
Population AUC on hold minutes, losing vs reached (cannot cut-time-match — hold IS the matching var).
Report both medians; DIRECTION is the read.

### Files / run
horse_race_spine.py (rank_auc, cluster_boot_ci, two_sided); trade_flow_exhaustion.py (build_groups);
config.toml; wrb_1m.parquet; es_1m_front (from config). Deterministic, read-only.
    python3 test_behavioral_baseline.py --config <cfg> --wrb <wrb_1m.parquet>

### Result (Oct-2025 ESZ5)
- MAE Design A: P=0.227, 95% CI [0.117, 0.364], 16 cuts -> SEPARATES. Loser MAE med 3.00 pts vs
  reached-peer med 1.25 pts (~2.4x further against entry at matched elapsed time).
- Time-stop: AUC 0.766; loser hold med 1.7 min vs reached 5.2 min -> losers cut MUCH FASTER.

===============================================================================
## B. WHAT IT MEANS (plain terms)

Losing trades went against him FURTHER and FASTER, and he got out FAST. In equal time-in-trade, a
loser had run ~3 points against entry vs ~1.25 for a trade still heading to target — and losers were
held ~1.7 min vs ~5.2.

So the cuts look like a REACTIVE ADVERSE-PRICE response, not a clock: he is not holding losers waiting
for a time-stop (he cuts them faster than winners), he is reacting to price moving against him quickly.
A chart-readable "it's going against me" rule reproduces the SEPARATION with no order book at all.

Crucially this is SEPARATION, not REPRODUCTION. "Losers have bigger MAE" is not "one threshold fires at
his exact exits" — the distributions overlap (3.0 vs 1.25 with spread). Whether a single stop level
actually lands where he got out is UNTESTED (that is 06-6, below).

Caveats kept honest: 16 losers, one month, discovery. Two-sided CI clears 0.5 but n is small. The
3.0-pt loser MAE may be slightly inflated by entry-bar inclusion. Weak evidence of a real effect, not
a validated magnitude.

===============================================================================
## C. WHAT WE BUILD ON FROM IT

1. Leading hypothesis for EXIT behavior is now: adverse-price risk reaction, replicable without MBP-10.
   Sits beside the consistent exit-microstructure nulls (book-direction 03/04/05; impact 06-2) and the
   raw-movement separation (06-3, 07a-numerator).
2. The signals that SURVIVE are split by lifecycle: ENTRY-anchored flow LEVEL (early_flow_confirmation,
   0.672, frozen) separates at trade start; ADVERSE EXCURSION (this test) explains the cut. The exit
   edge being stop-like does NOT kill the separate entry-selection edge.
3. Next test = 06-6 REPRODUCTION (the decisive one): does a single MAE threshold (and/or adverse-velocity
   rule) FIRE at his actual exit times — precision/recall against his real cuts, not just group AUC.
   This distinguishes "stop explains him" from "losers merely have bigger MAE".

===============================================================================
## D. PRACTICAL TRADING USE (what a working version could do)

If 06-6 confirms reproduction, the practical artifact is a DETERMINISTIC ADVERSE-EXCURSION EXIT FILTER,
not a microstructure indicator:
- Rule shape: "if open trade's adverse excursion from entry exceeds ~X points before target (pt1) is
  reached, the trade is in the loser-like population — cut / do not add." X calibrated on the loser vs
  reached-peer MAE gap (Oct: loser med 3.0 vs reached 1.25), VALIDATED on holdout before use.
- Pairs with the entry signal, not competes: early_flow_confirmation (entry) screens trade QUALITY at
  start; this MAE filter manages RISK once in. Two different jobs, two different lifecycle points.
- Determinism fit: MAE from bar lows/highs is fully mechanical -> portable to a YAML exit rule and a
  Pine/transpiler path with no LLM/tick dependency. This is exactly the kind of mechanically observable,
  reproducible exit condition the project is hunting.
- Honest limit: this is an exit-RISK rule (cut bad trades early), not an alpha signal. Its value is
  reducing time-in-loser / adverse give-back, consistent with "MBP-10's realistic role = filter out
  dead/adverse trades early." It does NOT claim to predict direction.
- DO NOT deploy on the discovery basis: separation on 16 Oct losers is a hypothesis. Reproduction (06-6)
  + holdout-month validation are required before any rule is trusted.
