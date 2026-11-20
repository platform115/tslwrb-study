# S6 PLAN — HIS ENTRIES vs VALIDATED STRUCTURES (for review before any run)
> Goal (charter): "some percent of his entries are caught by a system, or
> more than one system, each day" — on the ONE training month (2025-10)
> until a good portion of his trades is selected. One-rule-for-all is NOT
> expected: he runs at least two systems (Key-KME-Zone trades; VTR trades).

## S6.0 PREREQUISITE — truncation-harness extension for the resolver
The standing gate (T-EN101) covers entry/signal scripts; the resolver's
generator outputs were ≤t BY CONSTRUCTION but never mechanically checked.
Before any S6 number counts: extend the harness — at sampled seconds,
recompute the resolver state from truncated data; any difference = fail.
REVIEW GATE: harness passes.

## S6.1 Structure presence at his entries vs matched null
For each of his 92 first entries (2025-10): resolver state at the entry
second — which objects (kind, role edge, direction) sit within each kind's
recommended tolerance. Null: ambient seconds matched by session and
time-of-day band. Deliverable: per-kind over-representation table (his
entries vs null), split long/short and by p6_1 momentum type.
REVIEW GATE before S6.2.

## S6.2 Signature conditioning
Cross the over-represented structures with: entry side vs role edge (long
at S-type edges?), KME window, tape state (battery features at the entry).
Deliverable: the joint signatures that describe his entry moments, each
with counts, never fitted thresholds. REVIEW GATE.

## S6.3 PRE-REGISTERED candidate selectors (no fishing)
Declared now, before any S6.1 results are seen:
  SEL-A: price within 1 pt of the most-recent reaction level — the S5b
         UNION (5m swing N=2 OR pct-zigzag 0.08%) — side matching the
         trade direction (reaction-level system).
  SEL-B: price within 1 pt of an unfilled hidden-gap edge, direction
         matched (gap/zone system; 5m gaps within 45 min of a KME, else 1m).
  SEL-C: price at the contraction/tight-range band edge (S5b: W=10
         q=0.67 for contraction, W=30 q=0.67 for tight range), role
         matched. Carries the weakest-kind flag.
  SEL-D: price within 3 pts of a STATED-price Key-zone level (prior
         mentions only; implied lists failed in S5b and are excluded).
Metrics per selector, per day: catch rate of HIS entries; qualifying-
moment volume (how often it fires with nobody there — attention realism);
catch share of the UNION; overlap matrix between selectors.
Stopping rule: selectors are scored once; one refinement round is allowed
only for a selector whose catch is below 20%, and the refinement must be
drawn from S6.1/S6.2 evidence, not from scanning the entry list.
REVIEW GATE.

## S6.4 Catch accounting + second-month decision
Daily table: entries caught by >=1 selector / by >=2 / uncaught, with the
uncaught entries listed verbatim for the next program cycle. Only after
review does any second month open (per standing directive).

## Explicitly OUT of S6 scope
P&L of selectors (that is strategy work, after selection passes review);
non-ES structures; VTR definition (parked; SEL-B/C may catch VTR-like
trades incidentally, which S6.4 will show).

## Honest risks, stated up front
n=92 entries; presence rates at band objects are base-rate heavy (the S3
fair-null discipline continues: every rate ships with its matched null);
selector multiplicity is capped by pre-registration above.
