# A3b SPEC — GROUPING RE-RUN WITH CORRECTED ENCODINGS (pre-registered)
STATUS: FROZEN | 2026-11-25 | Track A step A3 refinement | Registry: T-IM45
One authorized refinement of T-IM44, spec committed before the run.
J's corrections honored: the 3 early trades are PRE-OPEN weekday trades
(7:00-8:26 CT), kept with fixed encoding, not excluded; the 14 Monday
trades are ordinary-hours trades whose news clock spans a weekend.

## CHANGES FROM A3 (each one stated, nothing silent)
1. mins_open -> mins_vs_open: minutes relative to the 8:30 CT bell,
   NEGATIVE before it (-4, -29, -90 for the three pre-open trades).
   Knowable at the moment; replaces the sentinel that made them outliers.
2. kme_mins_since capped at 480 min FOR THE CLUSTERING DISTANCE ONLY.
   The raw value stays in the table; event-level memory lives in the
   Key-KME-zone objects (S4: weeks-to-months), which are untouched.
3. All standardized features winsorized at +/-3 IQR before Ward -
   distance computation only.
4. All 307 trades kept.
Everything else identical to A3_SPEC.md: same 15 features (mins_vs_open
replacing mins_open), robust standardization, Ward, k 2-8, silhouette +
bootstrap-Jaccard stability (>=0.6 rule), ARI vs the hand taxonomy.

## TAXONOMY PATHS (J asked for expert options; all three run)
A. COMBINATION TABLE (ground truth, no ordering bias): the exact
   structure-context vector (reaction x squeeze x gap x shadow) per
   trade, with counts and the same vector's rate at matched nulls -
   shows which COMBINATIONS are over-represented, no priority rule.
B. REVERSED-PRIORITY SENSITIVITY: reassign primary context checking
   reaction FIRST (then squeeze, zones). How many trades change label =
   how much of the 73% squeeze share is assignment order.
C. ENRICHMENT-BASED PRIMARY (feeds A4): primary = the active family
   RAREST at matched nulls (most surprising to see). Deterministic,
   no ordering choice.

## OUTPUT
Same tables as A3 + the three taxonomy views. Review gate: J picks the
taxonomy view the program standardizes on.
