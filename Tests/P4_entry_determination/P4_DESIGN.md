# P4 — Entry Determination: design record
**Status:** active · discovery on Oct-2025 (ESZ5) + Feb-2022 (ESH2) · updated 2026-11-14

Plain-language terms used in this phase:
- **signal** — a completed 1-minute WRB (per WRB_Definition.txt)
- **zone** — an unfilled WRB Hidden Gap (WHG) that no bar has fully traded through yet
- **news event / KME** — a scheduled economic release from the committed calendar
  (`Data/inputs/kme_calendar.parquet`); "event size" = its measured typical market move
  (`kme_event_impact.csv`, median ticks moved from 1 min before to 5 min after release)
- **at his desk** — the window from 60 minutes before his first trade of the day to his
  last exit of the day (user-confirmed: he was usually at the desk 30–60 min before trading)
- **passed on** — a signal during his desk window while he was not in a trade

## Decisions on record (2026-11-14, user-approved)
1. **Desk window: 60 min before first trade** is the primary definition; 30 min is the
   cross-check. Basis: user's direct statement, not inference. Counts barely differ
   (720 vs 769 vs 797 free signals in Oct), so this choice cannot drive results.
2. **Standing caveat — "passed on" includes "possibly away".** Some skipped signals are
   absences (stepped away), not decisions. This dilutes skipped-side patterns; it cannot
   fabricate them. A stricter "definitely seen" variant (signals close in time to his
   actual order activity) is available later if needed.
3. **News importance — three-width test (approach A), user's reading leads.** The impact
   ranking showed nearly every scheduled event moves the market well beyond quiet minutes
   (user: "most if not all should be considered important" — matching Perry's own wording).
   So probes test news-proximity at three widths, side by side:
   ALL timestamped events · events ≥20 ticks median move · the biggest cluster ≥45 ticks
   (jobs/CPI/Fed). Widths were chosen after seeing the ranking — recorded as such; testing
   several widths side by side is the control for that.
   Approach C stays open: if Perry's material names specific events, that list becomes a
   fourth width. (His material is hit-and-miss on this — no dependency.)
4. **Sample for discovery:** the two months above only (both fully quality-gated). The
   full 5-year history (4,842 trades) is reserved for later validation and is UNEVEN —
   1,710 trades in 2022 vs 398 in 2023 — so validation must not assume his behavior was
   constant across years.

## Order of work
P4.2 entry characterization (descriptive — this folder's `p4_2_entry_context.py`)
→ P4.3 lock the taken-vs-skipped definitions from its output (pre-registration checkpoint)
→ P4.4 probes (one registry row each; news-width grid per decision 3)
→ P4.5 entry-rule synthesis → validation on reserved years → P&L test in the backtester.

## Open items
- **MUST RECONCILE before P4.3 locks anything:** this script finds ~61-64% of entries
  INSIDE a live zone; the October zone work (probe_whg_arrival, SPEC_06-10) reported
  only ~32-42% inside-or-near on the same months. Two implementations of "live zone at
  entry" disagree by roughly 2x. Diff the two scripts, find the definitional difference,
  and decide which is right - neither number is usable until then.
- Perry-named event list (approach C) — pending user finding it in source material.
- "Definitely seen" strict variant of the skipped label — build only if needed.
- Zone tables (`whg_*_2025-10/2022-02.parquet`) are derived files present in the working
  tree but not in git (parquet rule); regenerate with `06-10_whg_fill/build_whg_series.py`.
