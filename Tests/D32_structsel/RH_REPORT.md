# RH REPORT — R-1 TRUNCATION HARNESS ON FL-RWY (T-RH01)
STATUS: CLOSED | 2026-11-28 | Spec: RH_SPEC.md (frozen first) | P0 harness rules (T-EN99/100 lineage)

- production comparisons: 240 (150 touches incl. banked-value re-derivation + 90 fills, six months, quiet + window)
- mismatches: 14
  - ('touch', '2022-02', 1645734874, 3.0, 70.75)
  - ('touch', '2022-02', 1644503460, 3.25, 9.25)
  - ('touch', '2022-02', 1644850903, 1.5, 2.25)
  - ('touch', '2022-02', 1644250106, 1.25, 0.75)
  - ('touch', '2025-10', 1760724325, 1.25, 53.75)
  - ('touch', '2025-10', 1760451348, 1.25, 1.5)
  - ('touch', '2025-10', 1761832215, 3.75, 6.0)
  - ('touch', '2025-10', 1760711063, 1.25, 2.5)
  - ('touch', '2025-10', 1760103108, 1.25, 17.25)
  - ('touch', '2025-10', 1759326023, 2.0, 7.5)
  - ('touch', '2025-10', 1760632223, 6.25, 23.75)
  - ('cand', '2023-05', 1683037947, 1.75, inf)
  - ('cand', '2025-10', 1761678869, 1.25, 1.0)
  - ('cand', '2025-10', 1759330020, 0.75, 1.25)
- poison arm (end-of-day structures): 28/60 mismatched (sensitivity requires >= 1)

## VERDICT
- zero production mismatches: FAIL
- poison sensitivity: PASS
OVERALL: FAIL - FL-RWY systems frozen pending anatomy

Registry: T-RH01.
