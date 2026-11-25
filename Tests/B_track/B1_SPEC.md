# B1 SPEC — ANATOMY OF THE G2 TARGET (pre-registered; committed before run)
STATUS: FROZEN | 2026-11-25 | Track B step B1 | Registry: T-IM47
Target (B0, J confirmed): G2 = squeeze context (Path C), entry 5-45 min
after a scheduled release. 62 trades, training months. Validation
months untouched.

## QUESTIONS, IN ORDER (each answered with distributions, not averages)
1. WORTH REPLICATING? His realized P&L on the 62: net points, win rate,
   avg win/loss, worst trade, per month. If the group loses for HIM,
   Track B stops here and the ranking is revisited - stated now.
2. ENTRY ANATOMY - what the moment looks like:
   - the trigger: nearest interacted squeeze-band edge; displacement of
     his fill past it (the entry-price rule, G2-specific);
   - the clock: minutes since the release; which events;
   - the tape: the A2 intensity dial and the stacking conditions
     (movement, persistence, flow, signal) at his entries;
   - direction: his side vs the break side of the band.
3. OUTCOME ANATOMY (labels only - never features):
   - MAE / MFE / hold distributions (1-second resolution, from the
     audited ground truth);
   - time-to-peak: how quickly the move he catches happens (the
     "moves quickly in our favor" clause of the program goal);
   - scratch-vs-runner split: his own management on this group.
4. THE TRIPLE-BARRIER FRAME (Lopez de Prado 2018 ch.3): barriers set
   from HIS outcome quantiles, as RANGES per J's standing rule -
   profit barrier candidates = his MFE q25/q50/q75; stop candidates =
   his MAE q50/q75/q90; time barrier candidates = his hold q50/q75/q90.
   These define the LABEL for B2's meta-filter (did a candidate entry
   reach profit before stop/time). No barrier is chosen here - B2
   tests the grid.

## METHOD NOTES
Join key = (month, entry second) - episode_id is known non-unique
(T-IM46 defect). Squeeze edges via the certified resolver at the entry
second. All entry-anatomy fields are knowable at entry; outcome fields
are labeled y and quarantined from feature use (R-1 discipline).

## OUTPUT
B1 report (plain language, distributions); barrier-grid table handed to
B2. Review gate: J sees the anatomy before B2 designs the entry rule.
