# SPEC 06-6 — MAE reproduction (adverse-excursion as exit signal "S2")
Status: COMPLETE. In-sample October, holdout-pending. Not a validated edge.

## Purpose
Reproduce, on price alone, whether wrbtrader's cuts look like an adverse-excursion (MAE) stop, and
check robustness across measurement instrument (per-second mid vs 1m bar extreme) and grouping
(clean loss-based vs pt1).

## Feature
adverse / MAE = max excursion AGAINST entry over [entry, exit], in points:
  long:  entry_price − lowest_price_since_entry
  short: highest_price_since_entry − entry_price
Measured two ways: per-second MID (fine timing, under-reads extreme) and 1m BAR low/high (true extreme,
minute timing). Truth is bracketed between the two.

## Populations
- clean = losing_trade(16) vs reached_target(47)
- pt1   = failed_trades(40) vs target_reached(52)

## Design
Cut-time-matched separation; two-sided AUC + cluster-bootstrap CI; firing floor >=8.

## Result (in-sample)
- Loser MAE separates from reached. Per-second mid: loser median ~2.5 pt vs reached pre-pt1 ~0.12.
- bars + clean: separation SURVIVES true extremes (loser MAE median ~3.0 vs reached ~1.0). Winner-kill:
  a stop at ~2.5 pt clips ~21% of eventual winners; at ~3.0 pt ~13% (true bar-extreme prices).
- mid + pt1: separation COLLAPSES on 52/40 (cut median ~0.19 vs spared ~0.06) — confirms the loss-based
  relabel is necessary; pt1 grouping dilutes exit-signal separation.
- No single threshold gives both high sensitivity AND specificity (loser/winner MAE overlap). Cut timing
  is BIMODAL: some losers cut sharply at ~3 pt (gap ~2 s), others cut early at ~1.5–2 pt after holding
  ~15–20 s. So S2 is a reactive stop, not one clean level.

## Files
- mae_reproduction_engine.py  — CANONICAL. Parametrized: --instrument {mid,bars} --grouping {clean,pt1}.
- test_06-6_mae_reproduction.py — original one-off, SUPERSEDED by the engine; kept for provenance.

## Reproduce (06-6_reproduction/, SSD mounted for --instrument mid)
  python3 mae_reproduction_engine.py --config ../../../config.toml --wrb ../../../wrb_1m.parquet \
    --instrument bars --grouping clean

## Caveats
16 losers, October, in-sample. Winner-kill %s are the cost side of any stop level; choose knowing them.
Holdout-pending.
