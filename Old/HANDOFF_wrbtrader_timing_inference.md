# Handoff — wrbtrader trade-timing inference (entry + exit)

## Goal
Recover *mechanical, simple, deterministic* rules for **entry timing** and **exit/target** that produce trades in a similar spirit to wrbtrader's, tested on a chronological holdout. Not replicating his exact discretionary trades. Ignore sizing/commissions/costs.
- Scope note: the OHLCV phase took his entries as **given** and modeled only exits. The order-flow phase puts **entry timing on equal footing** with exits — order flow's best-documented use is marking the *start* of a move, so the cleaner signal may be on the entry side.

## Data on hand (1m OHLCV era)
- `tsl_episodes_clean.parquet` (~4,842 completed trades; 97% = 4,715 single entry/exit, used for analysis), `tsl_fills_clean.parquet`, `es_1m_front.parquet` (RTH), `wrb_1m.parquet` (106,003 WRBs; **reproduces exactly from `es_1m_front`**, so regenerable if not attached), `WRB_Definition.txt`, `README.md`.
- New (to be pulled): Databento **MBP-10**, dataset `GLBX.MDP3`, **whole sample month** per contract (Databento's request wizard makes 53 per-window requests impractical, so buy the full month and **window locally in the script**). ~92GB for Oct 2025 (full month). See "Aligning MBP-10" and "Hardware & local processing".
- NOTE: files do **not** carry across chats automatically — but the order-flow phase runs locally, so a new chat needs only this doc (see "Workflow & what the new chat needs").
- Assumption for this thread (user-set): trades happened as recorded; no censoring. (Chat 1 flagged censoring; parked.)

## Stated model — targets/exits (user)
- Target = "next WRB": wait for a WRB that **forms after entry**, directional (bullish for long / bearish for short); exit at/soon after its **close**. pt1/2/3 = 1st/2nd/3rd such. Mostly full exit at one pt, little scaling.
- Stop/early-exit = discretionary "price action unstable / not moving in my favour." The unknown.
- Entries: originally given; user now believes the right **entry timing** is also driven by "speed" (order flow), not OHLCV.
- User steers: exits imprecise ("soon after," not exact price); which pt chosen is discretionary on the "stability" read; decisions judged by *strength*, not a clock; **the strength signal is likely "speed" and likely NOT in OHLCV**.

## What we established (4,715 single-exit subset)
- **R0 (his actual exits):** total 23,052 pts, mean 4.89, win 76.7%, avg win 6.82, avg loss **-1.56**, worst **-11.25**. Build(<=2023) 10,473 / Test(2024-26) 12,579 — *improves* out-of-sample (robust).
- **Regimes by hold time:** fast 1-2 bar = 42% of trades, only 13% of edge (65% win); patient 6+ bar = 29% of trades, **67% of edge** (93% win, median +8.5, median MFE 10.75 vs MAE 1.0). Patient/WRB regime is essentially the whole edge. Regimes are *outcomes*, not entry-selectable.
- **WRB target is real in timing, not price:** exits don't sit at WRB close prices (~1-6%), but winners exit ~2x above chance near directional-WRB *bars*.
- **MAE:** losers sit through median 3.25 pts adverse (tail to 23) and exit on a bounce at ~-1.6 -> loss-cutting is *recovery-aware*; no fixed adverse ceiling.
- **Timestamp precision (measured):** entry/exit times are **second-resolution** (~1.8% on :00 = chance; all 60 second-values; e.g. 13:31:49, 13:34:26). Prior 1m analyses floored to the minute (fine there); **order-flow work must keep the seconds.** Treat each as decision-time +/- a small possible post-lag (recorded time may trail the fill by seconds).

## OHLCV mechanisms tested — all fail to reach R0's signature (77% win + ~-1.6 avg loss)
Exit rules on his actual entries (entry timing NOT assessed in this phase — it enters scope with order flow), chronological holdout:
- **R1** (exit at first WRB either dir): ~8,123 (~35% of R0), win 62%, avg loss -3.5, worst -51.
- **R2** (ride through directional WRBs, exit at first counter-direction WRB): ~8,673 (~38% of R0), captures winner *size* (avg win 6.54 ~ R0) but win 52%, median +0.25 (gives back small winners), avg loss -3.4, worst -80. **Best mechanical rule so far; the scaffold the order-flow refinement attaches to.**
- **Fixed stop on R2:** edge-neutral. Correction logged: prior "stop recovers ~half of R0" was a *hindsight cap*, not a tradeable stop — wrong.
- **A WHG-gate:** neutral. **B volume-gate / C velocity(body)-gate:** big *in-sample* totals that are **mirages** (collapse ~50% OOS, avg loss -13 to -16, worst -95 to -176) — delayed exits riding trends/losers, overfit.
- **Favorable-deceleration (stall) banking:** edge-neutral.

**Conclusion (committed):** management edge is **not mechanizable from 1m OHLCV** (tape *speed* is destroyed by 1-min aggregation). Bounded rule-out of ~7 pre-specified mechanisms, not proof no OHLCV rule exists.

## CORRECTION to earlier reasoning (read before trusting older notes)
An earlier plan framed order flow's "tens-of-seconds horizon" as a reason to expect a **null** at his ~3-min holds. **Category error** — conflated order flow's *prediction horizon* with the trade's *holding period*. Corrected: order flow is a **seconds-scale trigger** marking a move's *start* (entry) or *end* (exit); the move plays out over minutes; its duration is irrelevant to detecting the edge. Timing entries into moves is order flow's **best-documented** use. With second-resolution timestamps, this is genuinely testable. **Revised expectation: open question, entry-timing side well-grounded — NOT "likely null."** Remaining honest risks: (a) post-time lag (use a window, not exact-instant); (b) reversals/exits noisier to call than entries/initiations; (c) overfitting (holdout + short pre-committed feature list).

## Current decision — go external (order flow)
- Hypothesis: the strength/"speed" read is **order flow** — tape velocity (trade-arrival rate), cumulative delta (aggressor-signed volume), and possibly book imbalance/absorption — informing both **entry timing** and **exit**.
- Documented anchor: Cont, Kukanov & Stoikov (2010), order-flow imbalance ~ linear with short-horizon price change (used as a *move-initiation* signal, per the correction).
- **Buy: Databento `MBP-10`, windowed, 1 sample month** (then 1-2 months in a *different regime* before full history).
  - MBP-10 **includes the trades**, so one buy tests speed (embedded trades) *and* book signals (depth imbalance/absorption). Trades alone would rule on speed but leave book untested.
  - MBP-10 = L2/DOM = deepest level both human-readable and **live-reproducible**. MBO (L3) is over-engineering, not retail-live-reproducible.
  - Databento historical & live share identical schemas/code -> backtest deploys live unchanged. Data-only; production = Databento Live (or broker feed) for signal + broker API for execution. `Trades` is stateless live; MBP-10/MBO require maintaining a live book.

## Aligning MBP-10 with the ES + chatlog parquets
All UTC; align on **time**, **contract/roll**, **price scale**, then **verify** before features.
1. **Contract / roll (most error-prone).** His trades and `es_1m_front` use a **front-month continuous, unadjusted** series (real levels, gaps at rolls — README; mismatched rolls were the quarantine cause). MBP-10 is per-contract. Either request the explicit contract `es_1m_front` used per date, or request continuous `ES.c.0` and confirm the roll rule matches. Verify in step 4.
2. **Decode.** Via `databento` `.to_df()`, `ts_event`/`ts_recv` are UTC datetimes, prices decimals. Raw DBN: `ts_event` is int64 ns UTC (`pd.to_datetime(ts, utc=True)`); prices fixed-point, /1e9. ES tick = 0.25 -> prices must land on a 0.25 grid (scale check).
3. **Session.** MBP-10 is continuous; filter to the **same RTH definition** as `es_1m_front` (session == 'RTH').
4. **Verify FIRST (like README's price-in-bar check).** Resample MBP-10 *trades* to 1-min OHLCV (floor `ts_event` to minute, RTH) and reconcile O/H/L/C against `es_1m_front` on overlapping minutes. Match within tick -> aligned. Constant offset on some dates -> wrong contract/roll there; fix by selecting the matching contract. **Do not build features until this passes.**
5. **Join his trades.** Each `datetime_utc` is second-resolution UTC. Slice MBP-10 events in a window around it. Entry features use a **pre-entry lookback** (e.g. [t-30s, t], + a few sec after for post-lag) to avoid lookahead; exit features bracket the exit. Use `wrb_1m` (or regenerate) to mark the directional/counter-WRBs near each decision so order flow can be related to the WRB scaffold.
6. **Bar context** (MAE/MFE) from `es_1m_front` (or verified aggregated MBP-10).

## Pre-committed discipline (highest overfitting-risk phase)
- **Diagnostic before any rule.** First scripts: (a) confirm MBP-10's embedded trades complete vs a Trades view + the alignment verification (step 4); (b) the diagnostics below, each vs a **within-window null**. Build a rule only if a test clears.
- **Short feature list:** tape intensity + cumulative delta to start; add book OFI/absorption. No feature zoo.
- Chronological holdout; signals pre-specified from documented concepts; **a null result is an acceptable, money-saving end** -> if so, ship R2 (~38% of edge) + document discretion as irreducible.

## The diagnostics (plain terms) — entry AND exit
1. **ENTRY surge + does it predict move size? (strongest, best-grounded).** In ~30s before each entry: tape speed (trades/contracts per sec) + delta (net aggressor volume). (a) Is entry-moment flow anomalous vs random RTH timestamps? (b) **Money test:** does surge size predict subsequent favorable move (MFE)? Likely connects to the regime split — his big-move (patient, 67%-of-edge) entries may carry an order-flow signature the fast scalps lack -> an **entry filter/timing rule**.
2. **EXIT exhaustion/absorption (real but noisier).** At exits: delta divergence (new price extreme not confirmed by delta) and absorption (large resting size halts the move). Coincidence vs null; optionally relate to the counter-WRBs exits cluster near. Weaker prior — reversals harder than initiations.
3. **Held-vs-cut recovery-aware test (highest value, most speculative).** Split adverse-going trades into HELD-and-recovered vs CUT-for-loss; compare order flow *during the dip* (fast/high-delta/absorption-broken vs slow/low-volume drift). If flow separates them, it mechanizes the recovery-aware skill OHLCV couldn't capture.

## Immediate next action
1. Pull Databento `MBP-10`, dataset `GLBX.MDP3`, **the whole sample month** for the contract below. (Per-window requests were dropped — the wizard forces round-hour, manual per-window selection; impractical for 53 windows. So buy the full month; **windowing happens locally in the script**, not in the request.) ~92GB for Oct 2025.
   - **Month 1 (start here): October 2025 — contract `ESZ5` (Dec 2025).** Recent/representative microstructure, roll-free, n=92, 16 losers; powers entry (Test 1) and exit (Test 2), first read on Test 3. (Alt: Aug 2025, n=89/13, contract `ESU5` (Sep 2025).)
   - **Month 2 (after M1 validates): February 2022 — contract `ESH2` (Mar 2022).** Different regime (old era, smaller moves), roll-free, n=217, 60 losers; powers Test 3 (held-vs-cut) and tests transfer. Denser/pricier (2022 high-vol). (Alt: May 2022, n=204/55, contract `ESM2` (Jun 2022).)
   - Skip April 2025 for now (tariff-shock outlier, densest/priciest); save as a later stress-regime check. Pick months on n/era/roll-cleanliness, NOT on win rate/P&L.
   - Run `metadata.get_cost` (schema `mbp-10`, the contract, the full month) for exact $/bytes before buying. Whole-month is the practical unit given the wizard; the windowing that saves *processing* (not data cost) happens locally.
2. Claude writes deterministic local scripts (`databento` lib): (a) alignment/verification (Aligning step 4) + trades-completeness; (b) the diagnostics vs within-window null, keeping second-resolution timestamps + a +/- window for post-lag. User runs locally, pastes back summaries.
3. If a diagnostic clears -> Month 2 (transfer) -> rule build (entry-timing and/or exit refinement on the R2 scaffold) + holdout. If null -> stop, ship R2 + documented discretion.

## Workflow & what the new chat needs (data is local — too large to upload)
The order-flow phase runs **entirely on your machine**. Do **not** upload the big data anywhere. Loop:
1. Attach **this handoff doc** to the new chat (that's the carrier — not the gigabytes).
2. Claude writes deterministic scripts (`databento` lib); you run them in your project venv against your **local** parquets + the local MBP-10 pull.
3. You paste back the **summary outputs** (small tables/numbers — counts, win rates, null comparisons), not raw data. Claude interprets and writes the next script.
- Only files small enough to upload if an in-chat spot-check is ever needed: `tsl_episodes_clean.parquet` + `tsl_fills_clean.parquet` (~hundreds of KB). `es_1m_front`, `wrb_1m`, and MBP-10 stay local; `wrb_1m` is regenerable from `es_1m_front` anyway.
- First script to expect: the alignment/verification check (resample MBP-10 trades to 1m, reconcile against `es_1m_front`) — run it before anything else.

## Hardware & local processing (whole-month MBP-10 on an M1 Air, 8/16GB RAM)
The constraint is **RAM, not disk** — you cannot load a ~92GB month into pandas. Disk is just storage.
- **Storage:** external USB-C/Thunderbolt NVMe SSD, **~1TB** (Samsung T7/T9, Crucial X9/X10, SanDisk Extreme; ~$80-130). One month at a time also fits 512GB, but 1TB gives headroom for two months + the DBN-and-parquet copies + outputs. Internal 256GB M1 SSD is too small for 92GB. M1 Air USB-4/TB3 handles ~1GB/s fine.
- **Process by streaming, never whole-load.** Recommended pipeline:
  1. **Reduce first.** One streaming pass over the month (iterate DBN records, or convert DBN->parquet then query with **DuckDB** out-of-core) that keeps only RTH + the union of per-trade windows (computed from his timestamps, `[entry-15min, exit+~2min]`), writing a compact windowed parquet — roughly **15-25GB of just-the-windows** (exact size depends on activity; far below the ~92GB month). This is the windowing we wanted, done locally after buying the whole month.
  2. **Analyze the small file.** All diagnostics run on the reduced windowed parquet, which fits comfortably in RAM / chunks easily.
  - Never `.to_df()` the full month. Use the `databento` DBN iterator (record-by-record) or DuckDB over exported parquet; peak RAM = one window/chunk.
- **Cloud:** unnecessary for the 1-2 sample months (external SSD + streaming on the M1 is fine). Revisit only at full-history scale (many months -> hundreds of GB): a single rented VM (Hetzner cheap; AWS/GCP for ecosystem) with ~32GB RAM + SSD volume, batch-download DBN, run scripts over SSH; object storage (S3/GCS/B2) for raw files. Do NOT provision before the diagnostic clears.

## Structure & conventions (project: `tslwrb-study`)
Separate sibling dir to `es-trading-agent-v3` (research/EDA discipline, not the backtester's write-once-spec discipline). If a rule emerges, **port it into the backtester as a YAML spec** — one-way export, not a merge.
- **Repo holds:** numbered scripts, small summary outputs, docs, a config pointing at the SSD path. **Gitignore the big data** — raw `.dbn` and the windowed parquet live on the external SSD, never committed.
- **Numbered pipeline** (mirrors the backtester's `01`-`06`): e.g. `01_cost_check.py`, `02_reduce_to_windows.py`, `03_align_verify.py`, `04_diag_entry_surge.py`, ... — execution order legible from filenames.
- **Tag every data + result file with contract + month:** `mbp10_ESZ5_2025-10_windowed.parquet`, `03_align_ESZ5_2025-10.md`. Adding Feb 2022 later = new files tagged `ESH2_2022-02`, no collisions, no restructure. (This one habit is the "scalable" part.)
- **Reproducibility:** a config file (contract, month, schema, SSD path, pinned `databento` version) + each result stamped with git commit and data provenance (contract/month/window), so every number traces back.
- **Determinism rule carries over:** scripts compute, the LLM doesn't; params explicit; flag decisions for sign-off rather than defaulting.
- **Commit the small summary outputs** (the tables pasted back) — tiny, auditable, and the durable record if SSD data is deleted to reclaim space.
- A `CLAUDE.md` in the project root encodes the above so every Code session auto-applies it (don't re-brief each chat).

## Open / parked
- Scaled pt1/2/3 multi-exit episodes (~3%) still excluded; where ride-vs-bank is directly observable — fold in before finalizing any rule.
- ES/NQ lead-lag: lighter "external" alternative (1m only, no tick infra) if MBP-10 lift is deferred.
- Censoring question from Chat 1: parked.
