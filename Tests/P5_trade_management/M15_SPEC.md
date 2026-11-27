# M15_SPEC — FLOW-STATE CONDITIONED STALL (T-MG27)
STATUS: FROZEN BEFORE RUN | 2026-11-27 | Rule 2 + R-9
Basis: F-17 (his keeps carry OFI10 +831 above his exits at matched
duration AND profit, both months). Shape lesson from M12 (T-MG21):
book SNAPSHOT at the stall failed; this uses book MOTION - the
construction that actually separated. Cites F-11, F-16 (this is the
"new information" lane F-16 demands).

## MECHANIC (M15 = M7 with ONE conditional)
At each stall fire (60s without a new peak), compute trailing-30s
OFI10 signed with the position (from the per-second OFI series,
CKS construction, certified extractor lineage). If OFI10_30s >=
theta, DO NOT exit: reset the stall clock once per check and
continue (re-checks at each subsequent stall fire). The 480s cap,
stop and spike-capture are UNCHANGED and always bind. No book data
within 5s of the moment -> behave exactly as M7 (exit; counted).
Thetas, derivation-frozen: theta1 = 0 (any supportive flow);
theta2 = 125 (the pooled median OFI10 at HIS OWN exit moments,
tick-rounded from T-BK02: flow must exceed what typically
accompanies even his exits). Cells: CONTROL | th0 | th125.
Months: 2022-02 + 2025-10 ONLY (the depth-covered months).

## R-9 (abort on fail)
CONTROL reproduces the training pair exactly: 757 / +325.1
(+137.6/+187.5). Cells non-empty per month; counts reported:
stall checks, extensions granted, no-book fallbacks.

## VERDICT (mechanism-primary)
PRIMARY: twin-matched delta on changed trades > 0 pooled AND > 0 in
BOTH months. SECONDARY: cell pooled > +325.1 AND both months
positive. Both -> REGISTER TRAINING-ONLY, Tier-R (depth feed;
NOT Pine-portable; validation requires a future depth purchase -
stated now). Earners harmed reported.
Registry: T-MG27.

## STANDING ARCHITECTURE NOTE (J, 2026-11-27)
Two deployment tiers, recorded: Tier-P = Pine-portable strategies
(price+calendar only; G2-4 x M7). Tier-R = runner strategies
(depth feed via Rithmic R|API+ live / Databento MBP-10 historical;
the M15 line). Book dependencies never enter Tier-P.
