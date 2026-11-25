# C AUDIT REPORT — SQUEEZE COVERAGE (T-IM53)
STATUS: CLOSED | 2026-11-26 | Spec: C_AUDIT_SPEC.md | shipped cells = W{10,30} q0.67 (spec's 15/30 corrected from code)

edge_absent trades found: 9

| W | q | covers (of 9) | ambient edge-within-5 rate |
|---|---|---|---|
| 10 | 0.5 | 1 | 36% |
| 10 (shipped) | 0.67 | 0 | 64% |
| 10 | 0.8 | 4 | 72% |
| 15 | 0.5 | 2 | 37% |
| 15 | 0.67 | 2 | 59% |
| 15 | 0.8 | 3 | 68% |
| 20 | 0.5 | 3 | 36% |
| 20 | 0.67 | 2 | 58% |
| 20 | 0.8 | 4 | 64% |
| 30 | 0.5 | 2 | 29% |
| 30 (shipped) | 0.67 | 0 | 54% |
| 30 | 0.8 | 2 | 58% |
| 45 | 0.5 | 1 | 29% |
| 45 | 0.67 | 1 | 44% |
| 45 | 0.8 | 2 | 47% |

Reading: a cell is only worth adopting if it covers several of the missed trades WITHOUT a much higher ambient rate than the shipped cells. Adoption = Strategy 4 revision = full B2->B4 re-run + fresh validation (J's call). Registry: T-IM53.
