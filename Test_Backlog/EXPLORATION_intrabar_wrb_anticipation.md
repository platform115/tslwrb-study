# Exploration Brief — Intrabar WRB Anticipation via Order Flow ("faster WRB detector")
Discovery-phase brief to start in an independent chat. That chat has CURRENT_STATE.md (relies on it
for: bar OPEN-stamping, WRB completes at ts_event+60s, MBP-10 schema, side=="B"=buy/sign_mult=+1,
size uint32→int64, ESZ5 front, WRB pt1 definition). "faster WRB detector" / "intrabar WRB
anticipation" are descriptive project labels, not established terms.

## Where this came from
Test 01 (favorable_aggression) found that early favorable aggression separates runners from
non-runners ONLY through coupling with an early same-direction WRB (matched-time EXCL-22 AUC ≈ 0.55,
≈chance; INCL-22 0.67). So as a *predictive* feature beyond the WRB, it's redundant. The one
non-redundant angle left is TIMING: a 1m WRB is only confirmed at bar close (up to 60s latency);
order flow during the forming minute might confirm the same-direction impulse earlier.

## Scope (read before starting)
- This is an ENTRY / CONVICTION line (faster confirmation a trade is working). It is NOT the
  project's exit / loss-reduction / non-runner spine. Keep it labelled as such.
- DISCOVERY only: does a usable lead-time signal exist? Validation (P&L impact, holdout, execution
  realism) is a separate later phase. Do not conflate.

## The question (precise)
Q1. Partway through a forming 1m bar (at offset t < 60s), can order flow + price-so-far estimate
    whether the bar will CLOSE as a WRB (and its direction), earlier than the close?
Q2 (the one that matters). Does order flow add anticipation BEYOND intrabar body-so-far? If price has
    already printed a large body by t, "it's a WRB" is mostly a price fact, not a flow edge. The real
    test is incremental lift of flow over the price-only baseline.

## Honest prior (do not start assuming a win)
- delta and price move are ~0.76 correlated over these windows → flow's *lead* over price may be
  small. Plausible outcomes range from "a few seconds of latency saved" to "no lead beyond price."
- "Useful" is unproven until lead-time is measured against a price-only baseline.

## Data & ground truth
- Ground-truth WRB labels (+direction): wrb_1m.parquet, or recompute per WRB_Definition.txt §1
  (body[i] > each of prior 3 bodies). Decide which in-chat (single-source discipline).
- Intrabar flow: MBP-10 windowed parquet — trade prints (action=="T") have sub-second ts_event, so
  cumulative signed delta is computable at any offset t into the minute.
- 1m bars / body context: es_1m_front.parquet.
- Causal rule: at offset t use only data with ts_event ≤ bar_open + t. No bar-close info.

## Candidate measurements (documented methods only — no invented features)
- Intrabar cumulative signed delta / signed aggressor volume at t (order-flow trading; Lee & Ready
  1991 sign classification).
- Order Flow Imbalance (Cont, Kukanov & Stoikov, 2014) — book-update based.
- Aggressor imbalance ratio (buy vol / total) at t.
- PRICE-ONLY BASELINE to beat: intrabar body-so-far = (price_at_t − open). Flow must beat this.

## Suggested diagnostic (discovery, not a locked rule)
1. Universe: choose the bar set (e.g., all RTH 1m bars, or bars near entries) — decide in-chat.
2. Label each bar: same-direction WRB at close (from ground truth) vs not.
3. At offsets t ∈ {a small pre-registered set, e.g. 15/30/45s}, compute body-so-far and the flow
   feature(s) using only data ≤ open+t.
4. Measure: (a) how early a WRB is callable at acceptable precision/recall vs base rate; (b) AUC of
   body-so-far ALONE vs body-so-far + flow — the delta in AUC is the only thing that justifies "flow
   adds a lead". Pre-register; avoid offset/feature sweeping (multiple-testing; Bailey & López de
   Prado 2014). Diagnostic before any rule.

## Confounds / pitfalls to control
- Redundancy: flow correlated with body-so-far; report incremental lift, not raw flow AUC.
- Causality: strictly ≤ open+t; the WRB definition is bar-close (forward-looking) — labels only.
- Base rate: same-direction WRBs are a minority of bars; precision must beat that base rate.
- Session edges: thin 08:00–08:30 CT pre-cash-open book; roll-day bodies; maintenance gaps.
- This labels on a close-defined event → fine for discovery, but a deployable detector needs a
  real-time-decidable trigger, resolved at validation.

## Significance bar (state before looking)
Worth carrying forward only if, at some t < 60s, flow gives a meaningful AUC lift OVER body-so-far
AND the implied lead-time is large enough to matter for the actual trading workflow. If flow adds
no lift beyond price, the only value is price-path latency alone → likely not worth a feature.

## Open questions to resolve in-chat (no assumptions)
- Ground-truth source: wrb_1m vs recompute?
- Universe of bars and the offset set.
- Concrete "lead-time that matters" threshold tied to the live workflow.
