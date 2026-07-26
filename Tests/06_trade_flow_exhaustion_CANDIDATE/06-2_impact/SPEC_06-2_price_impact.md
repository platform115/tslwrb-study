# SPEC 06-2 — Price Impact (Kyle/Amihud lens): 07a plain + 07b oriented-subset

Status: RUN (Oct-2025 ESZ5 discovery). Result: impact lens NULL. Recreatable from this doc +
`horse_race_spine.py` + `trade_flow_exhaustion.py` + CURRENT_STATE.md + WRB_Definition.txt.

## CLAIM TESTED
Does price impact (price move per unit traded volume) over a short pre-exit window separate
losing/non-runner exits from runners? Two documented mechanisms, OPPOSITE signs, so TWO-SIDED:
high impact = thin/easy-to-push = vulnerable (Kyle 1985 depth); low impact = volume absorbed
without price moving = absorption. Ref: Kyle (1985); Amihud (2002); Cont-Kukanov-Stoikov (2014).

## TWO TESTS
- 07a PLAIN (undirected): impact over ALL window seconds. The Amihud ratio and the Kyle-λ slope
  both cancel trade orientation, so 07a is direction-agnostic (`side` unused). This is the clean λ.
- 07b ORIENTED-SUBSET (directional): same formulas but only over seconds where flow is WITH the
  trade (oriented_flow > 0). The subset USES the trade sign, so 07b is the only directional impact
  test. Absorption = low impact on with-trade flow.

## FEATURE FORMULAS (per per-second series in window; diff-seconds i=1..n-1)
    dmid_i (ticks) = (mid_i - mid_{i-1}) / TICK          TICK=0.25
    vol_i          = buy_vol_i + sell_vol_i              (total traded size that second)
    sflow_i        = buy_vol_i - sell_vol_i              (signed aggressor flow)
    oriented_flow_i = sflow_i * (+1 long / -1 short);  oriented_dmid_i = dmid_i * sign
  RATIO (Amihud-family) = Σ|dmid_i| / Σ vol_i            (07b: over subset {oriented_flow>0})
  SLOPE (Kyle λ)        = Cov(x,y)/Var(x), x=sflow,y=dmid (07a) ;
                          x=oriented_flow,y=oriented_dmid over subset (07b); n>=2 & Var>0 else NaN
  NUMERATOR-ONLY (07a only) = Σ|dmid_i|  — raw movement, the necessary-vs-sufficient probe vs 08.
  Per-second build: trade prints only (action=="T"); buy_vol=Σsize(side=="B"), sell_vol=Σsize(side=="A"),
  mid=last (bid_px_00+ask_px_00)/2 per second; sizes uint32 -> int64.

## POPULATION & WINDOW
- 52 target_reached vs 40 failed_trades (Reading B, frozen pt1; via build_groups). TWO-SIDED.
- PRIMARY window = Design A (cut-time-matched, trailing W=60s): each failed cut at [max(entry,exit-W),
  exit) vs target_reached peers still pre-pt1 at tau=hold over [max(entry,entry+tau-W), entry+tau).
  Per-cut AUC = P(reached value > failed value); cluster-bootstrap CI (seed 0, 10000) over 40 cuts.
- Context (inherits pt1 coil confound, not for inference): A1 [entry-180s,entry); anchor (A2/B collapse).
- Tripwire: window with gap>120s or |mid jump|>40 ticks -> excluded. Floor: <8 valid cuts -> uninformative.

## COMBINED READING-A VERDICT (pre-registered)
Impact LENS = {07a ratio, 07a slope, 07b ratio, 07b slope}. Lens INFORMATIVE if ANY 95% CI excludes
0.5 at >=8 cuts; else NULL. (07a numerator-only is NOT in the lens — it is raw movement, the 08 signal.)
Combination of features ACROSS tests is a HOLDOUT-only hypothesis (forbidden on discovery).

## FILES / RUN
- horse_race_spine.py (shared: grouping, Design A enumeration, rank AUC, cluster CI, coherence).
- trade_flow_exhaustion.py (frozen: build_groups, read_per_second, constants). config.toml, wrb_1m.parquet.
- MBP-10 windowed parquet (run.resolved.windowed_parquet); stream ~73M rows, ~252k per-second grid.
    python3 test_07a_impact.py --config <cfg> --wrb <wrb_1m.parquet>
    python3 test_07b_impact.py --config <cfg> --wrb <wrb_1m.parquet>   # also recomputes 07a + verdict

## RESULT (Oct-2025 ESZ5, 40 cuts, two-sided)
- 07a ratio P=0.424 [0.332,0.521] null ; 07a slope P=0.434 [0.339,0.532] null
- 07b ratio P=0.483 [0.388,0.583] null ; 07b slope P=0.493 [0.405,0.580] null  (subset ~26 sec/window)
- 07a NUMERATOR-ONLY P=0.242 [0.166,0.323] SEPARATES (failed>reached movement) — same direction as 08.
- VERDICT: impact LENS NULL. Volume normalization flattens the signal (|Δmid| and volume co-scale on
  active bars: coherence Σnum/Σden ~equal across arms). Raw movement separates; impact ratio does not.
- Interpretation (discovery, weak-n): the impact transform does NOT earn MBP-10 complexity here; the
  thing distinguishing cuts from runners is how much price MOVES, not move-per-volume. Closes the
  impact channel for October. Does NOT touch the flow-LEVEL channel (early_flow_confirmation) which
  separates at entry. CI's overlap at n=40 — directional/consistency claim only, not a ranking.
