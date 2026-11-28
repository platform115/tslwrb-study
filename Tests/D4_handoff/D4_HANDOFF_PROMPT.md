# D4_HANDOFF_PROMPT — paste this to start the Pine conversation
(Attach alongside it: D4_PORT_SPEC.md, D4_CONSTANTS.md, the
vectors/ folder, pine_inputs_2025-10_levels.txt,
pine_inputs_2025-10_events.txt.)

---

You are implementing a fully specified, already-validated futures
trading strategy in **Pine Script v6** on TradingView. The research
is finished and frozen. Your job is **faithful implementation —
not improvement, not interpretation, not optimization.**

**The attached documents:**
- `D4_PORT_SPEC.md` — the complete rule book. The ONLY authority on
  rules.
- `D4_CONSTANTS.md` — every number, named. The ONLY authority on
  values. Your code must use these names.
- `vectors/` — golden vectors: the certified engine's exact output
  for three sessions (2025-10-13 ordinary, 2025-10-15 busy,
  2025-10-31 near-empty): structure values per minute, every
  signal/order, every trade with exit reason and P/L, plus the
  tolerance sheet (V_SUMMARY.md).
- `pine_inputs_2025-10_levels.txt` / `_events.txt` — the two
  paste-in input blocks covering the vector sessions.

**Ground rules — no exceptions:**
1. If anything is ambiguous, missing, or contradictory: **STOP and
   ask J.** Never fill a gap with a plausible assumption. Never
   invent, change, or tune a number — including to make a vector
   match.
2. Build a **strategy** (simulated fills only), Pine v6,
   1 contract, **1-second chart**, structure from 1-minute bars of
   the same symbol, sessions and times per spec section 1. The
   script header must state: spec version, symbol and roll setting
   used, data feed, and current stage.
3. Work **one stage at a time**. Stop at the end of every stage and
   wait for J. J runs TradingView (adds the script, pastes inputs,
   reads tables/plots) and pastes results back to you.
   - **S1 — scaffolding**: session handling (17:00 CT reset, RTH),
     parse both pasted input blocks, prove it by plotting/printing
     the day's levels and event windows back. Gate: J confirms the
     echo matches the .txt files.
   - **S2 — W20 bands** (spec 2a): plot band_lo/band_hi per 1m bar.
     Gate: match `v_structure_<sd>.csv` columns w20_lo/w20_hi.
   - **S3 — squeeze edges** (spec 2b): same, for sqz10/sqz30.
     Gate: match the sqz columns. This stage is the likeliest place
     for subtle divergence — treat every mismatched bar as a
     finding to explain, not noise.
   - **S4 — signals** (spec 3, 4a, 4b): detect crosses inside event
     windows, apply lockouts, both techniques, place orders. Gate:
     match `v_signals_<sd>.csv` within the tolerance sheet.
   - **S5 — fills**: stop-order fills and 300s expiries. Gate:
     fill/expire outcomes match per tolerance sheet.
   - **S6 — exits** (spec 5): the M7 state machine. Gate: match
     `v_trades_<sd>.csv` exit reasons and per-trade P/L per
     tolerance sheet.
   - **S7 — full replay**: all three sessions end-to-end; compare
     trade lists and session nets; write the divergence report
     (what differs, why, measured — never patched).
4. **Mismatch protocol:** report yours vs expected with your
   diagnosis (feed difference, bar difference, logic difference).
   If mismatches lean one direction systematically: stop — that is
   a finding for J, possibly a spec defect, and J relays it to the
   research side. The research side fixes specs; you never
   compensate in code.
5. Keep a LINEAGE comment block at the top of the script: spec
   version, stages passed with their vector results, open
   questions, every J decision with its date.
6. Forward paper phase (after S7, J's go): J pastes fresh weekly
   event times and daily levels (formats in the .txt files; the
   research side generates them). The strategy runs on the live 1s
   chart. Its trades are compared later against the research
   side's replay of the same days ("forward-parallel check") — so
   never adjust anything mid-week; divergence is information.

**Known honest divergences (do not "fix" these):** TradingView 1s
bars are trade-based, the research engine watched quote midpoints;
feeds differ slightly; TradingView's order emulator has its own
fill model. The vectors + tolerance sheet exist exactly to measure
this.

Begin with S1. End every reply with: current stage, gate result
(pass / fail / awaiting J), and open questions for J (or "none").
